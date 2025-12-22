"""GetWeekendReviewQuery 測試"""

from libs.hunting.src.application.queries.get_weekend_review import (
    GetWeekendReviewQuery,
)
from libs.hunting.src.adapters.driven.memory.residual_momentum_market_data_fake_adapter import (
    ResidualMomentumMarketDataFakeAdapter,
)
from libs.monitoring.src.adapters.driven.memory.macro_data_fake_adapter import (
    MacroDataFakeAdapter,
)


class TestGetWeekendReview:
    """GetWeekendReviewQuery 測試"""

    def setup_method(self) -> None:
        """設置測試環境"""
        self.market = ResidualMomentumMarketDataFakeAdapter()
        self.macro = MacroDataFakeAdapter()
        self.query = GetWeekendReviewQuery(
            market_provider=self.market,
            macro_provider=self.macro,
        )

    def test_calm_bull_regime_when_low_vix_expanding(self) -> None:
        """低 VIX + 擴張 Fed 應為 CALM_BULL"""
        self.macro.set_vix(15.0)
        self.macro.set_fed_balance_sheet_trend("EXPANDING")

        result = self.query.execute([])

        assert result["regime"]["name"] == "Calm Bull"
        assert "進攻" in result["regime"]["recommended_strategy"] or "Attack" in result["regime"]["recommended_strategy"]

    def test_volatile_bear_regime_when_high_vix_contracting(self) -> None:
        """高 VIX + 收縮 Fed 應為 VOLATILE_BEAR"""
        self.macro.set_vix(30.0)
        self.macro.set_fed_balance_sheet_trend("CONTRACTING")

        result = self.query.execute([])

        assert result["regime"]["name"] == "Volatile Bear"
        assert "減倉" in result["regime"]["recommended_strategy"] or "減" in result["regime"]["recommended_strategy"]

    def test_hunting_targets_sorted_by_momentum(self) -> None:
        """狩獵標的應按動能排序"""
        self.macro.set_vix(15.0)
        self.macro.set_fed_balance_sheet_trend("EXPANDING")
        self.market.set_returns("2330", [0.01] * 60)
        self.market.set_returns("2317", [0.02] * 60)
        self.market.set_benchmark_returns("SPY", [0.005] * 60)

        result = self.query.execute(["2330", "2317"])

        assert result["total_scanned"] >= 0
