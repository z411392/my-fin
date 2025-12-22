"""股票資料 Driven Port

定義取得股票資料的介面
"""

from typing import Protocol
from decimal import Decimal

import numpy as np


class StockDataPort(Protocol):
    """股票資料 Port"""

    def get_returns_matrix(
        self,
        symbols: list[str],
        days: int = 252,
    ) -> np.ndarray:
        """取得多標的報酬矩陣

        Args:
            symbols: 股票代號列表
            days: 天數 (預設 252 交易日 = 1 年)

        Returns:
            np.ndarray: 報酬矩陣 (時間 × 標的)
        """
        ...

    def get_average_daily_volume(
        self,
        symbol: str,
        days: int = 20,
    ) -> float:
        """取得平均日成交量

        Args:
            symbol: 股票代號
            days: 天數 (預設 20 交易日)

        Returns:
            float: 平均日成交量
        """
        ...

    def get_current_price(
        self,
        symbol: str,
    ) -> Decimal:
        """取得現價

        Args:
            symbol: 股票代號

        Returns:
            Decimal: 現價
        """
        ...
