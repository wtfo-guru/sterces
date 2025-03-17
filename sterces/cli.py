"""Top level module cli from package sterces."""

import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger
from pykeepass.pykeepass import PyKeePass, create_database, debug_setup

from sterces.app import app
from sterces.constants import CONTEXT_SETTINGS, VERSION
from sterces.entries import commands as entry_actions
from sterces.groups import commands as group_actions

HOME = Path.home()
DEFAULT_PASSWORD_FILE = HOME / ".sterces/.ssapeek"
DEFAULT_DATABASE_FILE = HOME / ".sterces/db.kdbx"


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


cli.add_command(group_actions.group)
cli.add_command(entry_actions.entry)

if __name__ == "__main__":
    sys.exit(cli())  # pragma no cover
