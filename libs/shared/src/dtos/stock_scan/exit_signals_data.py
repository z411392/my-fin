"""Exit Signals Data DTO

Corresponds to stock_data_builder.build_exit_signals return structure
"""

from typing import TypedDict


class ExitSignalsData(TypedDict, total=False):
    """Exit Signals Data Structure"""

    # Stop Loss Triggered
    stop_loss_triggered: bool | None

    # Beta Change
    beta_change_pct: float | None  # Beta Change Percentage
    beta_spike_alert: bool | None  # Beta Spike Alert

    # ATR Trailing Stop
    atr_trailing_stop: float | None  # ATR Trailing Stop Price

    # P1 New Fields
    volatility_expansion_flag: bool | None  # Volatility Expansion Flag
    correlation_drift: float | None  # Correlation Coefficient Drift
    short_term_reversal: float | None  # Short Term Reversal
    rolling_beta_60d: float | None  # 60-day Rolling Beta
