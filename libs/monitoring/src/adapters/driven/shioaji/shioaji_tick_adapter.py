"""Shioaji Tick Data Adapter

Implements TickDataProviderPort for collecting tick data for VPIN calculation
"""

import threading
from collections import deque

from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient
from libs.shared.src.dtos.market.tick_dto import TickDTO


import logging
from libs.monitoring.src.ports.tick_provider_port import TickProviderPort


class ShioajiTickAdapter(TickProviderPort):
    """Shioaji Tick Data Subscriber"""

    def __init__(self, client: ShioajiClient, max_ticks: int = 10000) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._client = client
        self._max_ticks = max_ticks
        self._ticks: dict[str, deque] = {}
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Connect to Shioaji API"""
        if not self._client.connect():
            return False

        api = self._client.api

        # Set quote callback
        @api.quote.on_event
        def on_event(_resp_code: int, _event_code: int, _info: str, _event: str):
            pass

        @api.quote.on_quote
        def on_quote(topic: str, quote: dict):
            self._handle_quote(topic, quote)

        return True

    def disconnect(self) -> None:
        """Disconnect"""
        if self._client.connected:
            for symbol in list(self._ticks.keys()):
                self.unsubscribe(symbol)
            self._client.disconnect()

    def subscribe(self, symbol: str) -> bool:
        """Subscribe to tick data"""
        if not self._client.connected:
            if not self.connect():
                return False

        try:
            api = self._client.api
            contract = api.Contracts.Stocks[symbol]
            if contract is None:
                self._logger.info(f"Contract not found: {symbol}")
                return False

            with self._lock:
                if symbol not in self._ticks:
                    self._ticks[symbol] = deque(maxlen=self._max_ticks)

            api.quote.subscribe(contract, quote_type="tick")
            return True
        except Exception as e:
            self._logger.warning(f"Subscribe failed {symbol}: {e}")
            return False

    def unsubscribe(self, symbol: str) -> None:
        """Unsubscribe"""
        if not self._client.connected:
            return

        try:
            api = self._client.api
            contract = api.Contracts.Stocks[symbol]
            if contract:
                api.quote.unsubscribe(contract, quote_type="tick")
        except Exception:
            pass

    def _handle_quote(self, topic: str, quote: dict) -> None:
        """Handle received quote"""
        parts = topic.split("/")
        if len(parts) < 4:
            return

        symbol = parts[-1]

        with self._lock:
            if symbol in self._ticks:
                tick_data = {
                    "time": quote.get("Time", ""),
                    "price": (
                        quote.get("Close", [0])[0]
                        if isinstance(quote.get("Close"), list)
                        else quote.get("Close", 0)
                    ),
                    "volume": (
                        quote.get("Volume", [0])[0]
                        if isinstance(quote.get("Volume"), list)
                        else quote.get("Volume", 0)
                    ),
                    "tick_type": (
                        quote.get("TickType", [0])[0]
                        if isinstance(quote.get("TickType"), list)
                        else quote.get("TickType", 0)
                    ),
                    "vol_sum": (
                        quote.get("VolSum", [0])[0]
                        if isinstance(quote.get("VolSum"), list)
                        else quote.get("VolSum", 0)
                    ),
                }
                self._ticks[symbol].append(tick_data)

    def get_ticks(self, symbol: str) -> list[TickDTO]:
        """Get collected tick data"""
        with self._lock:
            if symbol in self._ticks:
                return list(self._ticks[symbol])
            return []

    def clear_ticks(self, symbol: str) -> None:
        """Clear tick data"""
        with self._lock:
            if symbol in self._ticks:
                self._ticks[symbol].clear()

    def get_tick_count(self, symbol: str) -> int:
        """Get tick count"""
        with self._lock:
            if symbol in self._ticks:
                return len(self._ticks[symbol])
            return 0
