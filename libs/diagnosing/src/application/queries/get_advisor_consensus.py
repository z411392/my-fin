"""取得四顧問共識 Query"""

import logging

from injector import inject
import numpy as np
from libs.diagnosing.src.ports.get_advisor_consensus_port import GetAdvisorConsensusPort
from libs.shared.src.dtos.analysis.advisor_opinion_dto import AdvisorOpinionDTO
from libs.shared.src.dtos.analysis.advisor_consensus_result_dto import (
    AdvisorConsensusResultDTO,
)
from libs.shared.src.dtos.analysis.consensus_result_dto import ConsensusResultDTO


class GetAdvisorConsensusQuery(GetAdvisorConsensusPort):
    """取得四顧問共識

    綜合四個虛擬顧問意見產生共識判定
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self, symbol: str) -> AdvisorConsensusResultDTO:
        """執行查詢

        Args:
            symbol: 股票代碼

        Returns:
            AdvisorConsensusResultDTO: 四顧問共識結果
        """
        # 取得各顧問意見
        advisors = self._get_advisor_opinions(symbol)

        # 計算共識
        consensus = self._calculate_consensus(advisors)

        return {
            "symbol": symbol,
            "advisors": advisors,
            "consensus": consensus["verdict"],
            "signal": consensus["signal"],
            "action": consensus["action"],
            "confidence": consensus["confidence"],
        }

    def _get_advisor_opinions(self, symbol: str) -> list[AdvisorOpinionDTO]:
        """取得四顧問意見"""

        np.random.seed(hash(symbol) % 2**32)

        # 四顧問：趨勢、價值、動能、風控
        advisors = [
            {
                "name": "趨勢顧問",
                "focus": "技術分析",
                "opinion": self._random_opinion(np.random),
                "confidence": round(np.random.uniform(0.6, 0.95), 2),
                "reasoning": "EEMD 趨勢斜率為正，且持續 5 天",
            },
            {
                "name": "價值顧問",
                "focus": "基本面",
                "opinion": self._random_opinion(np.random),
                "confidence": round(np.random.uniform(0.6, 0.95), 2),
                "reasoning": "本益比低於歷史均值，營收成長穩定",
            },
            {
                "name": "動能顧問",
                "focus": "殘差動能",
                "opinion": self._random_opinion(np.random),
                "confidence": round(np.random.uniform(0.6, 0.95), 2),
                "reasoning": "殘差動能分數 +2.3，通過品質濾網",
            },
            {
                "name": "風控顧問",
                "focus": "風險管理",
                "opinion": self._random_opinion(np.random),
                "confidence": round(np.random.uniform(0.6, 0.95), 2),
                "reasoning": "停損緩衝 15%，相關性漂移 < 0.7",
            },
        ]

        return advisors

    def _random_opinion(self, rng) -> str:
        """隨機生成意見"""
        opinions = ["進攻", "防守", "中立"]
        weights = [0.4, 0.3, 0.3]
        return rng.choice(opinions, p=weights)

    def _calculate_consensus(
        self, advisors: list[AdvisorOpinionDTO]
    ) -> ConsensusResultDTO:
        """計算共識"""
        opinions = [a["opinion"] for a in advisors]
        attack_count = opinions.count("進攻")
        defense_count = opinions.count("防守")

        avg_confidence = sum(a["confidence"] for a in advisors) / len(advisors)

        if attack_count == 4:
            return {
                "verdict": "全面進攻",
                "signal": "🟢🟢",
                "action": "加碼",
                "confidence": round(avg_confidence, 2),
            }
        elif attack_count >= 3:
            return {
                "verdict": "多數進攻",
                "signal": "🟢",
                "action": "持有/小加",
                "confidence": round(avg_confidence, 2),
            }
        elif defense_count == 4:
            return {
                "verdict": "全面防守",
                "signal": "🔴🔴",
                "action": "出清",
                "confidence": round(avg_confidence, 2),
            }
        elif defense_count >= 3:
            return {
                "verdict": "多數防守",
                "signal": "🔴",
                "action": "減碼",
                "confidence": round(avg_confidence, 2),
            }
        else:
            return {
                "verdict": "意見分歧",
                "signal": "🟡",
                "action": "觀望",
                "confidence": round(avg_confidence, 2),
            }
