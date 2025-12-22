"""Synthetic Index Return Calculator

Domain Service: Calculates equal-weighted return of synthetic sector index.
"""

import logging
import numpy as np
import yfinance as yf


def get_synthetic_sector_benchmark(
    proxies: list[str], suffix: str = ".TW"
) -> np.ndarray:
    """Calculate synthetic index return (equal-weighted average)

    Args:
        proxies: List of proxy stock symbols
        suffix: Symbol suffix (e.g., ".TW")

    Returns:
        np.ndarray: Synthetic index daily return series
    """
    if not proxies:
        return np.array([])

    symbols = [f"{p}{suffix}" for p in proxies]

    try:
        # Suppress yfinance error messages
        yf_logger = logging.getLogger("yfinance")
        original_level = yf_logger.level
        yf_logger.setLevel(logging.CRITICAL)

        try:
            data = yf.download(symbols, period="1y", progress=False)["Close"]
        finally:
            yf_logger.setLevel(original_level)

        if data.empty:
            return np.array([])

        # Use fill_method=None to avoid FutureWarning
        returns = data.pct_change(fill_method=None).dropna()

        if returns.empty:
            return np.array([])

        # Equal-weighted average, using safe nanmean calculation
        def safe_nanmean(row: np.ndarray) -> float:
            """Safe nanmean calculation to avoid empty slice warnings"""
            valid = row[~np.isnan(row)]
            return float(np.mean(valid)) if len(valid) > 0 else 0.0

        return returns.apply(safe_nanmean, axis=1).values
    except Exception:
        return np.array([])
