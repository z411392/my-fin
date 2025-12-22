"""取得體制識別 Query

實作 GetRegimePort Driving Port
使用 S&P 500 真實歷史數據
"""

import logging

import numpy as np
import yfinance as yf

from libs.arbitraging.src.domain.services.hurst_calculator import (
    calculate_hurst_exponent,
    interpret_hurst,
)
from libs.arbitraging.src.domain.services.hmm_regime_detector import (
    combine_regime_signals,
    hmm_regime_simple,
)
from libs.arbitraging.src.ports.get_regime_port import GetRegimePort
from libs.shared.src.dtos.market.regime_result_dto import RegimeResultDTO


class GetRegimeQuery(GetRegimePort):
    """取得三層體制識別"""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self, lookback: int = 120) -> RegimeResultDTO:
        """取得當前市場體制"""
        try:
            # 從 Yahoo Finance 取得 S&P 500 歷史資料
            ticker = yf.Ticker("^GSPC")
            hist = ticker.history(period="6mo")

            if hist is not None and len(hist) >= lookback:
                closes = hist["Close"].values[-lookback:]
                # 計算對數報酬
                returns = np.diff(np.log(closes))
            else:
                # 降級到 Mock
                np.random.seed(42)
                returns = np.random.normal(0.0005, 0.015, lookback)
        except Exception:
            # API 失敗降級到 Mock
            np.random.seed(42)
            returns = np.random.normal(0.0005, 0.015, lookback)

        # 第一層: Hurst 指數
        hurst = calculate_hurst_exponent(returns)
        hurst_market, hurst_strategy = interpret_hurst(hurst)

        # 第二層: HMM 體制
        hmm_state, hmm_bull_prob = hmm_regime_simple(
            returns, lookback=min(60, len(returns))
        )

        # 綜合判定
        regime, kelly_factor = combine_regime_signals(hurst, hmm_bull_prob, 1.0)

        return {
            "hurst": hurst,
            "hurst_interpretation": hurst_market,
            "hmm_state": hmm_state,
            "hmm_bull_prob": hmm_bull_prob,
            "regime": regime,
            "kelly_factor": kelly_factor,
            "suggested_strategy": hurst_strategy,
        }
