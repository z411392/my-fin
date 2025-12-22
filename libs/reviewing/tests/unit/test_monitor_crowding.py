import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from libs.reviewing.src.application.queries.monitor_crowding import (
    MonitorCrowdingQuery,
)


class TestMonitorCrowdingQuery:
    @pytest.fixture
    def fake_stock_data(self):
        return MagicMock()

    @pytest.fixture
    def query(self, fake_stock_data):
        return MonitorCrowdingQuery(fake_stock_data)

    @patch("libs.reviewing.src.application.queries.monitor_crowding.assess_crowding")
    @patch(
        "libs.reviewing.src.application.queries.monitor_crowding.calculate_days_to_cover"
    )
    @patch(
        "libs.reviewing.src.application.queries.monitor_crowding.calculate_pairwise_correlation"
    )
    def test_execute(self, stub_corr, stub_days, stub_assess, query, fake_stock_data):
        # Fake data
        fake_stock_data.get_returns_matrix.return_value = np.array(
            [[0.01, 0.02], [0.01, 0.02]]
        )
        fake_stock_data.get_average_daily_volume.return_value = 1000000

        # Stub calculator returns
        stub_corr.return_value = 0.8
        stub_days.return_value = 2.5
        stub_assess.return_value = {
            "status": "擁擠",
            "action": "減碼",
            "pairwise_correlation": 0.8,
            "days_to_cover": 2.5,
            "dsr": 0.92,
            "alpha_half_life": 8.0,
        }

        result = query.execute(strategy="test_strategy")

        assert result["strategy"] == "test_strategy"
        assert result["status"] == "擁擠"
        assert result["pairwise_correlation"] == 0.8

    def test_execute_no_data(self, query, fake_stock_data):
        # Fake empty returns
        fake_stock_data.get_returns_matrix.return_value = np.array([])

        result = query.execute(strategy="test_strategy")

        assert result["status"] == "資料不足"
        assert result["action"] == "無法評估"
