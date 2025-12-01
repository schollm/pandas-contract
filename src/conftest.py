"""pytest setup module."""

import os

os.environ["PANDAS_CONTRACT_MODE"] = "raise"

# Run initialization code for pandas_contract
import pandas_contract

del pandas_contract
