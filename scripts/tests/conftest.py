# scripts/tests/conftest.py
import sys
from pathlib import Path

def _add_paths_for(*filenames: str):
    """
    Walk up from this file to the drive root; if we see any of the given
    filenames at the current dir or in a 'scripts' subdir, add those
    directories to sys.path so tests can import modules.
    """
    here = Path(__file__).resolve()
    for parent in [here.parent] + list(here.parents):
        # repo root candidate
        if any((parent / fn).exists() for fn in filenames):
            _push(parent)
            return
        # repo/scripts candidate
        scripts_dir = parent / "scripts"
        if scripts_dir.is_dir() and any((scripts_dir / fn).exists() for fn in filenames):
            _push(parent)        # repo root
            _push(scripts_dir)   # repo/scripts
            return

def _push(p: Path):
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)

# Make both module locations importable (root and scripts/)
_add_paths_for("Gmail_MAIN.py", "Ragpipeline.py")
