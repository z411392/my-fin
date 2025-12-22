from typing import Callable

from injector import inject

from libs.hunting.src.ports.i_fundamental_data_port import IFundamentalDataPort
from libs.shared.src.clients.statementdog.statement_dog_client import StatementDogClient
from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)
from libs.shared.src.dtos.statementdog.fundamental_summary_map_dto import (
    FundamentalSummaryMap,
)
import logging


class StatementDogFundamentalAdapter(IFundamentalDataPort):
    """財報狗基本面數據適配器

    由 lifespan.py 注入 StatementDogClient
    """

    @inject
    def __init__(self, client: StatementDogClient) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.client = client
        self._cache: dict[str, FundamentalSummaryDTO] = {}

    def batch_get_f_score(
        self,
        symbols: list[str],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> FundamentalSummaryMap:
        """批次取得 F-Score"""
        self.logger.info(
            f"Fetching F-Score for {len(symbols)} symbols via StatementDog..."
        )
        try:
            results = self.client.batch_get_fundamental_summaries(
                symbols, max_concurrent=5, on_progress=on_progress
            )
            return results
        except Exception as e:
            self.logger.error(f"Failed to fetch F-Score: {e}")
            return {}

    def get_fundamental_summary(self, symbol: str) -> FundamentalSummaryDTO | None:
        """取得單一股票的基本面摘要"""
        try:
            return self.client.get_fundamental_summary(symbol)
        except Exception as e:
            self.logger.warning(f"[{symbol}] 無法取得基本面資料: {e}")
            return None

    async def batch_get_summaries_async(
        self,
        symbols: list[str],
        max_concurrent: int = 8,
        on_progress: Callable[[str, FundamentalSummaryDTO], None] | None = None,
    ) -> FundamentalSummaryMap:
        """批次並發取得多檔股票的基本面摘要 (Async 版本)

        Args:
            symbols: 股票代號列表
            max_concurrent: 最大並發分頁數 (預設 5)
            on_progress: 進度回調函數 (symbol, result) -> None

        Returns:
            {symbol: summary} 的字典 (已格式化)
        """
        # _batch_analyze_async 已返回格式化好的數據
        # 包含: symbol, is_valid, revenue_momentum, earnings_quality, valuation_metrics, f_score
        results = await self.client._batch_analyze_async(
            symbols, max_concurrent, on_progress
        )

        # 過濾掉有錯誤的結果，並快取
        summaries: dict[str, FundamentalSummaryDTO] = {}
        error_count = 0
        error_symbols: list[str] = []

        for symbol, data in results.items():
            if data and not data.get("error"):
                self._cache[symbol] = data
                summaries[symbol] = data
            else:
                error_count += 1
                error_msg = data.get("error", "unknown") if data else "no data"
                error_symbols.append(f"{symbol}({error_msg[:30]})")

        # 報告統計
        if error_count > 0:
            self.logger.warning(
                f"財報狗抓取統計: 成功 {len(summaries)}/{len(results)}, "
                f"失敗 {error_count} 檔: {', '.join(error_symbols[:5])}"
                + ("..." if len(error_symbols) > 5 else "")
            )
        else:
            self.logger.info(
                f"財報狗抓取統計: 全部成功 {len(summaries)}/{len(results)}"
            )

        return summaries
