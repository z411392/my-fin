"""Run Daily Scan Command — Orchestration Command

Orchestrates alpha_hunter for residual momentum scanning
"""

import logging

from injector import inject
from libs.hunting.src.ports.scan_residual_momentum_port import (
    ScanResidualMomentumPort,
)
from libs.scanning.src.ports.run_daily_scan_port import RunDailyScanPort
from libs.shared.src.dtos.scanning.daily_scan_result_dto import DailyScanResultDTO


class RunDailyScanCommand(RunDailyScanPort):
    """Daily scan orchestration command"""

    @inject
    def __init__(self, scan_residual: ScanResidualMomentumPort):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._scan_residual = scan_residual

    async def execute(
        self,
        market: str = "tw",
        top_n: int = 20,
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> DailyScanResultDTO:
        """Execute scan process (full flow: momentum evaluation + StatementDog)"""
        self._logger.info(f"掃描 {market} 市場...")
        result = await self._scan_residual.execute(
            market=market, top_n=top_n, stocks=stocks, start_from=start_from
        )
        self._logger.info(f"{market} 掃描完成")
        return result

    async def execute_momentum(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> DailyScanResultDTO:
        """Execute only momentum evaluation phase (without StatementDog)"""
        self._logger.info(f"動能評估 {market} 市場...")
        result = await self._scan_residual.execute_momentum(
            market=market, stocks=stocks, start_from=start_from
        )
        self._logger.info(f"{market} 動能評估完成")
        return result

    async def execute_fundamental(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> DailyScanResultDTO:
        """Execute only StatementDog crawler phase (read existing JSON, add StatementDog data)"""
        self._logger.info(f"財報狗爬蟲 {market} 市場...")
        result = await self._scan_residual.execute_fundamental(
            market=market, stocks=stocks, start_from=start_from
        )
        self._logger.info(f"{market} 財報狗爬蟲完成")
        return result
