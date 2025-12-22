"""觸發出場 Command"""

import logging

from injector import inject
from libs.diagnosing.src.ports.trigger_exit_port import TriggerExitPort
from libs.shared.src.dtos.analysis.checkup_result_dto import TriggerExitResultDTO


class TriggerExitCommand(TriggerExitPort):
    """觸發出場動作

    根據論點失效或診斷結果觸發出場
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(
        self, symbol: str, action: str = "REDUCE", reason: str = ""
    ) -> TriggerExitResultDTO:
        """執行觸發出場

        Args:
            symbol: 股票代號
            action: 動作 (REDUCE/SELL)
            reason: 出場理由

        Returns:
            TriggerExitResultDTO: 出場結果
        """
        valid_actions = ["REDUCE", "SELL"]
        if action not in valid_actions:
            return {"error": f"Invalid action. Must be one of {valid_actions}"}

        # 模擬計算建議部位調整
        if action == "SELL":
            target_position = 0
            urgency = "HIGH"
        else:
            target_position = 0.5  # 減碼一半
            urgency = "MEDIUM"

        return {
            "symbol": symbol,
            "action": action,
            "target_position_pct": target_position,
            "urgency": urgency,
            "reason": reason or f"系統觸發 {action}",
            "executed": False,  # 實際執行需用戶確認
        }
