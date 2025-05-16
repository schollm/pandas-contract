# pandas-contract
Provide decorators to check functions arguments and return values using pandas DataFrame.

The decorators utilize the [pandera.io](https://pandera.readthedocs.io/) library to validate
data types and constraints of the input arguments and output values of functions.

## Documentation
Documentation on [pandas-contract.readthedocs.io](https://pandas-contract.readthedocs.io/en/latest/)

## Installation
```bash
pip install pandas-contract
```
## Setup

See [Setup](https://pandas-contract.readthedocs.io/en/latest/module-mode.html) for first-time setup information.

## Usage
> ℹ️ **Info:** Generally, the standard abbreviations for the package imports are
> ```python
> import pandas as pd
> import pandas_contract as pc
> import pandera as pa
> ```


### Check Dataframe structure
The following defines a function that takes a DataFrame with a column `'x'` of type
integer as input and returns a DataFrame with the column `'x'` of type string as output.

The [Pandera.io documentation](http://pandera.readthedocs.io) provides a full overview of the DataFrame/DataSeries
checks.

```python
@pc.argument("df", pa.DataFrameSchema({"x": pa.Int}))
@pc.result(pa.DataFrameSchema({"x": pa.String}))
def col_x_to_string(df: pd.DataFrame) -> pd.DataFrame:
    """Convert column x to string"""
    return df.assign(x=df["x"].astype(str))
```

### Dynamic Arguments and return values
Required columns and arguments can also be specified dynamically using a function that returns a schema.
```python
@pc.argument("df", pa.DataFrameSchema(
    {pc.from_arg("col"): pa.Column()})
)
@pc.result(pa.DataFrameSchema({pc.from_arg("col"): pa.String}))
def col_to_string(df: pd.DataFrame, col: str) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str)})
```
#### Multiple columns in function argument
The decorator also supports multiple columns from the function argument.
```python
@pc.argument("df", pa.DataFrameSchema(
        {pc.from_arg("cols"): pa.Column()}
    )
)
@pc.result(pa.DataFrameSchema({pc.from_arg("cols"): pa.String}))
def cols_to_string(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    return df.assign(**{col: df[col].astype(str) for col in cols})
```

### Retrieve dataframes from a more complex argument
Sometimes the dataframe is not a direct argument of the function, but is part of a more complex argument.
In this case, the decorator argument `key` can be used to specify the key of the dataframe in the argument.

If `key` is a callable, it will be called with the argument and the result will be used as the dataframe.
Otherwise, it will be used as a key to retrieve the dataframe from the argument, i.e. `arg[key]`.

#### Dataframe result is wrapped within another object
```python
@pc.result(key="data")
def into_dict():
    """Dataframe wrapped in a dict"""
    return dict(data=pd.DataFrame())
```

See [Key Type](https://pandas-contract.readthedocs.io/en/latest/public-api.html#pandas_contract._decorator_v2.KeyT) for 
more information and examples.