"""Exit Signal DTO

Encapsulates Exit Signal Matrix Data
Corresponds to plan.md Phase 1.2
"""

from typing import TypedDict


class ExitSignalDTO(TypedDict):
    """Exit Signal Data Structure"""

    # 10% Hard Stop Loss
    stop_loss_triggered: bool  # Whether triggered
    stop_loss_drawdown: float  # Drawdown from monthly high

    # ATR Trailing Stop
    atr_stop_triggered: bool  # Whether triggered
    atr_stop_price: float  # ATR Stop Price
    atr_buffer_pct: float  # Buffer Percentage

    # RSI Divergence
    rsi_divergence_triggered: bool  # Price high but RSI not high
    rsi_divergence_type: str  # none/bearish/bullish

    # Time Stop
    time_stop_triggered: bool  # Held for more than 12 months
    holding_months: float  # Holding Months

    # Volatility Expansion
    vol_expansion_triggered: bool  # YZ-Vol Percentile > 95%
    vol_percentile: float  # Current Volatility Percentile

    # Combined Recommendation
    exit_recommendation: str  # HOLD/REDUCE/EXIT
    triggered_signals: list[str]  # List of triggered signals
