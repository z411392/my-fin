"""Fama-French 因子 Adapter (使用 pandas-datareader)"""

from functools import lru_cache

import pandas as pd
import pandas_datareader.data as web

from libs.hunting.src.ports.fama_french_factor_provider_port import (
    FamaFrenchFactorProviderPort,
)


class DatareaderFamaFrenchAdapter(FamaFrenchFactorProviderPort):
    """使用 pandas-datareader 從 Kenneth French Data Library 取得因子資料"""

    @lru_cache(maxsize=1)
    def get_ff3_daily(self) -> pd.DataFrame:
        """取得 Fama-French 三因子（日頻）

        Returns:
            DataFrame with columns: Mkt-RF, SMB, HML, RF
        """
        return web.DataReader(
            "F-F_Research_Data_Factors_daily",
            "famafrench",
        )[0]

    @lru_cache(maxsize=1)
    def get_momentum_daily(self) -> pd.DataFrame:
        """取得動能因子（日頻）

        Returns:
            DataFrame with column: Mom
        """
        return web.DataReader(
            "F-F_Momentum_Factor_daily",
            "famafrench",
        )[0]
