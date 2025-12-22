"""SyncCatalogCommand 單元測試

使用 Fake Adapter 模擬 Shioaji，遵循 testing.md Classicist 學派規範
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from libs.arbitraging.src.adapters.driven.memory.catalog_fake_adapter import (
    CatalogFakeAdapter,
)
from libs.arbitraging.src.application.commands.sync_catalog_command import (
    SyncCatalogCommand,
)


class TestSyncCatalogCommand:
    """商品目錄同步指令測試"""

    @pytest.fixture
    def temp_dir(self):
        """建立暫存目錄"""
        temp = tempfile.mkdtemp()
        yield temp
        shutil.rmtree(temp, ignore_errors=True)

    @pytest.fixture
    def fake_catalog(self):
        """建立 Fake Catalog Adapter (同時作為台股和美股 provider)"""
        fake = CatalogFakeAdapter()
        fake.set_tw_stocks(
            [
                {
                    "code": "2330",
                    "name": "台積電",
                    "market": "TSE",
                    "industry": "24",
                    "currency": "TWD",
                },
                {
                    "code": "2317",
                    "name": "鴻海",
                    "market": "TSE",
                    "industry": "25",
                    "currency": "TWD",
                },
            ]
        )
        return fake

    @pytest.fixture
    def command(self, fake_catalog, temp_dir):
        """建立 Command 實例 (arch.md R3: 注入兩個 ports)"""
        cmd = SyncCatalogCommand(
            catalog_adapter=fake_catalog,
            us_stock_adapter=fake_catalog,
        )
        cmd._catalog_path = Path(temp_dir) / "catalog.json"
        return cmd

    def test_execute_fetches_and_saves_catalog(self, command) -> None:
        """成功取得資料並儲存"""
        result = command.execute(force=True)

        assert result["status"] == "success"
        assert result["tw_count"] == 2
        assert os.path.exists(command._catalog_path)

    def test_execute_fails_on_empty_data(self, temp_dir) -> None:
        """資料為空時應回報失敗"""
        fake_empty = CatalogFakeAdapter()
        fake_empty.set_tw_stocks([])

        cmd = SyncCatalogCommand(
            catalog_adapter=fake_empty,
            us_stock_adapter=fake_empty,
        )
        cmd._catalog_path = Path(temp_dir) / "catalog.json"

        result = cmd.execute(force=True)

        assert result["status"] == "failed"
        assert "No TW data" in result["message"]

    def test_execute_groups_tw_stocks_by_etf(self, temp_dir) -> None:
        """台股應依產業分群至對應 ETF"""
        fake = CatalogFakeAdapter()
        fake.set_tw_stocks(
            [
                {
                    "code": "2330",
                    "name": "台積電",
                    "market": "TSE",
                    "industry": "24",
                    "currency": "TWD",
                },
                {
                    "code": "2882",
                    "name": "國泰金",
                    "market": "TSE",
                    "industry": "17",
                    "currency": "TWD",
                },
                {
                    "code": "1101",
                    "name": "台泥",
                    "market": "TSE",
                    "industry": "01",
                    "currency": "TWD",
                },
            ]
        )

        cmd = SyncCatalogCommand(
            catalog_adapter=fake,
            us_stock_adapter=fake,
        )
        cmd._catalog_path = Path(temp_dir) / "catalog.json"

        result = cmd.execute(force=True)

        assert result["status"] == "success"
        assert "0052" in result["tw_groups"]
        assert "0055" in result["tw_groups"]
        assert "0050" in result["tw_groups"]
