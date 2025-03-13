"""Top level module app in package sterces."""

import errno
import os
import re
from pathlib import Path
from stat import filemode
from typing import Optional, Tuple

import click
from loguru import logger

# from pykeepass.group import Group
from pykeepass.pykeepass import PyKeePass


class StercesApp:  # noqa: WPS214
    """StercesApp class."""

    debug: int
    verbose: int
    _pkobj: Optional[PyKeePass]
    _check_status: dict[str, int]
    _chmod: Optional[str]
    _dirty: int

    def __init__(self) -> None:
        self.debug = 0
        self.verbose = 0
        self._pkobj = None
        self._chmod = None
        self._check_status = {}
        self._dirty = 0

    def __del__(self) -> None:  # noqa: WPS603
        if self._chmod is not None:
            self._pkobj = None
            path = Path(self._chmod)
            mode = 0o600
            path.chmod(mode)

    @property
    def pko(self):
        if self._pkobj is None:
            raise ValueError("Instance of StercesApp _pkobj is None")
        return self._pkobj

    def initialize(
        self, debug: int, verbose: int, pkobj: PyKeePass, chmod: Optional[str] = None
    ) -> None:
        self.debug = debug
        self.verbose = verbose
        self._pkobj = pkobj
        self._chmod = chmod

    def group(  # noqa: WPS231
        self, add: bool, path: Optional[str], remove: bool
    ) -> int:
        if add:
            if not path:
                raise ValueError("Path is required for add action")
            self._ensure_group(path)
        elif remove:
            if not path:
                raise ValueError("Path is required for remove action")
            group = self.pko.find_groups(path=self._group_path(path))
            if group:
                self.pko.delete_group(group)
            else:
                logger.warning("Group not found: {0}".format(path))
        print(self.pko.groups)
        self._save()
        return 0

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
        if group:
            groups = self.pko.find_groups(name=group, first=False)
        else:
            group = self.pko.root_group
        if self.debug:
            click.echo("group: {0}".format(group))
            click.echo("title: {0}".format(title))
            if self.debug > 1:
                click.echo("password: {0}".format(password))
        logger.warning("Not Implemented yet!")
        return 0

    def pre_flight(
        self, database: str, passphrase: str, key_file: Optional[str], warn: bool
    ) -> Tuple[bool, str]:
        create = self._check_file(database, warn, missing_ok=True)
        self._check_file(passphrase, warn, missing_ok=False)
        if key_file:
            self._check_file(key_file, warn, missing_ok=True)
        with open(passphrase) as fd:
            return create, fd.readline().strip()

    def _check_file(self, fn: str, warn: bool, missing_ok: bool) -> bool:
        DIR_MODE = r"rwx------$"
        FILE_MODE = r"-rw-------$"
        fp = Path(fn)
        exists = fp.exists()
        if exists:
            self._check_mode(fn, fp.stat().st_mode, FILE_MODE, warn)
            self._check_mode(str(fp.parent), fp.parent.stat().st_mode, DIR_MODE, warn)
        elif not missing_ok:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fn)
        return not exists

    def _check_mode(self, fn: str, mode: int, exp: str, warn: bool) -> None:
        if re.search(exp, filemode(mode)):
            return
        if warn:
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

    def _group_path(self, path: str) -> list[str]:
        return path.strip("/").split("/")

    def _ensure_group(self, path: str) -> None:
        parts = self._group_path(path)
        print(parts)
        end = 1
        cur_grp = self.pko.root_group
        while True:
            pl = parts[0:end]
            found = self.pko.find_groups(path=pl)
            if found:
                cur_grp = found[0]
                continue
            logger.info("creating group '{0}'".format(pl[-1]))
            cur_grp = self.pko.add_group(cur_grp, pl[-1])
            if cur_grp is not None:
                self._dirty += 1
            end += 1
            if end > len(parts):
                break

    def _group_exists(self, path: str) -> bool:
        groups = self.pko.find_groups(path=self._group_path(path))
        return len(groups) == 1

    def _save(self) -> None:
        if self._dirty > 0:
            self.pko.save()
            self._dirty = 0


app = StercesApp()
