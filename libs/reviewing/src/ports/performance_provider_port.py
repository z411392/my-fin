"""績效提供者 Port"""

from typing import Protocol


class PerformanceProviderPort(Protocol):
    """績效提供者 Port"""

    def get_sharpe_ratio(self) -> float:
        """取得夏普比率"""
        ...

    def get_num_trials(self) -> int:
        """取得測試次數 (交易次數)"""
        ...

    def get_benchmark_sharpe(self) -> float:
        """取得基準夏普比率"""
        ...
