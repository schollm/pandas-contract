"""Unit tests for the CheckSchema class."""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.pandas import DataFrameSchema

from pandas_contract import from_arg
from pandas_contract._private_checks import CheckSchema


def test_none() -> None:
    """Test mk_check function if schema is None."""
    check = CheckSchema(
        schema=None, head=None, tail=None, sample=None, random_state=None
    )
    res = check(lambda _: 0, (), {})
    assert res(pd.Series(dtype=object)) == []


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


def test_call_mutates_input_due_to_inplace_validate() -> None:
    """Demonstrate the current inplace=True side effect in schema validation."""
    check = CheckSchema(schema=DataFrameSchema({"x": pa.Column(int, coerce=True)}))
    df = pd.DataFrame({"x": [1.0]})
    dtype_before = df["x"].dtype

    check_fn = check(lambda df: 0, (df,), {})
    assert list(check_fn(df)) == []

    assert df["x"].dtype == dtype_before

