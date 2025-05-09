 # Installation
```bash
(.venv) pip install pandas-contract
```

# Setup package

> ❗**Important** By default, the decorators will be attached to the functions, but
> **they will not run**. This ensures that production code is not affected
> 
> The method {py:meth}`pc.set_mode() <pandas_contract.set_mode>` and the context generator 
> {py:meth}`pc.as_mode() <pandas_contract.as_mode>` can be used to set the global or context-specific mode.
> 
> It is recommended to set the mode once in the main module of your application.
> For tests, this can be overwritten in the test-setup.
> 
> Additionally, for specific runs, the context generators 
> {py:meth}`pc.raises() <pandas_contract.raises>` and 
> {py:meth}`pc.silent() <pandas_contract.silent>` can be used to set the mode to
> `raise` / `silent` for a specific function.
>
> ```python
> import pandas_contract as pc
> 
> pc.set_mode("warn")  # print warn messages on standard log for all violations.
> with pc.as_mode("raise"):  # Within the context, raise an ValueError on violation.
>     ...
> ```


## List of all modes
The arguments to {py:meth}`pc.set_mode() <pandas_contract.set_mode>` and 
{py:meth}`pc.as_mode() <pandas_contract.as_mode>` are the keys or string values of 
{py:obj}`pandas_contract.Modes`
```{eval-rst}
  .. autoclass:: pandas_contract.Modes
```
