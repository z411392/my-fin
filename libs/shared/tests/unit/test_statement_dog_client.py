"""
StatementDogClient Unit Tests

Tests HTML parsing and numeric conversion logic.
"""

import pytest

from libs.shared.src.clients.statementdog.statement_dog_client import StatementDogClient


class TestParseValue:
    """Test _parse_value method"""

    @pytest.fixture
    def client(self) -> StatementDogClient:
        """Create test client"""
        return StatementDogClient()

    def test_parse_integer(self, client: StatementDogClient) -> None:
        """Test integer parsing"""
        result = client._parse_value("123")
        assert result == 123.0

    def test_parse_float(self, client: StatementDogClient) -> None:
        """Test float parsing"""
        result = client._parse_value("45.67")
        assert result == 45.67

    def test_parse_negative(self, client: StatementDogClient) -> None:
        """Test negative number parsing"""
        result = client._parse_value("-12.34")
        assert result == -12.34

    def test_parse_percentage(self, client: StatementDogClient) -> None:
        """Test percentage parsing (remove % symbol)"""
        result = client._parse_value("25.5%")
        assert result == 25.5

    def test_parse_with_comma(self, client: StatementDogClient) -> None:
        """Test comma separated value parsing"""
        result = client._parse_value("1,234,567")
        assert result == 1234567.0

    def test_parse_dash_returns_none(self, client: StatementDogClient) -> None:
        """Test dash returns None"""
        result = client._parse_value("-")
        assert result is None

    def test_parse_na_returns_none(self, client: StatementDogClient) -> None:
        """Test N/A returns None"""
        result = client._parse_value("N/A")
        assert result is None

    def test_parse_double_dash_returns_none(self, client: StatementDogClient) -> None:
        """Test double dash returns None"""
        result = client._parse_value("--")
        assert result is None

    def test_parse_empty_string_returns_none(self, client: StatementDogClient) -> None:
        """Test empty string returns None"""
        result = client._parse_value("")
        assert result is None

    def test_parse_text_returns_string(self, client: StatementDogClient) -> None:
        """Test non-numeric text returns original string"""
        result = client._parse_value("良好")
        assert result == "良好"


class TestParseTable:
    """Test _parse_table method"""

    @pytest.fixture
    def client(self) -> StatementDogClient:
        """Create test client"""
        return StatementDogClient()

    def test_parse_simple_table(self, client: StatementDogClient) -> None:
        """Test simple table parsing"""
        html = """
        <html>
        <body>
        <table>
            <tr><th>指標</th><th>2024Q1</th><th>2024Q2</th></tr>
            <tr><td>營收</td><td>1,000</td><td>1,200</td></tr>
            <tr><td>毛利率</td><td>45.5%</td><td>46.2%</td></tr>
        </table>
        </body>
        </html>
        """
        result = client._parse_table(html)

        assert len(result) == 2

        assert result[0]["name"] == "營收"
        assert result[0]["values"]["2024Q1"] == 1000.0
        assert result[0]["values"]["2024Q2"] == 1200.0

        assert result[1]["name"] == "毛利率"
        assert result[1]["values"]["2024Q1"] == 45.5
        assert result[1]["values"]["2024Q2"] == 46.2

    def test_parse_table_with_missing_values(self, client: StatementDogClient) -> None:
        """Test table parsing with missing values"""
        html = """
        <html>
        <body>
        <table>
            <tr><th>指標</th><th>2024Q1</th><th>2024Q2</th></tr>
            <tr><td>ROE</td><td>15.2%</td><td>-</td></tr>
        </table>
        </body>
        </html>
        """
        result = client._parse_table(html)

        assert len(result) == 1
        assert result[0]["name"] == "ROE"
        assert result[0]["values"]["2024Q1"] == 15.2
        assert result[0]["values"]["2024Q2"] is None

    def test_parse_empty_table(self, client: StatementDogClient) -> None:
        """Test empty table parsing"""
        html = """
        <html>
        <body>
        <table>
            <tr><th>指標</th></tr>
        </table>
        </body>
        </html>
        """
        result = client._parse_table(html)
        assert result == []

    def test_parse_no_table(self, client: StatementDogClient) -> None:
        """Test HTML with no table"""
        html = """
        <html>
        <body>
        <div>No table here</div>
        </body>
        </html>
        """
        result = client._parse_table(html)
        assert result == []

    def test_parse_table_with_text_values(self, client: StatementDogClient) -> None:
        """Test table with text values"""
        html = """
        <html>
        <body>
        <table>
            <tr><th>指標</th><th>評價</th></tr>
            <tr><td>財務體質</td><td>良好</td></tr>
        </table>
        </body>
        </html>
        """
        result = client._parse_table(html)

        assert len(result) == 1
        assert result[0]["name"] == "財務體質"
        assert result[0]["values"]["評價"] == "良好"


class TestClientConfiguration:
    """Test client configuration"""

    def test_default_configuration(self) -> None:
        """Test default configuration"""
        client = StatementDogClient()
        assert client._headless is True
        assert client._delay == 0.3

    def test_custom_configuration(self) -> None:
        """Test custom configuration"""
        client = StatementDogClient(headless=False, delay_seconds=2.5)
        assert client._headless is False
        assert client._delay == 2.5

    def test_metrics_defined(self) -> None:
        """Test metrics list is defined"""
        assert len(StatementDogClient.METRICS) > 0
        assert "monthly-revenue" in StatementDogClient.METRICS
        assert "eps" in StatementDogClient.METRICS
        assert "roe-roa" in StatementDogClient.METRICS

    def test_base_url_defined(self) -> None:
        """Test base URL is defined"""
        assert StatementDogClient.BASE_URL == "https://statementdog.com/analysis"
