from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort

"""殘差動能市場數據 Fake Adapter"""


class ResidualMomentumMarketDataFakeAdapter(MarketDataProviderPort):
    """市場數據提供者 Mock (殘差動能計算用)"""

    def __init__(self) -> None:
        self._returns: dict[str, list[float]] = {}
        self._spy_returns: list[float] = [0.01, -0.005, 0.015, 0.002, -0.008]
        self._sector_returns: dict[str, list[float]] = {}
        self._ivol_percentile: dict[str, float] = {}
        self._amihud_percentile: dict[str, float] = {}

    def set_returns(self, symbol: str, returns: list[float]) -> None:
        self._returns[symbol] = returns

    def set_spy_returns(self, returns: list[float]) -> None:
        self._spy_returns = returns

    def set_sector_returns(self, symbol: str, returns: list[float]) -> None:
        self._sector_returns[symbol] = returns

    def set_ivol_percentile(self, symbol: str, pct: float) -> None:
        self._ivol_percentile[symbol] = pct

    def set_amihud_percentile(self, symbol: str, pct: float) -> None:
        self._amihud_percentile[symbol] = pct

    def get_returns(self, symbol: str, days: int) -> list[float]:
        return self._returns.get(symbol, [0.02, 0.01, -0.01, 0.015, 0.005])

    def get_spy_returns(self, days: int) -> list[float]:
        return self._spy_returns

    def get_sector_returns(self, symbol: str, days: int) -> list[float]:
        return self._sector_returns.get(symbol, [0.01, 0.005, -0.002, 0.008, 0.003])

    def get_ivol_percentile(self, symbol: str) -> float:
        return self._ivol_percentile.get(symbol, 50.0)

    def get_amihud_percentile(self, symbol: str) -> float:
        return self._amihud_percentile.get(symbol, 50.0)

    def get_daily_returns(self, symbol: str, days: int) -> list[float]:
        """取得日報酬 (別名)"""
        return self._returns.get(symbol, [])

    def set_benchmark_returns(self, symbol: str, returns: list[float]) -> None:
        """設置基準報酬"""
        self._spy_returns = returns

    def get_benchmark_returns(self, symbol: str, days: int) -> list[float]:
        """取得基準報酬"""
        return self._spy_returns
