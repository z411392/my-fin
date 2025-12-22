"""Sync Data Port — Driving Port for maintaining orchestration"""

from typing import Protocol


class SyncDataPort(Protocol):
    """同步資料的 Driving Port"""

    def execute(self, force: bool = False) -> None:
        """執行資料同步"""
        ...
