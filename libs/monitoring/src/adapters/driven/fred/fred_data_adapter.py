"""FRED Economic Data Adapter - Real Implementation"""

import os
from datetime import date

import pandas as pd
from libs.monitoring.src.ports.fred_data_provider_port import FredDataProviderPort
from fredapi import Fred


class FredDataAdapter(FredDataProviderPort):
    """FRED Economic Data Adapter

    Data source: Federal Reserve Economic Data
    Requires FRED_API_KEY environment variable
    """

    # 常用 FRED Series IDs
    SERIES_IDS = {
        "VIX": "VIXCLS",  # CBOE VIX
        "FED_ASSETS": "WALCL",  # Fed Total Assets
        "M2": "M2SL",  # M2 Money Supply
        "HY_SPREAD": "BAMLH0A0HYM2",  # High Yield Spread
        "IG_SPREAD": "BAMLC0A0CM",  # Investment Grade Spread
        "TGA": "WTREGEN",  # Treasury General Account
        "RRP": "RRPONTSYD",  # Overnight Reverse Repo
        "CPI": "CPIAUCSL",  # Consumer Price Index
        "UNRATE": "UNRATE",  # Unemployment Rate
        "GDP": "GDP",  # Gross Domestic Product
        "PMI": "MANEMP",  # Manufacturing Employment (PMI proxy)
    }

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("FRED_API_KEY")
        if not self._api_key:
            raise ValueError("FRED_API_KEY not set, please set in .env")
        self._fred = Fred(api_key=self._api_key)
        self._cache: dict[str, pd.Series] = {}

    def get_series(
        self,
        series_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> pd.Series:
        """Get FRED time series"""
        cache_key = f"{series_id}_{start_date}_{end_date}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            series = self._fred.get_series(
                series_id,
                observation_start=start_date,
                observation_end=end_date,
            )
            self._cache[cache_key] = series
            return series
        except Exception as e:
            raise ValueError(f"Unable to get FRED data {series_id}: {e}")

    def get_latest_value(self, series_id: str) -> float:
        """Get latest value of time series"""
        series = self.get_series(series_id)
        if series.empty:
            return 0.0
        return float(series.iloc[-1])

    def get_vix(self) -> float:
        """Get VIX index"""
        return self.get_latest_value(self.SERIES_IDS["VIX"])

    def get_fed_balance_sheet(self) -> float:
        """Get Fed balance sheet size (in millions USD)"""
        return self.get_latest_value(self.SERIES_IDS["FED_ASSETS"])

    def get_fed_balance_sheet_trend(self) -> str:
        """Determine Fed balance sheet trend

        Compare recent 4-week average vs prior 4-week average:
        - Recent 4 weeks > Prior 4 weeks → "expanding"
        - Recent 4 weeks < Prior 4 weeks → "contracting"
        - Difference < 0.5% → "stable"
        """
        series = self.get_series(self.SERIES_IDS["FED_ASSETS"])
        if len(series) < 8:
            return "unknown"

        recent_4w = series.iloc[-4:].mean()
        prior_4w = series.iloc[-8:-4].mean()

        if prior_4w == 0:
            return "unknown"

        change_pct = (recent_4w - prior_4w) / prior_4w * 100

        if change_pct > 0.5:
            return "expanding"
        elif change_pct < -0.5:
            return "contracting"
        else:
            return "stable"

    def get_m2_yoy(self) -> float:
        """Get M2 year-over-year growth rate (%)"""
        series = self.get_series(self.SERIES_IDS["M2"])
        if len(series) < 13:
            return 0.0
        current = series.iloc[-1]
        year_ago = series.iloc[-13]  # 約 12 個月前
        if year_ago == 0:
            return 0.0
        return round((current / year_ago - 1) * 100, 2)

    def get_credit_spread(self) -> float:
        """Get credit spread (HY - IG)"""
        try:
            hy = self.get_latest_value(self.SERIES_IDS["HY_SPREAD"])
            ig = self.get_latest_value(self.SERIES_IDS["IG_SPREAD"])
            return round(hy - ig, 2)
        except Exception:
            return 0.0

    def get_net_liquidity(self) -> float:
        """Get net liquidity = Fed Assets - TGA - RRP"""
        try:
            fed_assets = self.get_latest_value(self.SERIES_IDS["FED_ASSETS"])
            tga = self.get_latest_value(self.SERIES_IDS["TGA"])
            rrp = self.get_latest_value(self.SERIES_IDS["RRP"])
            return fed_assets - tga - rrp
        except Exception:
            return 0.0

    def get_cpi_yoy(self) -> float:
        """Get CPI year-over-year growth rate (%)"""
        series = self.get_series(self.SERIES_IDS["CPI"])
        if len(series) < 13:
            return 0.0
        current = series.iloc[-1]
        year_ago = series.iloc[-13]
        if year_ago == 0:
            return 0.0
        return round((current / year_ago - 1) * 100, 2)

    def get_unemployment_rate(self) -> float:
        """Get unemployment rate (%)"""
        return self.get_latest_value(self.SERIES_IDS["UNRATE"])

    def get_gli_z_score(self, lookback_weeks: int = 52) -> float:
        """Calculate GLI (Global Liquidity Index) Z-Score

        GLI = Fed Assets - TGA - RRP (net liquidity)
        Z-Score = (current value - mean) / standard deviation

        Args:
            lookback_weeks: Number of weeks to look back for mean and std calculation

        Returns:
            Z-Score value, positive means ample liquidity, negative means tight liquidity
        """
        try:
            fed_series = self.get_series(self.SERIES_IDS["FED_ASSETS"])
            tga_series = self.get_series(self.SERIES_IDS["TGA"])
            rrp_series = self.get_series(self.SERIES_IDS["RRP"])

            # Calculate net liquidity series (use common dates)
            common_idx = fed_series.index.intersection(tga_series.index).intersection(
                rrp_series.index
            )
            if len(common_idx) < lookback_weeks:
                return 0.0

            net_liq = (
                fed_series.loc[common_idx]
                - tga_series.loc[common_idx]
                - rrp_series.loc[common_idx]
            )

            # Take most recent lookback_weeks of data
            recent = net_liq.iloc[-lookback_weeks:]

            current = float(recent.iloc[-1])
            mean = float(recent.mean())
            std = float(recent.std())

            if std == 0:
                return 0.0

            return round((current - mean) / std, 2)
        except Exception:
            return 0.0
