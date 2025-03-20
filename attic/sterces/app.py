"""Top level module app in package sterces."""

import errno
import json
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
from sterces.foos import add_arg_if, str_to_date

ENTRY_NOT_EXIST = "Entry {0} does not exist"
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
    _kpobj: Optional[PyKeePass]
    _check_status: dict[str, int]
    _chmod: Optional[str]
    _dirty: int

    def __init__(self) -> None:
        self.debug = 0
        self.verbose = 0
        self._kpobj = None
        self._chmod = None
        self._check_status = {}
        self._dirty = 0

    def __del__(self) -> None:  # noqa: WPS603
        if self._chmod is not None:
            self._kpobj = None
            path = Path(self._chmod)
            mode = 0o600
            path.chmod(mode)



    def initialize(
        self, debug: int, verbose: int, kpobj: PyKeePass, chmod: Optional[str] = None
    ) -> None:
        self.debug = debug
        self.verbose = verbose
        self._kpobj = kpobj
        self._chmod = chmod

    def store(  # noqa: WPS210, WPS211
        self,
        path: str,
        expiry: Optional[datetime],
        tags: Optional[list[str]],
        **kwargs,
    ) -> int:
        keywords: list[str] = tags if tags else []
        entry = self.kpo.find_entries(path=self._str_to_path(path))
        if entry:
            logger.error("Entry {0} already exists".format(path))
            return 1
        group_path, title = self._entry_path(path)
        group = self._ensure_group(group_path)
        entry = self.kpo.add_entry(
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
        entry = self.kpo.find_entries(path=self._str_to_path(path))
        if not entry:
            logger.error(ENTRY_NOT_EXIST.format(path))
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

    def remove(self, path: str) -> int:
        entry = self.kpo.find_entries(path=self._str_to_path(path))
        if not entry:
            logger.warning(ENTRY_NOT_EXIST.format(path))
            return 1
        self.kpo.delete_entry(entry)
        self._dirty += 1
        self._save()
        logger.info("Entry {0} has been removed".format(path))
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

    def show(self, path: Optional[str], mask: bool = True) -> int:
        if path:
            entry = self.kpo.find_entries(path=self._str_to_path(path))
            if not entry:
                logger.error(ENTRY_NOT_EXIST.format(path))
                return 1
            self._print_entry(entry, mask)
            return 0
        entries = self.kpo.entries
        if entries:
            for entry in entries:
                self._print_entry(entry, mask)
        else:
            logger.warning("No entries found")
        return 0

    def dump(self, path: Optional[str], mask: bool = True) -> int:
        e_list: list[dict[str, str]] = []
        if path:
            entry = self.kpo.find_entries(path=self._str_to_path(path))
            if not entry:
                logger.error(ENTRY_NOT_EXIST.format(path))
                return 1
            e_list.append(self._entry_to_dict(entry, mask))
        else:
            entries = self.kpo.entries
            if entries:
                for entry in entries:
                    e_list.append(self._entry_to_dict(entry, mask))
        print(json.dumps(e_list))
        return 0

    def lookup(self, path: str, attr: str) -> int:
        entry = self.kpo.find_entries(path=self._str_to_path(path))
        if not entry:
            logger.error(ENTRY_NOT_EXIST.format(path))
            return 1
        print(eval("entry.{0}".format(attr)))
        return 0

    def _entry_to_dict(
        self, entry: Entry, mask: bool = True
    ) -> dict[str, str]:  # noqa: C901
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
        add_arg_if(ed, "url", entry.url)
        add_arg_if(ed, "notes", entry.notes)
        if entry.expires:
            ed["expiry"] = entry.expiry_time.strftime("%Y-%m-%d %H:%M:%S")
        add_arg_if(ed, "notes", entry.otp)
        return ed

    def _print_entry(self, entry: Entry, mask: bool = True) -> None:
        ed = self._entry_to_dict(entry, mask)
        print(ed)



    def _str_to_path(self, path: str) -> list[str]:
        return path.strip("/").split("/")

    def _entry_path(self, path: str) -> Tuple[list[str], str]:
        group_path = self._str_to_path(path)
        title = group_path.pop()
        return group_path, title

    def _group_exists(self, path: str) -> bool:
        groups = self.kpo.find_groups(path=self._str_to_path(path))
        return len(groups) == 1



app = StercesApp()
