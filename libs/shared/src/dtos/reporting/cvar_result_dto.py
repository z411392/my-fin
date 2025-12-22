"""CVaR Result DTO

CVaR Risk Assessment Result
"""

from typing import TypedDict


class CvarResultDTO(TypedDict):
    """CVaR Risk Assessment Result"""

    cvar_95: float
    var_95: float
    tail_risk: str
