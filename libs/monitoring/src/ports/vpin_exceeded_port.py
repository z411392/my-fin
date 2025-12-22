"""
VpinExceededPort - Driving Port

實作者: VpinExceededPolicy
"""

from typing import Protocol


class VpinExceededPort(Protocol):
    """Driving Port for VpinExceededPolicy"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
