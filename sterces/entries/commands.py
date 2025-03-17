"""Commands module entry of package sterces."""

import getpass
import sys
from typing import NoReturn, Optional

import click
import pyotp
from loguru import logger

from sterces.app import app, ATTRIBUTES
from sterces.constants import CONTEXT_SETTINGS
from sterces.foos import add_arg, add_arg_if, str_to_date


@click.group()
def entry(context_settings=CONTEXT_SETTINGS):
    """Action group for entries."""


@entry.command()
@click.option("-e", "--expires", type=str, help="specify expire date/time")
@click.option("-n", "--notes", type=str, help="specify notes")
@click.option("-o", "--otp", type=str, help="specify notes")
@click.option("-p", "--password", type=str, help="specify password")
@click.option("-P", "--path", type=str, required=True, help="specify path of entry")
@click.option("-T", "--tags", type=str, multiple=True, help="specify tags")
@click.option("-u", "--username", type=str, help="specify username")
@click.option("--url", type=str, help="specify url")
def add(  # noqa: WPS231, C901
    expires: Optional[str],
    notes: Optional[str],
    otp: Optional[str],
    password: Optional[str],
    path: str,
    tags: Optional[list[str]],
    url: Optional[str],
    username: Optional[str],
) -> NoReturn:
    """Add or update an entry."""
    sgrawk: dict[str, str] = {}
    if not path:
        raise ValueError("Path option cannot be empty")
    if expires:
        expiry = str_to_date(expires)
        if expiry is None:
            raise ValueError("Invalid date time string: {0}".format(expires))
    else:
        expiry = None
    if otp:
        parsed = pyotp.parse_uri(otp)
        if parsed is None:
            raise ValueError("Invalid otp uri: {0}".format(otp))
    if not password:
        password = getpass.getpass()
    add_arg_if(sgrawk, "notes", notes)
    add_arg_if(sgrawk, "otp", otp)
    add_arg_if(sgrawk, "password", password)
    add_arg_if(sgrawk, "url", url)
    add_arg_if(sgrawk, "username", username)
    app.store(path, expiry, tags, **sgrawk)
    sys.exit(0)


@entry.command()
@click.option(
    "-a",
    "--attrs",
    multiple=True,
    required=True,
    type=str,
    help="specify attributes to update",
)
@click.option("-e", "--expires", type=str, help="specify expire date/time")
@click.option("-n", "--notes", type=str, help="specify notes")
@click.option("-o", "--otp", type=str, help="specify notes")
@click.option("-p", "--password", type=str, help="specify password")
@click.option("-P", "--path", type=str, required=True, help="specify path of entry")
@click.option("-T", "--tags", type=str, multiple=True, help="specify tags")
@click.option("-u", "--username", type=str, help="specify username")
@click.option("--url", type=str, help="specify url")
def update(
    attrs: list[str],
    expires: Optional[str],
    notes: Optional[str],
    otp: Optional[str],
    password: Optional[str],
    path: str,
    tags: Optional[list[str]],
    url: Optional[str],
    username: Optional[str],
) -> NoReturn:
    """Update specified attributes of entry."""
    sgrawk: dict[str, str] = {}
    for attr in attrs:
        if attr not in ATTRIBUTES:
            raise ValueError("Invalid attribute: {0} Must be one of: {1}".format(attr,",".join(ATTRIBUTES)))
        add_arg(sgrawk, attr, eval(attr))
    app.update(path, **sgrawk)
    sys.exit(0)


@entry.command()
@click.option("-P", "--path", type=str, required=True, help="specify path of entry")
def remove(path: str) -> NoReturn:
    """Remove specified entry."""
    logger.warning("Command entry remove not implemented yet.")
    sys.exit(0)


@entry.command()
@click.option("-P", "--path", type=str, help="specify path of entry")
def show(path: Optional[str]) -> NoReturn:
    """Show specified entry or all entries if path not specified."""
    logger.warning("Command entry show not implemented yet.")
    sys.exit(0)


@entry.command()
@click.option("-P", "--path", type=str, help="specify path of entry")
def dump(path: Optional[str]) -> NoReturn:
    """Dump specified entry or all entries if path not specified."""
    logger.warning("Command entry dump not implemented yet.")
    sys.exit(0)
