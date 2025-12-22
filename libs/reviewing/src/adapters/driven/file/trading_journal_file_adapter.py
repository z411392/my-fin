"""交易日誌資料庫 File Adapter"""

import json
import os
from typing import Dict, List, Optional

from libs.reviewing.src.ports.trading_journal_repository_port import (
    TradingJournalRepositoryPort,
)


class TradingJournalFileAdapter(TradingJournalRepositoryPort):
    """交易日誌資料庫 File Adapter

    使用 data/journal.json 作為資料來源
    """

    def __init__(self, file_path: str = "data/journal.json") -> None:
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """確保檔案存在"""
        if not os.path.exists(self.file_path):
            directory = os.path.dirname(self.file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)

            initial_data = {
                "trades": [],
                "theses": {},  # NVDA: {thesis: [], date: str}
                "_schema": {
                    "symbol": "股票代號",
                    "entry_date": "進場日期",
                    "entry_price": "進場價格",
                    "exit_date": "出場日期",
                    "exit_price": "出場價格",
                    "shares": "股數",
                    "followed_rules": "是否遵守規則",
                    "notes": "備註",
                },
            }
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4, ensure_ascii=False)

    def _load_data(self) -> Dict:
        """讀取資料"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"trades": [], "theses": {}}

    def _save_data(self, data: Dict) -> None:
        """儲存資料"""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_trade(self, trade_id: str) -> Optional[dict]:
        """取得特定交易紀錄"""
        data = self._load_data()
        for trade in data.get("trades", []):
            if trade.get("id") == trade_id:
                return trade
        return None

    def get_trades_by_symbol(self, symbol: str) -> List[dict]:
        """取得特定標的的所有交易"""
        data = self._load_data()
        return [t for t in data.get("trades", []) if t.get("symbol") == symbol]

    def get_trades_by_period(self, start_date: str, end_date: str) -> List[dict]:
        """取得指定期間的交易"""
        data = self._load_data()
        result = []
        for t in data.get("trades", []):
            trade_date = t.get("entry_date") or t.get("date")  # 相容舊格式
            if trade_date and start_date <= trade_date <= end_date:
                result.append(t)
        return result

    def get_entry_thesis(self, symbol: str) -> Optional[dict]:
        """取得買入理由"""
        data = self._load_data()

        # 1. 嘗試從 theses 字典讀取 (新格式)
        theses = data.get("theses", {})
        if symbol in theses:
            return theses[symbol]

        # 2. 嘗試從最新一筆交易讀取 notes/thesis fields (Fallback)
        trades = self.get_trades_by_symbol(symbol)
        if trades:
            last_trade = trades[-1]
            return {
                "thesis": last_trade.get("notes", "").split("\n"),
                "date": last_trade.get("entry_date"),
                "price": last_trade.get("entry_price"),
            }

        return None

    def record_trade(self, trade: dict) -> str:
        """記錄交易"""
        data = self._load_data()

        # 生成 ID
        existing_ids = [t.get("id") for t in data.get("trades", []) if t.get("id")]
        next_id = 1
        if existing_ids:
            # 簡單解析 T001
            try:
                max_id = max(
                    [
                        int(tid[1:])
                        for tid in existing_ids
                        if tid.startswith("T") and tid[1:].isdigit()
                    ]
                )
                next_id = max_id + 1
            except ValueError:
                pass

        trade_id = f"T{next_id:03d}"
        trade["id"] = trade_id

        if "trades" not in data:
            data["trades"] = []

        data["trades"].append(trade)
        self._save_data(data)

        return trade_id
