"""Foos module for package sterces."""

from datetime import datetime
from typing import Optional

import dateparser


def str_to_date(date: str) -> Optional[datetime]:
    return dateparser.parse(date)


def add_arg_if(sgrawk: dict[str, str], key: str, valor: Optional[str]) -> None:
    if valor is not None:
        sgrawk[key] = valor
