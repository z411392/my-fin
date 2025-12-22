"""
VPIN Shioaji Adapter

Implements VPINCalculatorPort, combines Tick data with VPIN calculator
"""

import pandas as pd

from libs.monitoring.src.domain.services.vpin_calculator import (
    calculate_vpin,
    classify_vpin,
)
from libs.shared.src.dtos.market.tick_dto import TickDTO
from libs.shared.src.dtos.market.vpin_result_dto import VPINResultDTO


import logging
import time
from libs.monitoring.src.ports.v_p_i_n_provider_port import VPINProviderPort
from libs.monitoring.src.ports.tick_provider_port import TickProviderPort


class VPINShioajiAdapter(VPINProviderPort):
    """VPIN Calculator Adapter (using Shioaji tick data)"""

    def __init__(self, tick_provider: TickProviderPort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._tick_adapter = tick_provider
        self._connected = False

    def connect(self) -> bool:
        """Connect"""
        self._connected = self._tick_adapter.connect()
        return self._connected

    def disconnect(self) -> None:
        """Disconnect"""
        self._tick_adapter.disconnect()
        self._connected = False

    def calculate(self, symbol: str) -> VPINResultDTO:
        """Calculate VPIN (implements VPINCalculatorPort)"""
        return self.calculate_vpin_realtime(symbol)

    def calculate_vpin_realtime(
        self,
        symbol: str,
        collect_seconds: int = 60,
        bucket_size: int = 50,
    ) -> VPINResultDTO:
        """Calculate VPIN in real-time"""

        if not self._connected:
            if not self.connect():
                return self._get_fallback_result()

        if not self._tick_adapter.subscribe(symbol):
            return self._get_fallback_result()

        self._logger.info(
            f"Collecting {symbol} tick data ({collect_seconds} seconds)..."
        )
        time.sleep(collect_seconds)

        ticks = self._tick_adapter.get_ticks(symbol)
        tick_count = len(ticks)

        if tick_count < 10:
            self._logger.info(f"Insufficient tick data: {tick_count}")
            return self._get_fallback_result(tick_count=tick_count)

        df = self._ticks_to_dataframe(ticks)
        if df.empty:
            return self._get_fallback_result(tick_count=tick_count)

        vpin = calculate_vpin(df, bucket_size=bucket_size)
        level, action = classify_vpin(vpin)

        return {
            "vpin": round(vpin, 4),
            "level": level.value,
            "action": action,
            "tick_count": tick_count,
            "source": "Shioaji",
        }

    def calculate_vpin_from_ticks(self, ticks: list[TickDTO]) -> VPINResultDTO:
        """Calculate VPIN from collected tick data"""
        if not ticks or len(ticks) < 10:
            return self._get_fallback_result()

        df = self._ticks_to_dataframe(ticks)
        if df.empty:
            return self._get_fallback_result()

        vpin = calculate_vpin(df)
        level, action = classify_vpin(vpin)

        return {
            "vpin": round(vpin, 4),
            "level": level.value,
            "action": action,
            "tick_count": len(ticks),
            "source": "Shioaji",
        }

    def _ticks_to_dataframe(self, ticks: list[TickDTO]) -> pd.DataFrame:
        """Convert tick list to DataFrame for VPIN calculation"""
        if not ticks:
            return pd.DataFrame()

        df = pd.DataFrame(ticks)

        if "volume" not in df.columns:
            return pd.DataFrame()

        if "price" in df.columns:
            df["price_change"] = df["price"].diff().fillna(0)
        elif "tick_type" in df.columns:
            df["price_change"] = df["tick_type"].apply(
                lambda x: 1 if x == 1 else (-1 if x == 2 else 0)
            )
        else:
            df["price_change"] = 0

        return df[["volume", "price_change"]]

    def _get_fallback_result(self, tick_count: int = 0) -> VPINResultDTO:
        """Return fallback result"""
        return {
            "vpin": 0.55,
            "level": "NORMAL",
            "action": "Normal trading",
            "tick_count": tick_count,
            "source": "Fallback",
        }
