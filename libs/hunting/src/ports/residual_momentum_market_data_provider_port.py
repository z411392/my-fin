"""殘差動能市場數據提供者 Port"""

from typing import Protocol


class ResidualMomentumMarketDataProviderPort(Protocol):
    """殘差動能市場數據提供者 Port"""

    def get_returns(self, symbol: str, days: int) -> list[float]:
        """取得日報酬序列"""
        ...

    def get_spy_returns(self, days: int) -> list[float]:
        """取得 SPY 報酬序列"""
        ...

    def get_sector_returns(self, symbol: str, days: int) -> list[float]:
        """取得產業指數報酬序列"""
        ...

    def get_ivol_percentile(self, symbol: str) -> float:
        """取得 IVOL 百分位"""
        ...

    def get_amihud_percentile(self, symbol: str) -> float:
        """取得 Amihud ILLIQ 百分位"""
        ...
