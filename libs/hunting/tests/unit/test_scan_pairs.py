import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np
from libs.hunting.src.application.queries.scan_pairs import ScanPairsQuery


class TestScanPairsQuery:
    @pytest.fixture
    def query(self):
        return ScanPairsQuery()

    @patch("yfinance.Ticker")
    @patch("libs.hunting.src.application.queries.scan_pairs.scan_pairs")
    @patch("libs.hunting.src.application.queries.scan_pairs.detect_pairs_opportunity")
    def test_execute(self, stub_detect, stub_scan, stub_ticker, query):
        # Stub yfinance Ticker history
        stub_ticker_instance = MagicMock()
        stub_ticker.return_value = stub_ticker_instance

        # Create a stub DataFrame for history
        # Create 100 days of data to satisfy > 60 check
        dates = pd.date_range(start="2023-01-01", periods=100)
        closes = np.random.rand(100) * 100
        stub_hist = pd.DataFrame({"Close": closes}, index=dates)

        stub_ticker_instance.history.return_value = stub_hist

        # Stub scan_pairs calculator
        stub_scan.return_value = [
            {
                "symbol_a": "2330.TW",
                "symbol_b": "2317.TW",
                "correlation": 0.95,
                "cointegration": 0.01,
                "spread_zscore": 2.5,
                "spread_mean": 10.0,
                "spread_std": 2.0,
                "half_life": 5.0,
                "last_spread": 15.0,
            }
        ]

        # Stub detect_pairs_opportunity
        stub_detect.return_value = ("SHORT A / LONG B", "Entry")

        result = query.execute(sector="半導體", market="TW")

        assert "pairs" in result
        assert len(result["pairs"]) == 1
        pair = result["pairs"][0]
        assert pair["symbol_a"] == "2330"  # .TW is removed
        assert pair["symbol_b"] == "2317"  # .TW is removed
        assert pair["signal"] == "SHORT A / LONG B"
