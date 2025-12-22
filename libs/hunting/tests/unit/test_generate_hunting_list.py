"""GenerateHuntingListCommand 單元測試"""

from libs.hunting.src.application.commands.generate_hunting_list import (
    GenerateHuntingListCommand,
)
from libs.hunting.src.adapters.driven.memory.scan_residual_momentum_fake_adapter import (
    ScanResidualMomentumFakeAdapter,
)


class TestGenerateHuntingListCommand:
    """測試 GenerateHuntingListCommand"""

    def test_execute_returns_hunting_list(self) -> None:
        """應返回狩獵清單"""
        fake_scan = ScanResidualMomentumFakeAdapter()
        command = GenerateHuntingListCommand(scan_query=fake_scan)
        result = command.execute(top_n=5)

        assert "date" in result
        assert "total_scanned" in result
        assert "passed_filters" in result
        assert "hunting_list" in result

    def test_hunting_list_respects_top_n(self) -> None:
        """狩獵清單應遵守 top_n 限制"""
        fake_scan = ScanResidualMomentumFakeAdapter()
        command = GenerateHuntingListCommand(scan_query=fake_scan)
        result = command.execute(top_n=2)

        assert len(result["hunting_list"]) <= 2

    def test_hunting_targets_have_required_fields(self) -> None:
        """狩獵標的應包含必要欄位"""
        fake_scan = ScanResidualMomentumFakeAdapter()
        command = GenerateHuntingListCommand(scan_query=fake_scan)
        result = command.execute(top_n=10)

        if result["hunting_list"]:
            target = result["hunting_list"][0]
            assert "symbol" in target
            assert "momentum_score" in target
            assert "trend_status" in target
            assert "quality_passed" in target
            assert "ivol" in target
            assert "f_score" in target

    def test_total_scanned_from_scan_result(self) -> None:
        """total_scanned 應來自掃描結果"""
        fake_scan = ScanResidualMomentumFakeAdapter()
        fake_scan.set_result(
            {
                "market": "tw",
                "scanned": 500,
                "targets": [],
            }
        )
        command = GenerateHuntingListCommand(scan_query=fake_scan)
        result = command.execute(top_n=10)

        assert result["total_scanned"] == 500
