"""Update Supply Chain Mapping Table Command"""

import logging

from injector import inject
from libs.linking.src.ports.update_supply_chain_map_port import (
    UpdateSupplyChainMapPort,
)
from libs.shared.src.dtos.market.supply_chain_command_result_dto import (
    SupplyChainMapUpdateResultDTO,
)


class UpdateSupplyChainMapCommand(UpdateSupplyChainMapPort):
    """Update supply chain mapping table

    Executed quarterly, syncs supply chain mapping data from external sources
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self) -> SupplyChainMapUpdateResultDTO:
        """Execute update supply chain mapping table

        Returns:
            SupplyChainMapUpdateResultDTO: Update result
        """
        # Default supply chain mapping (actual data should come from TEJ or custom database)
        supply_chain_map = [
            {"us_symbol": "NVDA", "tw_symbols": ["3017", "2454", "3034"]},
            {"us_symbol": "AMD", "tw_symbols": ["2454", "3017"]},
            {"us_symbol": "AAPL", "tw_symbols": ["2330", "3711", "2382"]},
            {"us_symbol": "TSLA", "tw_symbols": ["2308", "1590"]},
            {"us_symbol": "INTC", "tw_symbols": ["2330", "2344"]},
        ]

        total_pairs = sum(len(item["tw_symbols"]) for item in supply_chain_map)

        return {
            "source": "default",
            "us_companies": len(supply_chain_map),
            "total_pairs": total_pairs,
            "supply_chain_map": supply_chain_map,
        }
