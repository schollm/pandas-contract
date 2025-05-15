from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from pandas_contract import checks
from pandas_contract._decorator_v2 import argument as argument2
from pandas_contract._decorator_v2 import result as result2
from pandas_contract._private_checks import (
    Check,
    CheckSchema,
)

from ._lib import UNDEFINED, ValidateDictT

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Sequence

    from pandera.api.base.schema import BaseSchema


"""Mark a parameter as undefined."""
_T = TypeVar("_T", bound=Callable[..., Any])
""""Type variable for the function type."""


@dataclass
class argument:  # noqa: N801
    """Decorator to check the input DataFrame for required columns using pandera.

    :param arg: The name of the argument to check. This must correspond to one of the
     arguments of the function.
    :param schema: The schema to validate the input DataFrame.
        See the `pandera documentation <https://pandera.readthedocs.io/en/stable>`_ for
        `DataFrameSchema <https://pandera.readthedocs.io/en/stable/dataframe_schemas.html>`_
        and `SeriesSchema <https://pandera.readthedocs.io/en/stable/series_schemas.html>`_.
    :param head: The number of rows to validate from the head. If None, all rows are
        used for validation.
    :param tail: The number of rows to validate from the tail. If None, all rows are
        used for validation.
    :param sample: The number of rows to validate randomly. If None, all rows are used
        for validation.
    :param random_state: The random state for the random sampling.
    :param same_index_as: The name of the input argument(s) that should have the same
        index.
    :param same_size_as: The name of the input argument(s) that should have the same
        size.
    :param key: The key of the input to check. If None, the entire input is checked.
    :param extends: Name of argument that this output extends.

    Examples
    --------
    **Common imports for all examples**

    >>> import pandas as pd
    >>> import pandera as pa
    >>> import pandas_contract as pc

    *Ensure that the input dataframe has a column "a" of type int.*

    >>> @argument("df", schema=pa.DataFrameSchema({"a": pa.Column(pa.Int)}))
    ... def func(df: pd.DataFrame) -> None:
    ...    ...

    *Ensure that input dataframe as a column "a" of type int and "b" of type float.*

    >>> @argument(
    ...     "df",
    ...     schema=pa.DataFrameSchema(
    ...         {"a": pa.Column(pa.Int), "b": pa.Column(pa.Float)}
    ...     ),
    ... )
    ... def func(df: pd.DataFrame) -> None:
    ...     ...

    *Ensure that the dataframes df1 and df2 have the same indices*

    >>> @argument("df1", same_index_as="df2")
    ... def func(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    ...     ...

    *Ensure that the dataframes df1 and df2 have the same size*

    >>> @argument("df1", same_size_as="df2")
    ... def func(df1: pd.DataFrame, df2: pd.DataFrame) -> None:
    ...     ...

    *All-together*

    Ensure that the input dataframe has a column `"a"` of type int, the same index as
    df2, and the same size as df3.

    >>> @argument(
    ...     "dfs",
    ...     schema=pa.DataFrameSchema({"a": pa.Column(pa.Int)}),
    ...     same_index_as="df2",
    ...     same_size_as="df3",
    ... )
    ... def func(dfs: pd.DataFrame, df2: pd.DataFrame, df3: pd.DataFrame) -> None:
    ...     ...

    *Data Series*

    Instead of a DataFrame, one can also validate a Series. Then the schema must
    be of type pa.SeriesSchema.

    For example, to ensure that the input series is of type int, one can use:

    >>> @argument("ds", schema=pa.SeriesSchema(pa.Int))
    ... def func(ds: pd.Series) -> None:
    ...     ...

    """

    arg: str
    schema: BaseSchema | None = None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None
    same_index_as: str | Sequence[str] = ()
    same_size_as: str | Sequence[str] = ()
    key: Any = UNDEFINED
    extends: str | None = None

    def __post_init__(self) -> None:
        checks_lst: list[Check] = [
            CheckSchema(
                self.schema, self.head, self.tail, self.sample, self.random_state
            ),
            checks.same_index_as(self.same_index_as),
            checks.same_length_as(self.same_size_as),
            checks.extends(self.extends, self.schema),
        ]

        self._decorator = argument2(
            self.arg,
            *(check for check in checks_lst if check.is_active),
            key=self.key,
            validate_kwargs=ValidateDictT(
                head=self.head,
                tail=self.tail,
                sample=self.sample,
                random_state=self.random_state,
            ),
        )

    def __call__(self, fn: _T) -> _T:
        return self._decorator(fn)


@dataclass
class result:  # noqa: N801
    """Validate a DataFrame result using pandera.

    The schema is used to validate the output DataFrame of the function.

    :param schema: The schema to validate the output DataFrame.
    :param head: The number of rows to validate from the head.
    :param tail: The number of rows to validate from the tail.
    :param sample: The number of rows to validate randomly.
    :param random_state: The random state for the random sampling.
    :param same_index_as: The name of the input argument(s) that should have the
        same index.
    :param same_size_as: The name of the input argument(s) that should have the same
        size.
    :param key: The key of the output to check. If None, the entire output is checked.
        This can be used if the function returns a tuple or a mapping.
    :param extends: The name of the input argument that the output extends. Only
        columns defined in the output schema are allowed to be mutated or added.
    :param is_: Name of argument that the output is identical to. The resulting
        data-frame/series is identical to the given argument (assert fn(df) is df),
        i.e., the function changes the dataframe in-place.

    Examples:
    =========

    >>> import pandas as pd
    >>> import pandera as pa
    >>> import pandas_contract as pc


    Ensure column exists
    --------------------

    Ensure that the output dataframe has a column "a" of type int and "b" of type
    float.

    >>> @result(
    ...     schema=pa.DataFrameSchema(
    ...         {"a": pa.Column(pa.Int), "b": pa.Column(pa.Float)}
    ...    )
    ... )
    ... def func() -> pd.DataFrame:
    ...     return pd.DataFrame({"a": [1, 2], "b": [1.0, 2.0]})

    Ensure equal length
    -------------------
    Ensure that the output dataframe has the same size as df.

    >>> @result(schema=pa.DataFrameSchema({"a": pa.Column(pa.Int)}), same_size_as="df")
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df

    Ensure same indices
    --------------------

    Ensure that the output dataframe has the same index as df.

    >>> @result(schema=pa.DataFrameSchema({"a": pa.Column(pa.Int)}), same_index_as="df")
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df


    **Ensure same index.**
    Ensure that the output dataframe has the same index as df1 and the same size as df2.

    >>> @result(
    ...     schema=pa.DataFrameSchema({"a": pa.Column(pa.Int)}),
    ...     same_index_as="df1",
    ...     same_size_as="df2",
    ... )
    ... def func(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    ...     return df1

    Extends input
    --------------
    Ensures that the output extends the input schema.

    >>> @result(extends="df", schema=pa.DataFrameSchema({"a": pa.Column(int)}))
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(a=1)

    Note that any columns listed the result schema can be modified. To specify a column
    that is returned, but cannot be modified, use the schema argument of the input
    argument.

    Ensures that the output extends the input schema and has a column "a" of type int.
    The following will fail in any of the three cases:

    * df does not have a column "in" of type int
    * The result does not have a column "out" of type int
    * The column 'a' was changed.

    >>> @pc.argument("df", schema=pa.DataFrameSchema({"in": pa.Column(pa.Int)}))
    ... @pc.result(
    ...     schema=pa.DataFrameSchema({"out": pa.Column(pa.Int)}),
    ...     extends="df"
    ... )
    ... def func(df: pd.DataFrame) -> pd.DataFrame:
    ...     return df.assign(out=1)

    """

    schema: BaseSchema | None = None
    head: int | None = None
    tail: int | None = None
    sample: int | None = None
    random_state: int | None = None
    same_index_as: str | Sequence[str] = ()
    same_size_as: str | Sequence[str] = ()
    key: Any = UNDEFINED
    extends: str | None = None
    is_: str | None = None
    is_not: str | Sequence[str] = ()

    def __post_init__(self) -> None:
        checks_lst: list[Check] = [
            CheckSchema(
                self.schema, self.head, self.tail, self.sample, self.random_state
            ),
            checks.same_index_as(self.same_index_as),
            checks.same_length_as(self.same_size_as),
            checks.extends(self.extends, self.schema),
            checks.is_(self.is_),
            checks.is_not(self.is_not),
        ]
        self._decorator = result2(
            *(check for check in checks_lst if check.is_active),
            key=self.key,
            validate_kwargs=ValidateDictT(
                head=self.head,
                tail=self.tail,
                sample=self.sample,
                random_state=self.random_state,
            ),
        )

    def __call__(self, fn: _T) -> _T:
        return self._decorator(fn)
