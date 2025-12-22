"""Full Stock Scan Result DTO

Corresponds to stock_data_builder.build_full_push_data return structure
"""

from typing import TypedDict

from libs.shared.src.dtos.stock_scan.market_data import MarketData
from libs.shared.src.dtos.stock_scan.momentum_data import MomentumData
from libs.shared.src.dtos.stock_scan.pricing_data import PricingData
from libs.shared.src.dtos.stock_scan.alpha_beta_data import AlphaBetaData
from libs.shared.src.dtos.stock_scan.lifecycle_data import LifecycleData
from libs.shared.src.dtos.stock_scan.exit_signals_data import ExitSignalsData
from libs.shared.src.dtos.stock_scan.statementdog_data import StatementDogData


class StockScanResult(TypedDict, total=False):
    """Full Stock Scan Result (Push to Google Sheets)

    Corresponds to GAS v3.3 format
    """

    symbol: str
    date: str
    market_data: MarketData
    momentum: MomentumData
    pricing: PricingData
    alpha_beta: AlphaBetaData
    lifecycle: LifecycleData
    exit_signals: ExitSignalsData
    statementdog: StatementDogData
