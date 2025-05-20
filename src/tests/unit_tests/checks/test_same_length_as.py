"""Tests for pandas_contract.checks.same_length_as."""

from __future__ import annotations

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import argument
from pandas_contract.checks import same_length_as


@pytest.mark.parametrize("arg", [["df2"], "df2", "", None])
def test(arg: list[str] | str) -> None:
    """Test same_length_as argument."""

    @argument(
        "df",
        same_length_as(arg),
    )
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    df_ = pd.DataFrame({"a": [1]})
    res = my_fn(df=df_, df2=pd.DataFrame({"b": ["x"]}))
    assert res is df_


@pytest.mark.parametrize("arg", ["df3", ["df3"], ["df2", "df3"]])
def test_no_such_argument(arg: str | list[str]) -> None:
    """Test same_length_as argument failing because of missing argument."""

    @argument(
        "df",
        pa.DataFrameSchema({"a": pa.Column(int)}),
        same_length_as(arg),
    )
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    with pytest.raises(ValueError, match="requires argument 'df3'"):
        my_fn(pd.DataFrame(), pd.DataFrame())


@pytest.mark.parametrize("arg", [("df2"), (["df2"])])
def test_failing(arg: str | list[str]) -> None:
    """Test same_length_as argument failing."""

    @argument("df", same_length_as(arg))
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    with pytest.raises(ValueError, match="Length of df2 = 2 != 1."):
        my_fn(
            df=pd.DataFrame([[0]], index=[0]),
            df2=pd.DataFrame([[0]], index=[0, 1]),
        )
