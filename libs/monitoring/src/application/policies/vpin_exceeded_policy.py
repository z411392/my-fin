"""VPIN 超閾值警報策略

監聽 VPIN 超過 0.75/0.85/0.95 閾值時發送警報
"""

import logging

from injector import inject
from libs.shared.src.dtos.policy_alert_dto import PolicyAlertDTO
from libs.shared.src.enums.alert_level import AlertLevel
from libs.shared.src.enums.vpin_level import VPINLevel
from libs.monitoring.src.ports.vpin_exceeded_port import VpinExceededPort


# VPIN 閾值定義
VPIN_THRESHOLDS = {
    VPINLevel.ELEVATED: 0.75,
    VPINLevel.HIGH: 0.85,
    VPINLevel.CRITICAL: 0.95,
}


def get_vpin_level(vpin: float) -> VPINLevel:
    """根據 VPIN 值判斷等級"""
    if vpin >= VPIN_THRESHOLDS[VPINLevel.CRITICAL]:
        return VPINLevel.CRITICAL
    if vpin >= VPIN_THRESHOLDS[VPINLevel.HIGH]:
        return VPINLevel.HIGH
    if vpin >= VPIN_THRESHOLDS[VPINLevel.ELEVATED]:
        return VPINLevel.ELEVATED
    return VPINLevel.NORMAL


class VpinExceededPolicy(VpinExceededPort):
    """VPIN 超閾值警報策略"""

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._previous_level: VPINLevel | None = None

    def evaluate(self, vpin_value: float) -> PolicyAlertDTO | None:
        """評估是否需要發送警報

        Args:
            vpin_value: 當前 VPIN 數值 (0-1)

        Returns:
            PolicyAlertDTO | None: 警報，若無需警報則為 None
        """
        current_level = get_vpin_level(vpin_value)

        # 首次執行，記錄當前狀態
        if self._previous_level is None:
            self._previous_level = current_level
            return None

        # 等級未變化
        if current_level == self._previous_level:
            return None

        # 記錄之前的 level
        previous = self._previous_level
        self._previous_level = current_level

        # 只對惡化 (level 上升) 發送警報
        level_order = [
            VPINLevel.NORMAL,
            VPINLevel.ELEVATED,
            VPINLevel.HIGH,
            VPINLevel.CRITICAL,
        ]
        prev_idx = level_order.index(previous)
        curr_idx = level_order.index(current_level)

        if curr_idx <= prev_idx:
            return None  # 改善或不變，不發警報

        # 決定警報等級
        alert_level_map = {
            VPINLevel.ELEVATED: AlertLevel.WARNING,
            VPINLevel.HIGH: AlertLevel.SEVERE,
            VPINLevel.CRITICAL: AlertLevel.CRITICAL,
        }
        alert_level = alert_level_map.get(current_level, AlertLevel.WARNING)

        return {
            "code": f"VPIN_{current_level.name}",
            "level": alert_level.value,
            "message": f"VPIN 升級: {previous.name} → {current_level.name}",
            "current_value": vpin_value,
            "threshold": VPIN_THRESHOLDS.get(current_level, 0.75),
            "action": self._get_action(current_level),
        }

    def _get_action(self, level: VPINLevel) -> str:
        """取得建議動作"""
        actions = {
            VPINLevel.ELEVATED: "注意市場波動",
            VPINLevel.HIGH: "減少新倉位",
            VPINLevel.CRITICAL: "考慮減倉或對沖",
        }
        return actions.get(level, "持續觀察")

    def reset(self) -> None:
        """重置狀態"""
        self._previous_level = None
