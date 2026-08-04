import hashlib
from pathlib import Path

from takara.background_removal import (
    BackgroundRemovalResult,
    KitType,
    remove_background,
)
from takara.monitor import RunMonitor, monitor, tail

# Bump on every change to this package.
__version__ = "0.3.0"


def _build_id() -> str:
    """Short content hash of every source file in this package.

    ``__version__`` is hand-maintained and can be forgotten on a bump; this cannot lie.
    The deployed copy on a Latch pod lives at ``.../technology_docs/takara/lib/takara``,
    which is an artifact *copied* from the repo rather than a checkout of it — so "which
    branch did I launch from" does not answer "which code is actually running". This does.
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
    "RunMonitor",
    "monitor",
    "tail",
    "describe",
    "__version__",
    "__build__",
]
