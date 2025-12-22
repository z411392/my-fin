"""Fama-French 因子資料提供者 Port"""

from typing import Protocol

import pandas as pd


class FamaFrenchFactorProviderPort(Protocol):
    """Fama-French 因子資料提供者介面

    提供 Fama-French 三因子和動能因子資料，
    用於美股的因子剝離計算。
    """

    def get_ff3_daily(self) -> pd.DataFrame:
        """取得 Fama-French 三因子（日頻）

        Returns:
            DataFrame with columns: Mkt-RF, SMB, HML, RF
        """
        ...

    def get_momentum_daily(self) -> pd.DataFrame:
        """取得動能因子（日頻）

        Returns:
            DataFrame with column: Mom
        """
        ...
