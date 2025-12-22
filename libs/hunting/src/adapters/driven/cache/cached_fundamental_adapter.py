"""Cached StatementDog Fundamental Adapter

Wrapper pattern: wraps the real StatementDogFundamentalAdapter
Event-driven cache invalidation: based on quarterly earnings release dates
Each symbol is stored separately in data/fundamental/{symbol}.json
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Callable

from libs.hunting.src.ports.i_fundamental_data_port import IFundamentalDataPort
from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)
from libs.shared.src.dtos.statementdog.fundamental_summary_map_dto import (
    FundamentalSummaryMap,
)
from libs.shared.src.dtos.event.calendar_raw_data_dto import CalendarRawDataDTO


class CachedFundamentalAdapter(IFundamentalDataPort):
    """StatementDog adapter with event-driven cache

    - Cache stored in data/fundamental/{symbol}.json (one file per symbol)
    - Invalidation based on quarterly earnings events in economic_calendar.json
    """

    def __init__(
        self,
        inner: IFundamentalDataPort,
        cache_dir: Path | None = None,
        calendar_path: Path | None = None,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._inner = inner
        self._cache_dir = cache_dir or Path("data/fundamental")
        self._calendar_path = calendar_path or Path("data/economic_calendar.json")
        self._memory_cache: dict[str, FundamentalSummaryDTO] = {}

    def _get_symbol_cache_path(self, market: str, symbol: str) -> Path:
        """Get cache file path for a single symbol"""
        # Remove .TW suffix for filename (e.g., 1101.TW -> 1101.json)
        filename = symbol.replace(".TW", "").replace(".TWO", "") + ".json"
        return self._cache_dir / filename

    def _load_calendar(self) -> CalendarRawDataDTO:
        """Load economic calendar"""
        if not self._calendar_path.exists():
            return {}
        return json.loads(self._calendar_path.read_text(encoding="utf-8"))

    def _get_next_earnings_date(self, market: str) -> str | None:
        """Get next quarterly earnings release date

        Args:
            market: 'tw' or 'us'

        Returns:
            Date in YYYY-MM-DD format, or None
        """
        calendar = self._load_calendar()
        today = datetime.now().strftime("%Y-%m-%d")
        year = datetime.now().year

        # Try events for current year and next year
        for y in [year, year + 1]:
            key = f"earnings_{market}_{y}"
            dates = calendar.get(key, [])
            for date_str in dates:
                if date_str > today:
                    return date_str

        return None

    def _is_symbol_cache_valid(self, market: str, symbol: str) -> bool:
        """Check if cache for a single symbol is still valid"""
        cache_path = self._get_symbol_cache_path(market, symbol)
        if not cache_path.exists():
            return False

        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            invalidate_after = cache.get("invalidate_after")
            if not invalidate_after:
                return False

            today = datetime.now().strftime("%Y-%m-%d")
            return today < invalidate_after
        except Exception as e:
            self._logger.warning(f"Failed to read {symbol} cache: {e}")
            return False

    def _load_symbol_cache(
        self, market: str, symbol: str
    ) -> FundamentalSummaryDTO | None:
        """Load cache for a single symbol"""
        cache_path = self._get_symbol_cache_path(market, symbol)
        if not cache_path.exists():
            return None

        try:
            cache = json.loads(cache_path.read_text(encoding="utf-8"))
            return cache.get("data")
        except Exception as e:
            self._logger.warning(f"Failed to read {symbol} cache: {e}")
            return None

    def _save_symbol_cache(
        self, market: str, symbol: str, data: FundamentalSummaryDTO
    ) -> None:
        """Save cache for a single symbol"""
        cache_path = self._get_symbol_cache_path(market, symbol)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        next_date = self._get_next_earnings_date(market)
        cache = {
            "created_at": datetime.now().isoformat(),
            "invalidate_after": next_date,
            "market": market,
            "symbol": symbol,
            "data": data,
        }

        cache_path.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _detect_market(self, symbols: list[str]) -> str:
        """Detect market from stock symbols"""
        if not symbols:
            return "tw"
        # TW stocks are usually numeric, US stocks are alphabetic
        first = symbols[0]
        return "us" if first.isalpha() else "tw"

    def batch_get_f_score(
        self,
        symbols: list[str],
        on_progress: Callable[[str, int, int], None] | None = None,
    ) -> FundamentalSummaryMap:
        """Batch get F-Score (with cache)"""
        return self._inner.batch_get_f_score(symbols, on_progress)

    def get_fundamental_summary(self, symbol: str) -> FundamentalSummaryDTO | None:
        """Get fundamental summary for a single stock (with cache)"""
        # Check memory cache first
        if symbol in self._memory_cache:
            return self._memory_cache[symbol]

        # Check file cache
        market = "us" if symbol.isalpha() else "tw"
        if self._is_symbol_cache_valid(market, symbol):
            cached = self._load_symbol_cache(market, symbol)
            if cached:
                self._memory_cache[symbol] = cached
                return cached

        # Cache miss, call original adapter
        result = self._inner.get_fundamental_summary(symbol)
        if result:
            self._memory_cache[symbol] = result
            self._save_symbol_cache(market, symbol, result)
        return result

    async def batch_get_summaries_async(
        self,
        symbols: list[str],
        max_concurrent: int = 5,
        on_progress: Callable[[str, FundamentalSummaryDTO], None] | None = None,
    ) -> FundamentalSummaryMap:
        """Batch async get fundamental summaries for multiple stocks (with incremental cache)

        Logic:
        1. Check each symbol's cache validity individually
        2. Separate cache hits from misses
        3. Only fetch missing symbols
        4. Update individual cache file after each fetch
        """
        market = self._detect_market(symbols)
        cached_data: dict[str, FundamentalSummaryDTO] = {}
        missing_symbols: list[str] = []

        # Check cache for each symbol individually
        for symbol in symbols:
            if self._is_symbol_cache_valid(market, symbol):
                data = self._load_symbol_cache(market, symbol)
                if data:
                    cached_data[symbol] = data
                else:
                    missing_symbols.append(symbol)
            else:
                missing_symbols.append(symbol)

        self._logger.info(
            f"Cache hit: {len(cached_data)}/{len(symbols)}, need to fetch: {len(missing_symbols)}"
        )

        # Call on_progress for cached items
        for symbol in cached_data:
            if on_progress:
                on_progress(symbol, cached_data[symbol])

        def incremental_callback(symbol: str, data: FundamentalSummaryDTO) -> None:
            """Update individual cache after each fetch"""
            # Save to individual file
            self._save_symbol_cache(market, symbol, data)
            # Update accumulated data
            cached_data[symbol] = data
            # Call original callback
            if on_progress:
                on_progress(symbol, data)

        # Fetch missing symbols (using incremental callback)
        if missing_symbols:
            await self._inner.batch_get_summaries_async(
                symbols=missing_symbols,
                max_concurrent=max_concurrent,
                on_progress=incremental_callback,
            )

        # Return complete results (only requested symbols)
        return {s: cached_data[s] for s in symbols if s in cached_data}
