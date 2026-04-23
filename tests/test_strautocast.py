from typing import Any

import pytest

from polyconfig.polyconfig import strautocast


@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        # booleans - true
        ("true", True),
        ("True", True),
        ("t", True),
        ("YES", True),
        (" y ", True),
        ("on", True),
        #
        # booleans - false
        ("false", False),
        ("False", False),
        ("f", False),
        ("NO", False),
        (" n ", False),
        ("off", False),
        #
        # none-like
        ("none ", None),
        (" null", None),
        (" NIL ", None),
        #
        # integers
        ("0", 0),
        ("42", 42),
        (" 123 ", 123),
        #
        # floats
        ("3.14", 3.14),
        (" 2.0 ", 2.0),
        #
        # non-string input, return as is
        (123, 123),
        (3.14, 3.14),
        (True, True),
        (None, None),
        #
        # strings, return as is
        ("hello", "hello"),
        ("123abc", "123abc"),
        ("3.14.15", "3.14.15"),
    ],
)
def test_strautocast(input_value: Any, expected: Any) -> None:
    assert strautocast(input_value) == expected
