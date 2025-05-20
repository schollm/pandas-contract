"""Unit tests for the CheckExtends class."""

from __future__ import annotations

from typing import Any

import pandas as pd
import pandera as pa
import pytest
from pandera import DataFrameSchema, SeriesSchema

from pandas_contract import from_arg, result
from pandas_contract.checks import extends

"""Unit tests for the CheckExtends class."""


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
    assert check.arg == ""
    assert check.modified is modified


@pytest.mark.parametrize(
    "schema",
    [
        SeriesSchema(),
        [1, 2],
    ],
)
def test_init__fail(schema: Any) -> None:
    """Test initialization of CheckExtends."""
    with pytest.raises(
        TypeError,
        match="CheckExtends: If modified is set, then it must be of type "
        "pandera.DataFrameSchema, got",
    ):
        extends("df", schema)


@pytest.mark.parametrize(
    "df_to_be_extend, expect",
    [
        (pd.DataFrame({"a": [1]}), []),
        (pd.DataFrame({"a": [1.0]}), ["extends df: Column 'a' was changed."]),
        (
            pd.DataFrame({"b": [1]}),
            ["extends df: Columns differ: ['a'] != ['b']"],
        ),
        (pd.DataFrame({"a": [1]}, index=[1]), ["extends df: index differ"]),
        (1, ["extends df: df not a DataFrame, got int."]),
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
    exc.match(r"Columns differ: .*\['aa', 'other'\] != \['aa'\]")


def test_mk_check__invalid_output() -> None:
    """Test mk_check method of CheckExtends."""
    check = extends("df", modified=DataFrameSchema())
    df = pd.DataFrame([])
    df2 = pd.Series([])
    fn = check(lambda df: df, (df,), {})
    assert list(fn(df2)) == [
        "extends df: Backend DataFrameSchema not applicable to Series",
        "extends df: <input> not a DataFrame, got Series.",
    ]


def test_mk_check__invalid_output__identical_arg() -> None:
    """Test mk_check method of CheckExtends."""
    check = extends("df2", DataFrameSchema())
    df = pd.Series([])
    fn = check(lambda df2, df: df2, (df, df), {})
    assert list(fn(df)) == [
        "extends df2: Backend DataFrameSchema not applicable to Series",
        "extends df2: <input> not a DataFrame, got Series.",
        "extends df2: df2 not a DataFrame, got Series.",
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
        "extends df: Columns differ: ['a', 'x'] != ['a']"
    ]
