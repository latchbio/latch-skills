"""Guarded workflow launching.

`w_workflow(automatic=True)` fires an execution every time its cell runs, and in Plots *editing*
a cell runs it. A launch cell that fails once — the RCTD docs anticipate exactly that, since the
registered `wf_name`/`version` drift — therefore gets edited (run #1, a real execution) and then
often explicitly re-run (run #2, a second real execution seconds later). That is how a Seeker test
session started two RCTD deconvolutions ~10s apart.

`w_workflow`'s only dedup lever is its `key`: "subsequent cell runs with the same key will not
relaunch". But the key is a literal the agent types, so rewriting the cell to fix it is precisely
the moment the key stops being stable. `launch_workflow_once` closes both holes:

1. the widget key is derived from a hash of (wf_name, version, params), so an edited or regenerated
   cell with unchanged parameters reuses the same widget — and a genuinely different run
   (new reference, new `run_name`) still gets a new key and is still allowed; and
2. before rendering anything it asks *Latch* whether a matching execution is already in flight,
   which — unlike a widget key — survives a pod restart, a lost kernel, and a second agent turn.

Nothing here raises. A launch cell that dies before it renders is a missing launch button, which is
a worse failure than a duplicate run; when the duplicate check cannot run, the launch is *disarmed*
(`automatic=False`) rather than withheld, so a human click is what starts the workflow.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

CLAIM_FILENAME_PREFIX = ".takara_launch"


def claim_filename(key_prefix: str) -> str:
    """One claim file per workflow, so two workflows sharing an output directory don't collide.

    Workflows that take a `run_name` get their own run directory and could have used a single fixed
    name; the demux and merger workflows write straight into `output_directory` and could not.
    """
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key_prefix) or "wf"
    return f"{CLAIM_FILENAME_PREFIX}_{safe}.json"

# An execution in one of these is over; anything else (`QUEUED`, `RUNNING`, `INITIALIZING`,
# `WAITING_FOR_RESOURCES`, or a status this list has not caught up with) counts as still in flight,
# so an unrecognized status blocks rather than waves a second run through. `ABORTING` counts as
# over: the user asked for it to stop, so relaunching is a reasonable next action, not an accident.
TERMINAL_STATUSES = frozenset({
    "SUCCEEDED",
    "FAILED",
    "ABORTED",
    "SKIPPED",
    "CANCELLED",
    "ABORTING",
})


class LaunchStatus(str, Enum):
    """What `launch_workflow_once` actually did."""

    LAUNCHED = "LAUNCHED"
    """The workflow was launched by this call (`automatic=True`) or by the user's click."""

    LAUNCH_ARMED = "LAUNCH_ARMED"
    """`automatic=False`: the button is rendered and waiting for a click. Nothing started yet."""

    BLOCKED_RUNNING = "BLOCKED_RUNNING"
    """A matching execution is already in flight. No widget was rendered and nothing was started."""

    ALREADY_COMPLETE = "ALREADY_COMPLETE"
    """A matching execution already finished. Point the user at the resume button."""

    DEGRADED = "DEGRADED"
    """The duplicate check could not run. The button is rendered but disarmed — click to launch."""


class ExecutionQueryError(RuntimeError):
    """Latch could not be asked what is running. Callers degrade; they do not propagate this."""


@dataclass(frozen=True)
class LiveExecution:
    """One row of the workspace's execution list, narrowed to what the guard needs."""

    id: str
    status: str
    display_name: str = ""
    workflow_name: str = ""
    workflow_version: str = ""
    start_time: str = ""

    @property
    def is_live(self) -> bool:
        return self.status not in TERMINAL_STATUSES

    def describe(self) -> str:
        started = f", started {self.start_time}" if self.start_time else ""
        name = self.display_name or self.workflow_name or "execution"
        return f"{name} (id {self.id}, {self.status}{started})"


@dataclass
class LaunchGuardResult:
    """Outcome of a guarded launch. Read `.status` before touching `.execution`."""

    status: LaunchStatus
    key: str
    fingerprint: str
    execution: Any = None
    existing: Optional[LiveExecution] = None
    message: str = ""
    check_error: Optional[str] = None
    claim: Optional[dict] = field(default=None, repr=False)

    @property
    def started_anything(self) -> bool:
        return self.execution is not None

    @property
    def blocked(self) -> bool:
        return self.status in (LaunchStatus.BLOCKED_RUNNING, LaunchStatus.ALREADY_COMPLETE)


# --------------------------------------------------------------------------------------------
# Fingerprinting
# --------------------------------------------------------------------------------------------


def _canonical(value: Any) -> Any:
    """Render a params value as something JSON-stable across object identity.

    `LatchFile("latch:///x")` built in two different cells is two objects with one meaning, so the
    fingerprint has to key on the remote path, not on `repr`.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    for attr in ("remote_path", "path"):
        got = getattr(value, attr, None)
        if isinstance(got, str) and got:
            return got
        if callable(got):  # LPath-likes occasionally expose `path` as a method
            try:
                called = got()
            except Exception:
                called = None
            if isinstance(called, str) and called:
                return called
    if isinstance(value, dict):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_canonical(v) for v in value)
    return str(value)


def params_fingerprint(wf_name: str, version: Optional[str], params: dict) -> str:
    """Stable short hash of everything that makes this launch *this* launch.

    Same idiom as `takara._build_id`: sorted, content-addressed, no reliance on a hand-maintained
    label. Change any parameter and you get a different fingerprint — which is what authorizes a
    genuine second run.
    """
    payload = json.dumps(
        {"wf": wf_name, "version": version, "params": _canonical(params)},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:10]


def launch_key(key_prefix: str, fingerprint: str) -> str:
    """The `w_workflow` key. Derived, never typed by hand — see this module's docstring."""
    return f"{key_prefix}_{fingerprint}"


# --------------------------------------------------------------------------------------------
# Asking Latch what is running
# --------------------------------------------------------------------------------------------


def _auth_headers() -> list[dict]:
    """Header variants to try, most likely first.

    `latch_cli` is inconsistent here — `launch_v2` signs with `Latch-SDK-Token`, `get_executions`
    with `Bearer`, against neighbouring nucleus endpoints. Rather than guess, try both.
    """
    variants: list[dict] = []
    try:
        from latch_cli.utils import get_auth_header

        variants.append({"Authorization": get_auth_header()})
    except Exception:
        pass

    token = os.environ.get("LATCH_SDK_TOKEN", "")
    if not token:
        try:
            from latch_sdk_config.user import user_config

            token = user_config.token
        except Exception:
            token = ""
    if token:
        variants.append({"Authorization": f"Bearer {token}"})

    if not variants:
        raise ExecutionQueryError("no Latch credentials available in this kernel")
    return variants


def list_executions(*, workspace_id: Optional[str] = None) -> list[LiveExecution]:
    """Every execution in the workspace, as Latch currently sees it.

    Hits `config.api.execution.list` (`/sdk/get-executions`) directly rather than going through
    `latch_cli.services.get_executions.get_executions`, which renders a terminal UI and is not
    callable from a notebook.

    Raises `ExecutionQueryError` on any failure — callers degrade rather than propagate.
    """
    try:
        from latch_cli.tinyrequests import post
        from latch_sdk_config.latch import config
    except Exception as e:
        raise ExecutionQueryError(f"latch SDK unavailable: {e}") from e

    if workspace_id is None:
        workspace_id = os.environ.get("LATCH_WORKSPACE") or None
    if workspace_id is None:
        try:
            from latch.utils import current_workspace

            workspace_id = current_workspace()
        except Exception as e:
            raise ExecutionQueryError(f"could not resolve the current workspace: {e}") from e

    last_error: Optional[Exception] = None
    for headers in _auth_headers():
        try:
            resp = post(
                url=config.api.execution.list,
                headers=headers,
                json={"ws_account_id": workspace_id},
            )
            if resp.status_code in (401, 403):
                last_error = ExecutionQueryError(f"auth rejected (HTTP {resp.status_code})")
                continue
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:  # noqa: BLE001 - any failure means "cannot check"
            last_error = e
            continue

        if not isinstance(data, dict):
            raise ExecutionQueryError(f"unexpected execution list payload: {type(data).__name__}")

        out: list[LiveExecution] = []
        for row in data.values():
            if not isinstance(row, dict):
                continue
            out.append(
                LiveExecution(
                    id=str(row.get("id", "")),
                    status=str(row.get("status", "UNDEFINED")).upper(),
                    display_name=str(row.get("display_name") or ""),
                    workflow_name=str(row.get("workflow_name") or ""),
                    workflow_version=str(row.get("workflow_version") or ""),
                    start_time=str(row.get("start_time") or ""),
                )
            )
        return out

    raise ExecutionQueryError(f"execution list request failed: {last_error}")


def _wf_matches(row_name: str, wf_name: str) -> bool:
    """Loose workflow-name match.

    The registry, `.latch/workflow_name`, and the value the agent types disagree often enough that
    an exact comparison would silently never match — RCTD alone appears as `RCTD`, `rctd_wf`, and
    `wf.__init__.RCTD_workflow`. Compare on the last dotted segment, case-insensitively.
    """
    a = (row_name or "").rsplit(".", 1)[-1].strip().lower()
    b = (wf_name or "").rsplit(".", 1)[-1].strip().lower()
    return bool(a) and bool(b) and (a == b or a in b or b in a)


def find_live_executions(wf_name: str, *, workspace_id: Optional[str] = None) -> list[LiveExecution]:
    """Non-terminal executions of `wf_name` in this workspace, newest first."""
    rows = [e for e in list_executions(workspace_id=workspace_id) if e.is_live]
    rows = [e for e in rows if _wf_matches(e.workflow_name, wf_name)]
    rows.sort(key=lambda e: int(e.id) if e.id.isdigit() else 0, reverse=True)
    return rows


# --------------------------------------------------------------------------------------------
# The claim file
# --------------------------------------------------------------------------------------------


def _as_lpath(target: Any) -> Any:
    from latch.ldata.path import LPath

    if isinstance(target, LPath):
        return target
    path = getattr(target, "path", None) or getattr(target, "remote_path", None) or str(target)
    return LPath(str(path).rstrip("/"))


def _run_dir(output_dir: Any, run_name: Optional[str]) -> Any:
    """Where this run's outputs land. `run_name` is optional — the demux/merger workflows have none."""
    base = _as_lpath(output_dir)
    return base / run_name if run_name else base


def _claim_path(output_dir: Any, run_name: Optional[str], key_prefix: str) -> Any:
    return _run_dir(output_dir, run_name) / claim_filename(key_prefix)


def read_claim(output_dir: Any, run_name: Optional[str], key_prefix: str) -> Optional[dict]:
    """The launch record this run directory already carries, if any.

    The executions list does not expose input parameters, so it cannot tell a rerun from a
    different run. This is where parameter identity lives, and it survives a pod restart for the
    same reason the rest of this skill trusts Latch Data over kernel state.
    """
    name = claim_filename(key_prefix)
    try:
        claim = _claim_path(output_dir, run_name, key_prefix)
        if not claim.exists():
            return None
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / name
            claim.download(local)
            return json.loads(local.read_text())
    except Exception:
        return None


def write_claim(
    output_dir: Any,
    run_name: Optional[str],
    key_prefix: str,
    *,
    wf_name: str,
    version: Optional[str],
    fingerprint: str,
    execution_id: Optional[str],
) -> bool:
    """Record what was just launched. Best effort — a failed write must not fail the launch."""
    record = {
        "wf_name": wf_name,
        "version": version,
        "params_fingerprint": fingerprint,
        "execution_id": execution_id,
        "run_name": run_name,
        "launched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    name = claim_filename(key_prefix)
    try:
        run_dir = _run_dir(output_dir, run_name)
        run_dir.mkdirp()
        dest = run_dir / name
        with tempfile.TemporaryDirectory() as td:
            local = Path(td) / name
            local.write_text(json.dumps(record, indent=2))
            dest.upload_from(local)
        return True
    except Exception:
        return False


# --------------------------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------------------------


def _notice(content: str, *, key: str, box: str = "info") -> None:
    """Render a message in the notebook. Silently no-op outside Plots (e.g. under test)."""
    try:
        from lplots.widgets.text import w_text_output

        w_text_output(content=content, appearance={"message_box": box}, key=key)
    except Exception:
        print(content)


def _execution_id(execution: Any) -> Optional[str]:
    for attr in ("id", "execution_id", "flytedb_id"):
        got = getattr(execution, attr, None)
        if got not in (None, ""):
            return str(got)
    return None


# --------------------------------------------------------------------------------------------
# The entry point
# --------------------------------------------------------------------------------------------


def launch_workflow_once(
    *,
    wf_name: str,
    params: dict,
    label: str,
    key_prefix: str,
    output_dir: Any,
    run_name: Optional[str] = None,
    version: Optional[str] = None,
    automatic: bool = True,
    readonly: bool = False,
    allow_concurrent: bool = False,
    render: bool = True,
    workspace_id: Optional[str] = None,
) -> LaunchGuardResult:
    """Launch a Latch workflow at most once for a given set of parameters.

    Call this instead of `w_workflow` for everything in `wf/`. Arguments mirror `w_workflow`
    except:

    - `key_prefix` replaces `key`. The widget key is derived from the parameters, so an edited or
      regenerated launch cell cannot start a second run of the same thing.
    - `run_name` / `output_dir` locate the claim file that carries parameter identity across pod
      restarts. Pass the same values that are in `params`. Omit `run_name` for the workflows that
      have none (the demux and merger workflows write straight into `output_directory`).
    - `readonly=True` disables the button, as in `w_workflow`. It also skips the duplicate check:
      a disabled button cannot launch, and the parameter-entry cells re-run on every keystroke.
    - `allow_concurrent=True` deliberately permits a second in-flight run of the same workflow.
      Only set it when the user has asked for two runs at once.

    Never raises. Inspect `.status`:

    - `BLOCKED_RUNNING` / `ALREADY_COMPLETE` — nothing was rendered and nothing started. Tell the
      user what is already happening; do not "retry".
    - `DEGRADED` — the duplicate check failed, so the button was rendered disarmed. The user clicks.
    - `LAUNCH_ARMED` — `automatic=False` and no click yet.
    - `LAUNCHED` — `.execution` is live.
    """
    fp = params_fingerprint(wf_name, version, params)
    key = launch_key(key_prefix, fp)

    def result(status: LaunchStatus, **kw: Any) -> LaunchGuardResult:
        return LaunchGuardResult(status=status, key=key, fingerprint=fp, **kw)

    # `run_name` only appears in messages from here on; keep it printable.
    where = f"`{run_name}`" if run_name else "this output directory"

    # --- 1. What does the run directory say we already did? ---
    claim = None if readonly else read_claim(output_dir, run_name, key_prefix)
    claim_matches = bool(claim) and claim.get("params_fingerprint") == fp

    # --- 2. What does Latch say is running? ---
    # Skipped while the button is disabled: nothing can launch, and a parameter-entry cell re-runs
    # on every keystroke, so checking there would be one API round trip per character typed.
    check_error: Optional[str] = None
    live: list[LiveExecution] = []
    if not readonly:
        try:
            live = find_live_executions(wf_name, workspace_id=workspace_id)
        except ExecutionQueryError as e:
            check_error = str(e)
        except Exception as e:  # noqa: BLE001 - a guard that crashes a cell is worse than no guard
            check_error = f"unexpected error querying executions: {e}"

    # True only when both halves of the check actually ran. `readonly` skips them, so an empty
    # `live` list must not be read as "nothing is running".
    checked = not readonly and check_error is None

    claimed_id = str(claim.get("execution_id") or "") if claim else ""
    claimed_live = next((e for e in live if e.id and e.id == claimed_id), None)

    if checked and not allow_concurrent:
        # This run directory launched something and it is still going. Block whether or not the
        # parameters match: a second run writing into `<output_dir>/<run_name>/` would clobber the
        # outputs the live one is still producing.
        if claimed_live is not None:
            if claim_matches:
                why = (
                    f"It was launched from {where} with these exact parameters, so nothing new was "
                    "started. Watch it in the workflows executions tab, and use the results button "
                    "when it finishes."
                )
            else:
                why = (
                    f"It is writing into {where}, which this launch also targets, with different "
                    "parameters. Nothing new was started, because a second run would overwrite its "
                    "outputs. Either wait for it to finish, or give this launch a new `run_name`."
                )
            msg = f"**{label} is already running** — {claimed_live.describe()}. {why}"
            if render:
                _notice(msg, key=f"{key}_blocked", box="warning")
            return result(
                LaunchStatus.BLOCKED_RUNNING, existing=claimed_live, message=msg, claim=claim
            )

        # Same workflow, same parameters, but no claim to tie it to a run directory — still a
        # duplicate as far as the user is concerned. This is the 10-seconds-apart case.
        if live and claim_matches:
            hit = live[0]
            msg = (
                f"**{label} is already running** — {hit.describe()}. These parameters were "
                f"already launched from {where}, so nothing new was started."
            )
            if render:
                _notice(msg, key=f"{key}_blocked", box="warning")
            return result(LaunchStatus.BLOCKED_RUNNING, existing=hit, message=msg, claim=claim)

        # Same workflow live, but different parameters. Do not block a legitimately different run;
        # say so and continue.
        if live and render:
            _notice(
                f"Note: {len(live)} other **{label}** execution(s) are already running in this "
                f"workspace ({', '.join(e.describe() for e in live[:3])}). Their parameters differ "
                "from this launch, so this one is going ahead.",
                key=f"{key}_concurrent",
                box="info",
            )

    if checked and claim_matches and claimed_id and claimed_live is None:
        msg = (
            f"**{label} already ran** with these parameters (execution {claimed_id}) and is no "
            f"longer in flight. Its outputs are in {where}. Use the results button rather than "
            "launching again; change a parameter (a new `run_name`, a new reference) if you "
            "genuinely want another run."
        )
        if render:
            _notice(msg, key=f"{key}_complete", box="success")
        return result(LaunchStatus.ALREADY_COMPLETE, message=msg, claim=claim)

    # --- 3. Launch (or arm the button) ---
    if check_error is not None:
        # Cannot verify, so do not auto-fire. A human click cannot happen twice in 10 seconds.
        automatic = False
        if render:
            _notice(
                f"The duplicate-run check could not reach Latch ({check_error}), so **{label}** "
                "will not launch on its own. Check the workflows executions tab for a run that is "
                "already in flight, then click the button below to launch.",
                key=f"{key}_degraded",
                box="warning",
            )

    try:
        from lplots.widgets.workflow import w_workflow
    except Exception as e:  # noqa: BLE001
        msg = f"`lplots` is unavailable in this kernel, so no launch button could be rendered: {e}"
        if render:
            _notice(msg, key=f"{key}_no_lplots", box="error")
        return result(LaunchStatus.DEGRADED, message=msg, check_error=str(e))

    # Unconditional and at the top level of the caller's cell: an unrendered `w_workflow` is a
    # missing launch button, which strands the user worse than a duplicate run would.
    widget = w_workflow(
        wf_name=wf_name,
        key=key,
        version=version,
        params=params,
        automatic=automatic,
        readonly=readonly,
        label=label,
    )
    execution = widget.value

    if execution is None:
        status = LaunchStatus.DEGRADED if check_error else LaunchStatus.LAUNCH_ARMED
        return result(status, message="Waiting for the user to click Launch.", check_error=check_error)

    if not claim_matches or str(claim.get("execution_id") or "") != (_execution_id(execution) or ""):
        write_claim(
            output_dir,
            run_name,
            key_prefix,
            wf_name=wf_name,
            version=version,
            fingerprint=fp,
            execution_id=_execution_id(execution),
        )

    return result(LaunchStatus.LAUNCHED, execution=execution, check_error=check_error)


__all__ = [
    "CLAIM_FILENAME_PREFIX",
    "ExecutionQueryError",
    "LaunchGuardResult",
    "LaunchStatus",
    "LiveExecution",
    "TERMINAL_STATUSES",
    "claim_filename",
    "find_live_executions",
    "launch_key",
    "launch_workflow_once",
    "list_executions",
    "params_fingerprint",
    "read_claim",
    "write_claim",
]
