from __future__ import annotations

import copy
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Protocol, Union, cast

import pandas as pd
import pandera as pa
import pandera.errors as pa_errors

if TYPE_CHECKING:  # pragma: no cover
    from pandera.api.base.schema import BaseSchema

    from ._lib import MyFunctionType


DataCheckFunctionT = Callable[[Union[pd.DataFrame, pd.Series]], Iterable[str]]


class Check(Protocol):  # pragma: no cover
    """Protocol for a DataFrame or Series check class."""

    @property
    def args(self) -> Sequence[str]:
        """Get a list of all arguments."""
        ...

    @property
    def is_active(self) -> bool:
        """Whether the check is active.

        This is used by the decorator to determine whether the check should be applied
        at all. It can be set as attribute within ``__init__``.
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

    schema: BaseSchema | None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None

    @property
    def is_active(self) -> bool:
        return self.schema is not None

    @property
    def args(self) -> list[str]:
        return []

    def mk_check(
        self, fn: Callable, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> DataCheckFunctionT:
        if self.schema is None:
            return cast("DataCheckFunctionT", lambda _: [])

        def check(df: pd.DataFrame | pd.Series) -> Iterable[str]:
            try:
                parsed_schema = self._parse_schema(self.schema, fn, args, kwargs)
                parsed_schema.validate(
                    df,
                    head=self.head,
                    tail=self.tail,
                    sample=self.sample,
                    random_state=self.random_state,
                    lazy=True,
                    inplace=True,
                )

            except (pa_errors.SchemaErrors, pa_errors.SchemaError) as exc:
                return exc.args
            except pa_errors.BackendNotFoundError:
                return [
                    f"Backend {type(self.schema).__qualname__} not applicable to"
                    f" {type(df).__qualname__}"
                ]
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
