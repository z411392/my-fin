"""
SyncReferenceDataPort - Driving Port

實作者: SyncReferenceDataCommand
"""

from typing import Protocol


class SyncReferenceDataPort(Protocol):
    """Driving Port for SyncReferenceDataCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
