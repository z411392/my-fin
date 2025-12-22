"""宏觀數據 FRED Adapter

實作 MacroDataProviderPort，使用 FRED API 取得宏觀經濟數據
"""

import os

import pandas as pd
from libs.reviewing.src.ports.macro_data_provider_port import MacroDataProviderPort
from fredapi import Fred


class MacroDataFredAdapter(MacroDataProviderPort):
    """宏觀數據 FRED Adapter"""

    SERIES_IDS = {
        "VIX": "VIXCLS",
        "FED_ASSETS": "WALCL",
        "M2": "M2SL",
    }

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("FRED_API_KEY")
        self._fred: Fred | None = None
        self._cache: dict[str, pd.Series] = {}

    def _get_fred(self) -> Fred:
        """延遲初始化 FRED 客戶端"""
        if self._fred is None:
            if not self._api_key:
                raise ValueError("FRED_API_KEY 未設定")
            self._fred = Fred(api_key=self._api_key)
        return self._fred

    def _get_series(self, series_id: str) -> pd.Series:
        """取得 FRED 時間序列"""
        if series_id in self._cache:
            return self._cache[series_id]

        try:
            series = self._get_fred().get_series(series_id)
            self._cache[series_id] = series
            return series
        except Exception as e:
            raise ValueError(f"無法取得 FRED 數據 {series_id}: {e}")

    def _get_latest_value(self, series_id: str) -> float:
        """取得時間序列最新值"""
        series = self._get_series(series_id)
        if series.empty:
            return 0.0
        return float(series.iloc[-1])

    def get_vix(self) -> float:
        """取得 VIX 指數"""
        try:
            return self._get_latest_value(self.SERIES_IDS["VIX"])
        except Exception:
            return 20.0  # 預設值

    def get_fed_balance_sheet_trend(self) -> str:
        """取得 Fed 資產負債表趨勢"""
        try:
            series = self._get_series(self.SERIES_IDS["FED_ASSETS"])
            if len(series) < 5:
                return "UNKNOWN"

            # 比較最近 4 週趨勢
            recent = series.iloc[-1]
            month_ago = series.iloc[-5] if len(series) >= 5 else series.iloc[0]

            if recent > month_ago * 1.001:  # 0.1% 增長
                return "EXPANDING"
            elif recent < month_ago * 0.999:
                return "CONTRACTING"
            else:
                return "STABLE"
        except Exception:
            return "UNKNOWN"

    def get_m2_yoy(self) -> float:
        """取得 M2 年增率 (%)"""
        try:
            series = self._get_series(self.SERIES_IDS["M2"])
            if len(series) < 13:
                return 0.0

            current = series.iloc[-1]
            year_ago = series.iloc[-13]
            if year_ago == 0:
                return 0.0
            return round((current / year_ago - 1) * 100, 2)
        except Exception:
            return 0.0
