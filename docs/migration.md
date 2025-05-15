# Migration
## Update to 0.7.0
Version 0.6.0 introduced a new version for the decorators
[argument](#pandas_contract.argument) and [result](#pandas_contract.result),
named `argument2` and `result2`. The main difference is that instead of explicitly
defining all tests in the decorators via keyword arguments, they take check functions.

See below for an comparison of the two API styles

```python
import pandas_contract as pc
import pandera as pa
schema = pa.DataFrameSchema(...)
# OLD:
pc.argument(
   arg="dfs",
   schema=schema,
   same_index_as="df2",
   same_length_a="ds",
   key=0,
   head=10,
   random_state=42,

)
# NEW:
pc.argument2(
    "dfs",
    schema,
    pc.checks.same_index_as("df2"),
    pc.checks.same_length_a("ds"),
    key=0,
    validate_kwargs={"head": 10, "random_state": 42},
)
```

```{note}
Under the hood `pc.argument` calls `pc.argument2`, same for `pc.result`.
```

Version 0.7.0 combines these two by providing dispatcher decorators, `pc.argument` and
`pc.result` that will call the appropriate function, depending on the input arguments.
The legacy style is deprecated. This allows for a soft migration to the new style of
decorators.

Version 0.8.0 will remove the legacy style and only the new style will be supported
hence on.

To update to version 0.7.0, replace all keyword arguments `arg=/args=` in the
decorators `argument` and `result` with positional arguments (at first position):

1. `pc.argument(arg="df", ...)` -> `pc.argument("df", ...)`.

Note that at this stage, the deprecated v1 API is still used.

### Preparation for 0.8.0
To prepare for the migration in 0.8.0, which will remove V1 API, do the following four steps:

```{note}
The migration can be done on each decorator independently. Steps 2 and 3 can also be
done one after each other.
```

2. Replace all schema keyword arguments with positional only arguments,
   `pc.argument("df", schema=<schema>, ...)` -> `pc.argument("df", <schema>, ...)`.
3. Set all other arguments (apart from arg and schema) as keyword arguments.

```{note}
1. At this stage, everything should work. If these are the only two arguments to the
   decorator, it will already use the new API.
2. Steps 4 and 5 have to be applied together for each decorator .
```

4. Move the decorator arguments `head`, `tail`, `sample`, `random_state` into the
   argument `validate_kwargs` argument:
   ```python
   pc.argument(..., head=1, tail=2, ...)  # OLD
   pc.argument(..., validate_kwargs={"head": 1, "tail": 2, ...}) # NEW
   ```
5. Replace all check (keyword) arguments with their appropriate check function,
   `@argument(is_="df")` -> `@argument(pc.check.is_("df"))`

   | Old argument    | New function            |
   |-----------------|-------------------------|
   | `extends`       | `checks.extends`*       |
   | `is_`      | `checks.is_`            |
   | `is_not`        | `checks.is_not`         |
   | `same_index_as` | `checks.same_index_as`  |
   | `same_size_as`  | `checks.same_length_as` |

   *: Note that extends moves the old schema definition into the decorator, e.g.,
   ```python
   import pandas_contract as pc
   import pandera as pa

   schema = pa.DataFrameSchema({"x": pa.Column()})
   pc.result(schema, extends="df") # Old
   pc.result(pc.checks.extends("df", modified=schema)) # New
   ```

After running the tests, there should be no more deprecation warnings
with the text `"Deprecated API in use. See doc for new API."`


