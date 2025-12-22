"""複合風險警報策略

結合 VIX Tier 與 GEX Level 判斷複合風險
VIX Tier >= 2 且 GEX 為 SHORT 時觸發警報
"""

import logging

from injector import inject
from libs.shared.src.enums.alert_level import AlertLevel
from libs.shared.src.enums.vix_tier import VixTier
from libs.shared.src.enums.gex_level import GEXLevel
from libs.monitoring.src.ports.composite_risk_port import CompositeRiskPort
from libs.shared.src.dtos.monitoring.risk_alert_dto import RiskAlertDTO


class CompositeRiskPolicy(CompositeRiskPort):
    """複合風險警報策略

    同時考慮 VIX Tier 和 GEX Level 的複合判斷
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._previous_triggered: bool = False

    def evaluate(
        self,
        vix_tier: VixTier,
        gex_level: GEXLevel,
        vix_value: float,
        gex_value: float,
    ) -> RiskAlertDTO | None:
        """評估複合風險是否需要發送警報

        Args:
            vix_tier: 當前 VIX Tier
            gex_level: 當前 GEX Level
            vix_value: 當前 VIX 數值
            gex_value: 當前 GEX 數值

        Returns:
            RiskAlertDTO | None: 警報 DTO，若無需警報則為 None
        """
        # 判斷是否達到複合風險條件
        is_vix_risky = vix_tier in [VixTier.TIER_2, VixTier.TIER_3]
        is_gex_short = gex_level in [GEXLevel.MILD_SHORT, GEXLevel.STRONG_SHORT]

        current_triggered = is_vix_risky and is_gex_short

        # 首次觸發或狀態改變
        if current_triggered and not self._previous_triggered:
            self._previous_triggered = True

            # 決定警報等級
            if vix_tier == VixTier.TIER_3 and gex_level == GEXLevel.STRONG_SHORT:
                level = AlertLevel.CRITICAL
            elif vix_tier == VixTier.TIER_3 or gex_level == GEXLevel.STRONG_SHORT:
                level = AlertLevel.SEVERE
            else:
                level = AlertLevel.WARNING

            return {
                "code": "COMPOSITE_RISK",
                "level": level.value,
                "message": f"複合風險警報! VIX {vix_tier.name} + GEX {gex_level.name}",
                "current_value": vix_value,
                "threshold": 25.0,  # VIX Tier 2 閾值
                "gex_value": gex_value,
                "action": self._get_action(vix_tier, gex_level),
            }

        # 風險解除
        if not current_triggered and self._previous_triggered:
            self._previous_triggered = False
            # 可選：發送風險解除通知
            return None

        return None

    def _get_action(self, vix_tier: VixTier, gex_level: GEXLevel) -> str:
        """根據組合決定建議動作"""
        if vix_tier == VixTier.TIER_3 and gex_level == GEXLevel.STRONG_SHORT:
            return "立即減倉 50%+，啟動防禦模式"
        if vix_tier == VixTier.TIER_3:
            return "緊急減倉 50%+，GEX 空方加劇風險"
        if gex_level == GEXLevel.STRONG_SHORT:
            return "減倉 30%，注意 Gamma 擠壓風險"
        return "減倉 20-30%，提高警戒"

    def reset(self) -> None:
        """重置狀態"""
        self._previous_triggered = False
