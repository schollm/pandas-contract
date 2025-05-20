"""Unit tests for the CheckExtends class."""

from __future__ import annotations

import pandas as pd

from pandas_contract import argument
from pandas_contract.checks import (
    is_,
    is_not,
)


class TestIs:
    """Test cases for CheckIsNot."""

    def test(self) -> None:
        """Test for inplace argument."""
        res = is_("df")
        assert res is not None
        df = pd.DataFrame(index=[])
        fn = res(lambda df: df, (df,), {})
        assert list(fn(df)) == []
        assert list(fn(df.copy())) == ["is not df"]

    def test_check_none(self) -> None:
        """Test for inplace argument."""
        res = is_("")
        assert res is None

    def test_argument(self) -> None:
        """Test with argument decorator."""

        @argument("df", is_("df2"))
        def foo(df: pd.DataFrame, df2: pd.DataFrame) -> None:
            pass

        df = pd.DataFrame()
        foo(df, df)

    def test_argument_none(self) -> None:
        """Test with is_(arg=None)."""

        @argument("df", is_(""))
        def foo(df: pd.DataFrame, df2: pd.DataFrame) -> None:
            pass

        df = pd.DataFrame()
        foo(df, df)


class TestCheckIsNot:
    """Test cases for CheckIsNot."""

    def test_check(self) -> None:
        """Test is_not."""
        df = pd.DataFrame()
        check_factory = is_not("df")
        assert check_factory is not None
        check_fn = check_factory(lambda df: None, (df,), {})
        assert list(check_fn(df.copy())) == []
        assert list(check_fn(df)) == ["is df"]
