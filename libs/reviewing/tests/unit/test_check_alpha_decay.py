import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from libs.reviewing.src.application.queries.check_alpha_decay import (
    CheckAlphaDecayQuery,
)


class TestCheckAlphaDecayQuery:
    @pytest.fixture
    def fake_price_provider(self):
        return MagicMock()

    @pytest.fixture
    def query(self, fake_price_provider):
        return CheckAlphaDecayQuery(fake_price_provider)

    @patch(
        "libs.reviewing.src.application.queries.check_alpha_decay.interpret_alpha_decay"
    )
    @patch("libs.reviewing.src.application.queries.check_alpha_decay.check_alpha_decay")
    def test_execute_with_initial_alpha(
        self, stub_check, stub_interpret, query, fake_price_provider
    ):
        # Fake price
        fake_price_provider.get_current_price.return_value = Decimal("550.0")

        # Stub calculator
        stub_check.return_value = ("HOLD", 0.8)
        stub_interpret.return_value = ("正常", "續抱")

        result = query.execute(
            symbol="2330",
            entry_price=500.0,
            target_price=600.0,
            initial_alpha=0.2,
        )

        assert result["symbol"] == "2330"
        assert result["current_price"] == 550.0
        assert result["remaining"] == 0.8
        assert result["status"] == "正常"

        # Verify initial_alpha passed correctly
        stub_check.assert_called_with(
            initial_alpha=0.2,
            target_price=600.0,
            current_price=550.0,
            entry_price=500.0,
        )

    @patch(
        "libs.reviewing.src.application.queries.check_alpha_decay.interpret_alpha_decay"
    )
    @patch("libs.reviewing.src.application.queries.check_alpha_decay.check_alpha_decay")
    def test_execute_without_initial_alpha(
        self, stub_check, stub_interpret, query, fake_price_provider
    ):
        fake_price_provider.get_current_price.return_value = Decimal("550.0")

        stub_check.return_value = ("HOLD", 0.5)
        stub_interpret.return_value = ("正常", "續抱")

        result = query.execute(
            symbol="2330",
            entry_price=500.0,
            target_price=600.0,
            initial_alpha=None,
        )

        # Expected initial alpha = (600 - 500) / 500 = 0.2
        assert result["initial_alpha"] == 0.2
        stub_check.assert_called_with(
            initial_alpha=0.2,
            target_price=600.0,
            current_price=550.0,
            entry_price=500.0,
        )

    def test_execute_zero_price(self, query, fake_price_provider):
        fake_price_provider.get_current_price.return_value = Decimal("0.0")

        result = query.execute(symbol="2330", entry_price=500.0, target_price=600.0)

        assert result["current_price"] == 0.0
        assert result["decision"] == "ABORT"
