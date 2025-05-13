Decorators
==========
.. autofunction:: pandas_contract.argument
.. autofunction:: pandas_contract.result
.. autofunction:: pandas_contract.from_arg

Decorators V2
=============
.. autofunction:: pandas_contract.argument2
.. autofunction:: pandas_contract.result2
.. autoclass:: pandas_contract._decorator_v2.KeyT

Check functions
---------------
.. autodoc2-summary::
    ~pandas_contract.checks.extends
    ~pandas_contract.checks.is_
    ~pandas_contract.checks.is_not
    ~pandas_contract.checks.same_index_as
    ~pandas_contract.checks.same_length_as


.. automodule:: pandas_contract.checks
    :members:
    :member-order: alphabetical
    :show-inheritance:
    :exclude-members: mk_check, is_active, all_args

Check Protocol
~~~~~~~~~~~~~~
.. autoclass:: pandas_contract._private_checks.Check
    :members:
    :class-doc-from: both

