"""Integration tests for ShioajiOptionsAdapter

這些測試需要 Shioaji API 帳號，預設使用模擬模式。
執行: pytest apps/risk_sentinel/tests/integration -v
"""

import pytest


@pytest.mark.integration
@pytest.mark.skip(
    reason="Shioaji + Python 3.13 segfault (skip until Shioaji supports 3.13)"
)
class TestShioajiOptionsAdapter:
    """測試 ShioajiOptionsAdapter"""

    def test_connect_simulation_mode(self) -> None:
        """測試模擬模式連線"""
        from libs.monitoring.src.adapters.driven.shioaji.shioaji_options_adapter import (
            ShioajiOptionsAdapter,
        )

        adapter = ShioajiOptionsAdapter(simulation=True)
        assert adapter.connect() is True
        adapter.disconnect()

    def test_get_options_chain(self) -> None:
        """測試取得選擇權鏈"""
        from libs.monitoring.src.adapters.driven.shioaji.shioaji_options_adapter import (
            ShioajiOptionsAdapter,
        )

        adapter = ShioajiOptionsAdapter(simulation=True)

        if not adapter.connect():
            pytest.skip("無法連線到 Shioaji")

        try:
            options = adapter.get_options_chain("TXO")
            # 模擬模式可能返回空列表
            assert isinstance(options, list)
        finally:
            adapter.disconnect()
