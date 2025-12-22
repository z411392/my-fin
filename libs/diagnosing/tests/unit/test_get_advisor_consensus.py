"""GetAdvisorConsensusQuery 單元測試"""

from libs.diagnosing.src.application.queries.get_advisor_consensus import (
    GetAdvisorConsensusQuery,
)


class TestGetAdvisorConsensusQuery:
    """測試 GetAdvisorConsensusQuery"""

    def test_execute_returns_consensus(self) -> None:
        """應返回共識結果"""
        query = GetAdvisorConsensusQuery()
        result = query.execute(symbol="2330")

        assert "symbol" in result
        assert "advisors" in result
        assert "consensus" in result
        assert "signal" in result
        assert "action" in result
        assert result["symbol"] == "2330"

    def test_has_four_advisors(self) -> None:
        """應有四個顧問"""
        query = GetAdvisorConsensusQuery()
        result = query.execute(symbol="2330")

        assert len(result["advisors"]) == 4

    def test_each_advisor_has_required_fields(self) -> None:
        """每個顧問應有必要欄位"""
        query = GetAdvisorConsensusQuery()
        result = query.execute(symbol="2330")

        for advisor in result["advisors"]:
            assert "name" in advisor
            assert "focus" in advisor
            assert "opinion" in advisor
            assert "confidence" in advisor
            assert "reasoning" in advisor

    def test_opinion_is_valid(self) -> None:
        """意見應為有效值"""
        query = GetAdvisorConsensusQuery()
        result = query.execute(symbol="2330")

        valid_opinions = ["進攻", "防守", "中立"]
        for advisor in result["advisors"]:
            assert advisor["opinion"] in valid_opinions

    def test_signal_is_emoji(self) -> None:
        """信號應為 emoji"""
        query = GetAdvisorConsensusQuery()
        result = query.execute(symbol="2330")

        valid_signals = ["🟢🟢", "🟢", "🟡", "🔴", "🔴🔴"]
        assert result["signal"] in valid_signals

    def test_confidence_in_range(self) -> None:
        """信心應在 0-1 範圍內"""
        query = GetAdvisorConsensusQuery()
        result = query.execute(symbol="2330")

        assert 0 <= result["confidence"] <= 1
