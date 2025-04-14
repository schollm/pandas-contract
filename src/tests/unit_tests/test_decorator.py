"""Tests for the `argument` and `result` decorators."""

from __future__ import annotations

import pandas as pd
import pandera as pa
import pytest

from pandas_contract import argument, result


@pytest.mark.parametrize(
    "verify",
    [
        argument(arg="x"),
        argument(arg="a", same_index_as="x"),
        argument(arg="a", same_size_as="x"),
        result(same_index_as="x"),
        result(same_size_as="x"),
    ],
)
def test_unknown_arg(verify: argument | result) -> None:
    """Test that the decorator raises an error for an unknown argument."""
    with pytest.raises(
        ValueError,
        match=(
            r"my_fn \@argument\(arg='x'\) requires argument 'x' in function signature."
        ),
    ):

        @argument(arg="x")
        def my_fn(a: int) -> None:
            pass


def test_multiple_decorators() -> None:
    """Test multiple decorators on the same function."""

    @result(
        same_index_as="df", schema=pa.DataFrameSchema({"a": pa.Column(int)}, checks=[])
    )
    @argument(arg="df", same_index_as="df2")
    @argument(arg="df", same_size_as="df2")
    @result(same_index_as="df")
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df

    my_fn(pd.DataFrame({"a": [1]}), pd.DataFrame({"a": [1]}))
