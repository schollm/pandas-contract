Pandas Contract
================

Decorators to check functions arguments and return values using pandas DataFrame.

.. code-block:: python

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
      pc.check.same_index_as("df2"),
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

The decorators use the `pandera.io <https://pandera.readthedocs.io/>`_` library to validate
data types and constraints of the input arguments and output values of functions.

Installation
------------

.. code-block:: sh

  (.venv) pip install pandas-contract


Setup package
-------------

.. important:: By default, the decorators will be attached to the functions, but
  **they will not run**. This ensures that production code is not affected
  See :py:mod:`pandas_contract.mode` for more information.

.. toctree::
    :caption: Index
    :hidden:

    self
    public-api
    module-mode
    details
