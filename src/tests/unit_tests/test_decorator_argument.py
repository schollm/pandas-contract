"""Tests for the argument decorator."""

from __future__ import annotations

from typing import Union

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import argument, as_mode, from_arg

MaybeListT = Union[list[str], str]


def test() -> None:
    """Test argument decorator."""

    @argument("df", schema=pa.DataFrameSchema({"a": pa.Column(int)}))
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

    @argument("df", schema=pa.DataFrameSchema({"a": pa.Column(int)}))
    def my_fn(df: pd.DataFrame) -> int:
        return len(df)

    with as_mode("error"):
        my_fn(df=pd.DataFrame({"a": ["x"]}))

    assert "my_fn: Argument df: " in caplog.text


@pytest.mark.parametrize("same_index_as", [["df2"], "df2"])
def test_same_index_as(same_index_as: list[str] | str) -> None:
    """Test same_index_as argument."""

    @argument(
        "df",
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        same_index_as=same_index_as,
    )
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    df_ = pd.DataFrame({"a": [1]})
    res = my_fn(df=df_, df2=pd.DataFrame({"b": ["x"]}))
    assert res is df_


@pytest.mark.parametrize("same_index_as", [("df2"), (["df2"])])
def test_same_index_as_failing(
    same_index_as: MaybeListT, caplog: pytest.LogCaptureFixture
) -> None:
    """Test same_index_as argument failing."""

    @argument(
        "df",
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        same_index_as=same_index_as,
    )
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    with as_mode("error"):
        my_fn(
            df=pd.DataFrame([[0]], index=[0]),
            df2=pd.DataFrame([[0]], index=[10]),
        )
    assert "Index not equal to index of df2." in caplog.text


@pytest.mark.parametrize("same_index_as", ["df3", ["df3"], ["df2", "df3"]])
def test_same_index_as__no_such_argument(
    same_index_as: MaybeListT, caplog: pytest.LogCaptureFixture
) -> None:
    """Test same_index_as argument failing because of missing argument."""
    with pytest.raises(ValueError, match="requires argument 'df3'"):

        @argument(
            "df",
            schema=pa.DataFrameSchema({"a": pa.Column(int)}),
            same_index_as=same_index_as,
        )
        def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
            return df


def test_series() -> None:
    """Test argument decorator with a Series."""

    @argument(
        "ds",
        schema=pa.SeriesSchema(int, name="a", nullable=False),
    )
    def my_fn(ds: pd.Series) -> int:
        return len(ds)

    my_fn(ds=pd.Series([1], name="a"))


def test_extends() -> None:
    """Test extends argument."""

    @argument(
        "df",
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        extends="df2",
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
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        extends="df2",
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
        schema=pa.SeriesSchema(float, name="a", nullable=False),
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

        @argument("df", schema=pa.DataFrameSchema({from_arg("a_col"): pa.Column(int)}))
        def my_fn(df: pd.DataFrame, a_col: str) -> int:
            """Test function."""
            return len(df[a_col])

        assert my_fn(df=pd.DataFrame({"a": [1]}), a_col="a") == 1

    def test_unknown_arg(self) -> None:
        """Test from_arg function failing."""

        @argument("df", schema=pa.DataFrameSchema({from_arg("x_col"): pa.Column(int)}))
        def my_fn(df: pd.DataFrame, a_col: str) -> int:
            """Test function."""
            return len(df[a_col])

        with pytest.raises(ValueError, match=r"my_fn does mot have argument 'x_col'"):
            my_fn(df=pd.DataFrame({"a": [1]}), a_col="a")

    def test_no_such_column(self) -> None:
        """Test from_arg function failing."""
        with pytest.raises(ValueError, match=r"requires argument 'xxx'"):

            @argument("df", same_index_as="xxx")
            def my_fn(df: pd.DataFrame) -> int:
                """Test function."""
                return len(df)


def test_no_handling__in_setup() -> None:
    """Test the no-handling mode."""
    with as_mode("skip"):

        @argument("ds", schema=pa.SeriesSchema(int))
        def my_fn(ds: pd.Series) -> None:
            return

        my_fn(pd.Series(["xx"]))


def test_no_handling__in_call() -> None:
    """Test the no-handling mode."""

    @argument("ds", schema=pa.SeriesSchema(int))
    def my_fn(ds: pd.Series) -> None:
        return

    with as_mode("skip"):
        my_fn(pd.Series(["xx"]))
