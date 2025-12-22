"""VpinExceededPolicy 單元測試"""

from libs.monitoring.src.application.policies.vpin_exceeded_policy import (
    VpinExceededPolicy,
    get_vpin_level,
)
from libs.shared.src.enums.vpin_level import VPINLevel


class TestGetVpinLevel:
    """VPIN 等級判斷測試"""

    def test_normal_level(self) -> None:
        """低於 0.75 應為 NORMAL"""
        assert get_vpin_level(0.5) == VPINLevel.NORMAL
        assert get_vpin_level(0.74) == VPINLevel.NORMAL

    def test_elevated_level(self) -> None:
        """0.75-0.85 應為 ELEVATED"""
        assert get_vpin_level(0.75) == VPINLevel.ELEVATED
        assert get_vpin_level(0.84) == VPINLevel.ELEVATED

    def test_high_level(self) -> None:
        """0.85-0.95 應為 HIGH"""
        assert get_vpin_level(0.85) == VPINLevel.HIGH
        assert get_vpin_level(0.94) == VPINLevel.HIGH

    def test_critical_level(self) -> None:
        """>= 0.95 應為 CRITICAL"""
        assert get_vpin_level(0.95) == VPINLevel.CRITICAL
        assert get_vpin_level(0.99) == VPINLevel.CRITICAL


class TestVpinExceededPolicy:
    """VPIN 超閾值策略測試"""

    def test_first_call_returns_none(self) -> None:
        """首次呼叫應返回 None"""
        policy = VpinExceededPolicy()
        result = policy.evaluate(0.5)
        assert result is None

    def test_no_alert_when_level_unchanged(self) -> None:
        """等級未變化不應發警報"""
        policy = VpinExceededPolicy()
        policy.evaluate(0.5)  # 初始化
        result = policy.evaluate(0.6)  # 仍是 NORMAL
        assert result is None

    def test_alert_on_level_escalation(self) -> None:
        """等級惡化應發警報"""
        policy = VpinExceededPolicy()
        policy.evaluate(0.5)  # NORMAL
        result = policy.evaluate(0.80)  # ELEVATED

        assert result is not None
        assert result["code"] == "VPIN_ELEVATED"
        assert result["level"] == "WARNING"
        assert "NORMAL → ELEVATED" in result["message"]

    def test_no_alert_on_improvement(self) -> None:
        """等級改善不應發警報"""
        policy = VpinExceededPolicy()
        policy.evaluate(0.90)  # HIGH
        result = policy.evaluate(0.70)  # NORMAL
        assert result is None

    def test_critical_alert(self) -> None:
        """升到 CRITICAL 應發 CRITICAL 警報"""
        policy = VpinExceededPolicy()
        policy.evaluate(0.90)  # HIGH
        result = policy.evaluate(0.96)  # CRITICAL

        assert result is not None
        assert result["level"] == "CRITICAL"
        assert "考慮減倉" in result["action"]

    def test_reset_clears_state(self) -> None:
        """reset 應清除狀態"""
        policy = VpinExceededPolicy()
        policy.evaluate(0.5)
        policy.reset()
        result = policy.evaluate(0.5)
        assert result is None
