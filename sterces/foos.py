"""Foos module for package sterces."""

from datetime import datetime
from typing import Optional

import dateparser


def str_to_date(date: str) -> Optional[datetime]:
    """Convert a string to a datetime object.

    :param date: str representation of a datetime
    :type date: str
    :return: datetime when date is parsable
    :rtype: Optional[datetime]
    """
    return dateparser.parse(date)


def add_arg_if(sgrawk: dict[str, str], key: str, valor: Optional[str]) -> None:
    """Add a str argument to a kwargs dictionary if it is not None or empty.

    :param sgrawk: kwargs dictionary
    :type sgrawk: dict[str, Optional[str]]
    :param key: argument key
    :type key: str
    :param valor: argument value
    :type valor: Optional[Union[str, list[str]]]
    """
    if valor is not None:
        sgrawk[key] = valor
