"""SyncCatalogPort - 同步股票目錄的 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.catalog.sync_result_dto import SyncResultDTO


class SyncCatalogPort(Protocol):
    """同步商品目錄的 Port"""

    def execute(self, force: bool = False) -> SyncResultDTO:
        """執行同步

        Args:
            force: 是否強制同步 (忽略快取)

        Returns:
            SyncResultDTO: 同步結果摘要
        """
        ...
