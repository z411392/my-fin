"""產生狩獵清單 Command"""

import asyncio
import logging
from datetime import date
from injector import inject

from libs.hunting.src.ports.generate_hunting_list_port import GenerateHuntingListPort
from libs.hunting.src.ports.scan_residual_momentum_port import ScanResidualMomentumPort
from libs.shared.src.dtos.hunting.hunting_list_result_dto import HuntingListResultDTO


class GenerateHuntingListCommand(GenerateHuntingListPort):
    """產生狩獵清單

    整合殘差動能掃描結果，產出狩獵標的
    """

    @inject
    def __init__(
        self,
        scan_query: ScanResidualMomentumPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._scan_query = scan_query

    def execute(self, top_n: int = 10, market: str = "tw") -> HuntingListResultDTO:
        """執行產生狩獵清單

        Args:
            top_n: 返回前 N 名
            market: 市場 ("tw" 或 "us")

        Returns:
            HuntingListResultDTO: 狩獵清單
        """

        # 使用真實掃描 Query (async 方法需包裝)
        scan_result = asyncio.run(self._scan_query.execute(top_n=top_n, market=market))

        # 轉換為狩獵清單格式
        hunting_list = []
        for target in scan_result.get("targets", []):
            hunting_list.append(
                {
                    "symbol": target.get("symbol", ""),
                    "momentum_score": target.get("momentum_score", 0.0),
                    "trend_status": target.get("trend_status", ""),
                    "trend_days": target.get("trend_days", 0),
                    "quality_passed": True,
                    "ivol": target.get("ivol", 0.0),
                    "f_score": target.get("f_score", 0),
                }
            )

        return {
            "date": date.today().isoformat(),
            "total_scanned": scan_result.get("scanned", 0),
            "passed_filters": len(hunting_list),
            "hunting_list": hunting_list,
        }
