"""Top level module constants in package sterces."""

from pathlib import Path

VERSION = "0.1.0-dev0"

# actions
ADD = "add"
REMOVE = "remove"
SHOW = "show"

STERCES_DN = Path().home() / ".sterces"
DEFAULT_DB_FN = str(STERCES_DN / "db.kdbx")
DEFAULT_PWD_FN = str(STERCES_DN / ".ssapeek")
