"""Test for checks.remove."""

from typing import Any

import pandas as pd
import pytest

from pandas_contract import from_arg
from pandas_contract.checks import removed


def test() -> None:
    """Base test."""
    check_factory = removed(["aa"])
    assert check_factory
    fn = check_factory(lambda: 0, (), {})
    assert list(fn(pd.DataFrame(columns=["a"]))) == []


def test_no_test() -> None:
    """Base test."""
    check_factory = removed([])
    assert check_factory is None


@pytest.mark.parametrize("arg_val", ["x", ["x", "y"]])
def test_from_arg__single(arg_val: Any) -> None:
    """Test with column from_arg."""
    check_factory = removed([from_arg("arg")])
    assert check_factory
    fn = check_factory(lambda arg: 0, (arg_val,), {})
    df = pd.DataFrame(columns=["x"])
    assert list(fn(df)) == ["Column 'x' still exists in DataFrame"]
