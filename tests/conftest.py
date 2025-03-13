"""Test level module test_cli for dailylog."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def ppfn():
    """Return name of test cache file."""
    path = Path("/tmp/esarhpssap")
    with open(path, "w") as fd:
        fd.write("492434cfcb0446f7152e34f5e8ba4e0e\n")
    return str(path)


@pytest.fixture(scope="session")
def gdbx():
    path = Path("/tmp/group.kdbx")
    if path.exists():
        path.unlink()
    return str(path)
