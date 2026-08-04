"""Progress and resource reporting for long-running steps in the Latch Plots portal.

The portal shows no progress indicator for a running cell, so a step that takes hours is
indistinguishable from one that has hung. This module makes a running step observable, and
— more importantly — leaves evidence behind when a run is aborted.

Three channels, because the live ones are not guaranteed:

* **the Latch logs widget.** Create ``w_logs_display()`` + ``submit_widget_state()`` in the
  cell before the monitored block and it renders the stream live. Per ``latch-plots-ui``,
  this — not bare ``print`` — is the supported way to show progress in the portal.
* **stdout and the ``takara.monitor`` logger**, flushed on every line. Which of the two the
  logs widget binds to is undocumented, so both are written.
* **an on-disk log**, appended, flushed and fsynced on every line. Always works, and
  survives an abort — after killing a run you can still read exactly how far it got and
  what the pod was doing. This is the channel to rely on.

A background heartbeat thread samples every ``interval`` seconds, so you get a pulse even
while a single opaque call (a matrix copy, an upload) is running with nothing to report.

The sampled counters are chosen to discriminate between the three things that can make a
step take hours when the arithmetic takes seconds:

===============================  ==========================================
observation                      diagnosis
===============================  ==========================================
``cpu`` high, memory steady      genuinely computing
``cpu`` low, ``swap`` climbing   thrashing — the pod is out of RAM
``cpu`` low, ``net_tx`` climbing uploading — a ``sync_to`` H5AD serialize
``cpu`` low, nothing moving      blocked on a lock or a remote call
===============================  ==========================================

Usage::

    from takara.monitor import monitor

    with monitor("background removal") as mon:
        result = remove_background(adata, kit_type=KitType.TEN_BY_TEN, progress=mon.phase)

and, from any later cell (including after an abort)::

    from takara.monitor import tail
    print(tail())
"""

from __future__ import annotations

import logging
import os
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

try:
    import psutil
except ImportError:  # pragma: no cover - psutil is present on Latch Plots pods
    psutil = None

__all__ = ["monitor", "RunMonitor", "tail", "log_path", "DEFAULT_LOG"]

DEFAULT_LOG = Path(os.environ.get("TAKARA_MONITOR_LOG", "/tmp/takara_progress.log"))

# Latch's w_logs_display renders the cell's log stream. Which stream it binds to (stdout,
# or the logging handlers) is not documented, so emit to both and let the widget pick.
_log = logging.getLogger("takara.monitor")

# Heartbeats below this are noise; a step worth monitoring runs for minutes.
_MIN_INTERVAL = 1.0


def log_path() -> Path:
    """Where :func:`monitor` writes by default. Override with ``$TAKARA_MONITOR_LOG``."""
    return DEFAULT_LOG


def tail(n: int = 60, path: Path | str | None = None) -> str:
    """Last ``n`` lines of the monitor log.

    Call this from a fresh cell after aborting a run — the log is on disk, so it is
    readable even though the kernel that wrote it is gone.
    """
    p = Path(path) if path is not None else DEFAULT_LOG
    if not p.exists():
        return f"(no monitor log at {p} — was the step run inside `with monitor(...)`?)"
    lines = p.read_text(errors="replace").splitlines()
    return "\n".join(lines[-n:])


def _fmt_bytes(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


@dataclass
class _Sample:
    t: float
    rss: int = 0
    avail: int = 0
    cpu: float = 0.0
    swap_in: int = 0
    swap_out: int = 0
    disk_r: int = 0
    disk_w: int = 0
    net_tx: int = 0
    net_rx: int = 0


@dataclass
class _PhaseRecord:
    name: str
    start: float
    end: float | None = None
    peak_rss: int = 0
    min_avail: int = 1 << 62
    swap_out: int = 0
    net_tx: int = 0
    cpu_samples: list[float] = field(default_factory=list)

    @property
    def duration(self) -> float:
        return (self.end if self.end is not None else time.monotonic()) - self.start

    @property
    def mean_cpu(self) -> float:
        return sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0.0


class RunMonitor:
    """Heartbeat + phase timer. Prefer the :func:`monitor` context manager."""

    def __init__(
        self,
        label: str,
        interval: float = 15.0,
        path: Path | str | None = None,
        echo: bool = True,
        sink: Callable[[str], None] | None = None,
    ) -> None:
        self.label = label
        self.interval = max(float(interval), _MIN_INTERVAL)
        self.path = Path(path) if path is not None else DEFAULT_LOG
        self.echo = echo
        self.sink = sink

        self._t0 = time.monotonic()
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._fh = None
        self._proc = psutil.Process() if psutil is not None else None
        self._base: _Sample | None = None
        self._last: _Sample | None = None
        self.phases: list[_PhaseRecord] = []

    # -- sampling ---------------------------------------------------------------

    def _sample(self) -> _Sample:
        s = _Sample(t=time.monotonic())
        if psutil is None:
            return s
        try:
            s.rss = self._proc.memory_info().rss
            vm = psutil.virtual_memory()
            s.avail = vm.available
            # interval=None -> non-blocking, measured since the previous call
            s.cpu = self._proc.cpu_percent(interval=None)
            sw = psutil.swap_memory()
            s.swap_in, s.swap_out = sw.sin, sw.sout
        except Exception:
            pass
        try:
            io = self._proc.io_counters()
            s.disk_r, s.disk_w = io.read_bytes, io.write_bytes
        except Exception:
            pass  # not available on macOS, and needs privileges in some containers
        try:
            net = psutil.net_io_counters()
            s.net_tx, s.net_rx = net.bytes_sent, net.bytes_recv
        except Exception:
            pass
        return s

    def _rates(self, cur: _Sample) -> str:
        """Per-second deltas against the previous sample, plus absolute levels."""
        if psutil is None:
            return "(psutil unavailable — timing only)"
        prev = self._last or self._base or cur
        dt = max(cur.t - prev.t, 1e-6)

        def rate(a: int, b: int) -> float:
            return max(a - b, 0) / dt

        parts = [
            f"rss={_fmt_bytes(cur.rss)}",
            f"avail={_fmt_bytes(cur.avail)}",
            f"cpu={cur.cpu:.0f}%",
        ]
        swap_rate = rate(cur.swap_out, prev.swap_out) + rate(cur.swap_in, prev.swap_in)
        parts.append(f"swap={_fmt_bytes(swap_rate)}/s")
        if cur.disk_r or cur.disk_w:
            parts.append(
                f"disk_r={_fmt_bytes(rate(cur.disk_r, prev.disk_r))}/s "
                f"disk_w={_fmt_bytes(rate(cur.disk_w, prev.disk_w))}/s"
            )
        if cur.net_tx or cur.net_rx:
            parts.append(f"net_tx={_fmt_bytes(rate(cur.net_tx, prev.net_tx))}/s")
        return " ".join(parts)

    # -- output -----------------------------------------------------------------

    def _write(self, kind: str, msg: str) -> None:
        line = (
            f"{time.strftime('%H:%M:%S')} [{self.label} +{time.monotonic() - self._t0:7.1f}s] "
            f"{kind:9s} {msg}"
        )
        with self._lock:
            if self._fh is not None:
                try:
                    self._fh.write(line + "\n")
                    self._fh.flush()
                    os.fsync(self._fh.fileno())
                except Exception:
                    pass
            if self.echo:
                print(line, flush=True)
                # Latch's stdout capture may buffer independently of Python's.
                try:
                    sys.stdout.flush()
                except Exception:
                    pass
                try:
                    _log.info(line)
                except Exception:
                    pass
            if self.sink is not None:
                try:
                    self.sink(line)
                except Exception:
                    pass

    # -- public API -------------------------------------------------------------

    def phase(self, name: str) -> None:
        """Mark the start of a new phase. Pass this as ``progress=`` to a step function."""
        # Step functions format their own "[fn +1.2s] msg" prefix so that plain
        # `progress=print` is useful on its own. We already stamp every line, so drop it.
        if name.startswith("[") and "] " in name:
            name = name.split("] ", 1)[1]
        now = time.monotonic()
        cur = self._sample()
        # Fold this sample into the outgoing phase before closing it, so a phase that
        # ends between two heartbeats still reports a CPU reading instead of 0%.
        self._accumulate(cur)
        if self.phases and self.phases[-1].end is None:
            prev = self.phases[-1]
            prev.end = now
            self._write(
                "PHASE-END",
                f"{prev.name!r} took {prev.duration:.1f}s "
                f"(mean cpu {prev.mean_cpu:.0f}%, peak rss {_fmt_bytes(prev.peak_rss)})",
            )
        self.phases.append(_PhaseRecord(name=name, start=now, peak_rss=cur.rss))
        self._write("PHASE", f"{name}  |  {self._rates(cur)}")
        self._last = cur

    def note(self, msg: str) -> None:
        """Log a one-off message without starting a phase."""
        self._write("NOTE", msg)

    def _accumulate(self, cur: _Sample) -> None:
        if not self.phases or self.phases[-1].end is not None:
            return
        p = self.phases[-1]
        p.peak_rss = max(p.peak_rss, cur.rss)
        if cur.avail:
            p.min_avail = min(p.min_avail, cur.avail)
        p.cpu_samples.append(cur.cpu)
        prev = self._last or self._base
        if prev is not None:
            p.swap_out += max(cur.swap_out - prev.swap_out, 0)
            p.net_tx += max(cur.net_tx - prev.net_tx, 0)

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            cur = self._sample()
            self._accumulate(cur)
            phase = self.phases[-1].name if self.phases else "(start)"
            self._write("HEARTBEAT", f"in {phase!r}  |  {self._rates(cur)}")
            self._last = cur

    def start(self) -> RunMonitor:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._fh = self.path.open("a", buffering=1)
        except Exception:
            self._fh = None
        if self._proc is not None:
            self._proc.cpu_percent(interval=None)  # prime the CPU delta
        self._base = self._sample()
        self._last = self._base
        # Stamp the running build into every log. A timing run against a stale deployed
        # copy is worse than no run at all, because it looks like evidence. Imported
        # lazily: takara/__init__ imports this module.
        try:
            from takara import describe

            self._write("BUILD", describe())
        except Exception:
            self._write("BUILD", "(takara build id unavailable)")
        self._write("START", f"log={self.path}  |  {self._rates(self._base)}")
        self._thread = threading.Thread(
            target=self._run, name=f"takara-monitor:{self.label}", daemon=True
        )
        self._thread.start()
        return self

    def stop(self, error: BaseException | None = None) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=self.interval + 2)
        now = time.monotonic()
        cur = self._sample()
        self._accumulate(cur)
        if self.phases and self.phases[-1].end is None:
            p = self.phases[-1]
            p.end = now
            self._write(
                "PHASE-END",
                f"{p.name!r} took {p.duration:.1f}s "
                f"(mean cpu {p.mean_cpu:.0f}%, peak rss {_fmt_bytes(p.peak_rss)})",
            )
        for line in self.summary(error).splitlines():
            self._write("SUMMARY", line)
        with self._lock:
            if self._fh is not None:
                try:
                    self._fh.close()
                except Exception:
                    pass
                self._fh = None

    def summary(self, error: BaseException | None = None) -> str:
        """Per-phase table plus a one-line reading of what the pod was bound by."""
        total = time.monotonic() - self._t0
        rows = [f"{self.label}: {'FAILED' if error else 'done'} in {total:.1f}s"]
        if error is not None:
            rows.append(f"  {type(error).__name__}: {error}")
        for p in self.phases:
            share = 100 * p.duration / total if total else 0
            rows.append(
                f"  {p.duration:8.1f}s ({share:4.1f}%)  cpu={p.mean_cpu:3.0f}%  "
                f"peak_rss={_fmt_bytes(p.peak_rss):>8s}  "
                f"swap_out={_fmt_bytes(p.swap_out):>8s}  "
                f"net_tx={_fmt_bytes(p.net_tx):>8s}  {p.name}"
            )
        rows.append(f"  verdict: {self._verdict()}")
        return "\n".join(rows)

    def _verdict(self) -> str:
        """Read the counters rather than making the user do it."""
        if psutil is None or not self.phases:
            return "no resource samples (psutil unavailable)"
        slowest = max(self.phases, key=lambda p: p.duration)
        if slowest.duration < 60:
            return "nothing slow enough to diagnose"
        swap = slowest.swap_out
        net = slowest.net_tx
        cpu = slowest.mean_cpu
        where = f"slowest phase {slowest.name!r} ({slowest.duration:.0f}s)"
        if swap > 512 << 20:
            return (
                f"{where} was swapping ({_fmt_bytes(swap)} paged out) — the pod is out of "
                "RAM. Fix the pod size or the load path, not the algorithm."
            )
        if cpu < 25 and net > 512 << 20:
            return (
                f"{where} was mostly idle while sending {_fmt_bytes(net)} — this looks "
                "like a sync_to H5AD upload, not computation."
            )
        if cpu < 25:
            return (
                f"{where} was mostly idle (cpu {cpu:.0f}%) with no swap or network "
                "traffic — blocked on I/O or a remote call, not computing."
            )
        return f"{where} was CPU-bound (cpu {cpu:.0f}%) — genuinely computing."


class monitor:
    """Context manager wrapping :class:`RunMonitor`.

    ``with monitor("background removal") as mon:`` starts the heartbeat, and ``mon.phase``
    is a ``progress``-compatible callable. The summary is written on exit, including when
    the body raises.
    """

    def __init__(
        self,
        label: str,
        interval: float = 15.0,
        path: Path | str | None = None,
        echo: bool = True,
        sink: Callable[[str], None] | None = None,
    ) -> None:
        self._mon = RunMonitor(label, interval=interval, path=path, echo=echo, sink=sink)

    def __enter__(self) -> RunMonitor:
        return self._mon.start()

    def __exit__(self, exc_type, exc, tb) -> bool:
        self._mon.stop(error=exc)
        return False
