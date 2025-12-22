"""取得供應鏈傳導分析 Query

實作 GetSupplyChainLinkPort Driving Port
使用真實 Yahoo Finance 數據
"""

import logging

import numpy as np
import yfinance as yf

from libs.linking.src.domain.services.kalman_beta_estimator import (
    kalman_beta_simple,
    estimate_supply_chain_lag,
)
from libs.hunting.src.domain.services.theoretical_price_calculator import (
    calculate_remaining_alpha,
    calculate_supply_chain_target,
)
from libs.linking.src.ports.get_supply_chain_link_port import (
    GetSupplyChainLinkPort,
)
from libs.shared.src.constants.supply_chain_map import SUPPLY_CHAIN_MAP
from libs.shared.src.dtos.strategy.supply_chain_link_result_dto import (
    SupplyChainLinkResultDTO,
)


class GetSupplyChainLinkQuery(GetSupplyChainLinkPort):
    """取得供應鏈傳導分析"""

    # 供應鏈對應表（從 shared constants 引入，保留 class 屬性以維持向後相容）
    SUPPLY_CHAIN_MAP = SUPPLY_CHAIN_MAP

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(
        self, us_symbol: str, tw_symbol: str, period: str = "6mo"
    ) -> SupplyChainLinkResultDTO:
        """分析供應鏈傳導關係

        Args:
            us_symbol: 美股代號
            tw_symbol: 台股代號
            period: 資料期間 (3mo, 6mo, 1y, 2y, 5y)
        """
        us_symbol = str(us_symbol).upper()
        tw_symbol = str(tw_symbol)
        # 處理台股代號格式
        if not tw_symbol.endswith(".TW"):
            tw_symbol = f"{tw_symbol}.TW"

        # 取得歷史數據
        us_returns = self._get_returns(us_symbol, period)
        tw_returns = self._get_returns(tw_symbol, period)

        if us_returns is None or tw_returns is None:
            return {
                "us_symbol": us_symbol,
                "tw_symbol": tw_symbol.replace(".TW", ""),
                "beta": 0.0,
                "lag": 0,
                "correlation": 0.0,
                "expected_move": 0.0,
                "signal": "NO_DATA",
            }

        # 對齊長度
        min_len = min(len(us_returns), len(tw_returns))
        us_returns = us_returns[-min_len:]
        tw_returns = tw_returns[-min_len:]

        # 計算動態 Beta
        betas = kalman_beta_simple(us_returns, tw_returns)
        current_beta = betas[-1] if len(betas) > 0 else 0.0

        # 估計領先滯後
        lag_days, correlation = estimate_supply_chain_lag(us_returns, tw_returns)

        # 預期台股走勢
        us_last_return = us_returns[-1] if len(us_returns) > 0 else 0.0
        expected_tw_move = current_beta * us_last_return

        # ========================================
        # 計算理論價格與剩餘 Alpha (新增)
        # ========================================
        # 取得台股當前價格
        try:
            tw_ticker = yf.Ticker(tw_symbol)
            tw_hist = tw_ticker.history(period="2d")
            if tw_hist is not None and len(tw_hist) >= 2:
                tw_prev_close = float(tw_hist["Close"].iloc[-2])
                tw_open = float(tw_hist["Open"].iloc[-1])
                tw_current = float(tw_hist["Close"].iloc[-1])
            else:
                tw_prev_close = 0.0
                tw_open = 0.0
                tw_current = 0.0
        except Exception:
            tw_prev_close = 0.0
            tw_open = 0.0
            tw_current = 0.0

        # 計算供應鏈傳導理論目標價
        if tw_prev_close > 0:
            target_price, expected_transmission = calculate_supply_chain_target(
                tw_prev_close=tw_prev_close,
                tw_open=tw_open,
                us_return=us_last_return,
                kalman_beta=current_beta,
            )

            # 計算剩餘 Alpha
            remaining_alpha, alpha_signal = calculate_remaining_alpha(
                target_price=target_price,
                current_price=tw_current,
                expected_move=abs(expected_transmission),
            )
        else:
            target_price = 0.0
            expected_transmission = 0.0
            remaining_alpha = 0.0

        # 訊號判定 (整合剩餘 Alpha)
        if abs(expected_tw_move) > 0.01:
            if remaining_alpha >= 0.6:
                signal = "EXECUTE" if expected_tw_move > 0 else "SHORT"
            elif remaining_alpha >= 0.4:
                signal = "REDUCE"
            else:
                signal = "ABORT"
        else:
            signal = "NEUTRAL"

        return {
            "us_symbol": us_symbol,
            "tw_symbol": tw_symbol.replace(".TW", ""),
            "beta": round(current_beta, 2),
            "lag": lag_days,
            "correlation": round(correlation, 3),
            "expected_move": round(expected_tw_move, 4),
            "signal": signal,
            "sample_size": min_len,
            "period": period,
            # 新增：理論價格與剩餘 Alpha
            "tw_prev_close": round(tw_prev_close, 2) if tw_prev_close > 0 else None,
            "tw_open": round(tw_open, 2) if tw_open > 0 else None,
            "tw_current": round(tw_current, 2) if tw_current > 0 else None,
            "target_price": round(target_price, 2) if target_price > 0 else None,
            "remaining_alpha": round(remaining_alpha, 2) if tw_prev_close > 0 else None,
        }

    def _get_returns(self, symbol: str, period: str = "3mo") -> np.ndarray | None:
        """取得股票報酬率"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist is None or len(hist) < 20:
                return None

            closes = hist["Close"].values
            returns = np.diff(np.log(closes))
            return returns

        except Exception:
            return None
