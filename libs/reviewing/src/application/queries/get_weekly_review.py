"""取得週度覆盤 Query (Read Model: WeeklyReviewDTO)"""

import logging

from injector import inject
from libs.reviewing.src.domain.services.skill_metrics_calculator import (
    SkillMetricsCalculator,
)
from libs.reviewing.src.ports.performance_provider_port import (
    PerformanceProviderPort,
)
from libs.reviewing.src.ports.trading_journal_repository_port import (
    TradingJournalRepositoryPort,
)
from libs.reviewing.src.ports.macro_data_provider_port import (
    MacroDataProviderPort,
)
from libs.shared.src.dtos.portfolio.trade_dto import TradeDTO
from libs.shared.src.dtos.weekly_review_dto import WeeklyReviewDTO
from libs.shared.src.dtos.reviewing.decision_quality_stats_dto import (
    DecisionQualityStatsDTO,
)
from libs.shared.src.enums.merril_clock_phase import MerrilClockPhase
from libs.shared.src.enums.skill_level import SkillLevel
from libs.reviewing.src.ports.get_weekly_review_port import GetWeeklyReviewPort


class GetWeeklyReviewQuery(GetWeeklyReviewPort):
    """
    取得週度覆盤視圖

    整合:
    - 技能指標 (DSR/PSR)
    - 決策品質審計
    - 美林時鐘定位
    - Red Queen 檢測
    """

    @inject
    def __init__(
        self,
        performance: PerformanceProviderPort,
        journal: TradingJournalRepositoryPort,
        macro: MacroDataProviderPort,
        skill_calculator: SkillMetricsCalculator,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._performance = performance
        self._journal = journal
        self._macro = macro
        self._skill = skill_calculator

    def execute(self) -> WeeklyReviewDTO:
        """
        取得週度覆盤

        Returns:
            WeeklyReviewDTO: 週度覆盤視圖
        """
        # 從 Driven Port 取得資料
        sharpe = self._performance.get_sharpe_ratio()
        num_trials = self._performance.get_num_trials()
        benchmark_sharpe = self._performance.get_benchmark_sharpe()
        trades = self._journal.get_closed_trades("weekly")
        m2_yoy = self._macro.get_m2_yoy()
        fed_trend = self._macro.get_fed_balance_sheet_trend()

        # 用 Domain Service 計算技能指標
        dsr = self._skill.calculate_dsr(sharpe, num_trials)
        psr = self._skill.calculate_psr(sharpe, benchmark_sharpe, num_trials)
        skill_level = self._skill.classify_skill(dsr)

        # 計算決策品質
        decision_stats = self._calculate_decision_quality(trades)

        # 判定美林時鐘
        merril_phase = self._determine_merril_clock(m2_yoy, fed_trend)

        return WeeklyReviewDTO(
            date="",  # 由呼叫端填入
            dsr=dsr,
            psr=psr,
            skill_judgment=skill_level.value,
            good_decision_rate=decision_stats["good_rate"],
            merril_phase=merril_phase.value,
            recommended_asset=self._get_recommended_asset(merril_phase),
            recommendation=self._get_recommendation(skill_level),
        )

    def _calculate_decision_quality(
        self, trades: list[TradeDTO]
    ) -> DecisionQualityStatsDTO:
        """計算決策品質統計"""
        if not trades:
            return {"good_rate": 0.0}

        good_count = 0
        for trade in trades:
            pnl = trade.get("pnl", 0)
            followed = trade.get("followed_rules", True)
            if (followed and pnl > 0) or (followed and pnl <= 0):
                good_count += 1

        return {"good_rate": good_count / len(trades) * 100}

    def _determine_merril_clock(
        self, m2_yoy: float, fed_trend: str
    ) -> MerrilClockPhase:
        """判定美林時鐘"""
        is_accelerating = m2_yoy > 0
        is_inflation_rising = fed_trend == "CONTRACTING"

        if is_accelerating and not is_inflation_rising:
            return MerrilClockPhase.RECOVERY
        elif is_accelerating and is_inflation_rising:
            return MerrilClockPhase.OVERHEAT
        elif not is_accelerating and is_inflation_rising:
            return MerrilClockPhase.STAGFLATION
        else:
            return MerrilClockPhase.RECESSION

    def _get_recommended_asset(self, phase: MerrilClockPhase) -> str:
        """取得推薦資產"""
        assets = {
            MerrilClockPhase.RECOVERY: "股票",
            MerrilClockPhase.OVERHEAT: "商品",
            MerrilClockPhase.STAGFLATION: "現金",
            MerrilClockPhase.RECESSION: "債券",
        }
        return assets.get(phase, "現金")

    def _get_recommendation(self, skill_level) -> str:
        """取得策略建議"""

        recommendations = {
            SkillLevel.SKILL_DOMINATED: "增加配置",
            SkillLevel.POSSIBLE_SKILL: "維持配置",
            SkillLevel.INDETERMINATE: "減少配置",
            SkillLevel.LUCK_DOMINATED: "考慮停用",
        }
        return recommendations.get(skill_level, "維持配置")
