"""GetWeeklyReviewQuery 測試"""

from libs.reviewing.src.application.queries.get_weekly_review import (
    GetWeeklyReviewQuery,
)
from libs.reviewing.src.domain.services.skill_metrics_calculator import (
    SkillMetricsCalculator,
)
from libs.reviewing.src.adapters.driven.memory.performance_fake_adapter import (
    PerformanceFakeAdapter,
)
from libs.reviewing.src.adapters.driven.memory.trading_journal_fake_adapter import (
    TradingJournalFakeAdapter,
)
from libs.monitoring.src.adapters.driven.memory.macro_data_fake_adapter import (
    MacroDataFakeAdapter,
)


class TestGetWeeklyReview:
    """GetWeeklyReviewQuery 測試"""

    def setup_method(self) -> None:
        """設置測試環境"""
        self.performance = PerformanceFakeAdapter()
        self.journal = TradingJournalFakeAdapter()
        self.macro = MacroDataFakeAdapter()
        self.skill_calc = SkillMetricsCalculator()
        self.query = GetWeeklyReviewQuery(
            performance=self.performance,
            journal=self.journal,
            macro=self.macro,
            skill_calculator=self.skill_calc,
        )

    def test_skill_dominated_when_high_sharpe(self) -> None:
        """高 Sharpe Ratio 應判定為技能主導"""
        self.performance.set_sharpe_ratio(2.5)
        self.performance.set_num_trials(100)
        self.performance.set_benchmark_sharpe(0.5)
        self.journal.set_closed_trades([])
        self.macro.set_m2_yoy(5.0)
        self.macro.set_fed_balance_sheet_trend("EXPANDING")

        result = self.query.execute()

        assert result["skill_judgment"] == "Skill Dominated"
        assert result["recommendation"] == "增加配置"

    def test_luck_dominated_when_low_sharpe(self) -> None:
        """低 Sharpe Ratio 應判定為運氣主導"""
        self.performance.set_sharpe_ratio(0.3)
        self.performance.set_num_trials(50)
        self.performance.set_benchmark_sharpe(0.5)
        self.journal.set_closed_trades([])
        self.macro.set_m2_yoy(-2.0)
        self.macro.set_fed_balance_sheet_trend("CONTRACTING")

        result = self.query.execute()

        assert result["skill_judgment"] == "Luck Dominated"
        assert result["recommendation"] == "考慮停用"

    def test_recovery_phase_when_expanding_positive_m2(self) -> None:
        """擴張 Fed + 正 M2 應為 RECOVERY"""
        self.performance.set_sharpe_ratio(1.0)
        self.performance.set_num_trials(50)
        self.performance.set_benchmark_sharpe(0.5)
        self.journal.set_closed_trades([])
        self.macro.set_m2_yoy(5.0)
        self.macro.set_fed_balance_sheet_trend("EXPANDING")

        result = self.query.execute()

        assert result["merril_phase"] == "RECOVERY"
        assert result["recommended_asset"] == "股票"
