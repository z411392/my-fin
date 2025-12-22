"""Fundamental Data Fake Adapter

Implements IFundamentalDataPort for testing
Simulates StatementDog API
"""

from typing import Callable

from libs.hunting.src.ports.i_fundamental_data_port import IFundamentalDataPort
from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)
from libs.shared.src.dtos.statementdog.fundamental_summary_map_dto import (
    FundamentalSummaryMap,
)


class FundamentalDataFakeAdapter(IFundamentalDataPort):
    """Fundamental Data Fake Adapter (simulates StatementDog)"""

    def __init__(self) -> None:
        self._summaries: dict[str, FundamentalSummaryDTO] = {}
        self._default_summary: FundamentalSummaryDTO = {
            "symbol": "DEFAULT",
            "is_valid": True,
            "revenue_momentum": {
                "yoy_growth": 15.0,
                "mom_growth": 3.0,
                "consecutive_growth_months": 6,
            },
            "earnings_quality": {
                "gross_margin": 45.0,
                "operating_margin": 20.0,
                "net_margin": 15.0,
                "roe": 18.0,
                "roa": 10.0,
            },
            "valuation_metrics": {
                "pe_ratio": 15.0,
                "pb_ratio": 2.5,
                "ps_ratio": 3.0,
                "dividend_yield": 3.5,
            },
            "f_score": {
                "total_score": 7,
                "profitability": 3,
                "leverage": 2,
                "efficiency": 2,
            },
        }

    def set_summary(self, symbol: str, summary: FundamentalSummaryDTO) -> None:
        """Set fundamental summary for specific stock (for testing)"""
        self._summaries[symbol] = summary

    def set_f_score(self, symbol: str, score: int) -> None:
        """Set F-Score for specific stock (for testing)"""
        if symbol not in self._summaries:
            self._summaries[symbol] = self._default_summary.copy()
            self._summaries[symbol]["symbol"] = symbol
        self._summaries[symbol]["f_score"] = {
            "total_score": score,
            "profitability": min(score, 4),
            "leverage": min(score - 4, 3) if score > 4 else 0,
            "efficiency": max(score - 7, 0),
        }

    def batch_get_f_score(
        self,
        symbols: list[str],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> FundamentalSummaryMap:
        """Batch get F-Score"""
        results: dict[str, FundamentalSummaryDTO] = {}
        for i, symbol in enumerate(symbols):
            if symbol in self._summaries:
                results[symbol] = self._summaries[symbol]
            else:
                # Provide default value
                default = self._default_summary.copy()
                default["symbol"] = symbol
                results[symbol] = default
            if on_progress:
                on_progress(symbol, i + 1, len(symbols))
        return results

    def get_fundamental_summary(self, symbol: str) -> FundamentalSummaryDTO | None:
        """Get fundamental summary for single stock"""
        if symbol in self._summaries:
            return self._summaries[symbol]
        # Provide default value
        default = self._default_summary.copy()
        default["symbol"] = symbol
        return default
