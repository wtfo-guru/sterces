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
from pykeepass.entry import Entry
from pykeepass.group import Group
from pykeepass.pykeepass import PyKeePass

from sterces.constants import ADD, REMOVE
from sterces.foos import str_to_date

# attributes
USERNAME = "username"
PASSWORD = "password"
URL = "url"
NOTES = "notes"
EXPIRY = "expiry"
TAGS = "tags"
OTP = "otp"
ATTRIBUTES = frozenset((USERNAME, PASSWORD, URL, NOTES, EXPIRY, TAGS, OTP))


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

    def group(self, path: Optional[str], action: str) -> int:
        if path:
            if action == ADD:
                self._option_required_for(path, "path", ADD)
                self._ensure_group(str(path))
            elif action == REMOVE:
                self._option_required_for(path, "path", REMOVE)
                group = self.pko.find_groups(path=self._str_to_path(str(path)))
                if group:
                    self.pko.delete_group(group)
                    self._dirty += 1
                else:
                    logger.warning("Group not found: {0}".format(path))
            else:
                logger.warning("Invalid action: {0}".format(action))
        click.echo(self.pko.groups)
        self._save()
        return 0

    def store(  # noqa: WPS210, WPS211
        self,
        path: str,
        expiry: Optional[datetime],
        tags: Optional[list[str]],
        **kwargs,
    ) -> int:
        keywords: list[str] = tags if tags else []
        entry = self.pko.find_entries(path=self._str_to_path(path))
        if entry:
            logger.error("Entry {0} already exists".format(path))
            return 1
        group_path, title = self._entry_path(path)
        group = self._ensure_group(group_path)
        entry = self.pko.add_entry(
            group,
            title,
            kwargs.pop(USERNAME, "undef"),
            kwargs.pop(PASSWORD, None),
            kwargs.pop(URL, None),
            kwargs.pop(NOTES, None),
            expiry,
            keywords,
            kwargs.pop(OTP, None),
        )
        self._dirty += 1
        self._print_entry(entry)
        self._save()
        return 0

    def update(  # noqa: WPS231, C901
        self,
        path: str,
        **kwargs,
    ) -> int:
        entry = self.pko.find_entries(path=self._str_to_path(path))
        if not entry:
            logger.error("Entry {0} does not exist".format(path))
            return 1
        for key, valor in kwargs.items():
            if key == "expires":
                if valor is None:
                    entry.expires = False
                else:
                    expiry = str_to_date(valor)
                    if expiry is None:
                        raise ValueError("Invalid date time string: {0}".format(expiry))
                    entry.expiry_time = expiry
                    entry.expires = True
            elif key == TAGS:
                entry.tags = valor.split(",")
            else:
                exec("entry.{0} = valor".format(key))
        self._dirty += 1
        self._print_entry(entry)
        self._save()
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

    def show(self, path: Optional[str]) -> int:
        if path:
            entries = self.pko.find_entries(path=path)
        else:
            entries = self.pko.entries
        for entry in entries:
            self._print_entry(entry)
        return 0

    def _print_entry(self, entry: Entry, mask: bool = True) -> None:  # noqa: C901
        ed: dict[str, str] = {}
        ed["path"] = entry.path
        ed["title"] = entry.title
        ed["username"] = entry.username
        if mask:
            masked = ""
            cnt = len(entry.password)
            while cnt > 0:
                masked = masked + "*"  # noqa: WPS336
                cnt -= 1
            ed["password"] = masked
        else:
            ed["password"] = entry.password
        if entry.tags:
            ed["tags"] = ",".join(entry.tags)
        if entry.url:
            ed["url"] = entry.url
        if entry.notes:
            ed["notes"] = entry.notes
        if entry.expires:
            ed["expiry"] = entry.expiry_time.strftime("%Y-%m-%d %H:%M:%S")
        if entry.otp:
            ed["otp"] = entry.otp
        click.echo(ed)

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

    def _str_to_path(self, path: str) -> list[str]:
        return path.strip("/").split("/")

    def _entry_path(self, path: str) -> Tuple[list[str], str]:
        group_path = self._str_to_path(path)
        title = group_path.pop()
        return group_path, title

    def _ensure_group(self, path: Union[str, list[str]]) -> Group:
        if isinstance(path, str):
            parts = self._str_to_path(path)
        else:
            parts = path.copy()
        end = 1
        cur_grp = self.pko.root_group
        while parts:
            pl = parts[0:end]  # noqa: WPS349
            found = self.pko.find_groups(path=pl)
            if found:
                cur_grp = found
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
        groups = self.pko.find_groups(path=self._str_to_path(path))
        return len(groups) == 1

    def _save(self) -> None:
        if self._dirty > 0:
            self.pko.save()
            self._dirty = 0
            logger.debug("saved database")


app = StercesApp()
