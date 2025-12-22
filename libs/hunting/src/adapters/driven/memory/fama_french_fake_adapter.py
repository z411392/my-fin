"""Fama-French Factor Fake Adapter

Implements FamaFrenchFactorProviderPort for testing
"""

import pandas as pd
import numpy as np

from libs.hunting.src.ports.fama_french_factor_provider_port import (
    FamaFrenchFactorProviderPort,
)


class FamaFrenchFakeAdapter(FamaFrenchFactorProviderPort):
    """Fama-French Factor Fake Adapter"""

    def __init__(self) -> None:
        self._ff3_data: pd.DataFrame | None = None
        self._momentum_data: pd.DataFrame | None = None
        # Generate default data (252 trading days)
        dates = pd.date_range(end=pd.Timestamp.today(), periods=252, freq="B")
        self._default_ff3 = pd.DataFrame(
            {
                "Mkt-RF": np.random.randn(252) * 0.01,
                "SMB": np.random.randn(252) * 0.005,
                "HML": np.random.randn(252) * 0.005,
                "RF": np.full(252, 0.0001),
            },
            index=dates,
        )
        self._default_momentum = pd.DataFrame(
            {"Mom": np.random.randn(252) * 0.008},
            index=dates,
        )

    def set_ff3_data(self, data: pd.DataFrame) -> None:
        """Set Fama-French 3-factor data (for testing)"""
        self._ff3_data = data

    def set_momentum_data(self, data: pd.DataFrame) -> None:
        """Set momentum factor data (for testing)"""
        self._momentum_data = data

    def get_ff3_daily(self) -> pd.DataFrame:
        """Get Fama-French 3-factor (daily)"""
        if self._ff3_data is not None:
            return self._ff3_data
        return self._default_ff3

    def get_momentum_daily(self) -> pd.DataFrame:
        """Get momentum factor (daily)"""
        if self._momentum_data is not None:
            return self._momentum_data
        return self._default_momentum
