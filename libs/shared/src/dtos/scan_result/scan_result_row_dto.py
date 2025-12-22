"""Scan Result Row DTO

Single data row for scan results (scan_residual_momentum, export_daily_summary)
Supports all fields from stock_data_builder
"""

from typing import TypedDict

from libs.shared.src.dtos.hunting.alpha_beta_contribution_dto import (
    AlphaBetaContributionDTO,
)
from libs.shared.src.dtos.stock_scan.statementdog_data import StatementDogData


class ScanResultRowDTO(TypedDict, total=False):
    """Scan Result Row - Generic Structure (Supports generate_daily_report methods)"""

    # Basic Info
    symbol: str
    name: str
    sector: str
    market: str

    # Price and Volume
    open: float
    high: float
    low: float
    close: float
    prev_close: float
    volume: int
    daily_return: float

    # Momentum Indicators
    momentum: float
    raw_momentum: float
    global_beta: float
    local_beta: float
    sector_beta: float

    # Volatility Indicators
    ivol: float
    ivol_percentile: float
    ivol_decile: int
    max_ret: float

    # Quality Indicators
    id_score: float
    id_pass: bool
    amihud_illiq: float
    overnight_return: float
    intraday_return: float
    overnight_pass: bool

    # EEMD Trend
    eemd_slope: float
    eemd_days: int
    eemd_confirmed: bool

    # StatementDog
    f_score: int
    pb: float
    roe: float

    # Signals
    signal: str
    entry_signal: str
    recommendation: str
    action_signal: str
    alpha_decay_status: str

    # Pricing Related (stock_data_builder.build_pricing)
    theo_price: float
    remaining_alpha: float
    theoretical_price_deviation_pct: float
    ou_upper_band: float
    ou_lower_band: float

    # Alpha/Beta Decomposition (stock_data_builder.build_alpha_beta)
    alpha_beta_decomposition: AlphaBetaContributionDTO

    # Lifecycle Related (stock_data_builder.build_lifecycle)
    signal_age_days: int
    remaining_meat_ratio: float
    residual_rsi: float
    rsi_divergence: str
    frog_in_pan_id: float
    theoretical_price: float

    # Exit Signals Related (stock_data_builder.build_exit_signals)
    stop_loss_triggered: bool
    beta_change_pct: float
    beta_spike_alert: bool
    atr_trailing_stop: float
    volatility_expansion_flag: bool
    correlation_drift: float
    short_term_reversal: float
    rolling_beta_60d: float

    # Other Fields
    half_life: float
    correlation_20d: float
    residual_source: str

    # StatementDog Nested Data
    statementdog: StatementDogData
