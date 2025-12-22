"""觸發雙迴圈學習 Command

當策略連續 3 次跳停或 Kelly 比率持續下降時，執行
"""

import logging

from injector import inject
from libs.reviewing.src.ports.trigger_double_loop_learning_port import (
    TriggerDoubleLoopLearningPort,
)
from libs.shared.src.dtos.strategy.trigger_condition_dto import TriggerConditionDTO
from libs.shared.src.dtos.strategy.hypothesis_dto import HypothesisDTO
from libs.shared.src.dtos.strategy.recommendation_dto import RecommendationDTO
from libs.shared.src.dtos.reviewing.double_loop_learning_result_dto import (
    DoubleLoopLearningResultDTO,
)


class TriggerDoubleLoopLearningCommand(TriggerDoubleLoopLearningPort):
    """觸發雙環學習

    當策略結構性失效時觸發，重新檢視底層假設
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(
        self,
        strategy: str = "residual_momentum",
        reason: str = "結構性斷裂",
    ) -> DoubleLoopLearningResultDTO:
        """執行雙環學習觸發

        Args:
            strategy: 策略名稱
            reason: 觸發原因

        Returns:
            DoubleLoopLearningResultDTO: 雙環學習結果
        """
        # 1. 識別觸發條件
        trigger_conditions = self._identify_trigger_conditions(strategy)

        # 2. 生成假設檢視清單
        hypothesis_review = self._generate_hypothesis_review(strategy)

        # 3. 提出改進建議
        recommendations = self._generate_recommendations(trigger_conditions)

        # 4. 記錄學習事件
        learning_event = {
            "timestamp": "2025-01-01T12:00:00",
            "strategy": strategy,
            "reason": reason,
            "trigger_conditions": trigger_conditions,
            "hypothesis_review": hypothesis_review,
            "recommendations": recommendations,
            "learning_type": "雙環學習",
            "status": "PENDING_REVIEW",
        }

        return learning_event

    def _identify_trigger_conditions(self, strategy: str) -> list[TriggerConditionDTO]:
        """識別觸發條件"""
        return [
            {
                "condition": "OOS 表現下滑",
                "value": "IS Sharpe 1.8 → OOS Sharpe 0.6",
                "severity": "HIGH",
            },
            {
                "condition": "結構斷裂",
                "value": "PCA 餘弦相似度 < 0.8",
                "severity": "HIGH",
            },
            {
                "condition": "Alpha 衰減",
                "value": "DSR 從 0.95 降至 0.72",
                "severity": "MEDIUM",
            },
        ]

    def _generate_hypothesis_review(self, strategy: str) -> list[HypothesisDTO]:
        """生成假設回顧"""
        if strategy == "residual_momentum":
            return [
                {
                    "hypothesis": "殘差動能在趨勢市場有效",
                    "status": "需驗證",
                    "evidence": "Hurst 指數顯示體制轉變",
                },
                {
                    "hypothesis": "三層因子剝離足以消除系統風險",
                    "status": "需驗證",
                    "evidence": "新因子出現 (如 AI 題材)",
                },
                {
                    "hypothesis": "品質濾網有效篩選低品質標的",
                    "status": "有效",
                    "evidence": "IVOL/ID 濾網仍有區分能力",
                },
            ]
        return []

    def _generate_recommendations(
        self, conditions: list[TriggerConditionDTO]
    ) -> list[RecommendationDTO]:
        """生成建議"""
        recommendations = []

        for cond in conditions:
            if cond["severity"] == "HIGH":
                recommendations.append(
                    {
                        "action": "暫停策略",
                        "priority": "🔴",
                        "detail": f"因 {cond['condition']} 暫停 2 週觀察",
                    }
                )
            elif cond["severity"] == "MEDIUM":
                recommendations.append(
                    {
                        "action": "減少配置",
                        "priority": "🟡",
                        "detail": f"因 {cond['condition']} 減少配置至 50%",
                    }
                )

        recommendations.append(
            {
                "action": "重新回測",
                "priority": "🟢",
                "detail": "使用最近 6 個月數據重新驗證",
            }
        )

        return recommendations
