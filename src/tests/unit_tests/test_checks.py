"""Unit tests for the CheckExtends class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
import pytest
from pandera import DataFrameSchema, SeriesSchema

from pandas_contract._checks import CheckExtends, CheckIs, CheckIsNot, CheckSchema

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestCheckExtends:
    """Unit tests for the CheckExtends class."""

    def test_init(self) -> None:
        """Test initialization of CheckExtends."""
        check = CheckExtends("df", DataFrameSchema(), "foo")
        assert check.extends == "df"
        assert check.schema == DataFrameSchema()
        assert check.arg_name == "foo"

    @pytest.mark.parametrize(
        "schema",
        [
            SeriesSchema(),
            None,
            [1, 2],
        ],
    )
    def test_init__fail(self, schema: Any) -> None:
        """Test initialization of CheckExtends."""
        with pytest.raises(
            TypeError,
            match="CheckExtends: If extends is set, then schema must be of type "
            "pandera.DataFrameSchema, got",
        ):
            CheckExtends("df", schema, "foo")

    @pytest.mark.parametrize("arg, expects", [("df", True), ("", False), (None, False)])
    def test_is_active(self, arg: str | None, expects: bool) -> None:
        """Test is_active property of CheckExtends."""
        assert CheckExtends(arg, DataFrameSchema(), "foo").is_active == expects

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
            (1, ["extends df: df not a DataFrame, got <class 'int'>."]),
        ],
    )
    def test_mk_check(self, df_to_be_extend: pd.DataFrame, expect: list[str]) -> None:
        """Test mk_check method of CheckExtends."""
        check = CheckExtends(extends="df", schema=DataFrameSchema(), arg_name="out_df")
        out_df = pd.DataFrame({"a": [1]}, index=[0])
        fn = check.mk_check(lambda df: df, (df_to_be_extend,), {})
        assert list(fn(out_df)) == expect

    def test_mk_check__invalid_output(self) -> None:
        """Test mk_check method of CheckExtends."""
        check = CheckExtends("df", DataFrameSchema(), "df2")
        df = pd.Series([])
        df2 = pd.Series([])
        fn = check.mk_check(lambda df: df, (df,), {})
        assert list(fn(df2)) == [
            "extends df: df2 not a DataFrame, got <class 'pandas.core.series.Series'>.",
            "extends df: df not a DataFrame, got <class 'pandas.core.series.Series'>.",
        ]

    def test_mk_check__invalid_output__identical_arg(self) -> None:
        """Test mk_check method of CheckExtends."""
        check = CheckExtends("df", DataFrameSchema(), "df2")
        df = pd.Series([])
        fn = check.mk_check(lambda df: df, (df,), {})
        assert list(fn(df)) == [
            "extends df: df2 not a DataFrame, got <class 'pandas.core.series.Series'>.",
            "extends df: df not a DataFrame, got <class 'pandas.core.series.Series'>.",
        ]


class TestCheckSchema:
    """Test cases for CheckSchema."""

    def test_none(self) -> None:
        """Test mk_check function if schema is None."""
        check = CheckSchema(
            schema=None, head=None, tail=None, sample=None, random_state=None
        )
        res = check.mk_check(lambda _: 0, (), {})
        assert res(pd.Series()) == []


class TestCheckIs:
    """Test cases for CheckIsNot."""

    def test(self) -> None:
        """Test for inplace argument."""
        res = CheckIs(other="df")
        df = pd.DataFrame(index=[])
        fn = res.mk_check(lambda df: df, (df,), {})
        assert fn(df) == []
        assert fn(df.copy()) == ["is not df"]

    def test_check_none(self) -> None:
        """Test for inplace argument."""
        res = CheckIs(other=None)
        df = pd.DataFrame(index=[])
        fn = res.mk_check(lambda df: df, (df,), {})
        assert fn(df) == []
        assert fn(df.copy()) == []


class TestCheckIsNot:
    """Test cases for CheckIsNot."""

    @pytest.mark.parametrize(
        "others, is_active",
        [("df", True), (["df"], True), (["df", "df2"], True), ([], False)],
    )
    def test_is_active(self, others: Sequence[str], is_active: bool) -> None:
        """Test is_active property of CheckIsNot."""
        assert CheckIsNot(others=others).is_active == is_active
