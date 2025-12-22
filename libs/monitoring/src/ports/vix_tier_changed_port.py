"""
VixTierChangedPort - Driving Port

實作者: VixTierChangedPolicy
"""

from typing import Protocol


class VixTierChangedPort(Protocol):
    """Driving Port for VixTierChangedPolicy"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
