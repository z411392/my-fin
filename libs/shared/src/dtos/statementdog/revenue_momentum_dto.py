"""Revenue Momentum Metrics DTO"""

from typing import TypedDict


class RevenueMomentumDTO(TypedDict, total=False):
    """Revenue Momentum Metrics"""

    symbol: str
    short_term_yoy: float  # Avg YoY last 3 months
    long_term_yoy: float  # Avg YoY last 12 months
    current_yoy: float  # Current Month YoY
    is_accelerating: bool  # Whether Accelerating
