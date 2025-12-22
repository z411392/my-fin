"""VIX Tier 變化警報策略

監聽 VIX Tier 變化，Tier >= 2 時觸發警報
"""

import logging

from injector import inject
from libs.shared.src.dtos.policy_alert_dto import PolicyAlertDTO
from libs.shared.src.enums.alert_level import AlertLevel
from libs.shared.src.enums.vix_tier import VixTier
from libs.monitoring.src.ports.vix_tier_changed_port import VixTierChangedPort


class VixTierChangedPolicy(VixTierChangedPort):
    """VIX Tier 變化警報策略"""

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._previous_tier: VixTier | None = None

    def evaluate(
        self, current_tier: VixTier, vix_value: float
    ) -> PolicyAlertDTO | None:
        """評估是否需要發送警報

        Args:
            current_tier: 當前 VIX Tier
            vix_value: 當前 VIX 數值

        Returns:
            PolicyAlertDTO | None: 警報，若無需警報則為 None
        """
        # 首次執行，記錄當前狀態
        if self._previous_tier is None:
            self._previous_tier = current_tier
            return None

        # Tier 未變化
        if current_tier == self._previous_tier:
            return None

        # 記錄之前的 tier 以便產生警報
        previous = self._previous_tier
        self._previous_tier = current_tier

        # 只對惡化 (tier 數值上升) 發送警報
        tier_order = [VixTier.TIER_0, VixTier.TIER_1, VixTier.TIER_2, VixTier.TIER_3]
        prev_idx = tier_order.index(previous)
        curr_idx = tier_order.index(current_tier)

        if curr_idx <= prev_idx:
            return None  # 改善或不變，不發警報

        # 決定警報等級
        if current_tier == VixTier.TIER_3:
            level = AlertLevel.CRITICAL
        elif current_tier == VixTier.TIER_2:
            level = AlertLevel.SEVERE
        else:
            level = AlertLevel.WARNING

        return {
            "code": f"VIX_{current_tier.name}",
            "level": level.value,
            "message": f"VIX Tier 升級: {previous.name} → {current_tier.name}",
            "current_value": vix_value,
            "threshold": self._get_threshold(current_tier),
            "action": current_tier.value,
        }

    def _get_threshold(self, tier: VixTier) -> float:
        """取得 tier 閾值"""
        thresholds = {
            VixTier.TIER_0: 20.0,
            VixTier.TIER_1: 20.0,
            VixTier.TIER_2: 25.0,
            VixTier.TIER_3: 35.0,
        }
        return thresholds.get(tier, 20.0)

    def reset(self) -> None:
        """重置狀態"""
        self._previous_tier = None
