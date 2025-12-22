"""掃描殘差動能 Driving Port"""

from typing import Protocol, runtime_checkable

from libs.shared.src.dtos.hunting.residual_momentum_scan_result_dto import (
    ResidualMomentumScanResultDTO,
)


@runtime_checkable
class ScanResidualMomentumPort(Protocol):
    """掃描殘差動能

    CLI Entry: fin scan / fin retain
    """

    async def execute(
        self,
        top_n: int = 10,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """
        掃描殘差動能標的 (完整流程：動能評估 + 財報狗)

        Args:
            top_n: 返回前 N 名
            market: 市場 (tw, tw_shioaji, us, us_full)
            stocks: 自訂股票清單 (retain 模式)
            start_from: 從指定 SYMBOL 開始掃描 (斷點續掃)

        Returns:
            ResidualMomentumScanResultDTO: 包含 targets 列表
        """
        ...

    async def execute_momentum(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """
        只執行動能評估階段 (不含財報狗)

        Args:
            market: 市場 (tw, tw_shioaji, us, us_full)
            stocks: 自訂股票清單 (retain 模式)
            start_from: 從指定 SYMBOL 開始掃描

        Returns:
            ResidualMomentumScanResultDTO: 包含 targets 列表 (無 statementdog 欄位)
        """
        ...

    async def execute_fundamental(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """
        只執行財報狗爬蟲階段 (讀取已有 JSON，補上財報狗資料)

        Args:
            market: 市場 (tw, tw_shioaji, us, us_full)
            stocks: 自訂股票清單 (retain 模式，若為空則讀取當日所有 JSON)
            start_from: 從指定 SYMBOL 開始掃描 (斷點續掃)

        Returns:
            ResidualMomentumScanResultDTO: 包含更新後的 targets 列表
        """
        ...
