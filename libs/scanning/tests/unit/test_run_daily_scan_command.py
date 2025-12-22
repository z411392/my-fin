"""RunDailyScanCommand 單元測試"""

from unittest.mock import AsyncMock, MagicMock
import pytest


class TestRunDailyScanCommand:
    """RunDailyScanCommand 測試"""

    @pytest.fixture
    def fake_scan_residual(self):
        """Fake ScanResidualMomentumPort"""
        fake = MagicMock()
        # execute 是 async 方法，需要用 AsyncMock
        fake.execute = AsyncMock(
            return_value={
                "market": "tw_shioaji",
                "trade_date": "2026-01-03",
                "regime": "牛市",
                "bull_prob": 0.65,
                "scanned": 100,
                "qualified": 20,
                "targets": [{"symbol": "2330", "momentum": 2.5}],
                "top_targets": [{"symbol": "2330", "momentum": 2.5}],
                "bottom_targets": [],
            }
        )
        return fake

    @pytest.mark.asyncio
    async def test_execute_calls_scan_residual(self, fake_scan_residual):
        """測試執行會呼叫 scan_residual.execute"""
        from libs.scanning.src.application.commands.run_daily_scan_command import (
            RunDailyScanCommand,
        )

        command = RunDailyScanCommand(scan_residual=fake_scan_residual)
        await command.execute(market="tw_shioaji", top_n=20)

        fake_scan_residual.execute.assert_called_once_with(
            market="tw_shioaji", top_n=20, stocks=None, start_from=""
        )

    @pytest.mark.asyncio
    async def test_execute_with_different_market(self, fake_scan_residual):
        """測試使用不同市場參數"""
        from libs.scanning.src.application.commands.run_daily_scan_command import (
            RunDailyScanCommand,
        )

        command = RunDailyScanCommand(scan_residual=fake_scan_residual)
        await command.execute(market="us", top_n=10)

        fake_scan_residual.execute.assert_called_once_with(
            market="us", top_n=10, stocks=None, start_from=""
        )

    @pytest.mark.asyncio
    async def test_execute_with_default_params(self, fake_scan_residual):
        """測試使用預設參數"""
        from libs.scanning.src.application.commands.run_daily_scan_command import (
            RunDailyScanCommand,
        )

        command = RunDailyScanCommand(scan_residual=fake_scan_residual)
        await command.execute()

        fake_scan_residual.execute.assert_called_once_with(
            market="tw", top_n=20, stocks=None, start_from=""
        )

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, fake_scan_residual):
        """測試異常處理"""
        from libs.scanning.src.application.commands.run_daily_scan_command import (
            RunDailyScanCommand,
        )

        fake_scan_residual.execute.side_effect = Exception("API Error")
        command = RunDailyScanCommand(scan_residual=fake_scan_residual)

        with pytest.raises(Exception, match="API Error"):
            await command.execute()
