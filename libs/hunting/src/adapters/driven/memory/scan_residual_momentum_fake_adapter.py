"""Fake ScanResidualMomentum Adapter for testing"""

from libs.hunting.src.ports.scan_residual_momentum_port import ScanResidualMomentumPort
from libs.shared.src.dtos.hunting.residual_momentum_scan_result_dto import (
    ResidualMomentumScanResultDTO,
)
from libs.shared.src.dtos.hunting.stock_evaluation_dto import StockEvaluationResultDTO


class ScanResidualMomentumFakeAdapter(ScanResidualMomentumPort):
    """InMemory Fake 實作 - 用於測試

    提供預設的掃描結果，可透過 set_result 設定自訂結果
    """

    def __init__(self) -> None:
        self._result: ResidualMomentumScanResultDTO = {
            "market": "tw",
            "date": "2026-01-03",
            "scanned": 100,
            "qualified": 5,
            "targets": [
                {
                    "symbol": "2330",
                    "momentum_score": 2.5,
                    "trend_status": "上升確認",
                    "trend_days": 5,
                    "ivol": 0.25,
                    "f_score": 8,
                },
                {
                    "symbol": "2454",
                    "momentum_score": 2.1,
                    "trend_status": "初期上升",
                    "trend_days": 3,
                    "ivol": 0.30,
                    "f_score": 7,
                },
                {
                    "symbol": "3017",
                    "momentum_score": 1.8,
                    "trend_status": "上升確認",
                    "trend_days": 4,
                    "ivol": 0.28,
                    "f_score": 7,
                },
            ],
        }

    def set_result(self, result: ResidualMomentumScanResultDTO) -> None:
        """設定自訂結果 (測試用)"""
        self._result = result

    async def execute(
        self,
        top_n: int = 10,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """模擬掃描執行"""
        result = dict(self._result)
        result["market"] = market
        # 根據 top_n 限制回傳數量
        if len(result.get("targets", [])) > top_n:
            result["targets"] = result["targets"][:top_n]
        return result

    async def execute_momentum(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """模擬動能評估執行"""
        return await self.execute(
            top_n=100, market=market, stocks=stocks, start_from=start_from
        )

    async def execute_fundamental(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """模擬財報狗爬蟲執行"""
        return await self.execute(
            top_n=100, market=market, stocks=stocks, start_from=start_from
        )

    def evaluate_single_stock(
        self, symbol: str, market: str = "auto"
    ) -> StockEvaluationResultDTO | None:
        """模擬單一股票評估"""
        return {
            "symbol": symbol,
            "momentum": 1.5,
            "signal": "🟢",
            "quality_score": 7.0,
        }
