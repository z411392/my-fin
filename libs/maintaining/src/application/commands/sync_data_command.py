"""Sync Data Command — Orchestration Command

Orchestrates multiple libs for data synchronization
"""

import logging

from injector import inject

from libs.arbitraging.src.ports.sync_catalog_port import SyncCatalogPort
from libs.arbitraging.src.ports.sync_reference_data_port import SyncReferenceDataPort
from libs.maintaining.src.ports.sync_data_port import SyncDataPort


class SyncDataCommand(SyncDataPort):
    """Data sync orchestration command

    Syncs the following files:
    - data/catalog.json: TW/US stock list + industry proxy stocks + ETF mapping
    - data/economic_calendar.json: Economic event calendar

    Note: US index constituents are integrated into catalog.json
    """

    @inject
    def __init__(
        self,
        sync_catalog: SyncCatalogPort,
        sync_reference: SyncReferenceDataPort,
    ):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._sync_catalog = sync_catalog
        self._sync_reference = sync_reference

    def execute(self, force: bool = False) -> None:
        """Execute data sync process"""
        self._logger.info("=== 同步資料開始 ===")

        # 1. Sync TW stock list (catalog.json)
        self._logger.info("[1/2] Syncing TW stock list (catalog.json)...")
        catalog_result = self._sync_catalog.execute(force=force)
        self._logger.info(f"  → {catalog_result.get('status', 'unknown')}")

        # 2. Sync reference data (economic_calendar.json)
        self._logger.info("[2/2] Syncing economic calendar...")
        ref_result = self._sync_reference.execute(scope="all", force=force)
        for file_info in ref_result.get("files", []):
            self._logger.info(f"  → {file_info.get('file')}: {file_info.get('status')}")

        self._logger.info("=== 資料同步完成 ===")
