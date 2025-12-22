"""
UpdateSupplyChainMapPort - Driving Port

實作者: UpdateSupplyChainMapCommand
"""

from typing import Protocol


class UpdateSupplyChainMapPort(Protocol):
    """Driving Port for UpdateSupplyChainMapCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
