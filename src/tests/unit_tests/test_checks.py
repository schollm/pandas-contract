"""Unit tests for the CheckExtends class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
import pandera as pa
import pytest
from pandera import DataFrameSchema, SeriesSchema

from pandas_contract import from_arg, result
from pandas_contract._private_checks import CheckSchema
from pandas_contract.checks import (
    extends,
    is_,
    is_not,
    removed,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class TestCheckExtends:
    """Unit tests for the CheckExtends class."""

    def test_init(self) -> None:
        """Test initialization of CheckExtends."""
        modified = DataFrameSchema()
        check = extends("df", modified=modified)
        assert check.args == ("df",)
        assert check.modified.schema is modified

    @pytest.mark.parametrize(
        "schema",
        [
            SeriesSchema(),
            [1, 2],
        ],
    )
    def test_init__fail(self, schema: Any) -> None:
        """Test initialization of CheckExtends."""
        with pytest.raises(
            TypeError,
            match="CheckExtends: If modified is set, then it must be of type "
            "pandera.DataFrameSchema, got",
        ):
            extends("df", schema)

    @pytest.mark.parametrize("arg, expects", [("df", True), ("", False), (None, False)])
    def test_is_active(self, arg: str | None, expects: bool) -> None:
        """Test is_active property of CheckExtends."""
        assert extends(arg, DataFrameSchema()).is_active == expects

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
    def test_mk_check(self, df_to_be_extend: pd.DataFrame, expect: list[str]) -> None:
        """Test mk_check method of CheckExtends."""
        check = extends("df", modified=DataFrameSchema())
        out_df = pd.DataFrame({"a": [1]}, index=[0])
        fn = check.mk_check(lambda df: df, (df_to_be_extend,), {})
        assert list(fn(out_df)) == expect

    def test_callable_key_in_modified(self) -> None:
        """Let extends.modified schema have a callable key."""

        @result(extends("df", DataFrameSchema({from_arg("col"): pa.Column(int)})))
        def my_fn(df: pd.DataFrame, col: str = "x") -> pd.DataFrame:
            return df.assign(**{col: 1})

        my_fn(pd.DataFrame(index=[0]))

    def test_callable_key_in_modified__failure(self) -> None:
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

    def test_mk_check__invalid_output(self) -> None:
        """Test mk_check method of CheckExtends."""
        check = extends("df", modified=DataFrameSchema())
        df = pd.DataFrame([])
        df2 = pd.Series([])
        fn = check.mk_check(lambda df: df, (df,), {})
        assert list(fn(df2)) == [
            "extends df: Backend DataFrameSchema not applicable to Series",
            "extends df: <input> not a DataFrame, got Series.",
        ]

    def test_mk_check__invalid_output__identical_arg(self) -> None:
        """Test mk_check method of CheckExtends."""
        check = extends("df2", DataFrameSchema())
        df = pd.Series([])
        fn = check.mk_check(lambda df2, df: df2, (df, df), {})
        assert list(fn(df)) == [
            "extends df2: Backend DataFrameSchema not applicable to Series",
            "extends df2: <input> not a DataFrame, got Series.",
            "extends df2: df2 not a DataFrame, got Series.",
        ]

    def test_modified_is_none(self) -> None:
        """Test for extends(modified=None)."""
        check = extends("df", modified=None)
        df = pd.DataFrame({"a": [1]})
        fn = check.mk_check(lambda df: None, (df,), {})
        assert list(fn(df)) == []

    def test_modified_is_none__add_column(self) -> None:
        """Test for extends(modified=None) and new column is added."""
        check = extends("df", modified=None)
        df = pd.DataFrame({"a": [1]})
        fn = check.mk_check(lambda df: None, (df,), {})
        assert list(fn(df.assign(x=1))) == [
            "extends df: Columns differ: ['a', 'x'] != ['a']"
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

    def test_key(self) -> None:
        """Test mk_check function if schema is None."""
        check = CheckSchema(
            schema=DataFrameSchema(
                {
                    from_arg("a_col"): pa.Column(),
                    from_arg("b_col"): pa.Column(),
                }
            )
        )
        check_fn = check.mk_check(lambda a_col, b_col: 0, ("a", "b"), {})
        assert list(check_fn(pd.DataFrame(columns=["a", "b"]))) == []
        errs = list(check_fn(pd.DataFrame(columns=["a", "x"])))
        assert len(errs) == 1
        assert "'b'" in str(errs[0])
        assert isinstance(errs[0], str)


class TestIs:
    """Test cases for CheckIsNot."""

    def test(self) -> None:
        """Test for inplace argument."""
        res = is_("df")
        df = pd.DataFrame(index=[])
        fn = res.mk_check(lambda df: df, (df,), {})
        assert list(fn(df)) == []
        assert list(fn(df.copy())) == ["is not df"]

    def test_check_none(self) -> None:
        """Test for inplace argument."""
        res = is_(None)
        df = pd.DataFrame(index=[])
        fn = res.mk_check(lambda df: df, (df,), {})
        assert list(fn(df)) == []
        assert list(fn(df.copy())) == []


class TestCheckIsNot:
    """Test cases for CheckIsNot."""

    @pytest.mark.parametrize(
        "others, is_active",
        [("df", True), (["df"], True), (["df", "df2"], True), ([], False)],
    )
    def test_is_active(self, others: Sequence[str], is_active: bool) -> None:
        """Test is_active property of CheckIsNot."""
        assert is_not(others).is_active == is_active

    def test_check(self) -> None:
        """Test is_not.mk_check."""
        df = pd.DataFrame()
        check_fn = is_not("df").mk_check(lambda df: None, (df,), {})
        assert list(check_fn(df.copy())) == []
        assert list(check_fn(df)) == ["is df"]


class TestCheckRemove:
    """Test for checks.remove."""

    def test(self) -> None:
        """Base test."""
        fn = removed(["x"]).mk_check(lambda: 0, (), {})
        assert list(fn(pd.DataFrame(columns=["a"]))) == []

    def test_from_arg__single(self) -> None:
        """Test with column from_arg."""
        fn = removed([from_arg("arg")]).mk_check(lambda arg: 0, ("x",), {})
        assert list(fn(pd.DataFrame(columns=["x"]))) == [
            "Column 'x' still exists in DataFrame"
        ]

    def test_from_arg__multipe(self) -> None:
        """Test with column from_arg."""
        fn = removed([from_arg("arg")]).mk_check(lambda arg: 0, (["x", "y"],), {})
        assert list(fn(pd.DataFrame(columns=["x"]))) == [
            "Column 'x' still exists in DataFrame"
        ]

    def test_failing(self) -> None:
        """Test failing test."""
        fn = removed(["x"]).mk_check(lambda: 0, (), {})
        assert list(fn(pd.DataFrame(columns=["x"]))) == [
            "Column 'x' still exists in DataFrame"
        ]

    @pytest.mark.parametrize("columns, is_active", [([], False), (["x"], True)])
    def test_is_active(self, columns: list[str], is_active: bool) -> None:
        """Test .is_active if columns exist."""
        assert removed(columns).is_active == is_active
