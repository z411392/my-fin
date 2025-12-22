"""績效追蹤器 Fake Adapter"""

from datetime import date

from libs.reviewing.src.ports.performance_provider_port import PerformanceProviderPort
from libs.shared.src.dtos.reviewing.returns_map_dto import ReturnsMapDTO


class PerformanceFakeAdapter(PerformanceProviderPort):
    """績效追蹤器 Mock"""

    def __init__(self) -> None:
        self._returns: ReturnsMapDTO = {}
        self._sharpe_ratio: float = 1.2
        self._num_trials: int = 50
        self._benchmark_sharpe: float = 0.5

    def set_returns(self, returns: ReturnsMapDTO) -> None:
        self._returns = returns

    def set_sharpe_ratio(self, sharpe: float) -> None:
        self._sharpe_ratio = sharpe

    def set_num_trials(self, n: int) -> None:
        self._num_trials = n

    def set_benchmark_sharpe(self, sharpe: float) -> None:
        self._benchmark_sharpe = sharpe

    def get_returns(self, start_date: date, end_date: date) -> ReturnsMapDTO:
        return self._returns

    def get_sharpe_ratio(self) -> float:
        return self._sharpe_ratio

    def get_num_trials(self) -> int:
        return self._num_trials

    def get_benchmark_sharpe(self) -> float:
        return self._benchmark_sharpe
