"""Top level module options in package sterces."""

import errno
import os
import re
from pathlib import Path
from stat import filemode
from typing import Optional

from loguru import logger
from pykeepass import PyKeePass


class Options:
    """Options class."""

    debug: int
    verbose: int
    pkobj: Optional[PyKeePass]
    _check_status: dict[str, int]

    def __init__(self) -> None:
        self.debug = 0
        self.verbose = 0
        self.pkobj = None
        self._check_status = {}

    def initialize(self, debug: int, verbose: int, pkobj: PyKeePass) -> None:
        self.debug = debug
        self.verbose = verbose
        self.pkobj = pkobj

    def pre_flight(self, database: str, passphrase: str) -> str:
        DIR_MODE = r"rwx------$"
        FILE_MODE = r"(-rw-------$"
        ppp = Path(passphrase)
        if not ppp.exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), passphrase)
        self._check_mode(passphrase, ppp.stat().st_mode, FILE_MODE)
        self._check_mode(str(ppp.parent), ppp.parent.stat().st_mode, DIR_MODE)
        dbp = Path(database)
        if not dbp.parent.exists():
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), database)
        self._check_mode(str(dbp.parent), dbp.parent.stat().st_mode, DIR_MODE)
        if dbp.exists():
            self._check_mode(database, ppp.stat().st_mode, FILE_MODE)
        with open(passphrase) as fd:
            return fd.readline()

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
        logger.warning("{0} permission are unsafe recommend '{1}".format(pt, rr))


options = Options()
