# Pandas Contract
Decorators to check functions arguments and return values using pandas DataFrame.

```python
import pandera as pa
import pandas_contract as pc
import pandas as pd

@pc.argument(
    pa.DataFrameSchema(
        {
            "full_name": pa.Column(str),
            "age": pa.Column(pa.Int, pa.Check.ge(0)),
        }
    ),
    same_index_as="df2",
)
@pc.result(
    pa.DataFrameSchema(
        {
            "name": pa.Column(str),
            pc.from_arg("target_col"): pa.Column(int)
        }
    ),
    extends="df",
    same_index_as="df2",
    is_not="df"
)
def my_function(df1, df2, target_col: str) -> pd.DataFrame():
    ...



```
The decorators utilize the [pandera.io](https://pandera.readthedocs.io/) library to validate
data types and constraints of the input arguments and output values of functions.
```{toctree}
:caption: General
:maxdepth: 1
:relative-docs: docs/

self
setup.md
usage.md
```

```{toctree}
:caption: API
:maxdepth: 2

public-api.md
```

```{toctree}
:caption: Details
:maxdepth: 1
:elative-docs: docs/

details.md
```
