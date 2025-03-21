"""Db module from sterces library."""

import errno
import json
import os
import re
from datetime import datetime
from pathlib import Path
from stat import filemode
from typing import Optional, Tuple, Union

from loguru import logger
from pykeepass.entry import Entry
from pykeepass.group import Group
from pykeepass.pykeepass import PyKeePass, create_database

from sterces.constants import (
    ADD,
    DEFAULT_DB_FN,
    DEFAULT_PWD_FN,
    REMOVE,
    VERSION,
)
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


class StercesDatabase:
    """StercesDatabase class."""

    debug: int
    verbose: int
    _kpobj: Optional[PyKeePass]
    _check_status: dict[str, int]
    _chmod: Optional[str]
    _dirty: int

    def __init__(self, **kwargs) -> None:
        """Construct a StercesDatabase class.

        :param kwargs: Additional optional keyword arguments.
            - **debug**: debug level.
            - **verbose**: verbosity level.
            - **db_fn**: path of db file.
            - **pwd_fn**: path of passphrase file.
            - **key_fn**: path of key_fn.
            - **tf_key**: transformation_key.
            - **warn**: warn if permission are inadequate.
        :type kwargs: dict

        """
        self._dirty = False
        self.debug = kwargs.get("debug", 0)
        self.verbose = kwargs.get("verbose", 0)
        self._kpobj = self._initialize_kpdb(
            kwargs.get("db_fn", DEFAULT_DB_FN),
            kwargs.get("pwd_fn", DEFAULT_PWD_FN),
            kwargs.get("key_fn", ""),
            kwargs.get("tf_key"),
            kwargs.get("warn", True),
        )

    @property
    def kpo(self) -> PyKeePass:
        """Return the KeePass database object.

        :raises ValueError When protected instance variable _kpobj is None
        :return: return code
        :rtype: int
        """
        if self._kpobj is None:
            raise ValueError("Instance of StercesApp _kpobj is None")
        return self._kpobj

    @property
    def version(self) -> str:
        """Return the version of the sterces library."""
        return VERSION

    def dump(self, path: Optional[str], mask: bool = True) -> int:
        """Dump the database to stdout.

        :param path: path to the output file
        :type path: Optional[str]
        :param mask: mask password fields when True
        :type mask: bool
        :return: return code
        :rtype: int
        """
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

    def group(self, path: Optional[str], action: str, quiet: bool = True) -> int:
        """Manage groups.

        :param path: path of the group
        :type path: Optional[str]
        :param action: action to perform (ADD, REMOVE)
        :type action: str
        :param quiet: don't show groups when True
        :type quiet: bool
        :return: return code
        :rtype: int
        """
        if path:
            if action == ADD:
                self._option_required_for(path, "path", ADD)
                self._ensure_group(str(path))
                self._dirty += 1
            elif action == REMOVE:
                self._option_required_for(path, "path", REMOVE)
                group = self.kpo.find_groups(path=self._str_to_path(str(path)))
                if group:
                    self.kpo.delete_group(group)
                    self._dirty += 1
                else:
                    logger.warning("Group not found: {0}".format(path))
            else:
                logger.warning("Invalid action: {0}".format(action))
        if not quiet:
            print(self.kpo.groups)
        self._save()
        return 0

    def lookup(self, path: str, attr: str) -> Optional[str]:  # noqa: WPS231
        """Return the value of the attribute.

        :param path: path of the entry
        :type path: str
        :param attr: attribute to lookup
        :type attr: str
        :return: value of found attribute or None
        :rtype: Optional[str]
        """
        if attr in ATTRIBUTES:
            entry = self.kpo.find_entries(path=self._str_to_path(path))
            if entry:
                if attr == TAGS:
                    return ",".join(entry.tags)
                elif attr == EXPIRY:
                    return (
                        entry.expiry_time.strftime("%Y-%m-%d %H:%M:%S")
                        if entry.expires
                        else None
                    )
                else:
                    return eval("entry.{0}".format(attr))
            logger.error(ENTRY_NOT_EXIST.format(path))
        else:
            logger.error(
                "Invalid attribute '{0}' not one of ({1}).".format(
                    attr, ",".join(ATTRIBUTES)
                )
            )
        return None

    def remove(self, path: str) -> int:
        """Remove an entry.

        :param path: path of the entry to remove
        :type path: str
        :return: return code
        :rtype: int
        """
        entry = self.kpo.find_entries(path=self._str_to_path(path))
        if not entry:
            logger.warning(ENTRY_NOT_EXIST.format(path))
            return 1
        self.kpo.delete_entry(entry)
        self._dirty += 1
        self._save()
        logger.info("Entry {0} has been removed".format(path))
        return 0

    def show(self, path: Optional[str] = None, mask: bool = True) -> int:
        """Show one or all entries.

        :param path: path of the entry to show, defaults to None
        :type path: Optional[str], optional
        :param mask: mask password, defaults to True
        :type mask: bool, optional
        :return: return code
        :rtype: int
        """
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

    def store(  # noqa: WPS210, WPS211
        self,
        path: str,
        expiry: Optional[datetime],
        tags: Optional[list[str]],
        **kwargs,
    ) -> int:
        """Add a new entry to the database.

        :param path: path of the entry to add
        :type path: str
        :param expiry: datetime of expiration
        :type expiry: Optional[datetime]
        :param tags: list of tag strings
        :type tags: Optional[list[str]]
        :param kwargs: Additional optional keyword arguments.
            - **username**: Value of username property (default undef).
            - **password**: Value of password property (default undef).
            - **url**: Value of url property.
            - **notes**: Value of notes property.
            - **otp**: Value of otp property.
        :type kwargs: dict
        :return: return code
        :rtype: int
        """
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
            kwargs.pop(PASSWORD, "undef"),
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
        """Update the entry specified by path.

        :param path: path of the entry to update
        :type path: str
        :param kwargs: Additional optional keyword arguments.
            - **username**: Value of username property (default undef).
            - **password**: Value of password property.
            - **url**: Value of url property.
            - **notes**: Value of notes property.
            - **otp**: Value of otp property.
            - **tags**: Comma separated list of tags.
            - **expires**: String representation of expiry datetime.
        :type kwargs: dict
        :raises ValueError: When expires is not parsable
        :return: return code
        :rtype: int
        """
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

    def _ensure_group(self, path: Union[str, list[str]]) -> Group:  # noqa: C901, WPS231
        if isinstance(path, str):
            parts = self._str_to_path(path)
        else:
            parts = path.copy()
        end = 1
        cur_grp = self.kpo.root_group
        while parts:
            pl = parts[0:end]  # noqa: WPS349
            found = self.kpo.find_groups(path=pl)
            if found:
                cur_grp = found
                end += 1
                if end > len(parts):
                    break
                continue
            logger.info("creating group '{0}'".format(pl[-1]))
            cur_grp = self.kpo.add_group(cur_grp, pl[-1])
            if cur_grp is not None:
                self._dirty += 1
            end += 1
            if end > len(parts):
                break
        return cur_grp

    def _entry_path(self, path: str) -> Tuple[list[str], str]:
        group_path = self._str_to_path(path)
        title = group_path.pop()
        return group_path, title

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

    def _initialize_kpdb(
        self,
        db_fn: str,
        pwd_fn: str,
        key_fn: Optional[str],
        tf_key: Optional[str],
        warn: bool,
    ) -> PyKeePass:
        create, pwd = self._pre_flight(db_fn, pwd_fn, key_fn, warn)
        if create:
            return create_database(db_fn, pwd, key_fn, tf_key)
        return PyKeePass(db_fn, pwd, key_fn, tf_key)

    def _option_required_for(
        self, option: Optional[str], name: str, action: str
    ) -> None:
        if not option:
            raise ValueError(
                "option {0} is required for {1} action".format(name, action)
            )

    def _pre_flight(
        self, database: str, passphrase: str, key_file: Optional[str], warn: bool
    ) -> Tuple[bool, str]:
        create = self._check_file(database, warn, missing_ok=True)
        self._check_file(passphrase, warn, missing_ok=False)
        if key_file:
            self._check_file(key_file, warn, missing_ok=True)
        with open(passphrase) as fd:
            return create, fd.readline().strip()

    def _print_entry(self, entry: Entry, mask: bool = True) -> None:
        ed = self._entry_to_dict(entry, mask)
        print(ed)

    def _save(self) -> None:
        if self._dirty > 0:
            self.kpo.save()
            self._dirty = 0
            logger.debug("saved database")

    def _str_to_path(self, path: str) -> list[str]:
        return path.strip("/").split("/")
