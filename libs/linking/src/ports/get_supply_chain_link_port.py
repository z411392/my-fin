"""供應鏈傳導分析 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.strategy.supply_chain_link_result_dto import (
    SupplyChainLinkResultDTO,
)


class GetSupplyChainLinkPort(Protocol):
    """供應鏈傳導分析

    CLI Entry: fin link
    """

    def execute(
        self, us_symbol: str, tw_symbol: str, period: str = "6mo"
    ) -> SupplyChainLinkResultDTO:
        """分析供應鏈傳導"""
        ...
