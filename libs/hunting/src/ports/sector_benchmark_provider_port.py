"""產業 Benchmark 提供者 Port

提供產業 ETF 對照、代表股查詢介面。
"""

from typing import Protocol


class SectorBenchmarkProviderPort(Protocol):
    """產業 Benchmark 提供者介面"""

    def get_sector_benchmark(self, symbol: str, market: str = "tw") -> str:
        """取得產業 benchmark（ETF 代碼或 synthetic 標記）

        Args:
            symbol: 股票代碼
            market: 市場 (tw / us)

        Returns:
            str: ETF 代碼 或 "synthetic:{industry_code}" 標記
        """
        ...

    def get_sector_proxies(self, industry: str) -> list[str]:
        """取得產業代表股清單

        Args:
            industry: 產業代碼 (如 "01", "24")

        Returns:
            list[str]: 代表股代碼列表
        """
        ...

    def get_industry(self, symbol: str) -> str | None:
        """取得股票的產業代碼

        Args:
            symbol: 股票代碼

        Returns:
            str | None: 產業代碼 (如 "24" 代表半導體)
        """
        ...

    def get_industry_name(self, symbol: str) -> str:
        """取得股票的產業名稱

        Args:
            symbol: 股票代碼

        Returns:
            str: 產業名稱
        """
        ...
