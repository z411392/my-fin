"""Run Daily Scan Port — Driving Port for scanning orchestration"""

from typing import Protocol

from libs.shared.src.dtos.scanning.daily_scan_result_dto import DailyScanResultDTO


class RunDailyScanPort(Protocol):
    """掃描台美股全市場的 Driving Port"""

    async def execute(
        self,
        market: str = "tw",
        top_n: int = 20,
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> DailyScanResultDTO:
        """執行每日掃描（完整流程：動能評估 + 財報狗）"""
        ...

    async def execute_momentum(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> DailyScanResultDTO:
        """只執行動能評估階段（不含財報狗）"""
        ...

    async def execute_fundamental(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> DailyScanResultDTO:
        """只執行財報狗爬蟲階段（讀取已有 JSON，補上財報狗資料）"""
        ...
