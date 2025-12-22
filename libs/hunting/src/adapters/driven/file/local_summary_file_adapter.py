"""Local Summary File Adapter — 本地 JSON 檔案儲存實作"""

import json
from pathlib import Path


from libs.hunting.src.ports.local_summary_storage_port import LocalSummaryStoragePort
from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO


class LocalSummaryFileAdapter(LocalSummaryStoragePort):
    """本地摘要檔案儲存器

    儲存格式: data/momentum/{date}/{symbol}.json
    """

    def __init__(self, base_dir: str = "data/momentum") -> None:
        """初始化

        Args:
            base_dir: 基礎目錄路徑
        """
        self._base_dir = Path(base_dir)

    def _get_dir_path(self, date: str) -> Path:
        """取得日期目錄路徑"""
        return self._base_dir / date

    def _get_file_path(self, date: str, symbol: str) -> Path:
        """取得 JSON 檔案路徑"""
        return self._get_dir_path(date) / f"{symbol}.json"

    def exists(self, date: str, symbol: str) -> bool:
        """檢查是否已存在

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼

        Returns:
            True if JSON file exists
        """
        return self._get_file_path(date, symbol).exists()

    def save(self, date: str, symbol: str, data: ScanResultRowDTO) -> None:
        """儲存資料

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼
            data: 要儲存的資料
        """
        dir_path = self._get_dir_path(date)
        dir_path.mkdir(parents=True, exist_ok=True)

        file_path = self._get_file_path(date, symbol)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, date: str, symbol: str) -> ScanResultRowDTO | None:
        """讀取資料

        Args:
            date: 日期 (YYYY-MM-DD)
            symbol: 股票代碼

        Returns:
            資料字典，若不存在則回傳 None
        """
        file_path = self._get_file_path(date, symbol)
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_symbols(self, date: str) -> list[str]:
        """列出指定日期的所有 symbol

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            該日期已儲存的所有 symbol 列表
        """
        dir_path = self._get_dir_path(date)
        if not dir_path.exists():
            return []

        symbols = []
        for file in dir_path.glob("*.json"):
            # 去掉 .json 副檔名
            symbols.append(file.stem)
        return sorted(symbols)
