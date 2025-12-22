"""Hunting Target DTO"""

from typing import TypedDict


class HuntingTargetDTO(TypedDict):
    """Hunting target data"""

    symbol: str
    residual_momentum: float
    trend: str
    signal: str  # 🟢 | 🟡 | 🔴
