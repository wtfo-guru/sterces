"""Commands module group of package sterces."""

import sys
from typing import NoReturn

import click

from sterces.app import app
from sterces.constants import ADD, CONTEXT_SETTINGS, REMOVE, SHOW


@click.group()
def group(context_settings=CONTEXT_SETTINGS):
    """Action group for groups."""


@group.command()
@click.option("-p", "--path", type=str, help="specify group path")
def add(path: str) -> NoReturn:
    """Add group and show."""
    sys.exit(app.group(path, ADD))


@group.command()
@click.option("-p", "--path", type=str, help="specify group path")
def remove(path: str) -> NoReturn:
    """Remove group and show."""
    sys.exit(app.group(path, REMOVE))


@group.command()
def show(path: str) -> NoReturn:
    """Show groups."""
    sys.exit(app.group(None, SHOW))
