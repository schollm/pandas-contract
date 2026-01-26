"""Unit tests for the CheckExtends class."""

from __future__ import annotations

from typing import Any, cast

import pandas as pd
import pandera.pandas as pa
import pytest
from pandera.pandas import DataFrameSchema

from pandas_contract import from_arg, result
from pandas_contract.checks import extends


def test_init() -> None:
    """Test initialization of CheckExtends."""
    modified = DataFrameSchema()
    check = extends("df", modified=modified)
    assert check.arg == "df"
    assert check.modified.schema is modified


@pytest.mark.parametrize("arg", [None, [], ""])
def test_init_none(arg: Any) -> None:
    """Test initialization of CheckExtends."""
    modified = DataFrameSchema()
    check = extends(arg, modified=modified)
    assert check.arg == arg
    assert check.modified.schema is modified
    check_fn = check(lambda df: df, (pd.DataFrame(),), {})
    assert list(check_fn(pd.DataFrame())) == ["extends: no arg specified."]


@pytest.mark.parametrize(
    "df_to_be_extend, expect",
    [
        (pd.DataFrame({"a": [1]}), []),
        (pd.DataFrame({"a": [1.0]}), ["extends df: Column 'a' data was changed."]),
        (
            pd.DataFrame({"b": [1]}),
            [
                "extends df: Column 'a' was added but not allowed.",
                "extends df: Column 'b' was removed but not allowed.",
            ],
        ),
        (pd.DataFrame({"a": [1]}, index=[1]), ["extends df: index differ"]),
        (1, ["extends df: <input> not a DataFrame, got int."]),
    ],
)
def test_mk_check(df_to_be_extend: pd.DataFrame, expect: list[str]) -> None:
    """Test mk_check method of CheckExtends."""
    check = extends("df", modified=DataFrameSchema())
    out_df = pd.DataFrame({"a": [1]}, index=[0])
    fn = check(lambda df: df, (df_to_be_extend,), {})
    assert list(fn(out_df)) == expect


def test_callable_key_in_modified() -> None:
    """Let extends.modified schema have a callable key."""

    @result(extends("df", DataFrameSchema({from_arg("col"): pa.Column(int)})))
    def my_fn(df: pd.DataFrame, col: str = "x") -> pd.DataFrame:
        return df.assign(**{col: 1})

    my_fn(pd.DataFrame(index=[0]))


def test_callable_key_in_modified__failure() -> None:
    """Test with argument key=callable()."""

    @result(extends("df", DataFrameSchema({lambda *_: "x": pa.Column(int)})))
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(other=1)

    with pytest.raises(ValueError, match="extends df:") as exc:
        my_fn(pd.DataFrame(index=[0], columns=["aa"]))
    # match from modified schema check: We expect x from col argument
    exc.match(r"column \'x\' not in dataframe")
    # match from origina (df minus modififed columns) data check: We expect no
    # columns outside of modified to get changed
    exc.match(r"Column \'other\' was added but not allowed")


def test_mk_check__invalid_output() -> None:
    """Test mk_check method of CheckExtends."""
    check = extends("df", modified=DataFrameSchema())
    ds_in = pd.Series([], dtype=object)
    fn = check(lambda df: ..., (ds_in,), {})
    assert list(fn(cast("pd.DataFrame", 1))) == [
        "extends df: Backend DataFrameSchema not applicable to int",
        "extends df: <input> not a DataFrame, got Series.",
        "extends df: <output> not a DataFrame, got int.",
    ]


def test_mk_check__invalid_output__identical_arg() -> None:
    """Test mk_check method of CheckExtends."""
    check = extends("df2", DataFrameSchema())
    ds = pd.Series([], dtype=object)
    fn = check(lambda df2, df: 1, (ds, ds), {})
    assert list(fn(ds)) == [
        "extends df2: Backend DataFrameSchema not applicable to Series",
        "extends df2: <input> not a DataFrame, got Series.",
        "extends df2: <output> not a DataFrame, got Series.",
    ]


def test_modified_is_none() -> None:
    """Test for extends(modified=None)."""
    check = extends("df", modified=None)
    df = pd.DataFrame({"a": [1]})
    fn = check(lambda df: None, (df,), {})
    assert list(fn(df)) == []


def test_modified_is_none__add_column() -> None:
    """Test for extends(modified=None) and new column is added."""
    check = extends("df", modified=None)
    df = pd.DataFrame({"a": [1]})
    fn = check(lambda df: None, (df,), {})
    assert list(fn(df.assign(x=1))) == [
        "extends df: Column 'x' was added but not allowed."
    ]
