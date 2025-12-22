import pytest
from unittest.mock import patch, mock_open
from libs.arbitraging.src.application.commands.sync_reference_data_command import (
    SyncReferenceDataCommand,
)


class TestSyncReferenceDataCommand:
    @pytest.fixture
    def command(self):
        return SyncReferenceDataCommand()

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("json.load", return_value={})
    @patch("json.dump")
    def test_execute_calendar_sync(self, stub_dump, _stub_load, _stub_file, command):
        # 測試同步行事曆
        result = command.execute(scope="calendar")

        # 驗證結果格式
        assert result["scope"] == "calendar"
        assert len(result["files"]) > 0
        assert result["files"][0]["file"] == "economic_calendar.json"

        # 驗證有寫入檔案
        assert stub_dump.called

    @patch("builtins.open", new_callable=mock_open, read_data="{}")
    @patch("json.load", return_value={})
    @patch("json.dump")
    def test_execute_all_sync(self, stub_dump, _stub_load, _stub_file, command):
        # 測試全部同步 (目前只有經濟日曆)
        result = command.execute(scope="all")

        assert result["scope"] == "all"
        assert len(result["files"]) == 1  # 只有 economic_calendar
        assert result["files"][0]["file"] == "economic_calendar.json"
