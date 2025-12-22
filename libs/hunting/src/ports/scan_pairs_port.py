"""掃描配對交易 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.hunting.pairs_scan_result_dto import PairsScanResultDTO


class ScanPairsPort(Protocol):
    """掃描統計套利配對

    CLI Entry: fin pairs
    """

    def execute(
        self,
        sector: str = "半導體",
        min_correlation: float = 0.7,
    ) -> PairsScanResultDTO:
        """
        掃描配對交易機會

        Returns:
            PairsScanResultDTO: 包含 pairs 列表
        """
        ...
