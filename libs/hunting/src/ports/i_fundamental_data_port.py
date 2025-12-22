from abc import ABC, abstractmethod
from typing import Callable

from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)
from libs.shared.src.dtos.statementdog.fundamental_summary_map_dto import (
    FundamentalSummaryMap,
)


class IFundamentalDataPort(ABC):
    """基本面數據 Port"""

    @abstractmethod
    def batch_get_f_score(
        self,
        symbols: list[str],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> FundamentalSummaryMap:
        """批次取得 F-Score"""
        pass

    @abstractmethod
    def get_fundamental_summary(self, symbol: str) -> FundamentalSummaryDTO | None:
        """取得單一股票的基本面摘要

        Returns:
            包含營收動能、獲利品質、評價指標、F-Score 的完整摘要
            若無法取得則回傳 None
        """
        pass
