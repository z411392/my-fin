"""Unit tests for F-Score and Alpha-Dog related methods"""

import pytest

from libs.shared.src.clients.statementdog.statement_dog_client import StatementDogClient


class TestStatementDogFScore:
    @pytest.fixture
    def client(self):
        return StatementDogClient(headless=True)

    @pytest.fixture
    def sample_data_perfect(self):
        """Mock data representing a perfect F-Score 9 stock with proper YoY data"""
        return {
            "symbol": "2330",
            # Profitability
            "roe-roa": [
                {
                    "name": "ROA",
                    "values": {
                        "2024Q3": 5.0,
                        "2024Q2": 4.8,
                        "2024Q1": 4.5,
                        "2023Q4": 4.2,
                        "2023Q3": 4.0,  # YoY comparison target
                    },
                }
            ],
            "cash-flow-statement": [
                {
                    "name": "Operating Cash Flow",
                    "values": {
                        "2024Q3": 100.0,
                        "2024Q2": 95.0,
                        "2024Q1": 90.0,
                        "2023Q4": 85.0,
                        "2023Q3": 80.0,
                    },
                },
            ],
            "income-statement": [
                {
                    "name": "Net Income",
                    "values": {
                        "2024Q3": 80.0,  # CFO > NI -> +1
                        "2024Q2": 75.0,
                        "2024Q1": 70.0,
                        "2023Q4": 65.0,
                        "2023Q3": 60.0,
                    },
                },
                {
                    "name": "Revenue",  # Add Revenue for Asset Turnover
                    "values": {
                        "2024Q3": 500.0,
                        "2024Q2": 480.0,
                        "2024Q1": 460.0,
                        "2023Q4": 440.0,
                        "2023Q3": 400.0,
                    },
                },
            ],
            # Leverage/Liquidity
            "liabilities-and-equity": [
                {
                    "name": "Long-term Liabilities",
                    "values": {
                        "2024Q3": 100.0,
                        "2024Q2": 110.0,
                        "2024Q1": 120.0,
                        "2023Q4": 130.0,
                        "2023Q3": 150.0,  # YoY: 100 < 150 -> leverage improving
                    },
                },
                {
                    "name": "Total Liabilities",  # Add Total Liabilities
                    "values": {
                        "2024Q3": 400.0,
                        "2024Q2": 410.0,
                        "2024Q1": 420.0,
                        "2023Q4": 430.0,
                        "2023Q3": 450.0,
                    },
                },
                {
                    "name": "Equity",  # Use correct name
                    "values": {
                        "2024Q3": 600.0,
                        "2024Q2": 590.0,
                        "2024Q1": 580.0,
                        "2023Q4": 570.0,
                        "2023Q3": 550.0,
                    },
                },
                {
                    "name": "Current Liabilities",  # Add Current Liabilities
                    "values": {
                        "2024Q3": 200.0,
                        "2024Q2": 210.0,
                        "2024Q1": 220.0,
                        "2023Q4": 230.0,
                        "2023Q3": 250.0,  # 200 < 250 -> liquidity improving
                    },
                },
            ],
            # Efficiency
            "profit-margin": [
                {
                    "name": "Gross Margin",
                    "values": {
                        "2024Q3": 50.0,
                        "2024Q2": 48.0,
                        "2024Q1": 47.0,
                        "2023Q4": 46.0,
                        "2023Q3": 45.0,  # 50 > 45 -> improving
                    },
                }
            ],
        }

    def test_f_score_perfect(self, client, sample_data_perfect):
        """Test perfect F-Score with proper YoY comparison"""
        result = client.get_f_score("2330", sample_data_perfect)
        assert result["total_score"] == 9
        assert result["profitability_score"] == 4
        assert result["leverage_liquidity_score"] == 3
        assert result["efficiency_score"] == 2
        # Verify metrics
        assert result["roa_positive"] is True
        assert result["cfo_positive"] is True
        assert result["roa_improving"] is True  # 5.0 > 4.0 (YoY)
        assert result["accruals_valid"] is True  # CFO 100 > NI 80

    def test_f_score_poor(self, client):
        """Mock data representing a poor F-Score 0 stock"""
        sample_data = {
            "symbol": "0000",
            "roe-roa": [
                {
                    "name": "ROA",
                    "values": {
                        "2024Q3": -1.0,
                        "2024Q2": 0.0,
                        "2024Q1": 1.0,
                        "2023Q4": 1.5,
                        "2023Q3": 2.0,
                    },
                }
            ],
            "cash-flow-statement": [
                {
                    "name": "Operating Cash Flow",
                    "values": {
                        "2024Q3": -50.0,
                        "2024Q2": -40.0,
                        "2024Q1": -30.0,
                        "2023Q4": -20.0,
                        "2023Q3": 10.0,
                    },
                },
            ],
            "income-statement": [
                {
                    "name": "Net Income",
                    "values": {
                        "2024Q3": -10.0,  # CFO -50 < NI -10
                        "2024Q2": -5.0,
                        "2024Q1": 0.0,
                        "2023Q4": 5.0,
                        "2023Q3": 10.0,
                    },
                },
            ],
            "liabilities-and-equity": [
                {
                    "name": "Long-term Liabilities",
                    "values": {
                        "2024Q3": 200.0,
                        "2024Q2": 180.0,
                        "2024Q1": 150.0,
                        "2023Q4": 120.0,
                        "2023Q3": 100.0,  # Debt increased
                    },
                },
                {
                    "name": "Total Assets",
                    "values": {
                        "2024Q3": 1000.0,
                        "2024Q2": 1000.0,
                        "2024Q1": 1000.0,
                        "2023Q4": 1000.0,
                        "2023Q3": 1000.0,
                    },
                },
                {
                    "name": "Capital Stock",
                    "values": {
                        "2024Q3": 250.0,
                        "2024Q2": 230.0,
                        "2024Q1": 210.0,
                        "2023Q4": 200.0,
                        "2023Q3": 200.0,  # New shares issued
                    },
                },
            ],
            "liquidity-ratio": [
                {
                    "name": "Current Ratio",
                    "values": {
                        "2024Q3": 100.0,
                        "2024Q2": 110.0,
                        "2024Q1": 120.0,
                        "2023Q4": 130.0,
                        "2023Q3": 150.0,  # Liquidity deteriorated
                    },
                }
            ],
            "profit-margin": [
                {
                    "name": "Gross Margin",
                    "values": {
                        "2024Q3": 30.0,
                        "2024Q2": 35.0,
                        "2024Q1": 40.0,
                        "2023Q4": 42.0,
                        "2023Q3": 45.0,  # Margin declined
                    },
                }
            ],
            "asset-turnover": [
                {
                    "name": "Asset Turnover",
                    "values": {
                        "2024Q3": 0.2,
                        "2024Q2": 0.25,
                        "2024Q1": 0.3,
                        "2023Q4": 0.35,
                        "2023Q3": 0.4,  # Turnover declined
                    },
                }
            ],
        }
        result = client.get_f_score("0000", sample_data)
        assert result["total_score"] == 0

    def test_contract_liabilities_yoy(self, client):
        """Test contract liabilities with proper YoY comparison"""
        sample_data = {
            "liabilities-and-equity": [
                {
                    "name": "合約負債",
                    "values": {
                        "2024Q3": 150.0,
                        "2024Q2": 140.0,
                        "2024Q1": 130.0,
                        "2023Q4": 120.0,
                        "2023Q3": 100.0,  # YoY comparison: 150 vs 100
                    },
                }
            ]
        }

        result = client.get_contract_liabilities("2330", sample_data)
        assert result["current_value"] == 150.0
        assert result["previous_value"] == 100.0  # Should find 2023Q3
        assert result["yoy"] == pytest.approx(0.5)  # (150-100)/100 = 0.5
        assert result["is_growing"] is True
        assert result["latest_period"] == "2024Q3"
        assert result["compare_period"] == "2023Q3"

    def test_contract_liabilities_fallback(self, client):
        """Test fallback when YoY period not available"""
        sample_data = {
            "liabilities-and-equity": [
                {
                    "name": "合約負債",
                    "values": {
                        "2024Q3": 150.0,
                        "2024Q2": 120.0,
                        # No 2023Q3, should fallback
                    },
                }
            ]
        }

        result = client.get_contract_liabilities("2330", sample_data)
        assert result["current_value"] == 150.0
        assert result["previous_value"] == 120.0  # Fallback to previous period
        assert result["compare_period"] == "2024Q2"


class TestPeriodParsing:
    """Test period parsing helpers"""

    @pytest.fixture
    def client(self):
        return StatementDogClient(headless=True)

    def test_parse_period_key_quarterly(self, client):
        """Test quarterly format parsing"""
        assert client._parse_period_key("2024Q3") == (2024, 3)
        assert client._parse_period_key("2023Q1") == (2023, 1)

    def test_parse_period_key_yearly(self, client):
        """Test yearly format parsing"""
        assert client._parse_period_key("2024") == (2024, 0)
        assert client._parse_period_key("2023") == (2023, 0)

    def test_parse_period_key_monthly(self, client):
        """Test monthly format parsing"""
        assert client._parse_period_key("2024/01") == (2024, 1)
        assert client._parse_period_key("2024-12") == (2024, 12)

    def test_find_yoy_period_quarterly(self, client):
        """Test finding YoY period for quarterly data"""
        periods = ["2024Q3", "2024Q2", "2024Q1", "2023Q4", "2023Q3", "2023Q2"]
        assert client._find_yoy_period("2024Q3", periods) == "2023Q3"
        assert client._find_yoy_period("2024Q1", periods) is None  # 2023Q1 not in list

    def test_find_yoy_period_yearly(self, client):
        """Test finding YoY period for yearly data"""
        periods = ["2024", "2023", "2022"]
        assert client._find_yoy_period("2024", periods) == "2023"

    def test_find_yoy_period_monthly(self, client):
        """Test finding YoY period for monthly data"""
        periods = ["2024/03", "2024/02", "2024/01", "2023/12", "2023/03"]
        assert client._find_yoy_period("2024/03", periods) == "2023/03"


class TestRiverChart:
    """Test River Chart functionality"""

    @pytest.fixture
    def client(self):
        return StatementDogClient(headless=True)

    def test_river_chart_zones(self, client):
        """Test PE/PB zone calculation"""
        sample_data = {
            "pe": [
                {
                    "name": "本益比",
                    "values": {
                        "2024Q3": 8.0,  # Current - below 25th percentile
                        "2024Q2": 10.0,
                        "2024Q1": 12.0,
                        "2023Q4": 14.0,
                        "2023Q3": 16.0,
                        "2023Q2": 18.0,
                        "2023Q1": 20.0,
                    },
                }
            ],
            "pb": [
                {
                    "name": "股價淨值比",
                    "values": {
                        "2024Q3": 3.5,  # Current - above 75th percentile
                        "2024Q2": 3.0,
                        "2024Q1": 2.8,
                        "2023Q4": 2.5,
                        "2023Q3": 2.2,
                        "2023Q2": 2.0,
                        "2023Q1": 1.8,
                    },
                }
            ],
        }

        result = client.get_river_chart_data("2330", sample_data)
        assert result["current_pe"] == 8.0
        assert result["pe_zone"] == "Cheap"  # 8 < 25th percentile
        assert result["current_pb"] == 3.5
        assert result["pb_zone"] == "Expensive"  # 3.5 > 75th percentile
