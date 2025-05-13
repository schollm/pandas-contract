# pandas-contract
Provide decorators to check functions arguments and return values using pandas DataFrame.

The decorators utilize the [pandera.io](https://pandera.readthedocs.io/) library to validate
data types and constraints of the input arguments and output values of functions.

## Documentation
Full documentation on https://pandas-contract.readthedocs.io/en/latest/
## Installation
```bash
pip install pandas-contract
```

## Usage
> ℹ️ **Info:** Generally, the standard abbreviations for the package imports are
> ```python
> import pandas as pd
> import pandas_contract as pc
> import pandera as pa
> ```

### Setup

See [Setup](docs/setup.rst) for first-time setup information.

### Check Dataframe structure
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



### Retrieve dataframes from a more complex argument
Sometimes the dataframe is not a direct argument of the function, but is part of a more complex argument.
In this case, the decorator argument `key` can be used to specify the key of the dataframe in the argument.

If `key` is a callable, the
If it's a callable, it will be called with the argument and the result will be used as the dataframe.
Otherwise, it will be used as a key to retrieve the dataframe from the argument, i.e. `arg[key]`

#### Dataframe result is wrapped within another object
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

### Dynamic Arguments and return values
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
#### Multiple columns in function argument
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
