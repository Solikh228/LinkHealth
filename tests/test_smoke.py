from pathlib import Path
import sys


def test_environment_sanity():
    """Smoke test asserting Python version and basic environment sanity."""
    assert sys.version_info >= (3, 10), "Requires Python 3.10+"


def test_directory_structure():
    """Smoke test asserting top-level directories exist."""
    root = Path(__file__).resolve().parent.parent
    assert (root / "frontend").is_dir(), "frontend/ directory must exist"
    assert (root / "backend").is_dir(), "backend/ directory must exist"
    assert (root / "contract").is_dir(), "contract/ directory must exist"
    assert (root / "_docs").is_dir(), "_docs/ directory must exist"
