"""Stock Analysis Data DTO

Stock Analysis Data Structure
"""

from typing import TypedDict

import numpy as np


class StockAnalysisDataDTO(TypedDict):
    """Stock Analysis Data"""

    current_price: float
    monthly_high: float
    alpha: float
    volatility: float
    signal_age: int
    returns: np.ndarray
    prices: np.ndarray
    resid_rsi: np.ndarray
