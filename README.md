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

The following defines a function that takes a DataFrame with a column x of type integer as
input and returns a DataFrame with the column x of type string as output.
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

@pc.argument("df", schema=pa.DataFrameSchema({"x": pa.Int}))
@pc.result(schema=pa.DataFrameSchema({"x": pa.String}))
def col_x_to_string(df: pd.DataFrame) -> pd.DataFrame:
    return df.assign(x=df["x"].astype(str))
```
### Dynamic Arguments and return values
Required columns and arguments can also be specified dynamically using a function that returns a schema.
```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

@pc.argument("df", schema=pa.DataFrameSchema({pc.from_arg("val_col"): pa.Int}))
@pc.result(schema=pa.DataFrameSchema({pc.from_arg("val_col"): pa.String}))
def col_to_string(df: pd.DataFrame, val_col: str) -> pd.DataFrame:
    return df.assign(**{val_col: df[val_col].astype(str)})
```

### Cross-argument and output constraints
Additionally, it provides checks to ensure cross-argument and output constraints like 
#### Dataframes should have the same index.
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

#### Size of dataframes should be equal.
  ```python
import pandas as pd
import pandas_contract as pc

@pc.result(same_size_as="df1")
def my_func(df1: pd.DataFrame):
    # Output has the same size as input
    return pd.DataFrame(index=df1.index  + 1)
  ```

Additionally, it allows to extract a dataframe from a more complex argument or return value by specifying a key.

```python
import pandas as pd
import pandas_contract as pc
import pandera as pa

@pc.argument(arg="df", schema=pa.DataFrameSchema({"x": pa.Int}))
@pc.result(key="data", schema=pa.DataFrameSchema({"x": pa.Int}), same_index_as="df")
def into_dict(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return dict(data=df)
``` 