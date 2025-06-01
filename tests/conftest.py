"""Tests level module conftest for package sterces."""

from datetime import datetime, timezone
from shutil import rmtree
from tempfile import mkdtemp
from typing import Generator, Optional

import pytest
from pykeepass.pykeepass import PyKeePass  # type: ignore[import-untyped]

from sterces.db import StercesDatabase


@pytest.fixture(scope="session")
def expiry() -> datetime:
    """Create a test expiry datetime."""
    ts = int(datetime.now(timezone.utc).timestamp())
    ts += 864000  # add 10 days
    return datetime.fromtimestamp(ts, timezone.utc)


@pytest.fixture(scope="session")
def db() -> Generator[Optional[PyKeePass], None, None]:
    """Create a test StercesDatabase."""
    td = mkdtemp()
    ppf = "{0}/.ssapeek".format(td)
    dbf = "{0}/db.kdbx".format(td)
    with open(ppf, "w") as fd:
        fd.write("abc1234567890def\n")
    database: Optional[PyKeePass] = StercesDatabase(
        db_fn=str(dbf), pwd_fn=str(ppf), warn=True
    )

    yield database

    database = None
    rmtree(td)
