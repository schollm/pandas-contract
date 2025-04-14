"""Unit tests for the CheckExtends class."""

from typing import Any

import pandas as pd
import pytest
from pandera import DataFrameSchema, SeriesSchema

from pandas_contract._checks import CheckExtends, CheckInplace, CheckSchema


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
            ValueError, match="extends: Schema must be (provided|a DataFrameSchema)."
        ):
            CheckExtends("df", schema, "foo")

    @pytest.mark.parametrize(
        "check, expects",
        [
            (CheckExtends("df", DataFrameSchema(), "foo"), True),
            (CheckExtends("", DataFrameSchema(), "foo"), False),
            (CheckExtends(None, DataFrameSchema(), "foo"), False),
        ],
    )
    def test_is_active(self, check: CheckExtends, expects: bool) -> None:
        """Test is_active property of CheckExtends."""
        assert check.is_active == expects

    @pytest.mark.parametrize(
        "df, expect",
        [
            (pd.DataFrame({"a": [1]}), []),
            (pd.DataFrame({"a": [1.0]}), ["extends df: Column 'a' was changed."]),
            (
                pd.DataFrame({"b": [1]}),
                ["extends df: Columns differ: ['b'] != ['a']"],
            ),
            (pd.DataFrame({"a": [1]}, index=[1]), ["extends df: index differ"]),
            (1, ["extends df: df2 not a DataFrame, got <class 'int'>."]),
        ],
    )
    def test_mk_check(self, df: pd.DataFrame, expect: list[str]) -> None:
        """Test mk_check method of CheckExtends."""
        check = CheckExtends("df", DataFrameSchema(), "df2")
        df2 = pd.DataFrame({"a": [1]}, index=[0])
        fn = check.mk_check(lambda df: df, (df,), {})
        assert fn(df2) == expect

    def test_mk_check__invalid_output(self) -> None:
        """Test mk_check method of CheckExtends."""
        check = CheckExtends("df", DataFrameSchema(), "df2")
        df = pd.Series([])
        df2 = pd.Series([])
        fn = check.mk_check(lambda df: df, (df,), {})
        assert fn(df2) == [
            "extends df: df2 not a DataFrame, got <class 'pandas.core.series.Series'>.",
            "extends df: df not a DataFrame, got <class 'pandas.core.series.Series'>.",
        ]

    def test_no_extend(self) -> None:
        """Test CheckExtends with .extends=None."""
        check = CheckExtends(None, DataFrameSchema(), "df2")
        res = check.mk_check(lambda df: df, (1,), {})
        assert res(pd.Series([])) == []


class TestCheckSchema:
    """Test cases for CheckSchema."""

    def test_none(self) -> None:
        """Test mk_check function if schema is None."""
        check = CheckSchema(
            schema=None, head=None, tail=None, sample=None, random_state=None
        )
        res = check.mk_check(lambda _: 0, (), {})
        assert res(pd.Series()) == []


class TestCheckInplace:
    """Test cases for CheckIdentity."""

    def test(self) -> None:
        """Test for inplace argument."""
        res = CheckInplace(other="df")
        df = pd.DataFrame(index=[])
        fn = res.mk_check(lambda df: df, (df,), {})
        assert fn(df) == []
        assert fn(df.copy()) == ["is not df"]

    def test_check_none(self) -> None:
        """Test for inplace argument."""
        res = CheckInplace(other=None)
        df = pd.DataFrame(index=[])
        fn = res.mk_check(lambda df: df, (df,), {})
        assert fn(df) == []
        assert fn(df.copy()) == []
