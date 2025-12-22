"""Test Portfolio Optimization Modules (Phase C-E)"""

import pytest
import numpy as np

from libs.hunting.src.domain.services.sector_constraint import (
    apply_sector_cap,
    get_sector_exposure,
)
from libs.hunting.src.domain.services.correlation_filter import (
    filter_high_correlation,
    calculate_pairwise_correlation,
)
from libs.hunting.src.domain.services.atr_trailing_stop import (
    calculate_atr,
    calculate_trailing_stop,
    should_trigger_trailing_stop,
)
from libs.hunting.src.domain.services.time_stop import (
    should_exit_by_time,
    calculate_alpha_contribution,
)
from libs.hunting.src.domain.services.regime_weight import (
    get_factor_weights,
)
from libs.hunting.src.domain.services.hrp_allocator import (
    hrp_allocate,
    inverse_volatility_weights,
)


class TestSectorConstraint:
    """板塊限額測試"""

    def test_apply_sector_cap_limits_concentration(self):
        """板塊限額應限制集中度"""
        candidates = [
            {"symbol": "A", "sector": "Tech", "momentum": 10},
            {"symbol": "B", "sector": "Tech", "momentum": 9},
            {"symbol": "C", "sector": "Tech", "momentum": 8},
            {"symbol": "D", "sector": "Tech", "momentum": 7},
            {"symbol": "E", "sector": "Fin", "momentum": 6},
        ]
        # 30% cap = max 1.5 stocks per sector → 1 stock
        filtered, stats = apply_sector_cap(candidates, cap_pct=0.30)
        assert len([c for c in filtered if c["sector"] == "Tech"]) <= 2

    def test_get_sector_exposure(self):
        """板塊曝險計算"""
        candidates = [
            {"symbol": "A", "sector": "Tech"},
            {"symbol": "B", "sector": "Tech"},
            {"symbol": "C", "sector": "Fin"},
        ]
        exposure = get_sector_exposure(candidates)
        assert exposure["Tech"] == pytest.approx(66.7, abs=0.1)
        assert exposure["Fin"] == pytest.approx(33.3, abs=0.1)


class TestCorrelationFilter:
    """相關性過濾測試"""

    def test_calculate_pairwise_correlation(self):
        """計算相關係數"""
        a = np.random.randn(100)
        b = a + np.random.randn(100) * 0.1  # 高相關
        corr = calculate_pairwise_correlation(a, b)
        assert corr is not None
        assert corr > 0.8

    def test_filter_removes_lower_momentum(self):
        """高相關時應剔除動能較低者"""
        candidates = [
            {"symbol": "A", "momentum": 10},
            {"symbol": "B", "momentum": 5},
        ]
        base = np.random.randn(100)
        returns_data = {
            "A": base,
            "B": base + np.random.randn(100) * 0.05,  # 高相關
        }
        filtered, pairs = filter_high_correlation(
            candidates, returns_data, threshold=0.8
        )
        # B 應該被剔除
        assert len(filtered) == 1
        assert filtered[0]["symbol"] == "A"


class TestAtrTrailingStop:
    """ATR 移動停損測試"""

    def test_calculate_atr(self):
        """ATR 計算"""
        high = np.array([102, 104, 103, 105, 106])
        low = np.array([98, 99, 100, 101, 102])
        close = np.array([100, 103, 101, 104, 105])
        atr = calculate_atr(high, low, close, window=3)
        assert atr > 0

    def test_trailing_stop_calculation(self):
        """移動停損計算"""
        stop = calculate_trailing_stop(max_price=100, atr=2.5, multiplier=2)
        assert stop == 95.0

    def test_trigger_detection(self):
        """觸發判斷"""
        triggered, stop, buffer = should_trigger_trailing_stop(
            current_price=94, max_price=100, atr=2.5, multiplier=2
        )
        assert triggered is True
        assert stop == 95.0


class TestTimeStop:
    """時間止損測試"""

    def test_exit_on_time_and_negative_alpha(self):
        """持有超時且 Alpha 負值應出場"""
        should_exit, _reason = should_exit_by_time(
            holding_days=12, alpha_contribution=-0.02
        )
        assert should_exit is True

    def test_continue_if_alpha_positive(self):
        """Alpha 正值應繼續持有"""
        should_exit, _reason = should_exit_by_time(
            holding_days=12, alpha_contribution=0.05
        )
        assert should_exit is False

    def test_forced_exit_after_max_days(self):
        """超過最大天數強制出場"""
        should_exit, _reason = should_exit_by_time(
            holding_days=21, alpha_contribution=0.10
        )
        assert should_exit is True

    def test_alpha_contribution_calculation(self):
        """Alpha 貢獻計算"""
        alpha = calculate_alpha_contribution(
            entry_price=100, current_price=110, benchmark_return=0.05
        )
        assert alpha == pytest.approx(0.05, abs=0.01)  # 10% - 5% = 5%


class TestRegimeWeight:
    """體制權重測試"""

    def test_bull_regime_weights(self):
        """牛市應加重趨勢"""
        weights = get_factor_weights(hmm_state=1, bull_prob=0.8)
        assert weights["trend"] == 0.60
        assert weights["regime"] == "BULL"

    def test_bear_regime_weights(self):
        """熊市應零趨勢權重"""
        weights = get_factor_weights(hmm_state=0, bull_prob=0.2)
        assert weights["trend"] == 0.00
        assert weights["regime"] == "BEAR"

    def test_neutral_regime_weights(self):
        """震盪應均衡權重"""
        weights = get_factor_weights(hmm_state=0, bull_prob=0.5)
        assert weights["trend"] == 0.30
        assert weights["regime"] == "NEUTRAL"


class TestHrpAllocator:
    """HRP 配置測試"""

    def test_single_asset_returns_full_weight(self):
        """單一資產應返回 100% 權重"""
        weights = hrp_allocate(np.random.randn(50, 1), ["AAPL"])
        assert weights["AAPL"] == 1.0

    def test_weights_sum_to_one(self):
        """權重總和應為 1"""
        returns = np.random.randn(100, 4)
        symbols = ["A", "B", "C", "D"]
        weights = hrp_allocate(returns, symbols)
        assert sum(weights.values()) == pytest.approx(1.0, abs=0.01)

    def test_inverse_volatility_weights(self):
        """波動率倒數權重"""
        returns = np.column_stack(
            [
                np.random.randn(100) * 0.01,  # 低波動
                np.random.randn(100) * 0.05,  # 高波動
            ]
        )
        weights = inverse_volatility_weights(returns, ["LOW", "HIGH"])
        assert weights["LOW"] > weights["HIGH"]  # 低波動應有較高權重
