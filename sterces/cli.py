"""Top level module cli from package sterces."""

import sys
import types
from pathlib import Path
from typing import NoReturn

import click
from pykeepass import PyKeePass

from sterces.constants import VERSION
from sterces.options import options

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
    help="keepass db file ~/.sterces/db.kdbx",
)
@click.option(
    "-p",
    "--passphrase-file",
    default=DEFAULT_PASSWORD_FILE,
    help="passphrase file default ~/.sterces/.ssapeek",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    default=0,
    help="increment verbosity level",
)
@click.version_option(VERSION)
def cli(debug: int, db: str, passphrase_file: str, verbose: int) -> int:
    """Command interface for a KeePass database."""
    options.pre_flight(db, passphrase_file)
    options.initialize(debug, verbose, PyKeePass(db, passphrase_file))
    return 0


@cli.command()
def delete() -> NoReturn:
    """Delete a secret."""
    click.echo("function delete called ...")
    sys.exit(0)


@cli.command()
def store() -> NoReturn:
    """Store a secret."""
    click.echo("function store called ...")
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(cli())  # pragma no cover
