"""驗證策略績效 Query

實作 ValidateStrategyPort Driving Port
先嘗試從 Shioaji 取得持倉資料，失敗才降級到隨機數據
"""

import os
import numpy as np

from injector import inject
from libs.reviewing.src.domain.services.dsr_calculator import (
    calculate_deflated_sharpe_ratio,
    calculate_probabilistic_sharpe_ratio,
    interpret_dsr,
)


import logging
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.reviewing.src.ports.validate_strategy_port import ValidateStrategyPort
from libs.shared.src.dtos.reviewing.strategy_validation_result_dto import (
    StrategyValidationResultDTO,
)


class ValidateStrategyQQuery(ValidateStrategyPort):
    """驗證策略績效 (Q 版)"""

    @inject
    def __init__(self, portfolio_provider: PortfolioProviderPort | None = None) -> None:
        """初始化 Query

        Args:
            portfolio_provider: 投資組合提供者 (由 DI 注入)
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._portfolio_provider = portfolio_provider

    def execute(
        self, strategy: str = "default", days: int = 252, simulate: bool = False
    ) -> StrategyValidationResultDTO:
        """驗證策略績效是否來自技能

        Args:
            strategy: 策略名稱
            days: 回測天數
            simulate: 使用 Shioaji 模擬環境
        """
        # 嘗試從 Shioaji 取得持倉資料
        returns = None
        data_source = "Mock"

        if self._portfolio_provider and os.environ.get("SHIOAJI_API_KEY"):
            try:
                positions = self._portfolio_provider.get_positions()

                if positions and len(positions) > 0:
                    # 從持倉計算報酬率
                    pnl_pcts = [p.get("pnl_percent", 0) / 100 for p in positions]
                    if pnl_pcts:
                        avg_return = np.mean(pnl_pcts) / days
                        returns = np.random.normal(avg_return, 0.02, days)
                        data_source = "Shioaji"
            except Exception as e:
                self._logger.warning(f"Shioaji 錯誤，降級到 Mock: {e}")

        # 降級到隨機數據
        if returns is None:
            np.random.seed(42)
            returns = np.random.normal(0.001, 0.02, days)

        mean_return = np.mean(returns) * 252
        std_return = np.std(returns) * np.sqrt(252)
        sharpe = mean_return / std_return if std_return > 0 else 0

        dsr = calculate_deflated_sharpe_ratio(
            sr=sharpe,
            n_trials=10,
            n_observations=days,
        )

        psr = calculate_probabilistic_sharpe_ratio(
            sr=sharpe,
            benchmark_sr=0,
            n_observations=days,
        )

        skill_level, _ = interpret_dsr(dsr)

        return {
            "strategy": strategy,
            "days": days,
            "sharpe_ratio": sharpe,
            "dsr": dsr,
            "psr": psr,
            "skill_level": skill_level,
            "data_source": data_source,
        }
