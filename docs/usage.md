# Usage
## Imports

:::{note}
Generally, the standard abbreviations for the package imports are
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa
```
:::

```{eval-rst}
    .. autoclass:: pandas_contract._decorator.argument
``` 
## Check Dataframe structure
The following defines a function that takes a DataFrame with a column `'x'` of type
integer as input and returns a DataFrame with the column `'x'` of type string as output.

See [pandera.io](http://pandera.readthedocs.io) for the full documentation.
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

@pc.argument("df", schema=pa.DataFrameSchema({"x": pa.Int}))
@pc.result(schema=pa.DataFrameSchema({"x": pa.String}))
def col_x_to_string(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column x to string"""
    return df.assign(x=df["x"].astype(str))
```

## Cross-argument and output constraints
Additionally, it provides checks to ensure cross-argument and output constraints like
### Dataframes should have the same index.
  ```python
import pandas as pd
import pandas_contract as pc

@pc.result(same_index_as=["df1", "df2"])
def my_func(df1: pd.DataFrame, df2: pd.DataFrame):
    # Output has the same index as input
    return pd.DataFrame(index=df1.index)

@pc.argument("df1", same_index_as="df2")
def my_func(df1, df2):
    # Input dataframes have the same index
    df1["x"] = df2["x"]
  ```

### Size of dataframes should be equal.
  ```python
import pandas as pd
import pandas_contract as pc

@pc.result(same_size_as="df1")
def my_func(df1: pd.DataFrame):
    # Output has the same size as input
    return pd.DataFrame(index=df1.index  + 1)
  ```

## Dataframe is changed in-place or copied
The `result.is_: str` argument declares the output to be identical (in the sense of the same
objet) as a parameter.

The `result.is_not: str | Sequence[str]` is the opposite, it ensures that the output is
not identical, i.e. a new Dataframe is returned.
`result.is_not` can be a comma-separated string or a list of arguments.

```python
import pandas as pd
import pandas_contract as pc

# is_ argument
@pc.result(is_="df")
def inplace_change(df):
    df["x"] = 1
    return df

df = pd.DataFrame()
assert df is inplace_change(df)

# is_not argument
@pc.result(is_not=["df1", "df2"])
@pc.result(is_not="df1, df2")  # Alternative definition
def concat(df1, df2):
    return pd.concat((df1, df2))

df1 = df2 = pd.DataFrame()
assert df1 is not concat(df1, df2)
assert df2 is not concat(df1, df2)
```


## Dataframe output extends input
A common use-case is to extend the input dataframe with new columns. This can be done using the `extends` argument of the `result` decorator.
It ensures that the output dataframe extends the input dataframe, i.e. only the columns defined in the output schema are allowed to be changed.
```python
import pandas_contract as pc
import pandera as pa

@pc.argument(arg="df", schema=pa.DataFrameSchema({
    "a": pa.Column(pa.Int),
    "b": pa.Column(pa.Int),
}))
@pc.result(extends="df", schema=pa.DataFrameSchema({"b": pa.Int, "c": pa.Column(pa.Int)}))
def foo(df):
    # Column a is read, but not written,
    # Column b is both read and written
    # Column c is set (i.e. can be added)
    return df.assign(b=df["a"] + df["b"], c=df["a"] + 2)
```



## Retrieve dataframes from a more complex argument
Sometimes the dataframe is not a direct argument of the function, but is part of a more complex argument.
In this case, the decorator argument `key` can be used to specify the key of the dataframe in the argument.

If `key` is a callable, the
If it's a callable, it will be called with the argument and the result will be used as the dataframe.
Otherwise, it will be used as a key to retrieve the dataframe from the argument, i.e. `arg[key]`

### Dataframe result is wrapped within another object
```python
import pandas as pd
import pandas_contract as pc

@pc.result(key="data")
def into_dict():
    """Dataframe wrapped in a dict"""
    return dict(data=pd.DataFrame())


@pc.result(key=0)
def into_list():
    """Dataframe wraped in a list"""
    return [pd.DataFrame(), ...]


@pc.result(key=lambda out: out.foo)
def into_object():
    """Dataframe wrapped in an object"""
    class Out:
        foo = pd.DataFrame()
    # result.foo holds the dataframe
    return Out()
```

This can also be used to convert an object into a data-frame to test within the pandas_contract framework:
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa


@pc.result(
    key=pd.DataFrame,
    schema=pa.DataFrameSchema(
        {"a": pa.Column(int), "b": pa.Column(int)}
    )
)
def return_dict():
    # Return a structure that can be converted to a DataFrame
    return [{"a": 1, "b": 2.0}]
```

Note, if the key is a callable, it must be wrapped in a lambda function, otherwise it will be called with the argument:
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

def f1():
    ...

# Get the dataframe from the output item `f1`.
# @pc.result(key=f1, schema=pa.DataFrameSchema({"name": pa.String}))  - this will fail
@pc.result(key=lambda res: res[f1], schema=pa.DataFrameSchema({"name": pa.String}))
def return_generators():
    # f1 is a key to a dictionary holding the data frame to be tested.
    return {
        f1: pd.DataFrame([{"name": "f1"}])
    }
```

## Dynamic Arguments and return values
Required columns and arguments can also be specified dynamically using a function that returns a schema.
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

@pc.argument("df", schema=pa.DataFrameSchema(
    {pc.from_arg("col"): pa.Column()})
)
@pc.result(schema=pa.DataFrameSchema({pc.from_arg("col"): pa.String}))
def col_to_string(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str)})
```
### Multiple columns in function argument
The decorator also supports multiple columns from the function argument.
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

@pc.argument("df", schema=pa.DataFrameSchema(
        {pc.from_arg("cols"): pa.Column()}
    )
)
@pc.result(schema=pa.DataFrameSchema({pc.from_arg("cols"): pa.String}))
def cols_to_string(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str) for col in cols})
```
