"""監控策略擁擠度 Query

實作 MonitorCrowdingPort Driving Port
"""

import logging

from injector import inject

from libs.reviewing.src.domain.services.crowding_detector import (
    assess_crowding,
    calculate_days_to_cover,
    calculate_pairwise_correlation,
)
from libs.reviewing.src.ports.monitor_crowding_port import MonitorCrowdingPort
from libs.reviewing.src.ports.stock_data_port import StockDataPort
from libs.shared.src.dtos.reviewing.crowding_result_dto import CrowdingResultDTO


# 預設殘差動能策略標的 (混合市場)
DEFAULT_RESIDUAL_MOMENTUM_SYMBOLS = [
    # 美股大型科技
    "AAPL",  # Apple
    "MSFT",  # Microsoft
    "NVDA",  # NVIDIA
    "GOOGL",  # Google
    "AMZN",  # Amazon
    # 美股半導體
    "TSM",  # 台積電 ADR
    "AMD",  # AMD
    "INTC",  # Intel
    # 指數 ETF
    "SPY",  # S&P 500
    "QQQ",  # Nasdaq 100
]


class MonitorCrowdingQuery(MonitorCrowdingPort):
    """監控策略擁擠度"""

    @inject
    def __init__(self, stock_data: StockDataPort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._stock_data = stock_data

    def execute(
        self,
        strategy: str = "residual_momentum",
        symbols: list[str] | None = None,
        position_value: float = 1000000.0,
        dsr: float = 0.92,
        alpha_half_life: float = 8.0,
    ) -> CrowdingResultDTO:
        """監控策略擁擠度

        Args:
            strategy: 策略名稱
            symbols: 標的列表 (預設使用殘差動能策略標的)
            position_value: 持倉價值 (預設 100 萬)
            dsr: Deflated Sharpe Ratio (需外部計算)
            alpha_half_life: Alpha 半衰期 (週)

        Returns:
            dict: 擁擠度評估結果
        """
        if symbols is None:
            symbols = DEFAULT_RESIDUAL_MOMENTUM_SYMBOLS

        # 取得真實報酬矩陣
        returns = self._stock_data.get_returns_matrix(symbols, days=252)

        if returns.size == 0:
            return {
                "strategy": strategy,
                "pairwise_correlation": 0.0,
                "days_to_cover": 0.0,
                "dsr": dsr,
                "alpha_half_life": alpha_half_life,
                "status": "資料不足",
                "action": "無法評估",
            }

        # 計算成對相關性
        pairwise_corr = calculate_pairwise_correlation(returns)

        # 計算平倉天數 (使用第一個標的的成交量估算)
        avg_volume = self._stock_data.get_average_daily_volume(symbols[0], days=20)
        days_to_cover = calculate_days_to_cover(position_value, avg_volume)

        # 評估擁擠度
        result = assess_crowding(pairwise_corr, days_to_cover, dsr, alpha_half_life)

        return {
            "strategy": strategy,
            **result,
        }
