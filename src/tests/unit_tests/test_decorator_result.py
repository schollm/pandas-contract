"""Test decorator.result decorator."""

from __future__ import annotations

from collections.abc import Hashable
from typing import TYPE_CHECKING, Any, Callable, TypeVar

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import as_mode, from_arg, result

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


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
        match="Output: Index not equal to index of df\\.",
    ):
        my_fn(df=df)


def test_same_size_as() -> None:
    """Test same_size_as argument."""

    @result(same_size_as="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        """Test function."""
        return df.copy().assign(xx=1)

    df = pd.DataFrame({"a": [1]})
    res = my_fn(df=df)
    assert len(res) == len(df)


def test_same_size_as__failing() -> None:
    """Test same_size_as argument failing."""

    @result(same_size_as="df")
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


def test_result_extends__arg_name_is_list() -> None:
    """Test result decorator with extends argument."""

    @result(schema=pa.DataFrameSchema({from_arg("cols"): pa.Column()}))
    def my_fn(cols: list[str]) -> pd.DataFrame:
        return pd.DataFrame(dict.fromkeys(cols, (0,)))

    my_fn(["x", "y"])


def test_result_extends__fail_extra_column() -> None:
    """Test result decorator with extends argument failing: Extra columns."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(a=1, b=2)

    with pytest.raises(ValueError, match="Columns differ") as exc:
        my_fn(pd.DataFrame())
    assert "my_fn: Output: extends df: Columns differ: ['b'] != []" in exc.value.args[0]


def test_result_extends__fail_change_idx() -> None:
    """Test result decorator with extends argument failing: Change index."""

    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(a=1).set_index([10])

    with pytest.raises(KeyError, match="None of .10. are"):
        my_fn(pd.DataFrame(index=[0]))


def test_inplace() -> None:
    """Check inplace argument."""

    @result(is_="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df


def test_no_handling__in_setup() -> None:
    """Test the no-handling mode."""
    with as_mode("skip"):

        @result(same_size_as="df")
        def my_fn(df: pd.DataFrame) -> pd.DataFrame:
            return pd.DataFrame(index=[1, 2, 3, 4])

        my_fn(pd.DataFrame())


def test_no_handling__in_call() -> None:
    """Test the no-handling mode."""

    @result(same_size_as="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(index=[1, 2, 3, 4])

    with as_mode("skip"):
        my_fn(pd.DataFrame())


class TestIsNot:
    """Ensure argument is not identical to other."""

    @pytest.mark.parametrize(
        "is_not",
        [
            (),
            [],
            "df",
            ["df"],
            ["df", "df2"],
            "df, df2",  # foo
            " df  ,  df2 ",
        ],
    )
    def test_is_not(self, is_not: Sequence[str]) -> None:
        """Test is_not argument."""

        @result(is_not=is_not)
        def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
            return pd.concat((df, df2))

        my_fn(pd.DataFrame(), pd.DataFrame())

    def test_is_not__fail(self) -> None:
        """Test is_not argument failing."""

        @result(is_not="df")
        def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
            del df2
            return df

        with pytest.raises(ValueError, match="Output: is df"):
            my_fn(pd.DataFrame(), pd.DataFrame())
