"""Tests for the `argument` and `result` decorators."""

from __future__ import annotations

from typing import Callable

import pandas as pd
import pandera as pa
import pytest
from pandas import DataFrame

import pandas_contract as pc
from pandas_contract import argument, result


@pytest.mark.parametrize(
    "verify",
    [
        argument("x"),
        argument("x", same_index_as="x"),
        argument("x", same_size_as="x"),
        result(pc.checks.same_index_as("x")),
        result(pc.checks.same_length_as("x")),
    ],
)
def test_unknown_arg(verify: Callable) -> None:
    """Test that the decorator raises an error for an unknown argument."""
    with pytest.raises(
        ValueError,
        match=(r"requires argument 'x' in function signature."),
    ):

        @verify
        def my_fn(a: int) -> None:
            pass


class TestComplete:
    """Test multiple decorators on the same function."""

    @argument("df", pa.DataFrameSchema({"a": pa.Column(int)}))
    @argument(
        "df2", pa.DataFrameSchema({"b": pa.Column(int)}), pc.checks.same_length_as("df")
    )
    @argument("ds", pa.SeriesSchema(pa.Int), pc.checks.same_index_as("df"))
    @result(
        pa.DataFrameSchema({"x": pa.Column(int)}),
        pc.checks.extends("df", modified=pa.DataFrameSchema({"x": pa.Column(int)})),
        pc.checks.same_index_as("df2"),
        pc.checks.is_("df"),
    )
    def my_fn(
        self,
        df: DataFrame,
        df2: pd.DataFrame,
        ds: pd.Series,
        callback: Callable[[pd.DataFrame, pd.DataFrame, pd.Series], pd.DataFrame]
        | None = None,
    ) -> pd.DataFrame:
        """Test function."""
        if callback is None:
            df["x"] = df["a"] + df2["b"] + ds
            return df
        return callback(df, df2, ds)

    @pytest.fixture
    def df(self) -> pd.DataFrame:
        """Df input for my_fn."""
        return pd.DataFrame({"a": [1, 2]}, index=[10, 20])

    @pytest.fixture
    def df2(self) -> pd.DataFrame:
        """df2 input for my_fn."""
        return pd.DataFrame({"b": [0, 1]}, index=[10, 20])

    @pytest.fixture
    def ds(self) -> pd.Series:
        """Ds input for my_fn."""
        return pd.Series([10, 20], index=[10, 20])

    def test(self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series) -> None:
        """Test with default values."""
        assert isinstance(self.my_fn(df, df2, ds=ds), pd.DataFrame)

    def test_change_input(
        self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
    ) -> None:
        """Test with default values, but change input."""

        def change_df(
            df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
        ) -> pd.DataFrame:
            df["a"] -= 1
            df["x"] = df2["b"]
            return df

        with pytest.raises(ValueError, match="Column 'a' was changed"):
            self.my_fn(df, df2, ds=ds, callback=change_df)

    def test_different_input_index(
        self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
    ) -> None:
        """Change index of one input."""
        df_new = pd.DataFrame(df.to_dict(orient="list"), index=[100, 200])
        with pytest.raises(
            ValueError, match="Argument ds: Index not equal to index of df."
        ):
            self.my_fn(df_new, df2, ds=ds)

    def test_extra_output_col(
        self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
    ) -> None:
        """Change index of one input."""

        def change_df(
            df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
        ) -> pd.DataFrame:
            return df.assign(x=1, extra=0)

        with pytest.raises(
            ValueError, match="Output: extends df: Columns differ.*'extra'."
        ):
            self.my_fn(df, df2, ds=ds, callback=change_df)

    def test_change_output_index(
        self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
    ) -> None:
        """Change index of one input."""

        def change_df(
            df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
        ) -> pd.DataFrame:
            res = df.assign(x=1)
            res.index += 1
            return res

        with pytest.raises(
            ValueError,
            match="Output: Index not equal to index of df2.",
        ) as exc_info:
            self.my_fn(df, df2, ds=ds, callback=change_df)
        exc_info.match(" Output: extends df: index differ")

    def test_remove_output_col(
        self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
    ) -> None:
        """Change index of one input."""

        def change_df(
            df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
        ) -> pd.DataFrame:
            df.drop(columns="a", inplace=True)  # noqa:PD002
            df["x"] = 1
            return df

        with pytest.raises(ValueError, match=r"Columns differ:") as exc:
            self.my_fn(df, df2, ds=ds, callback=change_df)
        assert "Output: extends df: Columns differ: [] != ['a']" in exc.value.args[0]

    def test_output_is_input__fail(
        self, df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
    ) -> None:
        """Test result.inplace argument."""

        def change_df(
            df: pd.DataFrame, df2: pd.DataFrame, ds: pd.Series
        ) -> pd.DataFrame:
            return df.assign(x=ds)

        with pytest.raises(ValueError, match="Output: is not df"):
            self.my_fn(df, df2, ds, callback=change_df)
