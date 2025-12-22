"""CalculateKellyPositionQuery 單元測試

使用 Fake Adapter 模擬 Yahoo Finance，遵循 testing.md Classicist 學派規範
"""

import pytest
from libs.hunting.src.application.queries.calculate_kelly_position import (
    CalculateKellyPositionQuery,
)
from libs.hunting.src.adapters.driven.memory.alpha_hunter_market_data_fake_adapter import (
    AlphaHunterMarketDataFakeAdapter,
)


class TestCalculateKellyPositionQuery:
    """計算凱利部位 Query 測試"""

    @pytest.fixture
    def fake_market_data(self):
        """建立 Fake Market Data Adapter"""
        fake = AlphaHunterMarketDataFakeAdapter()
        # 設置測試用價格
        fake.set_current_price("^VIX", 18.5)  # 正常 VIX
        fake.set_current_price("2330.TW", 550.0)  # 台積電
        fake.set_current_price("AAPL", 180.0)  # Apple
        return fake

    @pytest.fixture
    def query(self, fake_market_data):
        """建立 Query 實例 (使用 Fake Adapter)"""
        return CalculateKellyPositionQuery(
            market_data_provider=fake_market_data,
        )

    def test_execute_returns_kelly_position(self, query):
        """測試正常執行返回凱利部位資訊"""
        result = query.execute(symbol="2330", capital=1000000)

        assert result["symbol"] == "2330"
        assert "kelly_pct" in result
        assert "position_size" in result
        assert "shares" in result
        assert "vix" in result
        assert "vix_tier" in result

    def test_kelly_position_respects_capital(self, query):
        """測試部位大小與資本成比例"""
        result1 = query.execute(symbol="2330", capital=1000000)
        result2 = query.execute(symbol="2330", capital=2000000)

        # 兩倍資本應該產生兩倍部位
        assert result2["position_size"] == result1["position_size"] * 2

    def test_shares_calculation(self, fake_market_data, query):
        """測試股數計算正確"""
        result = query.execute(symbol="2330", capital=1000000)

        # 股數 = 部位大小 / 股價
        expected_shares = int(result["position_size"] / 550.0)
        assert result["shares"] == expected_shares

    def test_high_vix_reduces_position(self):
        """測試高 VIX 應減少部位"""
        fake_low_vix = AlphaHunterMarketDataFakeAdapter()
        fake_low_vix.set_current_price("^VIX", 15.0)
        fake_low_vix.set_current_price("2330.TW", 550.0)
        query_low = CalculateKellyPositionQuery(market_data_provider=fake_low_vix)

        fake_high_vix = AlphaHunterMarketDataFakeAdapter()
        fake_high_vix.set_current_price("^VIX", 35.0)
        fake_high_vix.set_current_price("2330.TW", 550.0)
        query_high = CalculateKellyPositionQuery(market_data_provider=fake_high_vix)

        result_low = query_low.execute(symbol="2330", capital=1000000)
        result_high = query_high.execute(symbol="2330", capital=1000000)

        # 高 VIX 應該產生較小的部位
        assert result_high["kelly_pct"] <= result_low["kelly_pct"]

    def test_us_stock_symbol(self):
        """測試美股代碼處理"""
        fake = AlphaHunterMarketDataFakeAdapter()
        fake.set_current_price("^VIX", 18.5)
        fake.set_current_price("AAPL", 180.0)
        query = CalculateKellyPositionQuery(market_data_provider=fake)

        result = query.execute(symbol="AAPL", capital=100000)

        assert result["symbol"] == "AAPL"
        assert result["shares"] > 0
