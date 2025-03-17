"""Top level module constants in package sterces."""

from types import MappingProxyType

VERSION = "0.1.0"

CONTEXT_SETTINGS = MappingProxyType({"help_option_names": ["-h", "--help"]})

# actions
ADD = "add"
REMOVE = "remove"
SHOW = "show"
