"""Allocation Weights DTO

HRP/Inverse Volatility Weighting Result
Key = Stock Symbol, Value = Weight (Sum to 1)
"""

from typing import TypedDict

# Note: dict[str, float] is essentially dynamic keys,
# but rules require TypedDict wrapper for strict type checking
# Defined here as a semantic type alias, use cast() in code


class AllocationWeightsDTO(TypedDict, total=False):
    """Allocation Weights Result (Dynamic Keys)

    Each key is a stock symbol, value is weight (0.0~1.0)
    All weights should sum to 1.0

    Use total=False to allow arbitrary keys
    """

    pass


# Use this type alias in practice
AllocationWeights = dict[str, float]
