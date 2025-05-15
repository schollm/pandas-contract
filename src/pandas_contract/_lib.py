from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Protocol, TypedDict, TypeVar, cast

if TYPE_CHECKING:  # pragma: no cover
    import types
    from collections.abc import Iterable, Sequence

    import pandas as pd

_T = TypeVar("_T", bound=Callable)


class MyFunctionType(Protocol):  # pragma: no cover
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    __code__: types.CodeType
    __name__: str
    __defaults__: tuple[Any, ...] | None
    __kwdefaults__: dict[str, Any]
    __qualname__: str


class ValidateDictT(TypedDict, total=False):
    head: int | None
    tail: int | None
    sample: int | None
    random_state: int | None


class KeyT(Protocol):
    """KeyType protocol, define a lookup key for an argument or the result.

    A key can be used to get a DataFrame or Series from within a more complex argument
    or return value.

    Its value is either any hashable or a function that takes a single argument as
    an input and returns a DataFrame/Series.

    Note that `None` is a valid key in a dictionary and hence is not the default value.
    By default, the value is used as-is.

    >>> import pandas as pd
    >>> import pandas_contract as pc
    >>> import pandera as pa
    >>> @pc.result(pa.SeriesSchema(int), key=1)
    ... def f1():
    ...    return "res", pd.Series([1,2,3])

    The key can also be an arbitrary function that takes the input arg and has to
    return the DataFrame/Series to check.

    This can be used to create a Series, which is then checkable out of non-checkable
    Data:

    >>> @pc.result(pa.SeriesSchema(int), key=pd.Series)
    ... def f1():
    ...    return [1, 2, 3]


    Note, if the DataFrame/Series is wrapped in a mapping where the mapping keys are
    callables, then *Key* must be wrapped in another function:

    >>> def fn_as_key():
    ...    ...

    >>> # Get the dataframe from the output item `f1`.
    >>> # @pc.result(key=f1, schema=pa.DataFrameSchema({"name": pa.String}))  - fail
    >>> @pc.result(
    ...     pa.DataFrameSchema({"name": pa.Column(str)}),
    ...     key=lambda res: res[fn_as_key],
    ... )
    ... def return_generators():
    ...     # f1 is a key to a dictionary holding the data frame to be tested.
    ...     return {
    ...         fn_as_key: pd.DataFrame([{"name": "f1"}])
    ...     }

    """


class WrappedT(Protocol):
    """Type for wrapper function."""

    def __call__(self, fn: _T) -> _T: ...


UNDEFINED = object()
"""Mark a parameter as undefined."""

ORIGINAL_FUNCTION_ATTRIBUTE = "_pandas_contract_original_function"
"""Name of attribute to attach to decorated functions."""
# We need the original function to get the original argument names of the function.


def ensure_list(value: str | Sequence[str]) -> list[str]:
    """Ensure that the value is a list of strings."""
    if isinstance(value, str):
        return [value]
    return list(value)


def split_or_list(value: str | Iterable[str] | None) -> list[str]:
    """Split the value by comma and return a list of strings."""
    if value is None:
        return []
    if isinstance(value, str):
        return [v.strip() for v in value.split(",")]
    return list(value)


def from_arg(arg: str) -> Callable[[MyFunctionType, tuple[Any], dict[str, Any]], Any]:
    """Get the named argument from the function call via a call-back.

    Returns a call-back function that can be used to get the named argument from the
    function call.
    """

    def wrapper(
        fn: MyFunctionType, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> object:
        """Get the named argument from the function call."""
        fn = getattr(fn, ORIGINAL_FUNCTION_ATTRIBUTE, fn)
        return get_fn_arg(fn, arg, args, kwargs)

    return wrapper


def get_fn_arg(
    func: MyFunctionType, arg_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> object:
    """Get the named argument from function call (either from *args or **kwargs)."""
    if arg_name in kwargs:
        return kwargs[arg_name]
    co = func.__code__
    for var_name, arg in zip(co.co_varnames, args):
        if arg_name == var_name:
            return arg
    if func.__defaults__:
        for var_name, arg in zip(
            func.__code__.co_varnames[co.co_argcount - len(func.__defaults__) :],
            func.__defaults__,
        ):
            if arg_name == var_name:
                return arg
    if func.__kwdefaults__ is not None and arg_name in func.__kwdefaults__:
        return func.__kwdefaults__[arg_name]
    msg = f"{func.__qualname__} does mot have argument '{arg_name}'"
    raise ValueError(msg)


def get_df_arg(
    func: MyFunctionType, arg_name: str, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> pd.DataFrame:
    res = get_fn_arg(func, arg_name, args, kwargs)
    return cast("pd.DataFrame", res)


def has_fn_arg(func: MyFunctionType, arg_name: str) -> bool:
    """Check if the function has the named argument."""
    co = func.__code__
    return arg_name in co.co_varnames[: co.co_argcount + co.co_kwonlyargcount]
