"""VixTierChangedPolicy 單元測試"""

from libs.monitoring.src.application.policies.vix_tier_changed_policy import (
    VixTierChangedPolicy,
)
from libs.shared.src.enums.vix_tier import VixTier


class TestVixTierChangedPolicy:
    """VIX Tier 變化策略測試"""

    def test_first_call_returns_none(self) -> None:
        """首次呼叫應返回 None"""
        policy = VixTierChangedPolicy()
        result = policy.evaluate(VixTier.TIER_0, 18.0)
        assert result is None

    def test_no_alert_when_tier_unchanged(self) -> None:
        """Tier 未變化不應發警報"""
        policy = VixTierChangedPolicy()
        policy.evaluate(VixTier.TIER_0, 18.0)  # 初始化
        result = policy.evaluate(VixTier.TIER_0, 19.0)
        assert result is None

    def test_alert_on_tier_escalation(self) -> None:
        """Tier 惡化應發警報"""
        policy = VixTierChangedPolicy()
        policy.evaluate(VixTier.TIER_0, 18.0)  # 初始化
        result = policy.evaluate(VixTier.TIER_1, 22.0)

        assert result is not None
        assert result["code"] == "VIX_TIER_1"
        assert result["level"] == "WARNING"
        assert "TIER_0 → TIER_1" in result["message"]

    def test_no_alert_on_tier_improvement(self) -> None:
        """Tier 改善不應發警報"""
        policy = VixTierChangedPolicy()
        policy.evaluate(VixTier.TIER_2, 30.0)  # 初始化
        result = policy.evaluate(VixTier.TIER_1, 22.0)
        assert result is None

    def test_critical_alert_on_tier_3(self) -> None:
        """升到 TIER_3 應發 CRITICAL 警報"""
        policy = VixTierChangedPolicy()
        policy.evaluate(VixTier.TIER_2, 30.0)  # 初始化
        result = policy.evaluate(VixTier.TIER_3, 40.0)

        assert result is not None
        assert result["level"] == "CRITICAL"
        assert result["action"] == VixTier.TIER_3.value

    def test_severe_alert_on_tier_2(self) -> None:
        """升到 TIER_2 應發 SEVERE 警報"""
        policy = VixTierChangedPolicy()
        policy.evaluate(VixTier.TIER_1, 22.0)  # 初始化
        result = policy.evaluate(VixTier.TIER_2, 28.0)

        assert result is not None
        assert result["level"] == "SEVERE"

    def test_reset_clears_state(self) -> None:
        """reset 應清除狀態"""
        policy = VixTierChangedPolicy()
        policy.evaluate(VixTier.TIER_0, 18.0)
        policy.reset()
        result = policy.evaluate(VixTier.TIER_0, 18.0)
        assert result is None  # 應視為首次呼叫
