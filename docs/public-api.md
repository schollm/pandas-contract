
# Decorators
```{eval-rst}
.. autofunction:: pandas_contract.argument
.. autofunction:: pandas_contract.result
.. autofunction:: pandas_contract.from_arg
```
# Decorators V2
```{eval-rst}
.. autofunction:: pandas_contract.argument2
.. autofunction:: pandas_contract.result2
```
### Check functions
```{autodoc2-summary}
~pandas_contract.checks.extends
~pandas_contract.checks.is_
~pandas_contract.checks.is_not
~pandas_contract.checks.same_index_as
~pandas_contract.checks.same_length_as
```

```{eval-rst}
.. automodule:: pandas_contract.checks
    :members:
    :member-order: alphabetical
    :show-inheritance:
```

### Check Protocol
```{eval-rst}
.. autoclass:: pandas_contract._private_checks.Check
    :members:
    :class-doc-from: both
```

# Setup handling
Functions to setup handling of contract violation.
By default, the contract violation will be silenced.

```{eval-rst}
  .. autofunction:: pandas_contract.set_mode
  .. autofunction:: pandas_contract.as_mode
  .. autofunction:: pandas_contract.silent
  .. autofunction:: pandas_contract.raises
  .. autoclass:: pandas_contract.Modes
  .. autoclass:: pandas_contract.mode.ModesT

```



# Setup handling
Functions to setup handling of contract violation.
By default, the contract violation will be silenced.

```{eval-rst}
  .. autofunction:: pandas_contract.set_mode
  .. autofunction:: pandas_contract.as_mode
  .. autofunction:: pandas_contract.silent
  .. autofunction:: pandas_contract.raises
  .. autoclass:: pandas_contract.Modes
  .. autoclass:: pandas_contract.mode.ModesT

```
