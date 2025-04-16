# pandas-contract
Provide decorators to check functions arguments and return values using pandas DataFrame.

The decorators utilize the [pandera.io](https://pandera.readthedocs.io/) library to validate
data types and constraints of the input arguments and output values of functions.


## Installation
```bash
pip install pandas-contract
```

## Usage
The library provides decorators to check the input arguments and return values of functions.

All examples here are based on the following imports:
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa
```

The following defines a function that takes a DataFrame with a column x of type integer as
input and returns a DataFrame with the column x of type string as output.
```python
@pc.argument("df", schema=pa.DataFrameSchema({"x": pa.Int}))
@pc.result(schema=pa.DataFrameSchema({"x": pa.String}))
def col_x_to_string(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(x=df["x"].astype(str))
```
### Dynamic Arguments and return values
Required columns and arguments can also be specified dynamically using a function that returns a schema.
```python
@pc.argument("df", schema=pa.DataFrameSchema(
    {pc.from_arg("col"): pa.Column()})
)
@pc.result(schema=pa.DataFrameSchema({pc.from_arg("col"): pa.String}))
def col_to_string(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str)})
```
#### Multiple columns in function argument
The decorator also supports multiple columns from the function argument. 
```python
@pc.argument("df", schema=pa.DataFrameSchema(
        {pc.from_arg("cols"): pa.Column()}
    )
)
@pc.result(schema=pa.DataFrameSchema({pc.from_arg("cols"): pa.String}))
def cols_to_string(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str) for col in cols})
```

### Cross-argument and output constraints
Additionally, it provides checks to ensure cross-argument and output constraints like 
#### Dataframes should have the same index.
  ```python
@pc.result(same_index_as=["df1", "df2"])
def my_func(df1: pd.DataFrame, df2: pd.DataFrame):
    # Output has the same index as input
    return pd.DataFrame(index=df1.index)

@pc.argument("df1", same_index_as="df2")
def my_func(df1, df2):
    # Input dataframes have the same index
    df1["x"] = df2["x"]
  ```

#### Size of dataframes should be equal.
  ```python
@pc.result(same_size_as="df1")
def my_func(df1: pd.DataFrame):
    # Output has the same size as input
    return pd.DataFrame(index=df1.index  + 1)
  ```
### Retrieve dataframes from a more complex argument
Sometimes the dataframe is not a direct argument of the function, but is part of a more complex argument.
In this case, the decorator argument `key` can be used to specify the key of the dataframe in the argument.

If `key` is a callable, the 
If it's a callable, it will be called with the argument and the result will be used as the dataframe.
Otherwise, it will be used as a key to retrieve the dataframe from the argument, i.e. `arg[key]`

#### Dataframe output is a dictionary or a list
```python
@pc.result(key="data")
def into_dict() -> dict[str, pd.DataFrame]:
    return dict(data=pd.DataFrame())
``` 

#### Dataframe output is a list
```python
@pc.result(key=0)
def into_list():
    return [pd.DataFrame(), ...]
``` 

#### Dataframe output is an object
```python
@pc.result(key=lambda out: out.foo)
def into_object():
    class Out:
        def __init__(selfI, df):
            self.df = df
            
    return Out(pd.DataFrame())
``` 

This can also be used to convert an object into a data-frame to test within the pandas_contract framework:
```python
@pc.result(key=pd.DataFrame, schema=pa.DataFrameSchema({"a": pa.Int, "b": pa.Int}))
def return_dict():
    return [{"a": 1, "b": 2.0}]
``` 

Note, if the key is a callable, it must be wrapped in a lambda function, otherwise it will be called with the argument:
```python
def f1():
    ...

# Get the dataframe from the output item `f1`.
# @pc.result(key=f1, schema=pa.DataFrameSchema({"name": pa.String}))  - this will fail
@pc.result(key=lambda res: res[f1], schema=pa.DataFrameSchema({"name": pa.String}))
def return_generators():
    return {
        f1: pd.DataFrame([{"name": "f1"}])
    }
```


### Dataframe output extends input
A common use-case is to extend the input dataframe with new columns. This can be done using the `extends` argument of the `result` decorator.
It ensures that the output dataframe extends the input dataframe, i.e. only the columns defined in the output schema are allowed to be changed.
```python
@pc.argument(arg="df", schema=pa.DataFrameSchema({"a": pa.Column(pa.Int)}))
@pc.result(extends="df", schema=pa.DataFrameSchema({"b": pa.Int, "c": pa.Column(pa.Int)}))
def foo(df):
    return df.assign(b=df["a"] + df["b"], c=df["a"] + 2)

```