"""計算每日 Beta Command"""

import logging

from injector import inject

import numpy as np
import yfinance as yf

from libs.linking.src.domain.services.kalman_beta_estimator import kalman_beta_simple
from libs.linking.src.ports.calculate_daily_beta_port import CalculateDailyBetaPort
from libs.shared.src.dtos.market.supply_chain_command_result_dto import (
    DailyBetaResultDTO,
)


class CalculateDailyBetaCommand(CalculateDailyBetaPort):
    """計算每日動態 Beta

    每日盤後執行，更新 Kalman Filter Beta 估計
    使用 Yahoo Finance 真實市場數據
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(
        self, us_symbol: str, tw_symbol: str, lookback: int = 60
    ) -> DailyBetaResultDTO:
        """執行計算每日 Beta

        Args:
            us_symbol: 美股代號
            tw_symbol: 台股代號
            lookback: 回看天數

        Returns:
            DailyBetaResultDTO: Beta 計算結果
        """
        # 從 Yahoo Finance 取得真實數據
        us_returns, tw_returns, data_source = self._get_real_returns(
            us_symbol, tw_symbol, lookback
        )

        # Kalman Filter Beta
        betas = kalman_beta_simple(us_returns, tw_returns)
        current_beta = betas[-1] if len(betas) > 0 else 0.0

        # 計算預期移動
        last_us_return = us_returns[-1] if len(us_returns) > 0 else 0
        expected_tw_move = current_beta * last_us_return

        return {
            "us_symbol": us_symbol,
            "tw_symbol": tw_symbol,
            "current_beta": round(float(current_beta), 3),
            "expected_tw_move": round(float(expected_tw_move) * 100, 2),
            "lookback_days": lookback,
            "beta_history": [round(float(b), 3) for b in betas[-5:]],
            "data_source": data_source,
        }

    def _get_real_returns(
        self, us_symbol: str, tw_symbol: str, lookback: int
    ) -> tuple[np.ndarray, np.ndarray, str]:
        """從 Yahoo Finance 取得真實股票報酬"""
        try:
            # 美股報酬
            us_ticker = yf.Ticker(us_symbol)
            us_hist = us_ticker.history(period="6mo")

            if us_hist is None or len(us_hist) < lookback:
                raise ValueError(f"美股 {us_symbol} 數據不足")

            us_closes = us_hist["Close"].values[-lookback:]
            us_returns = np.diff(np.log(us_closes))

            # 台股報酬 (需加 .TW 後綴)
            tw_yahoo_symbol = (
                tw_symbol if tw_symbol.endswith(".TW") else f"{tw_symbol}.TW"
            )
            tw_ticker = yf.Ticker(tw_yahoo_symbol)
            tw_hist = tw_ticker.history(period="6mo")

            if tw_hist is None or len(tw_hist) < lookback:
                raise ValueError(f"台股 {tw_symbol} 數據不足")

            tw_closes = tw_hist["Close"].values[-lookback:]
            tw_returns = np.diff(np.log(tw_closes))

            # 對齊長度
            min_len = min(len(us_returns), len(tw_returns))
            us_returns = us_returns[-min_len:]
            tw_returns = tw_returns[-min_len:]

            return (
                us_returns,
                tw_returns,
                f"Yahoo Finance ({us_symbol}, {tw_yahoo_symbol})",
            )

        except Exception:
            self._logger.warning("Yahoo Finance API 失敗: {e}")
            # Fallback: 返回空陣列並標記
            return np.zeros(lookback - 1), np.zeros(lookback - 1), "N/A (API 失敗)"
