"""Test decorator.result decorator."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import from_arg, result

if TYPE_CHECKING:
    from collections.abc import Mapping


@pytest.mark.parametrize("lazy", [True, False])
def test(lazy: bool) -> None:
    """Test result decorator."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}))
    def my_fn() -> pd.DataFrame:
        return pd.DataFrame({"a": [1]})

    my_fn()


T = TypeVar("T", bound=Hashable)


@pytest.mark.parametrize(
    "key_arg, return_value",
    [
        ("out", {"out": pd.DataFrame({"a": [1]})}),
        (1, {1: pd.DataFrame({"a": [1]})}),
        (lambda x: x[0], {0: pd.DataFrame({"a": [1]})}),
        (None, {None: pd.DataFrame({"a": [1]})}),
    ],
)
def test_key_argument(
    key_arg: Callable[[Mapping[T, pd.DataFrame]], pd.DataFrame] | T,
    return_value: Mapping[T, pd.DataFrame],
) -> None:
    """Test result decorator with named output."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), key=key_arg)
    def my_fn() -> Mapping[Any, pd.DataFrame]:
        return return_value

    res = my_fn()
    assert res is return_value


def test_named_out() -> None:
    """Test result decorator with named output."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), key="out")
    def my_fn() -> dict[str, pd.DataFrame]:
        return {"out": pd.DataFrame({"a": [1]})}

    my_fn()


def test_arg_numeric() -> None:
    """Test result decorator with numeric key."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), key=1)
    def my_fn() -> tuple[int, pd.DataFrame]:
        return 0, pd.DataFrame({"a": [1]})

    my_fn()


def test_key_callable() -> None:
    """Test result.key argument as a callable."""

    @result(
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        key=lambda x: x[0],
    )
    def my_fn() -> list[pd.DataFrame]:
        return [pd.DataFrame({"a": [1]})]

    my_fn()


def test_same_index_as() -> None:
    """Test same_index_as argument."""

    @result(
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        same_index_as="df",
    )
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.copy().assign(xx=1)

    df = pd.DataFrame({"a": [1]})
    res = my_fn(df=df)
    assert res.index.equals(df.index)


def test_same_index_as__failing() -> None:
    """Test same_index_as argument failing."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), same_index_as="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        """Test function."""
        df.index = df.index + 1
        return df

    df = pd.DataFrame({"a": [1]})
    with pytest.raises(
        ValueError,
        match="Index of df not equal to output index",
    ):
        my_fn(df=df)


def test_same_size_as() -> None:
    """Test same_size_as argument."""

    @result(
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        same_size_as="df",
    )
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        """Test function."""
        return df.copy().assign(xx=1)

    df = pd.DataFrame({"a": [1]})
    res = my_fn(df=df)
    assert len(res) == len(df)


def test_same_size_as__failing() -> None:
    """Test same_size_as argument failing."""

    @result(
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        same_size_as="df",
    )
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return pd.concat((df, df))

    with pytest.raises(ValueError, match=r"Length of df = 1 != 2\."):
        my_fn(df=pd.DataFrame({"a": [1]}))


def test_same_size_as__failing2() -> None:
    """Test same_size_as argument failing."""

    @result(
        schema=pa.DataFrameSchema({"a": pa.Column(int)}),
        same_size_as="df",
    )
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        df.loc[len(df)] = [99]
        return df

    df = pd.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match=r"Length of df = 1 != 2\."):
        my_fn(df=df)


def test_series() -> None:
    """Test argument decorator with a Series."""

    @result(schema=pa.SeriesSchema(int))
    def my_fn() -> pd.Series:
        return pd.Series([1])

    my_fn()


def test_result_extends() -> None:
    """Test result decorator with extends argument."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(a=1)

    my_fn(pd.DataFrame({"x": [1]}))


def test_result_extends__arg_name() -> None:
    """Test result decorator with extends argument."""

    @result(schema=pa.DataFrameSchema({from_arg("col"): pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame, col: str) -> pd.DataFrame:
        return df.assign(**{col: 1})

    my_fn(pd.DataFrame({"x": [1]}), col="x")


def test_result_extends__fail_extra_column() -> None:
    """Test result decorator with extends argument failing: Extra columns."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(a=1, b=2)

    with pytest.raises(ValueError, match="Hash of result not equal to hash of df."):
        my_fn(pd.DataFrame())


def test_result_extends__fail_change_idx() -> None:
    """Test result decorator with extends argument failing: Change index."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(a=1).set_index([10])

    with pytest.raises(KeyError, match="None of .10. are"):
        my_fn(pd.DataFrame(index=[0]))
