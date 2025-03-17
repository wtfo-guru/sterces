"""Top level module cli from package sterces."""

import sys
import getpass
import dateparser
import pyotp
import types
from datetime import datetime
from pathlib import Path
from typing import NoReturn, Optional

import click
from loguru import logger
from pykeepass.pykeepass import PyKeePass, create_database, debug_setup

from sterces.app import app
from sterces.constants import VERSION

CONTEXT_SETTINGS = types.MappingProxyType({"help_option_names": ["-h", "--help"]})
HOME = Path.home()
DEFAULT_PASSWORD_FILE = HOME / ".sterces/.ssapeek"
DEFAULT_DATABASE_FILE = HOME / ".sterces/db.kdbx"

def _str_to_date(date: str) -> datetime:
    return dateparser.parse(date)

def _add_arg_if(sgrawk: dict[str, str], key: str, valor: str) -> None:
    if valor is not None:
        sgrawk[key] = valor

def _configure_logging(verbose: int) -> None:
    logger.remove()  # Remove the default handler.
    if verbose > 0:
        logger.add(sys.stderr, level="INFO")
    else:
        logger.add(sys.stderr, level="WARNING")


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option("-d", "--debug", count=True, default=0, help="increment debug level")
@click.option(
    "-D",
    "--db",
    "--database-file",
    default=DEFAULT_DATABASE_FILE,
    help="keepass db file ( default ~/.sterces/db.kdbx)",
)
@click.option(
    "-k",
    "--key-file",
    type=str,
    required=False,
    help="keepass key file (default None)",
)
@click.option(
    "-p",
    "--passphrase-file",
    default=DEFAULT_PASSWORD_FILE,
    help="passphrase file default ~/.sterces/.ssapeek",
)
@click.option(
    "-t",
    "--transformed-key",
    type=str,
    required=False,
    help="keepass transformed key (default None)",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="increment verbosity level",
)
@click.option(
    "--warn/--no-warn", default=True, help="Warn permissions flag (default True)"
)
@click.version_option(VERSION)
def cli(
    debug: int,
    db: str,
    key_file: Optional[str],
    transformed_key: Optional[str],
    passphrase_file: str,
    verbose: int,
    warn: bool,
) -> int:
    """Command interface for a KeePass database."""
    if debug == 0:
        _configure_logging(verbose)
    elif debug > 1:
        debug_setup()
    create, pwd = app.pre_flight(db, passphrase_file, key_file, warn)
    if create:
        pkobj = create_database(db, pwd, key_file, transformed_key)
    else:
        pkobj = PyKeePass(db, pwd, key_file, transformed_key)
    app.initialize(debug, verbose, pkobj, None)
    return 0


@cli.command()
def delete() -> NoReturn:
    """Delete a secret."""
    click.echo("function delete called ...")
    sys.exit(0)


@cli.command()
@click.option("-e", "--expires", type=str, help="specify expire date/time")
@click.option("-n", "--notes", type=str, help="specify notes")
@click.option("-o", "--otp", type=str, help="specify notes")
@click.option("-p", "--password", type=str, help="specify password")
@click.option("-P", "--path", type=str, required=True, help="specify path of entry")
@click.option("-T", "--tags", type=str, multiple=True, help="specify tags")
@click.option("-u", "--username", type=str, help="specify username")
@click.option("--url", type=str, help="specify url")
def store(
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
    sgrawk: dict[str,str] = {}
    if not path:
        raise ValueError("Path option cannot be empty")
    if expires:
        expiry = _str_to_date(expires)
        if expiry is None:
            raise ValueError("Invalid date time string: {0}".format(expires))
    else:
        expiry = None
    if otp:
        parsed = pyotp.parse_uri(otp)
        if parsed is None:
            raise ValueError("Invalid otp uri: {0}".format(otp))
    if str(password) == 'prompt':
        password = getpass.getpass()
    _add_arg_if(sgrawk, "notes", notes)
    _add_arg_if(sgrawk, "otp", otp)
    _add_arg_if(sgrawk, "password", password)
    _add_arg_if(sgrawk, "url", url)
    _add_arg_if(sgrawk, "username", username)
    app.store(path, expiry, tags, **sgrawk)
    sys.exit(0)


@cli.command()
@click.option("-a", "--add/--no-add", default=False, help="specify add action")
@click.option("-p", "--path", type=str, help="specify group path")
@click.option("-r", "--remove/--no-remove", default=False, help="specify remove action")
def group(add: bool, path: Optional[str], remove: bool) -> NoReturn:
    """Add/remove groups and/or list."""
    if add and remove:
        raise ValueError("option add and remove are mutually exclusive")
    sys.exit(app.group(add, path, remove))


if __name__ == "__main__":
    sys.exit(cli())  # pragma no cover
