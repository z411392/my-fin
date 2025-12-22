"""Test IVOL × F-Score Matrix"""

from libs.hunting.src.domain.services.quality_filters import (
    apply_ivol_fscore_matrix,
    get_ivol_percentile,
)


class TestIvolFscoreMatrix:
    """IVOL × F-Score 決策矩陣測試"""

    def test_high_ivol_high_fscore_is_opportunity(self):
        """高 IVOL + 高 F-Score = 錯殺機會"""
        passed, decision_type, _reason = apply_ivol_fscore_matrix(
            ivol=0.05, ivol_percentile=85, f_score=8
        )
        assert passed is True
        assert decision_type == "OPPORTUNITY"

    def test_high_ivol_low_fscore_is_rejected(self):
        """高 IVOL + 低 F-Score = 彩票剔除"""
        passed, decision_type, _reason = apply_ivol_fscore_matrix(
            ivol=0.05, ivol_percentile=85, f_score=3
        )
        assert passed is False
        assert decision_type == "REJECT"

    def test_mid_ivol_mid_fscore_is_standard(self):
        """中 IVOL + 中 F-Score = 標準候選"""
        passed, decision_type, _reason = apply_ivol_fscore_matrix(
            ivol=0.025, ivol_percentile=60, f_score=6
        )
        assert passed is True
        assert decision_type == "STANDARD"

    def test_low_ivol_high_fscore_is_defensive(self):
        """低 IVOL + 高 F-Score = 防禦型"""
        passed, decision_type, _reason = apply_ivol_fscore_matrix(
            ivol=0.01, ivol_percentile=20, f_score=7
        )
        assert passed is True
        assert decision_type == "DEFENSIVE"

    def test_none_fscore_high_ivol_rejected(self):
        """無 F-Score + 高 IVOL = 傳統剔除"""
        passed, decision_type, _reason = apply_ivol_fscore_matrix(
            ivol=0.05, ivol_percentile=85, f_score=None
        )
        assert passed is False
        assert decision_type == "REJECT"

    def test_none_fscore_mid_ivol_passes(self):
        """無 F-Score + 中 IVOL = 通過"""
        passed, decision_type, _reason = apply_ivol_fscore_matrix(
            ivol=0.025, ivol_percentile=60, f_score=None
        )
        assert passed is True
        assert decision_type == "STANDARD"


class TestIvolPercentile:
    """IVOL 百分位估算測試"""

    def test_low_ivol_returns_low_percentile(self):
        """低 IVOL 應該返回低百分位"""
        pct = get_ivol_percentile(0.01)
        assert pct <= 30

    def test_high_ivol_returns_high_percentile(self):
        """高 IVOL 應該返回高百分位"""
        pct = get_ivol_percentile(0.05)
        assert pct >= 80

    def test_with_history_uses_actual_rank(self):
        """有歷史資料時使用真實排名"""
        history = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11]
        pct = get_ivol_percentile(0.06, history)
        # 0.06 在 11 個值中排名第 6，百分位 = 6/11 ≈ 54.5%
        assert 50 <= pct <= 60
