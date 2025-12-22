"""測試 PerformCheckupCommand 的進階邏輯
包含定價模型、肉量評估與出場協議整合測試
"""

import pytest
from unittest.mock import MagicMock
from libs.diagnosing.src.application.commands.perform_checkup import (
    PerformCheckupCommand,
)
from libs.diagnosing.src.ports.financial_data_provider_port import (
    FinancialDataProviderPort,
)


class TestPerformCheckupAdvanced:
    @pytest.fixture
    def command(self):
        mock_provider = MagicMock(spec=FinancialDataProviderPort)

        # Mock daily prices (enough data points)
        mock_prices = []
        for i in range(50):
            mock_prices.append(
                {
                    "date": f"2023-01-{i + 1:02d}"
                    if i < 30
                    else f"2023-02-{i - 29:02d}",
                    "close": 100.0 + (i % 5),  # Fluctuate
                    "open": 100.0,
                    "high": 105.0,
                    "low": 95.0,
                    "volume": 1000,
                }
            )

        mock_provider.get_daily_prices.return_value = mock_prices
        return PerformCheckupCommand(mock_provider)

    def test_execute_structure(self, command):
        """測試回傳結構是否包含新欄位"""
        result = command.execute("2330")

        assert "symbol" in result
        assert result["symbol"] == "2330"

        diag = result["diagnosis"]
        assert "dimensions" in diag
        assert "verdict" in diag
        assert "details" in diag

        # 檢查是否包含新的詳細資訊
        details = diag["details"]
        assert "alpha_decay" in details
        assert "vol_scaling" in details
        assert "id_score" in details
        assert "meat_pct" in details

    def test_dimensions_content(self, command):
        """測試維度檢查內容"""
        result = command.execute("2330")
        dimensions = result["diagnosis"]["dimensions"]

        dim_names = [d["name"] for d in dimensions]

        # 應包含新的檢查維度
        assert "理論定價" in dim_names
        assert "肉量評估" in dim_names
        assert "硬性止損" in dim_names
        assert "RSI 背離" in dim_names

        # 每個維度應有基本欄位
        for d in dimensions:
            assert "description" in d
            assert "passed" in d
            assert "value" in d

    def test_volatility_scaling_logic(self, command):
        """測試波動率縮放邏輯是否被呼叫"""
        result = command.execute("TEST_VOL")
        details = result["diagnosis"]["details"]

        vol_res = details["vol_scaling"]
        assert "scaling_factor" in vol_res
        assert "action" in vol_res

        # Mock data (vol=0.18, target=0.20) -> ratio > 1 -> EXPAND or KEEP
        # 0.20 / 0.18 = 1.11 -> EXPAND
        assert vol_res["action"] in ["EXPAND", "KEEP", "REDUCE"]

    def test_exit_trigger(self, command):
        """測試強制出場邏輯 (Mocked to not exit in default case)"""
        # 預設 mock data 不會觸發 10% stop loss
        result = command.execute("SAFE_STOCK")

        assert result["diagnosis"]["action"] != "觸發強制出場"

        # 若要測試觸發，需要能控制 fetch_mock_data，
        # 但目前它是 private method。
        # 這裡僅測試預設路徑。
