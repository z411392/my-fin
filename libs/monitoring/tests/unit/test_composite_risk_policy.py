"""CompositeRiskPolicy 單元測試"""

from libs.monitoring.src.application.policies.composite_risk_policy import (
    CompositeRiskPolicy,
)
from libs.shared.src.enums.vix_tier import VixTier
from libs.shared.src.enums.gex_level import GEXLevel


class TestCompositeRiskPolicy:
    """複合風險策略測試"""

    def test_no_alert_when_conditions_not_met(self) -> None:
        """條件不滿足不應發警報"""
        policy = CompositeRiskPolicy()

        # VIX 高但 GEX 為 LONG
        result = policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_LONG, 30.0, 1e9)
        assert result is None

        # GEX SHORT 但 VIX 低
        result = policy.evaluate(VixTier.TIER_1, GEXLevel.STRONG_SHORT, 22.0, -1e9)
        assert result is None

    def test_alert_when_both_conditions_met(self) -> None:
        """VIX 高且 GEX SHORT 應發警報"""
        policy = CompositeRiskPolicy()
        result = policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_SHORT, 28.0, -5e8)

        assert result is not None
        assert result["code"] == "COMPOSITE_RISK"
        assert "VIX TIER_2" in result["message"]
        assert "GEX MILD_SHORT" in result["message"]

    def test_critical_alert_on_extreme_conditions(self) -> None:
        """VIX TIER_3 + GEX STRONG_SHORT 應發 CRITICAL"""
        policy = CompositeRiskPolicy()
        result = policy.evaluate(VixTier.TIER_3, GEXLevel.STRONG_SHORT, 40.0, -2e9)

        assert result is not None
        assert result["level"] == "CRITICAL"
        assert "50%" in result["action"]

    def test_no_repeated_alert(self) -> None:
        """相同條件不應重複發警報"""
        policy = CompositeRiskPolicy()
        result1 = policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_SHORT, 28.0, -5e8)
        result2 = policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_SHORT, 29.0, -5e8)

        assert result1 is not None
        assert result2 is None  # 不應重複

    def test_no_alert_on_risk_clearance(self) -> None:
        """風險解除時不發警報 (可選行為)"""
        policy = CompositeRiskPolicy()
        policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_SHORT, 28.0, -5e8)  # 觸發

        # 風險解除
        result = policy.evaluate(VixTier.TIER_1, GEXLevel.MILD_LONG, 22.0, 1e9)
        assert result is None

    def test_reset_clears_state(self) -> None:
        """reset 應清除狀態"""
        policy = CompositeRiskPolicy()
        policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_SHORT, 28.0, -5e8)
        policy.reset()

        # 應可再次觸發
        result = policy.evaluate(VixTier.TIER_2, GEXLevel.MILD_SHORT, 28.0, -5e8)
        assert result is not None
