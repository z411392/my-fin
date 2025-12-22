"""偵測體制變化 Command"""

import logging

import numpy as np
import yfinance as yf

from libs.arbitraging.src.domain.services.hurst_calculator import (
    calculate_hurst_exponent,
    interpret_hurst,
)
from libs.arbitraging.src.domain.services.hmm_regime_detector import (
    hmm_regime_simple,
    interpret_hmm_regime,
)
from libs.arbitraging.src.domain.services.pca_drift_detector import (
    calculate_pca_cosine_similarity,
    detect_structural_break,
)
from libs.arbitraging.src.ports.detect_regime_change_port import (
    DetectRegimeChangePort,
)
from libs.shared.src.dtos.event.event_command_result_dto import RegimeChangeResultDTO


class DetectRegimeChangeCommand(DetectRegimeChangePort):
    """偵測體制變化

    每週執行，使用三層融合判定
    使用 Yahoo Finance 真實市場數據
    """

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self, lookback: int = 120) -> RegimeChangeResultDTO:
        """執行體制變化偵測

        Args:
            lookback: 回看天數

        Returns:
            RegimeChangeResultDTO: 體制判定結果
        """
        # 從 Yahoo Finance 取得真實數據
        returns, data_source = self._get_real_returns(lookback)

        # 1. Hurst 指數
        prices = 100 * np.exp(np.cumsum(returns))
        hurst = calculate_hurst_exponent(prices)
        hurst_interp = interpret_hurst(hurst)

        # 2. HMM 體制識別
        hmm_state, hmm_bull_prob = hmm_regime_simple(returns)
        hmm_regime_str, _ = interpret_hmm_regime(hmm_state, hmm_bull_prob)

        # 3. PCA 結構比較
        period1 = returns[: lookback // 2].reshape(-1, 1)
        period2 = returns[lookback // 2 :].reshape(-1, 1)
        pca_similarity = calculate_pca_cosine_similarity(period1, period2)
        structural_break = detect_structural_break(pca_similarity)

        # 融合判定
        regime = self._fuse_regime(hurst, hmm_bull_prob, pca_similarity)

        return {
            "hurst": round(hurst, 3),
            "hurst_interpretation": hurst_interp,
            "hmm_bull_prob": round(hmm_bull_prob, 2),
            "hmm_regime": hmm_regime_str,
            "pca_similarity": round(pca_similarity, 3),
            "structural_break": structural_break,
            "regime": regime,
            "kelly_factor": self._get_kelly_factor(regime),
            "data_source": data_source,
        }

    def _get_real_returns(self, lookback: int) -> tuple[np.ndarray, str]:
        """從 Yahoo Finance 取得真實市場報酬"""
        try:
            # 取得 S&P 500 歷史資料
            ticker = yf.Ticker("^GSPC")
            hist = ticker.history(period="6mo")

            if hist is not None and len(hist) >= lookback:
                closes = hist["Close"].values[-lookback:]
                returns = np.diff(np.log(closes))
                return returns, "Yahoo Finance (S&P 500)"
            else:
                self._logger.warning(
                    f"S&P 500 數據不足 ({len(hist) if hist is not None else 0} < {lookback})"
                )
        except Exception as e:
            self._logger.warning(f"Yahoo Finance API 失敗: {e}")

        # Fallback: 返回空陣列並標記
        self._logger.warning("無法取得市場數據，體制判定可能不準確")
        return np.zeros(lookback), "N/A (API 失敗)"

    def _fuse_regime(self, hurst: float, bull_prob: float, pca: float) -> str:
        """三層融合體制判定"""
        if pca < 0.8:
            return "結構斷裂"
        if hurst > 0.55 and bull_prob > 0.7:
            return "趨勢牛市"
        if hurst < 0.45 and bull_prob < 0.3:
            return "恐慌熊市"
        if 0.45 <= hurst <= 0.55:
            return "震盪區間"
        return "未定義"

    def _get_kelly_factor(self, regime: str) -> float:
        """根據體制返回凱利係數"""
        factors = {
            "趨勢牛市": 0.5,
            "震盪區間": 0.25,
            "恐慌熊市": 0.0,
            "結構斷裂": 0.0,
            "未定義": 0.25,
        }
        return factors.get(regime, 0.25)
