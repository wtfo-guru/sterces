"""Tests module test_database for sterces library."""

from datetime import datetime, timezone

import pytest
from _pytest.logging import LogCaptureFixture
from loguru import logger
from pykeepass.pykeepass import PyKeePass

from sterces.constants import ADD, REMOVE, VERSION
from sterces.db import ATTRIBUTES, ENTRY_NOT_EXIST

ENTRY_TEST_UNO = "/test/test1"
ENTRY_TEST_DOS = "/test/test2"
ENTRY_TEST_TRES = "/test/test2"


@pytest.fixture
def caplog(caplog: LogCaptureFixture):
    """Capture loguru logs."""
    handler_id = logger.add(
        caplog.handler,
        format="{message}",
        level=0,
        filter=lambda record: record["level"].no >= caplog.handler.level,
        enqueue=False,  # Set to 'True' if your test is spawning child processes.
    )
    yield caplog
    logger.remove(handler_id)


def test_db_version(db: PyKeePass):
    """Test version property."""
    assert db.version == VERSION


def test_group_add(db: PyKeePass, capsys):
    """Test group add."""
    db.group("/internet/email/gmail/qs5779/", ADD, quiet=False)
    out, err = capsys.readouterr()
    assert (
        '[Group: "", Group: "internet", Group: "internet/email", Group: "internet/email/gmail", Group: "internet/email/gmail/qs5779"]'
        in out
    )


def test_group_remove(db: PyKeePass, capsys):
    """Test group remove."""
    db.group("/internet", REMOVE, quiet=False)
    out, err = capsys.readouterr()
    assert '[Group: ""]' in out


def test_entry_add(db: PyKeePass, expiry: datetime, capsys):
    """Test entry add."""
    db.store(ENTRY_TEST_UNO, expiry, ["test", "uno"], password="passw0rd")
    out, err = capsys.readouterr()
    md = expiry.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    match: str = (
        "'path': ['test', 'test1'], 'title': 'test1', 'username': 'undef', 'password': '********', 'tags': 'test,uno', 'expiry': '{0}'".format(
            md
        )
    )
    assert match in out


def test_entry_lookup(db: PyKeePass, expiry: datetime, caplog):
    """Test entry add."""
    attrs = {
        "username": "undef",
        "password": "passw0rd",
        "tags": "test,uno",
        "expiry": expiry.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    invalid = "invalid"
    db.lookup(ENTRY_TEST_UNO, invalid)
    for key, valor in attrs.items():
        assert db.lookup(ENTRY_TEST_UNO, key) == valor
    match = "Invalid attribute '{0}' not one of ({1}).".format(
        invalid, ",".join(ATTRIBUTES)
    )
    assert match in caplog.text


def test_entry_add_dup(db: PyKeePass, expiry: datetime, capsys, caplog):
    """Test entry add duplicate."""
    db.store(ENTRY_TEST_UNO, expiry, ["test", "uno"], password="passw0rd")
    out, err = capsys.readouterr()
    assert "Entry /test/test1 already exists" in caplog.text


def test_entry_update_username(db: PyKeePass, expiry: datetime, capsys):
    """Test entry update username."""
    db.update(ENTRY_TEST_UNO, username="joeblow")
    out, err = capsys.readouterr()
    md = expiry.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    match: str = (
        "'path': ['test', 'test1'], 'title': 'test1', 'username': 'joeblow', 'password': '********', 'tags': 'test,uno', 'expiry': '{0}'".format(
            md
        )
    )
    assert match in out


def test_entry_show_all(db: PyKeePass, expiry: datetime, capsys):
    """Test entry show all."""
    db.store(ENTRY_TEST_DOS, expiry, ["test", "dos"], password="passw0rd")
    db.show()
    out, err = capsys.readouterr()
    md = expiry.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    match1: str = (
        "'path': ['test', 'test2'], 'title': 'test2', 'username': 'undef', 'password': '********', 'tags': 'test,dos', 'expiry': '{0}'".format(
            md
        )
    )
    match: str = (
        "'path': ['test', 'test1'], 'title': 'test1', 'username': 'joeblow', 'password': '********', 'tags': 'test,uno', 'expiry': '{0}'".format(
            md
        )
    )
    assert match1 in out
    assert match in out


def test_entry_show_one(db: PyKeePass, expiry: datetime, capsys):
    """Test entry show one."""
    db.show(ENTRY_TEST_DOS)
    out, err = capsys.readouterr()
    md = expiry.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    match1: str = (
        "'path': ['test', 'test2'], 'title': 'test2', 'username': 'undef', 'password': '********', 'tags': 'test,dos', 'expiry': '{0}'".format(
            md
        )
    )
    match: str = (
        "'path': ['test', 'test1'], 'title': 'test1', 'username': 'joeblow', 'password': '********', 'tags': 'test,uno', 'expiry': '{0}'".format(
            md
        )
    )
    assert match1 in out
    assert match not in out


def test_entry_remove(db: PyKeePass, caplog):
    """Test entry remove."""
    db.remove(ENTRY_TEST_UNO)
    db.remove(ENTRY_TEST_DOS)
    db.remove(ENTRY_TEST_TRES)
    for path in (ENTRY_TEST_UNO, ENTRY_TEST_DOS):
        match = "Entry {0} has been removed".format(ENTRY_TEST_UNO)
        assert match in caplog.text
    match = ENTRY_NOT_EXIST.format(ENTRY_TEST_TRES)
    assert match in caplog.text


def test_entry_show_none(db: PyKeePass, caplog):
    """Test show none."""
    db.show()
    assert "No entries found" in caplog.text
