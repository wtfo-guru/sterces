"""Top level module app in package sterces."""

import errno
import os
import re
from datetime import datetime
from pathlib import Path
from stat import filemode
from typing import Optional, Tuple, Union

import click
from loguru import logger

from pykeepass.group import Group
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

    def group(self, add: bool, path: Optional[str], remove: bool) -> int:
        if add:
            self._option_required_for(path, "path", "add")
            self._ensure_group(str(path))
        elif remove:
            self._option_required_for(path, "path", "remove")
            group = self.pko.find_groups(path=self._group_path(str(path)))
            if group:
                self.pko.delete_group(group)
                self._dirty += 1
            else:
                logger.warning("Group not found: {0}".format(path))
        click.echo(self.pko.groups)
        self._save()
        return 0

    def store(  # noqa: WPS211
        self,
        path: str,
        expiry: Optional[datetime],
        tags: Optional[list[str]],
        **kwargs,
    ) -> int:
        keywords: list[str] = tags if tags else []
        entries = self.pko.find_entries(path=path)
        if not entries:
            group_path, title = self._entry_path(path)
            group = self._ensure_group(group_path)
            entry = self.pko.add_entry(
                group,
                title,
                kwargs.pop("username", "undef"),
                kwargs.pop("password", None),
                kwargs.pop("url", None),
                kwargs.pop("notes", None),
                expiry,
                keywords,
                kwargs.pop("otp", None),
            )
        else:
            entry = entries[0]
        print(entry)
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

    def _option_required_for(
        self, option: Optional[str], name: str, action: str
    ) -> None:
        if not option:
            raise ValueError(
                "option {0} is required for {1} action".format(name, action)
            )

    def _check_file(self, fn: str, warn: bool, missing_ok: bool) -> bool:
        DIR_MODE = r"rwx------$"
        # FILE_MODE = r"-rw-------$"
        fp = Path(fn)
        exists = fp.exists()
        if not exists:
            if not missing_ok:
                raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), fn)
            if not fp.parent.exists():
                raise FileNotFoundError(
                    errno.ENOENT, os.strerror(errno.ENOENT), str(fp.parent)
                )
        self._check_mode(
            str(fp.parent), fp.parent.stat().st_mode, DIR_MODE, warn
        )  # noqa: WPS221
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

    def _entry_path(self, path: str) -> Tuple[list[str], str]:
        group_path = self._group_path(path)
        title = group_path.pop()
        return group_path, title

    def _ensure_group(self, path: Union[str, list[str]]) -> Group:
        if isinstance(path, str):
            parts = self._group_path(path)
        else:
            parts = path.copy()
        end = 1
        cur_grp = self.pko.root_group
        while parts:
            pl = parts[0:end]  # noqa: WPS349
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
        return cur_grp

    def _group_exists(self, path: str) -> bool:
        groups = self.pko.find_groups(path=self._group_path(path))
        return len(groups) == 1

    def _save(self) -> None:
        if self._dirty > 0:
            self.pko.save()
            self._dirty = 0
            logger.debug("saved database")


app = StercesApp()
