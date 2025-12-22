"""UpdateSupplyChainMapCommand Unit Tests"""

from libs.linking.src.application.commands.update_supply_chain_map import (
    UpdateSupplyChainMapCommand,
)


class TestUpdateSupplyChainMapCommand:
    """Test UpdateSupplyChainMapCommand"""

    def test_execute_returns_map_data(self) -> None:
        """Should return supply chain mapping data"""
        command = UpdateSupplyChainMapCommand()
        result = command.execute()

        assert "source" in result
        assert "us_companies" in result
        assert "total_pairs" in result
        assert "supply_chain_map" in result

    def test_map_structure(self) -> None:
        """Supply chain mapping structure should be correct"""
        command = UpdateSupplyChainMapCommand()
        result = command.execute()

        supply_chain_map = result["supply_chain_map"]
        assert len(supply_chain_map) > 0

        for item in supply_chain_map:
            assert "us_symbol" in item
            assert "tw_symbols" in item
            assert isinstance(item["tw_symbols"], list)

    def test_total_pairs_calculation(self) -> None:
        """Total pairs calculation should be correct"""
        command = UpdateSupplyChainMapCommand()
        result = command.execute()

        expected_total = sum(
            len(item["tw_symbols"]) for item in result["supply_chain_map"]
        )
        assert result["total_pairs"] == expected_total
