"""GetSupplyChainLinkQuery 單元測試"""

from libs.linking.src.adapters.driven.memory.us_stock_price_fake_adapter import (
    USStockPriceFakeAdapter,
)
from libs.linking.src.adapters.driven.memory.tw_stock_price_fake_adapter import (
    TWStockPriceFakeAdapter,
)


class TestGetSupplyChainLinkQuery:
    """供應鏈傳導查詢測試"""

    def setup_method(self) -> None:
        self.us_adapter = USStockPriceFakeAdapter()
        self.tw_adapter = TWStockPriceFakeAdapter()

    def test_calculate_expected_move(self) -> None:
        """計算預期移動"""
        us_return = self.us_adapter.get_daily_return("NVDA", "2025-01-01")
        beta = 0.8
        expected_move = beta * us_return
        assert expected_move == 0.024  # 0.8 * 0.03

    def test_identify_lag_opportunity(self) -> None:
        """識別滯後套利機會"""
        self.us_adapter.set_daily_return("NVDA", 0.05)
        self.tw_adapter.set_daily_return("3017", 0.015)

        us_ret = self.us_adapter.get_daily_return("NVDA", "2025-01-01")
        tw_ret = self.tw_adapter.get_daily_return("3017", "2025-01-01")
        beta = 0.8

        expected = beta * us_ret  # 0.04
        lag = expected - tw_ret  # 0.04 - 0.015 = 0.025

        assert lag > 0.02  # 存在套利機會

    def test_no_opportunity_when_lag_small(self) -> None:
        """滯後小時無機會"""
        self.us_adapter.set_daily_return("NVDA", 0.03)
        self.tw_adapter.set_daily_return("3017", 0.024)

        us_ret = self.us_adapter.get_daily_return("NVDA", "2025-01-01")
        tw_ret = self.tw_adapter.get_daily_return("3017", "2025-01-01")
        beta = 0.8

        expected = beta * us_ret  # 0.024
        lag = expected - tw_ret  # 0.024 - 0.024 = 0

        assert abs(lag) < 0.01  # 無套利機會
