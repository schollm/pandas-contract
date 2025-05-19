"""Unit tests for the CheckSchema class."""

from __future__ import annotations

import pandas as pd
import pandera as pa
from pandera import DataFrameSchema

from pandas_contract import from_arg
from pandas_contract._private_checks import CheckSchema


def test_none() -> None:
    """Test mk_check function if schema is None."""
    check = CheckSchema(
        schema=None, head=None, tail=None, sample=None, random_state=None
    )
    res = check(lambda _: 0, (), {})
    assert res(pd.Series()) == []


def test_key() -> None:
    """Test mk_check function if schema is None."""
    check = CheckSchema(
        schema=DataFrameSchema(
            {
                from_arg("a_col"): pa.Column(),
                from_arg("b_col"): pa.Column(),
            }
        )
    )
    check_fn = check(lambda a_col, b_col: 0, ("a", "b"), {})
    assert list(check_fn(pd.DataFrame(columns=["a", "b"]))) == []
    errs = list(check_fn(pd.DataFrame(columns=["a", "x"])))
    assert len(errs) == 1
    assert "'b'" in str(errs[0])
    assert isinstance(errs[0], str)
