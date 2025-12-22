"""生成週度覆盤 Command"""

from injector import inject
from datetime import date
import json
import os

import numpy as np


import logging
from libs.reviewing.src.domain.services.dsr_calculator import (
    calculate_deflated_sharpe_ratio,
    calculate_probabilistic_sharpe_ratio,
    interpret_dsr,
)
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.reviewing.src.ports.generate_weekly_review_port import (
    GenerateWeeklyReviewPort,
)
from libs.shared.src.dtos.reviewing.scan_result_dto import WeeklyReviewResultDTO
from libs.shared.src.dtos.reviewing.decision_quality_assessment_dto import (
    DecisionQualityAssessmentDTO,
)


class GenerateWeeklyReviewCommand(GenerateWeeklyReviewPort):
    """生成週度覆盤

    整合技能指標、決策品質、資產配置建議
    使用真實交易記錄 (journal.json) 與持倉數據 (Shioaji)
    """

    @inject
    def __init__(self, portfolio_provider: PortfolioProviderPort | None = None) -> None:
        """初始化 Command

        Args:
            portfolio_provider: 投資組合提供者 (由 DI 注入)
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._portfolio_provider = portfolio_provider

    def execute(
        self, week: int | None = None, year: int | None = None
    ) -> WeeklyReviewResultDTO:
        """生成週度覆盤

        Args:
            week: 週數 (預設當週)
            year: 年份 (預設今年)

        Returns:
            WeeklyReviewResultDTO: 週度覆盤結果
        """

        today = date.today()
        week = week or today.isocalendar()[1]
        year = year or today.year

        # 嘗試從真實數據獲取績效
        returns, data_source = self._get_real_returns(week, year)

        mean_return = np.mean(returns) * 252
        std_return = np.std(returns) * np.sqrt(252)
        sharpe = mean_return / std_return if std_return > 0 else 0

        dsr = calculate_deflated_sharpe_ratio(sharpe, 10, len(returns))
        psr = calculate_probabilistic_sharpe_ratio(sharpe, 0, len(returns))
        skill_level, skill_action = interpret_dsr(dsr)

        return {
            "week": week,
            "year": year,
            "data_source": data_source,
            "performance": {
                "sharpe_ratio": round(sharpe, 2),
                "weekly_return": round(np.sum(returns[-5:]) * 100, 2)
                if len(returns) >= 5
                else 0,
                "ytd_return": round(np.sum(returns) * 100, 2),
            },
            "skill_assessment": {
                "dsr": round(dsr, 3),
                "psr": round(psr, 3),
                "level": skill_level,
                "recommendation": skill_action,
            },
            "decision_quality": self._assess_decision_quality(week, year),
            "next_week_plan": self._generate_next_week_plan(skill_level),
        }

    def _get_real_returns(self, week: int, year: int) -> tuple[np.ndarray, str]:
        """從真實數據源獲取報酬序列"""
        # 1. 嘗試從 journal.json 計算報酬
        try:
            journal_path = "data/journal.json"
            if os.path.exists(journal_path):
                with open(journal_path, "r") as f:
                    trades = json.load(f)

                if trades and len(trades) > 0:
                    # 篩選指定週的交易
                    week_trades = [
                        t
                        for t in trades
                        if date.fromisoformat(
                            t.get("date", "1970-01-01")
                        ).isocalendar()[1]
                        == week
                        and date.fromisoformat(t.get("date", "1970-01-01")).year == year
                    ]

                    if len(week_trades) >= 3:
                        # 計算每筆交易的報酬率
                        returns = [t.get("pnl_percent", 0) / 100 for t in week_trades]
                        return np.array(returns), "Journal"
        except Exception:
            self._logger.warning("讀取 journal.json 失敗: {e}")

        # 2. 嘗試從注入的 portfolio_provider 取得持倉損益
        try:
            if self._portfolio_provider and os.environ.get("SHIOAJI_API_KEY"):
                positions = self._portfolio_provider.get_positions()

                if positions and len(positions) > 0:
                    # 從持倉的損益推算報酬
                    pnl_pcts = [p.get("pnl_percent", 0) / 100 for p in positions]
                    # 假設持倉天數為 5 天 (一週)
                    daily_returns = [pnl / 5 for pnl in pnl_pcts for _ in range(5)]
                    return np.array(daily_returns), "Shioaji"
        except Exception:
            self._logger.warning("Shioaji 連線失敗: {e}")

        # 3. 無真實數據時返回空陣列並標記
        self._logger.warning("無法取得真實交易數據，使用空報酬序列")
        return np.zeros(5), "N/A (無交易記錄)"

    def _assess_decision_quality(
        self, week: int, year: int
    ) -> DecisionQualityAssessmentDTO:
        """評估決策品質 - 從 journal.json 讀取"""
        try:
            journal_path = "data/journal.json"
            if os.path.exists(journal_path):
                with open(journal_path, "r") as f:
                    trades = json.load(f)

                # 篩選指定週的交易
                week_trades = [
                    t
                    for t in trades
                    if date.fromisoformat(t.get("date", "1970-01-01")).isocalendar()[1]
                    == week
                    and date.fromisoformat(t.get("date", "1970-01-01")).year == year
                ]

                if len(week_trades) > 0:
                    # 分析交易品質
                    good_profit = sum(
                        1 for t in week_trades if t.get("pnl_percent", 0) > 5
                    )
                    bad_profit = sum(
                        1 for t in week_trades if 0 < t.get("pnl_percent", 0) <= 5
                    )
                    good_loss = sum(
                        1 for t in week_trades if -5 <= t.get("pnl_percent", 0) < 0
                    )
                    bad_loss = sum(
                        1 for t in week_trades if t.get("pnl_percent", 0) < -5
                    )

                    good_decisions = good_profit + good_loss
                    total = len(week_trades)

                    return {
                        "total_trades": total,
                        "good_profit": good_profit,
                        "bad_profit": bad_profit,
                        "good_loss": good_loss,
                        "bad_loss": bad_loss,
                        "good_decision_rate": round(good_decisions / total, 2)
                        if total > 0
                        else 0,
                        "data_source": "Journal",
                    }
        except Exception:
            self._logger.warning("決策品質分析失敗: {e}")

        return {
            "total_trades": 0,
            "good_profit": 0,
            "bad_profit": 0,
            "good_loss": 0,
            "bad_loss": 0,
            "good_decision_rate": 0,
            "data_source": "N/A",
        }

    def _generate_next_week_plan(self, skill_level: str) -> list[str]:
        """生成下週計劃"""
        plans = ["維持現有策略配置"]

        if skill_level == "技能主導":
            plans.append("考慮增加策略配置")
        elif skill_level == "運氣主導":
            plans.append("減少策略配置，檢視假設")

        plans.append("持續記錄交易日誌")
        return plans
