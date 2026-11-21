"""Czech alphabetical ordering for SQLite.

SQLite compares strings byte by byte, which puts "Černá" after "Zelený". This module
registers a `czech` collation on every SQLite connection so querysets can sort names
the Czech way: č, ř, š, ž and "ch" are separate letters (ch comes after h), other
accents (á, é, ě, í, ó, ú, ů, ý, ď, ť, ň) only break ties.
"""

import unicodedata

from django.db.backends.signals import connection_created

COLLATION_NAME = "czech"

_PRIMARY_ORDER = [
    "a", "b", "c", "č", "d", "e", "f", "g", "h", "ch", "i", "j", "k", "l", "m",
    "n", "o", "p", "q", "r", "ř", "s", "š", "t", "u", "v", "w", "x", "y", "z", "ž",
]  # fmt: skip
_PRIMARY_RANK = {letter: rank for rank, letter in enumerate(_PRIMARY_ORDER, start=1)}
_PRIMARY_LETTERS = {"č", "ř", "š", "ž"}


def _strip_accent(char: str) -> str:
    decomposed = unicodedata.normalize("NFD", char)
    return decomposed[0]


def czech_sort_key(value: str) -> tuple:
    text = value.casefold()
    primary = []
    i = 0
    while i < len(text):
        if text.startswith("ch", i):
            primary.append(_PRIMARY_RANK["ch"])
            i += 2
            continue
        char = text[i]
        base = char if char in _PRIMARY_LETTERS else _strip_accent(char)
        # Spaces/punctuation sort before letters, unknown characters after them.
        if base in _PRIMARY_RANK:
            primary.append(_PRIMARY_RANK[base])
        elif base.isalnum():
            primary.append(1000 + ord(base))
        else:
            primary.append(0)
        i += 1
    return (tuple(primary), text, value)


def _compare(a: str, b: str) -> int:
    key_a, key_b = czech_sort_key(a), czech_sort_key(b)
    return (key_a > key_b) - (key_a < key_b)


def register_czech_collation(sender, connection, **kwargs):
    if connection.vendor == "sqlite":
        connection.connection.create_collation(COLLATION_NAME, _compare)


def connect_signal():
    connection_created.connect(register_czech_collation, dispatch_uid="czech_collation")
