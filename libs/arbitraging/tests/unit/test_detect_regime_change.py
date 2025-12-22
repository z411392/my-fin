"""DetectRegimeChangeCommand 單元測試"""

from unittest.mock import patch
import numpy as np

from libs.arbitraging.src.application.commands.detect_regime_change import (
    DetectRegimeChangeCommand,
)


class TestDetectRegimeChangeCommand:
    """測試 DetectRegimeChangeCommand"""

    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.DetectRegimeChangeCommand._get_real_returns"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.calculate_hurst_exponent"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.hmm_regime_simple"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.calculate_pca_cosine_similarity"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.detect_structural_break"
    )
    def test_execute_returns_regime_data(
        self, stub_break, stub_pca, stub_hmm, stub_hurst, stub_get_returns
    ) -> None:
        """應返回體制識別數據"""
        # Stub data
        stub_get_returns.return_value = (
            np.zeros(200),
            "Stub Source",
        )  # returns, data_source
        stub_hurst.return_value = 0.6
        stub_hmm.return_value = (0, 0.8)  # state, bull_prob
        stub_pca.return_value = 0.9
        stub_break.return_value = False

        command = DetectRegimeChangeCommand()
        result = command.execute(lookback=120)

        assert "hurst" in result
        assert result["hurst"] == 0.6
        assert result["regime"] == "趨勢牛市"  # 0.6 + 0.8 + 0.9 -> High Bull

    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.DetectRegimeChangeCommand._get_real_returns"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.calculate_hurst_exponent"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.hmm_regime_simple"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.calculate_pca_cosine_similarity"
    )
    @patch(
        "libs.arbitraging.src.application.commands.detect_regime_change.detect_structural_break"
    )
    def test_kelly_factor_mapping(
        self, stub_break, stub_pca, stub_hmm, stub_hurst, stub_get_returns
    ) -> None:
        """Kelly factor 應根據體制正確映射 (Stub)"""
        # Test Case: Extreme Bear (Panic)
        stub_get_returns.return_value = (np.zeros(200), "Stub")
        stub_hurst.return_value = 0.3  # Mean Reverting
        stub_hmm.return_value = (1, 0.1)  # Bear, 10% Bull
        stub_pca.return_value = 0.2  # Structural Break
        stub_break.return_value = True

        command = DetectRegimeChangeCommand()
        result = command.execute()

        # 這種情況應該是結構斷裂或恐慌
        assert result["structural_break"] is True
        assert result["kelly_factor"] == 0.0
