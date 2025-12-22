"""SyncDataCommand Unit Tests"""

from unittest.mock import MagicMock
import pytest


class TestSyncDataCommand:
    """SyncDataCommand Tests"""

    @pytest.fixture
    def fake_sync_catalog(self):
        """Mock SyncCatalogPort"""
        mock = MagicMock()
        mock.execute.return_value = {
            "status": "success",
            "tw_count": 1800,
            "us_count": 500,
        }
        return mock

    @pytest.fixture
    def fake_sync_reference(self):
        """Mock SyncReferenceDataPort"""
        mock = MagicMock()
        mock.execute.return_value = {
            "status": "success",
            "files": [
                {"file": "economic_calendar.json", "status": "updated"},
            ],
        }
        return mock

    def test_execute_calls_sync_catalog(self, fake_sync_catalog, fake_sync_reference):
        """Test execute calls sync_catalog.execute"""
        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        command = SyncDataCommand(
            sync_catalog=fake_sync_catalog,
            sync_reference=fake_sync_reference,
        )
        command.execute(force=False)

        fake_sync_catalog.execute.assert_called_once_with(force=False)

    def test_execute_calls_sync_reference(self, fake_sync_catalog, fake_sync_reference):
        """Test execute calls sync_reference.execute"""
        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        command = SyncDataCommand(
            sync_catalog=fake_sync_catalog,
            sync_reference=fake_sync_reference,
        )
        command.execute(force=False)

        fake_sync_reference.execute.assert_called_once_with(scope="all", force=False)

    def test_execute_with_force_flag(self, fake_sync_catalog, fake_sync_reference):
        """Test execute with force parameter"""
        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        command = SyncDataCommand(
            sync_catalog=fake_sync_catalog,
            sync_reference=fake_sync_reference,
        )
        command.execute(force=True)

        fake_sync_catalog.execute.assert_called_once_with(force=True)
        fake_sync_reference.execute.assert_called_once_with(scope="all", force=True)

    def test_execute_without_console(self, fake_sync_catalog, fake_sync_reference):
        """Test can execute normally (now uses print output)"""
        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        command = SyncDataCommand(
            sync_catalog=fake_sync_catalog,
            sync_reference=fake_sync_reference,
        )
        # Should not raise exception
        command.execute()

        fake_sync_catalog.execute.assert_called_once()
        fake_sync_reference.execute.assert_called_once()

    def test_execute_logs_progress(
        self, fake_sync_catalog, fake_sync_reference, caplog
    ):
        """Test execute outputs progress messages (using logger)"""
        import logging

        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        with caplog.at_level(logging.INFO):
            command = SyncDataCommand(
                sync_catalog=fake_sync_catalog,
                sync_reference=fake_sync_reference,
            )
            command.execute()

        # Check logger output contains progress messages
        assert "同步資料開始" in caplog.text
        assert "資料同步完成" in caplog.text

    def test_execute_handles_catalog_exception(
        self, fake_sync_catalog, fake_sync_reference
    ):
        """Test sync_catalog exception handling"""
        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        fake_sync_catalog.execute.side_effect = Exception("Catalog sync failed")
        command = SyncDataCommand(
            sync_catalog=fake_sync_catalog,
            sync_reference=fake_sync_reference,
        )

        with pytest.raises(Exception, match="Catalog sync failed"):
            command.execute()

    def test_execute_handles_reference_exception(
        self, fake_sync_catalog, fake_sync_reference
    ):
        """Test sync_reference exception handling"""
        from libs.maintaining.src.application.commands.sync_data_command import (
            SyncDataCommand,
        )

        fake_sync_reference.execute.side_effect = Exception("Reference sync failed")
        command = SyncDataCommand(
            sync_catalog=fake_sync_catalog,
            sync_reference=fake_sync_reference,
        )

        with pytest.raises(Exception, match="Reference sync failed"):
            command.execute()
