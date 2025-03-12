"""Top level module cli from package sterces."""

import getpass
import sys
import types
from pathlib import Path
from typing import NoReturn, Optional

import click
from pykeepass.pykeepass import PyKeePass, create_database, debug_setup

from sterces.app import app
from sterces.constants import VERSION

CONTEXT_SETTINGS = types.MappingProxyType({"help_option_names": ["-h", "--help"]})
HOME = Path.home()
DEFAULT_PASSWORD_FILE = HOME / ".sterces/.ssapeek"
DEFAULT_DATABASE_FILE = HOME / ".sterces/db.kdbx"


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
@click.version_option(VERSION)
def cli(
    debug: int,
    db: str,
    key_file: Optional[str],
    transformed_key: Optional[str],
    passphrase_file: str,
    verbose: int,
) -> int:
    """Command interface for a KeePass database."""
    if debug:
        debug_setup()
    create, pwd = app.pre_flight(db, passphrase_file, key_file)
    if create:
        pkobj = create_database(db, pwd, key_file, transformed_key)
        chmod = db
    else:
        pkobj = PyKeePass(db, pwd, key_file, transformed_key)
        chmod = None
    app.initialize(debug, verbose, pkobj, chmod)
    return 0


@cli.command()
def delete() -> NoReturn:
    """Delete a secret."""
    click.echo("function delete called ...")
    sys.exit(0)


@cli.command()
@click.option("-e", "--expires", type=str, help="specify expire date/time")
@click.option("-g", "--group", type=str, help="specify group (default root_group)")
@click.option("-p", "--password", type=str, help="specify password")
@click.option("-n", "--notes", type=str, help="specify notes")
@click.option("-o", "--otp", type=str, help="specify notes")
@click.option("-t", "--title", type=str, required=True, help="specify title")
@click.option("-T", "--tags", type=str, multiple=True, help="specify tags")
@click.option("-u", "--username", type=str, help="specify username")
@click.option("--url", type=str, help="specify url")
def store(
    group: Optional[str],
    title: str,
    username: Optional[str],
    password: Optional[str],
    url: Optional[str],
    notes: Optional[str],
    expires: Optional[str],
    tags: Optional[list[str]],
    otp: Optional[str],
) -> NoReturn:
    """Store a secret."""
    if not password:
        password = getpass.getpass()
    app.store(group, title, username, password, url, notes, expires, tags, otp)
    sys.exit(0)


@cli.command()
@click.option("-a", "--add/--no-add", default=False, help="specify add action")
@click.option("-n", "--name", type=str, help="specify name of group")
@click.option("-r", "--remove/--no-remove", default=False, help="specify remove action")
@click.option("-p", "--parent", type=str, help="parent group (default root_group)")
def group(add: bool, name: Optional[str], parent: Optional[str], remove: bool) -> NoReturn:
    """Add or remove groups and list."""
    if add and remove:
        raise ValueError("option add and remove are mutually exclusive")
    sys.exit(app.group(add, name, parent, remove))

if __name__ == "__main__":
    sys.exit(cli())  # pragma no cover
