"""Db module from sterces library"""

import errno
import os
import re
from pathlib import Path
from stat import filemode
from typing import Optional, Tuple, Union

from loguru import logger
from pykeepass.entry import Entry
from pykeepass.group import Group
from pykeepass.pykeepass import PyKeePass, create_database

from sterces.constants import ADD, DEFAULT_DB_FN, DEFAULT_PWD_FN, REMOVE, VERSION


class StercesDatabase:
    """StercesDatabase class."""

    debug: int
    verbose: int
    _kpobj: Optional[PyKeePass]
    _check_status: dict[str, int]
    _chmod: Optional[str]
    _dirty: int

    def __init__(self, **kwargs) -> None:
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
    def kpo(self):
        if self._kpobj is None:
            raise ValueError("Instance of StercesApp _kpobj is None")
        return self._kpobj

    @property
    def version(self) -> str:
        return VERSION

    def group(self, path: Optional[str], action: str, quiet: bool = True) -> int:
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

    def _ensure_group(self, path: Union[str, list[str]]) -> Group:
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
                continue
            logger.info("creating group '{0}'".format(pl[-1]))
            cur_grp = self.kpo.add_group(cur_grp, pl[-1])
            if cur_grp is not None:
                self._dirty += 1
            end += 1
            if end > len(parts):
                break
        return cur_grp

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

    def _save(self) -> None:
        if self._dirty > 0:
            self.kpo.save()
            self._dirty = 0
            logger.debug("saved database")

    def _str_to_path(self, path: str) -> list[str]:
        return path.strip("/").split("/")
