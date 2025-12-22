"""VPIN 計算器 Yahoo Adapter

使用 yfinance 獲取歷史數據並計算 VPIN (Volume-synchronized Probability of Informed Trading)

Note: 真正的 VPIN 需要 tick 級數據，此實作使用日級數據的改良版本
"""

from datetime import date, timedelta

import numpy as np
import yfinance as yf
from libs.monitoring.src.ports.v_p_i_n_provider_port import VPINProviderPort
from libs.shared.src.dtos.market.vpin_result_dto import VPINResultDTO


class VPINYahooAdapter(VPINProviderPort):
    """VPIN 計算器 - Yahoo Finance 實作 (日級近似)"""

    def __init__(self, lookback_days: int = 50, n_buckets: int = 50):
        self._lookback_days = lookback_days
        self._n_buckets = n_buckets

    def calculate(self, symbol: str) -> VPINResultDTO:
        """計算 VPIN (使用日級數據的改良版)

        使用 Bulk Volume Classification (BVC) 方法估計
        基於 Easley, López de Prado, O'Hara (2012)

        Args:
            symbol: 股票代碼

        Returns:
            dict: {
                "vpin": float (0-1),
                "percentile": float (0-100),
                "level": str (NORMAL/ELEVATED/HIGH/CRITICAL),
                "avg_volume": float,
                "recent_imbalance": float
            }
        """
        # 處理台股代碼
        ticker_symbol = f"{symbol}.TW" if symbol.isdigit() else symbol

        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=self._lookback_days + 30)

            ticker = yf.Ticker(ticker_symbol)
            hist = ticker.history(start=start_date, end=end_date)

            if hist.empty or len(hist) < 20:
                return self._default_result()

            # 計算 BVC (Bulk Volume Classification)
            # 使用價格變動方向來估計買賣比例
            closes = hist["Close"].values
            volumes = hist["Volume"].values
            highs = hist["High"].values
            lows = hist["Low"].values

            # 計算每日買賣量估計 (使用 HL 範圍內的收盤位置)
            buy_volumes = []
            sell_volumes = []

            for i in range(len(closes)):
                hl_range = highs[i] - lows[i]
                if hl_range > 0:
                    # 收盤在高低範圍的相對位置 (0=low, 1=high)
                    position = (closes[i] - lows[i]) / hl_range
                    buy_vol = volumes[i] * position
                    sell_vol = volumes[i] * (1 - position)
                else:
                    buy_vol = volumes[i] / 2
                    sell_vol = volumes[i] / 2

                buy_volumes.append(buy_vol)
                sell_volumes.append(sell_vol)

            buy_volumes = np.array(buy_volumes)
            sell_volumes = np.array(sell_volumes)

            # 計算 VPIN
            # VPIN = mean(|buy - sell| / total_volume) over buckets
            window = min(20, len(buy_volumes))
            recent_buy = buy_volumes[-window:]
            recent_sell = sell_volumes[-window:]
            recent_vol = volumes[-window:]

            imbalances = np.abs(recent_buy - recent_sell)
            vpin = np.mean(imbalances / recent_vol) if np.mean(recent_vol) > 0 else 0

            # 計算百分位 (與歷史比較)
            all_imbalances = np.abs(buy_volumes - sell_volumes) / volumes
            percentile = (np.sum(all_imbalances < vpin) / len(all_imbalances)) * 100

            # 判定 level
            if vpin >= 0.8:
                level = "CRITICAL"
            elif vpin >= 0.6:
                level = "HIGH"
            elif vpin >= 0.4:
                level = "ELEVATED"
            else:
                level = "NORMAL"

            return {
                "vpin": round(float(vpin), 4),
                "percentile": round(float(percentile), 1),
                "level": level,
                "avg_volume": float(np.mean(volumes)),
                "recent_imbalance": round(float(np.mean(imbalances[-5:])), 0),
            }

        except Exception:
            return self._default_result()

    def _default_result(self) -> VPINResultDTO:
        """默認結果 (數據不足時)"""
        return {
            "vpin": 0.3,
            "percentile": 50.0,
            "level": "NORMAL",
            "avg_volume": 0,
            "recent_imbalance": 0,
        }
