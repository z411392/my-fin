"""GetDiagnosisQuery 測試"""

import pytest
from unittest.mock import MagicMock

from libs.diagnosing.src.application.queries.get_diagnosis import GetDiagnosisQuery


@pytest.fixture
def fake_financial_adapter():
    """提供 Fake Financial Adapter 給測試"""
    adapter = MagicMock()
    adapter.get_financial_info.return_value = {
        "name": "台積電",
        "price": 600.0,
        "roe": 25.0,
        "pe_ratio": 20.0,
        "revenue_growth": 15.0,
    }
    return adapter


class TestGetDiagnosis:
    """GetDiagnosisQuery 測試"""

    def test_returns_diagnosis_for_symbol(self, fake_financial_adapter) -> None:
        """應返回診斷結果"""
        query = GetDiagnosisQuery(financial_adapter=fake_financial_adapter)
        result = query.execute("2330")

        assert "symbol" in result
        assert result["symbol"] == "2330"
        assert "verdict" in result
        assert "rationale" in result

    def test_returns_fundamental_grade(self, fake_financial_adapter) -> None:
        """應返回基本面評級"""
        query = GetDiagnosisQuery(financial_adapter=fake_financial_adapter)
        result = query.execute("2330")

        assert "fundamental_grade" in result
        assert result["fundamental_grade"] in ["A", "B", "C", "D", "F", "N/A"]

    def test_returns_verdict(self, fake_financial_adapter) -> None:
        """應返回判定結果"""
        query = GetDiagnosisQuery(financial_adapter=fake_financial_adapter)
        result = query.execute("2330")

        assert "verdict" in result
        assert result["verdict"] in ["HOLD", "OBSERVE", "REDUCE", "EXIT"]

    def test_returns_advisor_consensus(self, fake_financial_adapter) -> None:
        """應返回四顧問共識"""
        query = GetDiagnosisQuery(financial_adapter=fake_financial_adapter)
        result = query.execute("2330")

        assert "advisor_consensus" in result
        assert result["advisor_consensus"] in ["進攻", "分歧", "防守"]
