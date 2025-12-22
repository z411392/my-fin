"""Integration tests for VPINShioajiAdapter

這些測試使用模擬資料，不需要 Shioaji 連線。
執行: pytest apps/risk_sentinel/tests/integration -v
"""

import pytest


@pytest.mark.integration
@pytest.mark.skip(
    reason="Shioaji + Python 3.13 segfault (skip until Shioaji supports 3.13)"
)
class TestVPINShioajiAdapter:
    """測試 VPINShioajiAdapter"""

    def test_calculate_vpin_from_sample_ticks(self) -> None:
        """測試使用模擬 tick 資料計算 VPIN"""
        from libs.monitoring.src.adapters.driven.shioaji.vpin_shioaji_adapter import (
            VPINShioajiAdapter,
        )

        adapter = VPINShioajiAdapter(simulation=True)

        sample_ticks = [
            {"volume": 100, "price": 600.0, "tick_type": 1},
            {"volume": 50, "price": 600.5, "tick_type": 1},
            {"volume": 80, "price": 600.0, "tick_type": 2},
            {"volume": 120, "price": 599.5, "tick_type": 2},
            {"volume": 60, "price": 600.0, "tick_type": 1},
            {"volume": 90, "price": 600.5, "tick_type": 1},
            {"volume": 70, "price": 600.0, "tick_type": 2},
            {"volume": 110, "price": 599.0, "tick_type": 2},
            {"volume": 85, "price": 599.5, "tick_type": 1},
            {"volume": 95, "price": 600.0, "tick_type": 2},
        ]

        result = adapter.calculate_vpin_from_ticks(sample_ticks)

        assert "vpin" in result
        assert "level" in result
        assert "action" in result
        assert "source" in result
        assert result["source"] == "Shioaji"

    def test_vpin_result_structure(self) -> None:
        """測試 VPIN 結果結構"""
        from libs.monitoring.src.adapters.driven.shioaji.vpin_shioaji_adapter import (
            VPINShioajiAdapter,
        )

        adapter = VPINShioajiAdapter(simulation=True)

        # 空資料應該返回預設值
        result = adapter.calculate_vpin_from_ticks([])

        assert isinstance(result["vpin"], (int, float))
        assert isinstance(result["level"], str)
        assert isinstance(result["action"], str)
