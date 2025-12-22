"""
FinancialDataProviderPort - Driven Port

實作者: YahooFinancialDataAdapter
"""

from typing import Protocol

from libs.shared.src.dtos.analysis.earnings_dto import EarningsDTO
from libs.shared.src.dtos.analysis.financial_info_dto import (
    FinancialInfoDTO,
    AnalystRatingsDTO,
)
from libs.shared.src.dtos.market.ohlcv_dto import DailyOhlcvDTO


class FinancialDataProviderPort(Protocol):
    """Driven Port for Financial Data"""

    def get_financial_info(self, symbol: str) -> FinancialInfoDTO:
        """Get fundamental financial info"""
        ...

    def get_earnings_history(self, symbol: str) -> list[EarningsDTO]:
        """Get earnings history"""
        ...

    def get_analyst_ratings(self, symbol: str) -> AnalystRatingsDTO:
        """Get analyst ratings"""
        ...

    def get_daily_prices(self, symbol: str, days: int = 252) -> list[DailyOhlcvDTO]:
        """Get daily price history"""
        ...

    def get_current_price(self, symbol: str) -> float:
        """Get current price"""
        ...
