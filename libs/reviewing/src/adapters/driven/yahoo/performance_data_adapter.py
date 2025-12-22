"""績效資料 Yahoo Adapter"""

from datetime import date, timedelta
import yfinance as yf
import numpy as np

from libs.shared.src.dtos.portfolio.position_dto import PositionDTO
from libs.reviewing.src.domain.services.dsr_calculator import (
    calculate_deflated_sharpe_ratio,
    calculate_probabilistic_sharpe_ratio,
    interpret_dsr,
)
from libs.hunting.src.domain.services.symbol_converter import to_yahoo_symbol
from libs.reviewing.src.ports.performance_data_provider_port import (
    PerformanceDataProviderPort,
)
from libs.shared.src.dtos.reviewing.dsr_result_dto import (
    DSRResultDTO,
    PerformanceSummaryDTO,
)


class PerformanceDataAdapter(PerformanceDataProviderPort):
    """績效數據 Adapter (直接使用 yfinance)"""

    def get_portfolio_performance(
        self, positions: list[PositionDTO], days: int = 252
    ) -> list[float]:
        """計算投資組合日報酬率"""
        if not positions:
            return []

        end_date = date.today()
        start_date = end_date - timedelta(days=days + 30)

        symbol_returns: dict[str, list[float]] = {}
        min_len = float("inf")

        for pos in positions:
            symbol = pos["symbol"]
            yahoo_symbol = to_yahoo_symbol(symbol)  # 轉換為 Yahoo 格式
            try:
                ticker = yf.Ticker(yahoo_symbol)
                df = ticker.history(start=start_date, end=end_date)

                if df.empty or len(df) < 2:
                    continue

                closes = df["Close"].values
                returns = []
                for i in range(1, len(closes)):
                    if closes[i - 1] > 0:
                        returns.append((closes[i] - closes[i - 1]) / closes[i - 1])

                symbol_returns[symbol] = (
                    returns[-days:] if len(returns) > days else returns
                )
                min_len = min(min_len, len(symbol_returns[symbol]))

            except Exception:
                continue

        if not symbol_returns or min_len < 1:
            return []

        portfolio_returns = []
        for i in range(int(min_len)):
            daily_return = 0.0
            total_weight = 0.0
            for pos in positions:
                symbol = pos["symbol"]
                weight = pos.get("weight", 0)
                if symbol in symbol_returns and i < len(symbol_returns[symbol]):
                    daily_return += symbol_returns[symbol][i] * weight
                    total_weight += weight

            if total_weight > 0:
                portfolio_returns.append(daily_return)

        return portfolio_returns

    def calculate_sharpe_ratio(
        self,
        returns: list[float],
        risk_free_rate: float = 0.05,
    ) -> float:
        """計算夏普比率"""
        if len(returns) < 30:
            return 0.0

        returns_arr = np.array(returns)
        mean_return = np.mean(returns_arr) * 252
        std_return = np.std(returns_arr) * np.sqrt(252)

        if std_return == 0:
            return 0.0

        return (mean_return - risk_free_rate) / std_return

    def calculate_dsr(
        self,
        returns: list[float],
        risk_free_rate: float = 0.05,
    ) -> DSRResultDTO:
        """計算 Deflated Sharpe Ratio"""
        sharpe = self.calculate_sharpe_ratio(returns, risk_free_rate)
        n_observations = len(returns)

        dsr = calculate_deflated_sharpe_ratio(
            sr=sharpe,
            n_trials=10,
            n_observations=n_observations,
        )

        psr = calculate_probabilistic_sharpe_ratio(
            sr=sharpe,
            benchmark_sr=0,
            n_observations=n_observations,
        )

        interpretation = interpret_dsr(dsr)

        return {
            "sharpe": round(sharpe, 2),
            "dsr": round(dsr, 2),
            "psr": round(psr, 2),
            "interpretation": interpretation,
        }

    def calculate_max_drawdown(self, returns: list[float]) -> float:
        """計算最大回撤"""
        if len(returns) < 2:
            return 0.0

        cumulative = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (cumulative - running_max) / running_max
        return float(np.min(drawdowns))

    def get_performance_summary(
        self, positions: list[PositionDTO], days: int = 252
    ) -> PerformanceSummaryDTO:
        """取得完整績效摘要"""
        returns = self.get_portfolio_returns(positions, days)

        if len(returns) < 30:
            return {
                "error": "資料不足",
                "days": days,
                "data_points": len(returns),
            }

        returns_arr = np.array(returns)
        dsr_result = self.calculate_dsr(returns)

        return {
            "days": days,
            "total_return": float((np.prod(1 + returns_arr) - 1) * 100),
            "annualized_return": float(np.mean(returns_arr) * 252 * 100),
            "volatility": float(np.std(returns_arr) * np.sqrt(252) * 100),
            "sharpe": dsr_result["sharpe"],
            "dsr": dsr_result["dsr"],
            "psr": dsr_result["psr"],
            "interpretation": dsr_result["interpretation"],
            "max_drawdown": float(self.calculate_max_drawdown(returns) * 100),
            "win_rate": float(np.mean(returns_arr > 0) * 100),
        }
