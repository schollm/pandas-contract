from __future__ import annotations

import copy
from dataclasses import dataclass
from itertools import zip_longest
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

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable

    from pandera.api.base.schema import BaseSchema

    from ._lib import MyFunctionType


DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], list[str]]


class Check(Protocol):  # pragma: no cover
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
        if schema is None:  # pragma: no cover
            raise RuntimeError(
                "schema: Schema must be provided (This should never happen)."
            )
        if isinstance(schema, pa.DataFrameSchema):
            schema = copy.deepcopy(schema)
            for col in list(getattr(schema, "columns", {})):
                if callable(col):
                    col_arg = col(fn, args, kwargs)
                    col_schema = schema.columns.pop(col)
                    for col_val in col_arg if isinstance(col_arg, list) else [col_arg]:
                        schema.columns[col_val] = col_schema
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
    arg_name: str

    @property
    def is_active(self) -> bool:
        return bool(self.extends)

    def __post_init__(self) -> None:
        super().__init__()
        if self.is_active:
            if self.schema is None:
                raise ValueError("extends: Schema must be provided.")
            if not isinstance(self.schema, pa.DataFrameSchema):
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
            if (df_hash := self._get_hash(df)) != hash_:
                return list(self._get_diff(hash_, df_hash))
            return []

        return check

    def _get_hash(self, df: Any) -> dict[str, Any]:
        if not isinstance(self.schema, pa.DataFrameSchema):  # pragma: no cover
            # We check this in __post_init__, but mypy doesn't see it.
            raise RuntimeError("This should never happen")  # noqa:TRY004

        if not isinstance(df, pd.DataFrame):
            return {"err": f"not a DataFrame, got {type(df)}.", "hash": id(df)}

        df_hash = df[[c for c in df if c not in self.schema.columns]]
        return {
            "type": pd.DataFrame,
            "index": hash(df.index.to_numpy().tobytes()),
            "columns": list(df_hash.columns),
            "data": [(col, hash(df_hash[col].to_numpy().tobytes())) for col in df_hash],
        }

    def _get_diff(
        self, hash_self: dict[str, Any], hash_other: dict[str, Any]
    ) -> Iterable[str]:
        """Get the difference between two hashes."""
        prefix = f"extends {self.extends}: "
        if "err" in hash_self or "err" in hash_other:
            if "err" in hash_self:
                yield f"{prefix}{self.arg_name} {hash_self['err']}"
            if "err" in hash_other:
                yield f"{prefix}{self.extends} {hash_other['err']}"
            return

        if hash_self["index"] != hash_other["index"]:
            yield f"{prefix}index differ"

        if hash_self["columns"] != hash_other["columns"]:
            yield (
                f"{prefix}Columns differ: "
                f"{hash_self['columns']} != {hash_other['columns']}"
            )

        for (col1, val1), (col2, val2) in zip_longest(
            cast("list[tuple[str, int]]", hash_self["data"]),
            cast("list[tuple[str, int]]", hash_other["data"]),
            fillvalue=("<missing>", -1),
        ):
            if col1 == col2 and val1 != val2:
                yield f"{prefix}Column {col1!r} was changed."


@dataclass(frozen=True)
class CheckInplace:
    other: str | None

    @property
    def is_active(self) -> bool:
        return bool(self.other)

    def mk_check(
        self, fn: Callable, args: tuple[Any], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        def check_fn(df: pd.DataFrame | pd.Series) -> list[str]:
            """Check if input is self,other."""
            if self.other is None:
                return []
            other_df = get_df_arg(fn, self.other, args, kwargs)
            return [f"is not {self.other}"] if df is not other_df else []

        return check_fn
