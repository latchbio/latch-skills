import hashlib
from pathlib import Path

from takara.background_removal import (
    BackgroundRemovalResult,
    KitType,
    remove_background,
)
from takara.launch import (
    LaunchGuardResult,
    LaunchStatus,
    find_live_executions,
    launch_workflow_once,
    params_fingerprint,
    read_claim,
)
from takara.monitor import RunMonitor, monitor, tail

# Bump on every change to this package.
__version__ = "0.4.0"


def _build_id() -> str:
    """Short content hash of every source file in this package.

    ``__version__`` is hand-maintained and can be forgotten on a bump; this cannot lie.

    It exists because a pod can import a *different* ``takara`` than the one you edited and
    give no sign of it. ``.../technology_docs/takara/lib/takara`` holds a frozen snapshot of
    this package from before the move into the latch-skills monorepo, kept for backward
    compatibility; it imports cleanly, and it is re-copied on pod start so its mtimes look
    current. Neither the path nor the file dates tell you what is running. This does.
    """
    h = hashlib.sha256()
    for p in sorted(Path(__file__).parent.glob("*.py")):
        h.update(p.name.encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:12]


__build__ = _build_id()


def describe() -> str:
    """One-line identity of the running package. Print this before trusting any timing run.

    A run whose build id does not match your working copy is testing code you did not write,
    and every conclusion drawn from it is about the wrong program.
    """
    here = Path(__file__).parent
    return (
        f"takara {__version__} build={__build__} path={here} "
        f"modules={sorted(p.name for p in here.glob('*.py'))}"
    )


__all__ = [
    "BackgroundRemovalResult",
    "KitType",
    "remove_background",
    "LaunchGuardResult",
    "LaunchStatus",
    "find_live_executions",
    "launch_workflow_once",
    "params_fingerprint",
    "read_claim",
    "RunMonitor",
    "monitor",
    "tail",
    "describe",
    "__version__",
    "__build__",
]
