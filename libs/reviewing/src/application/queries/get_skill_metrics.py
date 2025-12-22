"""取得技能指標 Query"""

from injector import inject
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
from libs.reviewing.src.ports.get_skill_metrics_port import GetSkillMetricsPort
from libs.shared.src.dtos.reviewing.skill_metrics_result_dto import (
    SkillMetricsResultDTO,
)


class GetSkillMetricsQuery(GetSkillMetricsPort):
    """取得技能指標

    計算 DSR/PSR/PBO 等技能判定指標
    使用真實交易記錄 (journal.json)
    """

    @inject
    def __init__(self, portfolio_provider: PortfolioProviderPort) -> None:
        """初始化 Query

        Args:
            portfolio_provider: 投資組合提供者
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._portfolio_provider = portfolio_provider

    def execute(
        self, strategy: str = "residual_momentum", days: int = 252
    ) -> SkillMetricsResultDTO:
        """執行查詢

        Args:
            strategy: 策略名稱
            days: 回測天數

        Returns:
            SkillMetricsResultDTO: 技能指標
        """

        # 從真實數據獲取報酬序列
        returns, data_source = self._get_real_returns(days)

        # 計算指標
        mean_return = np.mean(returns) * 252
        std_return = np.std(returns) * np.sqrt(252)
        sharpe = mean_return / std_return if std_return > 0 else 0

        dsr = calculate_deflated_sharpe_ratio(sharpe, 10, len(returns))
        psr = calculate_probabilistic_sharpe_ratio(sharpe, 0, len(returns))
        skill_level, skill_action = interpret_dsr(dsr)

        # 計算額外技能指標
        win_rate = np.mean(returns > 0) if len(returns) > 0 else 0
        profit_factor = (
            np.sum(returns[returns > 0]) / abs(np.sum(returns[returns < 0]))
            if np.sum(returns[returns < 0]) != 0
            else 0
        )
        max_drawdown = self._calculate_max_drawdown(returns)

        return {
            "strategy": strategy,
            "days": len(returns),
            "data_source": data_source,
            "sharpe_ratio": round(sharpe, 3),
            "dsr": round(dsr, 3),
            "psr": round(psr, 3),
            "skill_level": skill_level,
            "skill_action": skill_action,
            "win_rate": round(win_rate, 3),
            "profit_factor": round(profit_factor, 2),
            "max_drawdown": round(max_drawdown, 3),
            "is_skill": dsr > 0.95,
            "confidence": self._calculate_confidence(dsr, psr),
        }

    def _get_real_returns(self, days: int) -> tuple[np.ndarray, str]:
        """從真實數據源獲取報酬序列"""
        # 1. 嘗試從 journal.json 計算報酬
        try:
            journal_path = "data/journal.json"
            if os.path.exists(journal_path):
                with open(journal_path, "r") as f:
                    trades = json.load(f)

                if trades and len(trades) > 0:
                    # 取最近的交易
                    recent_trades = trades[-days:] if len(trades) > days else trades

                    if len(recent_trades) >= 5:
                        # 計算每筆交易的報酬率
                        returns = [t.get("pnl_percent", 0) / 100 for t in recent_trades]
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
                    return np.array(pnl_pcts), "Shioaji"
        except Exception:
            self._logger.warning("Shioaji 連線失敗: {e}")

        # 3. 無真實數據時返回空陣列
        self._logger.warning("無法取得真實交易數據，技能指標無法計算")
        return np.zeros(1), "N/A (無交易記錄)"

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """計算最大回撤"""
        if len(returns) == 0:
            return 0.0
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = running_max - cumulative
        return float(np.max(drawdowns)) if len(drawdowns) > 0 else 0.0

    def _calculate_confidence(self, dsr: float, psr: float) -> str:
        """計算信心程度"""
        avg = (dsr + psr) / 2
        if avg > 0.9:
            return "高度自信"
        elif avg > 0.7:
            return "中度自信"
        elif avg > 0.5:
            return "低度自信"
        else:
            return "無法判定"
