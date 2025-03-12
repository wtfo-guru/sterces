"""Top level module app in package sterces."""

import errno
import os
import re
from pathlib import Path
from stat import filemode
from typing import Optional, Tuple

import click
from loguru import logger
from pykeepass import PyKeePass


class StercesApp:  # noqa: WPS214
    """StercesApp class."""

    debug: int
    verbose: int
    _pkobj: Optional[PyKeePass]
    _check_status: dict[str, int]
    _chmod: Optional[str]

    def __init__(self) -> None:
        self.debug = 0
        self.verbose = 0
        self._pkobj = None
        self._chmod = None
        self._check_status = {}

    def __del__(self) -> None:  # noqa: WPS603
        if self._chmod is not None:
            self._pkobj = None
            path = Path(self._chmod)
            mode = 0o600
            path.chmod(mode)

    def initialize(
        self, debug: int, verbose: int, pkobj: PyKeePass, chmod: Optional[str] = None
    ) -> None:
        self.debug = debug
        self.verbose = verbose
        self._pkobj = pkobj
        self._chmod = chmod

    def group(
        self, add: bool, name: Optional[str], parent: Optional[str], remove: bool
    ) -> int:
        self._ensure_pkobj()
        if add or remove:
            if not parent:
                groups = self._pkobj.find_groups(group=self._pkobj.root_group)
            else:
                parent_parts = parent.split("/")
                while len(parent_parts) > 1:
                    group_name = parent_parts.pop()
                    groups = pkobj.find_groups(path=parent_parts, name=group_name)
            if add:
                if not groups:
                    pkobj.add_group(pkobj.root_group)

    def store(  # noqa: WPS211
        self,
        group: Optional[str],
        title: str,
        username: Optional[str],
        password: str,
        url: Optional[str],
        notes: Optional[str],
        expires: Optional[str],
        tags: Optional[list[str]],
        otp,
    ) -> int:
        if not group:
            group = self._pkobj.root_group
        else:
            groups = self._pkobj.find_groups(name=group, first=False)
        if self.debug:
            click.echo("group: {0}".format(group))
            click.echo("title: {0}".format(title))
            if self.debug > 1:
                click.echo("password: {0}".format(password))
        logger.warning("Not Implemented yet!")
        return 0

    def pre_flight(
        self, database: str, passphrase: str, key_file: Optional[str]
    ) -> Tuple[bool, str]:
        create = self._check_file(database, missing_ok=True)
        self._check_file(passphrase, missing_ok=False)
        if key_file:
            self._check_file(key_file, missing_ok=True)
        with open(passphrase) as fd:
            return create, fd.readline().strip()

    def ensure_pkobj(self) -> None:
        if self._pkobj is None:
            raise ValueError("Instance of StercesApp _pkobj is None")

    def _check_file(self, fn: str, missing_ok: bool) -> bool:
        DIR_MODE = r"rwx------$"
        FILE_MODE = r"-rw-------$"
        fp = Path(fn)
        exists = fp.exists()
        if exists:
            self._check_mode(fn, fp.stat().st_mode, FILE_MODE)
            self._check_mode(str(fp.parent), fp.parent.stat().st_mode, DIR_MODE)
        elif not missing_ok:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fn)
        return not exists

    def _check_mode(self, fn: str, mode: int, exp: str) -> None:
        if re.search(exp, filemode(mode)):
            return
        if self._check_status.get(fn) is not None:
            self._check_status[fn] += 1
            return
        self._check_status[fn] = 0
        if exp.find("rwx") == -1:
            pt = "File"
            rr = "600"
        else:
            pt = "Directory"
            rr = "700"
        logger.warning(
            "{0} permission are unsafe for '{1}' recommend '{2}'".format(pt, fn, rr)
        )


app = StercesApp()
