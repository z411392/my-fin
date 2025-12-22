"""績效數據 Yahoo Adapter - 實作 PerformanceProviderPort"""

import json
import os
from pathlib import Path

from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.reviewing.src.ports.performance_data_provider_port import (
    PerformanceDataProviderPort,
)
from libs.reviewing.src.ports.performance_provider_port import PerformanceProviderPort
from libs.shared.src.dtos.reviewing.performance_metrics_dto import (
    PerformanceMetricsDTO,
    PortfolioConfigDTO,
)


class PerformanceYahooAdapter(PerformanceProviderPort):
    """績效數據 Yahoo Adapter

    實作 PerformanceProviderPort 介面
    從 positions.json 讀取持倉，計算投資組合績效
    """

    def __init__(
        self,
        performance_data_provider: PerformanceDataProviderPort,
        portfolio_provider: PortfolioProviderPort | None = None,
        positions_file: str | None = None,
    ) -> None:
        self._adapter = performance_data_provider
        self._portfolio_provider = portfolio_provider
        self._positions_file = positions_file or self._default_positions_path()
        self._config = self._load_positions()
        self._cache: dict = {}

    def _default_positions_path(self) -> str:
        """取得預設持倉檔案路徑"""
        return str(Path(__file__).parents[6] / "data" / "positions.json")

    def _load_positions(self) -> PortfolioConfigDTO:
        """載入持倉設定

        優先順序：
        1. 嘗試從 Shioaji API 取得真實持倉
        2. Fallback: 從 positions.json 讀取
        """
        # 嘗試從 Shioaji 取得真實持倉
        if self._portfolio_provider is not None:
            try:
                if self._portfolio_provider.connect():
                    positions = self._portfolio_provider.get_positions()
                    self._portfolio_provider.disconnect()
                    if positions:
                        # 轉換為標準格式
                        normalized = []
                        for pos in positions:
                            normalized.append(
                                {
                                    "symbol": pos.get("symbol", ""),
                                    "weight": 1.0 / len(positions),  # 平均權重
                                    "shares": pos.get("quantity", 0),
                                }
                            )
                        return {
                            "positions": normalized,
                            "benchmark": "SPY",
                            "risk_free_rate": 0.05,
                        }
            except Exception:
                pass  # Fallback to JSON

        # Fallback: 從 positions.json 讀取
        if not os.path.exists(self._positions_file):
            return {
                "positions": [],
                "benchmark": "SPY",
                "risk_free_rate": 0.05,
            }
        with open(self._positions_file) as f:
            return json.load(f)

    def _get_performance_metrics(self) -> PerformanceMetricsDTO:
        """計算並快取績效指標"""
        if self._cache:
            return self._cache

        positions = self._config.get("positions", [])
        if not positions:
            self._cache = {
                "sharpe": 0.0,
                "num_trials": 0,
                "benchmark_sharpe": 0.0,
            }
            return self._cache

        # 計算投資組合績效
        summary = self._adapter.get_performance_summary(positions, days=252)

        if "error" in summary:
            self._cache = {
                "sharpe": 0.0,
                "num_trials": 0,
                "benchmark_sharpe": 0.0,
            }
            return self._cache

        # 計算基準績效
        benchmark = self._config.get("benchmark", "SPY")
        benchmark_summary = self._adapter.get_performance_summary(
            [{"symbol": benchmark, "weight": 1.0}], days=252
        )
        benchmark_sharpe = (
            benchmark_summary.get("sharpe", 0.5)
            if "error" not in benchmark_summary
            else 0.5
        )

        self._cache = {
            "sharpe": summary.get("sharpe", 0.0),
            "num_trials": summary.get("days", 252),
            "benchmark_sharpe": benchmark_sharpe,
        }
        return self._cache

    def get_sharpe_ratio(self) -> float:
        """取得夏普比率"""
        return self._get_performance_metrics()["sharpe"]

    def get_num_trials(self) -> int:
        """取得測試次數 (交易天數)"""
        return self._get_performance_metrics()["num_trials"]

    def get_benchmark_sharpe(self) -> float:
        """取得基準夏普比率"""
        return self._get_performance_metrics()["benchmark_sharpe"]
