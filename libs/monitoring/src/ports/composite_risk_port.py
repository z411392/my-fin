"""
CompositeRiskPort - Driving Port

實作者: CompositeRiskPolicy
"""

from typing import Protocol


class CompositeRiskPort(Protocol):
    """Driving Port for CompositeRiskPolicy"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
