"""Fundamental File Adapter — 財報狗資料本地 JSON 檔案儲存實作"""

import json
from pathlib import Path


from libs.hunting.src.ports.fundamental_storage_port import FundamentalStoragePort
from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)


class FundamentalFileAdapter(FundamentalStoragePort):
    """財報狗資料檔案儲存器

    儲存格式: data/fundamental/{symbol}.json
    無日期分層，只保留最新一份
    """

    def __init__(self, base_dir: str = "data/fundamental") -> None:
        """初始化

        Args:
            base_dir: 基礎目錄路徑
        """
        self._base_dir = Path(base_dir)

    def _get_file_path(self, symbol: str) -> Path:
        """取得 JSON 檔案路徑"""
        return self._base_dir / f"{symbol}.json"

    def exists(self, symbol: str) -> bool:
        """檢查是否已存在

        Args:
            symbol: 股票代碼

        Returns:
            True if JSON file exists
        """
        return self._get_file_path(symbol).exists()

    def save(self, symbol: str, data: FundamentalSummaryDTO) -> None:
        """儲存資料

        Args:
            symbol: 股票代碼
            data: 要儲存的財報狗資料
        """
        self._base_dir.mkdir(parents=True, exist_ok=True)

        file_path = self._get_file_path(symbol)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load(self, symbol: str) -> FundamentalSummaryDTO | None:
        """讀取資料

        Args:
            symbol: 股票代碼

        Returns:
            資料字典，若不存在則回傳 None
        """
        file_path = self._get_file_path(symbol)
        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_all(self) -> list[str]:
        """列出所有已儲存的 symbol

        Returns:
            所有已儲存的 symbol 列表
        """
        if not self._base_dir.exists():
            return []

        symbols = []
        for file in self._base_dir.glob("*.json"):
            symbols.append(file.stem)
        return sorted(symbols)
