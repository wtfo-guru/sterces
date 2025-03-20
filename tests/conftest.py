"""Tests level module conftest for package sterces."""

from shutil import rmtree
from tempfile import mkdtemp
from typing import Optional

import pytest
from pykeepass.pykeepass import PyKeePass

from sterces.db import StercesDatabase


@pytest.fixture(scope="session")
def db():
    td = mkdtemp()
    ppf = "{0}/.ssapeek".format(td)
    dbf = "{0}/db.kdbx".format(td)
    with open(ppf, "w") as fd:
        fd.write("abc1234567890def\n")
    database: Optional[PyKeePass] = StercesDatabase(
        db_fn=str(dbf), pwd_fn=str(ppf), warn=False
    )

    yield database

    database = None
    rmtree(td)
