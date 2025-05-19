"""Tests for the argument decorator."""

from __future__ import annotations

from typing import Union

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import argument, as_mode, checks, from_arg

MaybeListT = Union[list[str], str]


def test() -> None:
    """Test argument decorator."""

    @argument("df", pa.DataFrameSchema({"a": pa.Column(int)}))
    def my_fn(df: pd.DataFrame) -> int:
        return len(df)

    my_fn(df=pd.DataFrame({"a": [1]}))


def test_very_simple() -> None:
    """Test argument decorator."""

    @argument("df")
    def my_fn(df: pd.DataFrame) -> int:
        return len(df)

    my_fn(df=pd.DataFrame({"a": [1]}))


def test_fail(caplog: pytest.LogCaptureFixture) -> None:
    """Test argument decorator failing."""

    @argument("df", pa.DataFrameSchema({"a": pa.Column(int)}))
    def my_fn(df: pd.DataFrame) -> int:
        return len(df)

    with as_mode("error"):
        my_fn(df=pd.DataFrame({"a": ["x"]}))

    assert "my_fn: Argument df: " in caplog.text


def test_series() -> None:
    """Test argument decorator with a Series."""

    @argument(
        "ds",
        pa.SeriesSchema(int, name="a", nullable=False),
    )
    def my_fn(ds: pd.Series) -> int:
        return len(ds)

    my_fn(ds=pd.Series([1], name="a"))


def test_extends() -> None:
    """Test extends argument."""

    @argument(
        "df", checks.extends("df2", modified=pa.DataFrameSchema({"a": pa.Column(int)}))
    )
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    df_ = pd.DataFrame({"a": [1], "b": ["x"]})
    res = my_fn(df=df_, df2=pd.DataFrame({"b": ["x"]}))
    assert res is df_


def test_extends__fails() -> None:
    """Test extends argument."""

    @argument(
        "df",
        pa.DataFrameSchema({"a": pa.Column(int)}),
        checks.extends("df2", modified=None),
    )
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    df_ = pd.DataFrame({"a": [1], "b": ["x"], "c": 10})
    with pytest.raises(ValueError, match="my_fn: Argument df:") as excinfo:
        my_fn(df=df_, df2=pd.DataFrame({"b": ["y"], "c": 10}))
    excinfo.match("'b'")


@pytest.mark.parametrize(
    "ds_, expected_err",
    [
        (pd.Series([1], name="b", dtype="float"), ", found 'b'"),
        (pd.Series([1], name="a", dtype="int"), "got int64"),
        (pd.Series([float("nan")], name="a", dtype="float"), "contains null values"),
    ],
)
def test_series_fail(ds_: pd.Series, expected_err: str) -> None:
    """Test argument decorator with a Series."""

    @argument(
        "ds",
        pa.SeriesSchema(float, name="a", nullable=False),
    )
    def my_fn(ds: pd.Series) -> int:
        return len(ds)

    with pytest.raises(ValueError, match="my_fn: Argument ds:") as exc_info:
        my_fn(ds=ds_)
    exc_info.match(expected_err)


class TestFromArg:
    """Test from_arg function."""

    def test(self) -> None:
        """Test from_arg function."""

        @argument("df", pa.DataFrameSchema({from_arg("a_col"): pa.Column(int)}))
        def my_fn(df: pd.DataFrame, a_col: str) -> int:
            """Test function."""
            return len(df[a_col])

        assert my_fn(df=pd.DataFrame({"a": [1]}), a_col="a") == 1

    def test_unknown_arg(self) -> None:
        """Test from_arg function failing."""

        @argument("df", pa.DataFrameSchema({from_arg("x_col"): pa.Column(int)}))
        def my_fn(df: pd.DataFrame, a_col: str) -> int:
            """Test function."""
            return len(df[a_col])

        with pytest.raises(ValueError, match=r"my_fn requires argument 'x_col'"):
            my_fn(df=pd.DataFrame({"a": [1]}), a_col="a")

    def test_no_such_column(self) -> None:
        """Test from_arg function failing."""

        @argument("df", checks.same_index_as("xxx"))
        def my_fn(df: pd.DataFrame) -> int:
            """Test function."""
            return len(df)

        with pytest.raises(
            ValueError, match=r"my_fn requires argument 'xxx' for pandas_contract"
        ):
            my_fn(pd.DataFrame())


def test_no_handling__in_setup() -> None:
    """Test the no-handling mode."""
    with as_mode("skip"):

        @argument("ds", pa.SeriesSchema(int))
        def my_fn(ds: pd.Series) -> None:
            return

        my_fn(pd.Series(["xx"]))


def test_no_handling__in_call() -> None:
    """Test the no-handling mode."""

    @argument("ds", pa.SeriesSchema(int))
    def my_fn(ds: pd.Series) -> None:
        return

    with as_mode("skip"):
        my_fn(pd.Series(["xx"]))
