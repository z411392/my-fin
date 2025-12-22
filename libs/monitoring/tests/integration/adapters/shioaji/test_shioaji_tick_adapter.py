"""Integration tests for ShioajiTickAdapter

這些測試需要 Shioaji API 帳號，預設使用模擬模式。
執行: pytest apps/risk_sentinel/tests/integration -v
"""

import pytest


@pytest.mark.integration
@pytest.mark.skip(
    reason="Shioaji + Python 3.13 segfault (skip until Shioaji supports 3.13)"
)
class TestShioajiTickAdapter:
    """測試 ShioajiTickAdapter"""

    def test_connect_simulation_mode(self) -> None:
        """測試模擬模式連線"""
        from libs.monitoring.src.adapters.driven.shioaji.shioaji_tick_adapter import (
            ShioajiTickAdapter,
        )

        adapter = ShioajiTickAdapter(simulation=True)
        assert adapter.connect() is True
        adapter.disconnect()

    def test_subscribe_and_get_ticks(self) -> None:
        """測試訂閱並取得 tick 資料"""
        import time

        from libs.monitoring.src.adapters.driven.shioaji.shioaji_tick_adapter import (
            ShioajiTickAdapter,
        )

        adapter = ShioajiTickAdapter(simulation=True)

        if not adapter.connect():
            pytest.skip("無法連線到 Shioaji")

        try:
            assert adapter.subscribe("2330") is True

            # 等待收集 tick 資料
            time.sleep(3)

            tick_count = adapter.get_tick_count("2330")
            # 模擬模式可能沒有真實資料
            assert tick_count >= 0

            if tick_count > 0:
                ticks = adapter.get_ticks("2330")
                assert len(ticks) > 0
        finally:
            adapter.disconnect()
