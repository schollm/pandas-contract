"""Tests for the decorator API v2."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import argument, checks, result

if TYPE_CHECKING:
    from pandas_contract._lib import WrappedT


@argument(
    "df",
    checks.same_index_as("df2"),
    checks.same_length_as("df2, df3"),
    checks.extends("df2", modified=pa.DataFrameSchema({"a": pa.Column(int)})),
)
@result()
def foo(df: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame) -> pd.DataFrame:
    """Test function for other tests."""
    return df.assign(a=1)


class TestArgument:
    """Test argument decorator."""

    def test(self) -> None:
        """Base case."""
        df = pd.DataFrame({"a": 1}, index=[1, 2])
        foo(df, df2=df, df3=df)

    def test_same_index(self) -> None:
        """Test SameIndex check."""
        df = pd.DataFrame(index=[1, 2])
        with pytest.raises(
            ValueError,
            match="foo: Argument df: Index not equal to index of df2\\.",
        ):
            foo(df, df.reset_index(), df)

    def test_same_length(self) -> None:
        """Test SameLength check."""
        df = pd.DataFrame(index=[1, 2])
        with pytest.raises(
            ValueError,
            match="foo: Argument df: Length of df3 = 1 != 2\\.",
        ):
            foo(df, df, df[:1])

    def test_extends(self) -> None:
        """Test Extends check."""
        df = pd.DataFrame({"a": 1, "b": 2}, index=[1, 2])

        foo(df.assign(a=10), df, df)

    def test_extends_fail(self) -> None:
        """Test Extends check failing."""
        df = pd.DataFrame({"a": 1, "b": 2}, index=[1, 2])
        with pytest.raises(
            ValueError, match="foo: Argument df: extends df2: Column 'b' was changed."
        ):
            foo(df.assign(b=10), df, df)

    def test_key(self) -> None:
        """Test key."""

        @argument("dfs", pa.DataFrameSchema({"a_col": pa.Column(int)}), key=1)
        def foo_int(dfs: list[pd.DataFrame]) -> None:
            pass

        df = pd.DataFrame({"a_col": [1]})
        foo_int([df, df])

        with pytest.raises(IndexError, match="list index out of range"):
            foo_int([df])

        with pytest.raises(KeyError, match="a_col"):
            foo_int([df.drop("a_col")])


def test_result() -> None:
    """Test for result."""
    result()


@pytest.mark.parametrize(
    "verify",
    [
        argument("x"),
        argument("x", checks.same_index_as("x")),
        argument("x", checks.same_length_as("x")),
        result(checks.same_index_as("x")),
        result(checks.same_length_as("x")),
    ],
)
def test_unknown_arg(verify: WrappedT) -> None:
    """Test that the decorator raises an error for an unknown argument."""
    with pytest.raises(
        ValueError,
        match=(r"my_fn \@.* requires argument 'x' in function signature."),
    ):

        @verify
        def my_fn(a: int) -> None: ...
