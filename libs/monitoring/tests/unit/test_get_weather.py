"""GetWeatherQuery 單元測試"""

from libs.monitoring.src.domain.services.defcon_calculator import (
    calculate_defcon_level,
    get_defcon_action,
)
from libs.monitoring.src.domain.services.vix_tier_calculator import calculate_vix_tier
from libs.shared.src.enums.defcon_level import DefconLevel
from libs.shared.src.enums.vix_tier import VixTier


class TestGetWeatherQuery:
    """GetWeatherQuery 測試"""

    def test_defcon_5_green_weather(self) -> None:
        """正常條件應返回 DEFCON 5 綠燈"""
        level, emoji, permission = calculate_defcon_level(
            vix=15.0, hmm_state=0, vpin=0.5, gli_z=0.5
        )
        assert level == DefconLevel.DEFCON_5
        assert emoji == "🟢"

    def test_vix_tier_classification(self) -> None:
        """VIX 應正確分類 (methodology.md: 15/25/40 閾值)"""
        # VIX < 15: 平靜
        tier, _, _ = calculate_vix_tier(10.0)
        assert tier == VixTier.TIER_0

        # VIX 15-25: 警戒
        tier, _, _ = calculate_vix_tier(15.0)
        assert tier == VixTier.TIER_1

        tier, _, _ = calculate_vix_tier(22.0)
        assert tier == VixTier.TIER_1

    def test_defcon_3_limit_mode(self) -> None:
        """VIX > 30 應進入限制模式"""
        level, emoji, permission = calculate_defcon_level(
            vix=32.0, hmm_state=0, vpin=0.5, gli_z=0.5
        )
        assert level == DefconLevel.DEFCON_3
        assert permission == "Restricted mode"

    def test_defcon_action_mapping(self) -> None:
        """DEFCON 等級應對應正確行動"""
        action = get_defcon_action(DefconLevel.DEFCON_5)
        assert action == "Normal trading"

        action = get_defcon_action(DefconLevel.DEFCON_1)
        assert "Kill Switch" in action

    def test_requires_action_when_defcon_low(self) -> None:
        """DEFCON ≤ 3 應 requires_action"""
        level, _, _ = calculate_defcon_level(
            vix=45.0, hmm_state=2, vpin=0.9, gli_z=-2.0
        )
        requires_action = level.value <= 3
        assert requires_action is True
