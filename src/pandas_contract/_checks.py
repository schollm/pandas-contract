from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Protocol,
    Union,
    cast,
)

import pandas as pd
import pandera as pa
import pandera.errors as pa_errors

from pandas_contract._lib import get_df_arg

if TYPE_CHECKING:
    from pandera.api.base.schema import BaseSchema

    from ._lib import MyFunctionType


DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], list[str]]


class Check(Protocol):
    """Check the DataFrame."""

    @property
    def is_active(self) -> bool:
        """Whether the check is active.

        This is used by the decorator to determine whether the check should be applied
        at all. is_active can be set as attribute within __(post)init__.
        """
        ...

    def mk_check(
        self, fn: MyFunctionType, args: tuple, kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Create a check function.

        The check function takes a single data-frame and return a list of errors as
        a strings.

        :param fn: The function for which the check is created.
        :param args: The positional arguments of the function.
        :param kwargs: The keyword arguments of the function.
        :return: A function that takes a single data-frame and returns a list of errors.
        """
        ...


@dataclass(frozen=True)  # type: ignore[call-overload]
class CheckSchema:
    """Check the DataFrame using the schema."""

    schema: pa.DataFrameSchema | pa.SeriesSchema | None
    head: int | None
    tail: int | None
    sample: int | None
    random_state: int | None

    @property
    def is_active(self) -> bool:
        return self.schema is not None

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        if self.schema is None:
            return cast("DataCheckFunctionT", lambda _: [])

        def check(df: pd.DataFrame | pd.Series) -> list[str]:
            try:
                self._parse_schema(self.schema, fn, args, kwargs).validate(
                    df,
                    head=self.head,
                    tail=self.tail,
                    sample=self.sample,
                    random_state=self.random_state,
                    lazy=True,
                    inplace=True,
                )

            except (pa_errors.SchemaErrors, pa_errors.SchemaError) as exc:
                return list(exc.args)
            else:
                return []

        return check

    @staticmethod
    def _parse_schema(
        schema: BaseSchema | None,
        fn: Callable,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> BaseSchema:
        """Replace column name functions with actual column names.

        Return a copy of the schema where any callables column names are replaced with
        the actual values.

        :param fn: The function used to extract the column argument from.
        :param args: The positional arguments of the function.
        :param kwargs: The keyword arguments of the function.
        :return: The schema with the actual column names.
        """
        if schema is None:
            raise RuntimeError(
                "schema: Schema must be provided (This should never happen)."
            )
        if isinstance(schema, pa.DataFrameSchema):
            schema = copy.deepcopy(schema)
            for col in list(getattr(schema, "columns", {})):
                if callable(col):
                    schema.columns[col(fn, args, kwargs)] = schema.columns.pop(col)
        return schema


@dataclass(frozen=True)
class CheckKeepIndex:
    """Check that the DataFrame index is the same as another DataFrame.

    This check ensures that the index of the data-frame is identical to the dataframe of
    another argument (or a list of arguments).

    Example:
    ```
    @result(same_index_as="df2")
    def my_fn(df: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
        return df.join(df2)
    ```

    """

    same_index_as: list[str]

    @property
    def is_active(self) -> bool:
        return bool(self.same_index_as)

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        indices = [
            (arg, get_df_arg(fn, arg, args, kwargs).index) for arg in self.same_index_as
        ]
        return lambda df: [
            f"Index of {other_arg} not equal to output index."
            for other_arg, other_idx in indices
            if not df.index.equals(other_idx)
        ]


@dataclass(frozen=True)
class CheckKeepLength:
    """Check the DataFrame and keep the index."""

    same_length_as: list[str]

    @property
    def is_active(self) -> bool:
        return bool(self.same_length_as)

    def mk_check(
        self, fn: Callable, args: tuple[Any], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        lengths = [
            (arg, len(get_df_arg(fn, arg, args, kwargs))) for arg in self.same_length_as
        ]

        return lambda df: [
            f"Length of {other_arg} = {other_len} != {len(df)}."
            for other_arg, other_len in lengths
            if len(df) != other_len
        ]


@dataclass(frozen=True)
class CheckExtends:
    """Ensures resulting dataframe extends another dataframe.

    Check that the resulting dataframe extends another dataframe (provided
    via argument name). It ensures that
    a) only the columns are added that are also provided in `schema` and
    b) Any other columns have not been modified.

    Example:
    ```
    @result(schema=pa.DataFrameSchema({"a": pa.Column(int)}), extends="df")
    def my_fn(df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(a=1)
    ```

    """

    extends: str | None
    schema: pa.DataFrameSchema | pa.SeriesSchema | None

    @property
    def is_active(self) -> bool:
        return self.extends is not None

    def __post_init__(self) -> None:
        super().__init__()
        if self.is_active:
            if self.schema is None:
                raise ValueError("extends: Schema must be provided.")
            if isinstance(self.schema, pa.SeriesSchema):
                raise ValueError("extends: Schema must be a DataFrameSchema.")

    def mk_check(
        self, fn: Callable, args: tuple[Any], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        """Check the DataFrame and keep the index."""
        if not self.extends:
            return lambda _: []

        df_extends = get_df_arg(fn, self.extends, args, kwargs)
        hash_ = self._get_hash(df_extends)

        def check(df: pd.DataFrame | pd.Series) -> list[str]:
            """Check the DataFrame and keep the index."""
            if self._get_hash(df) != hash_:
                return [f"Hash of result not equal to hash of {self.extends}."]
            return []

        return check

    def _get_hash(self, df: pd.DataFrame | pd.Series) -> object:
        if not isinstance(self.schema, pa.DataFrameSchema):
            return 0
        if isinstance(df, pd.Series):
            return hash(df.to_numpy().tobytes()) + hash(df.index.to_numpy().tobytes())
        df_hash = df[[c for c in df if c not in self.schema.columns]]
        return hash(df_hash.to_numpy().tobytes()) + hash(
            df_hash.columns.to_numpy().tobytes()
        )
