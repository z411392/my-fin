"""交易日誌資料庫 Fake Adapter"""

from libs.shared.src.dtos.trading_journal.trade_record_dto import TradeRecordDTO
from libs.shared.src.dtos.trading_journal.entry_thesis_dto import EntryThesisDTO
from libs.reviewing.src.ports.trading_journal_repository_port import (
    TradingJournalRepositoryPort,
)


class TradingJournalRepositoryFakeAdapter(TradingJournalRepositoryPort):
    """交易日誌資料庫 Fake Adapter

    實作 TradingJournalRepositoryPort 介面
    """

    def __init__(self) -> None:
        self._trades: list[TradeRecordDTO] = [
            {
                "id": "T001",
                "symbol": "NVDA",
                "action": "BUY",
                "quantity": 100,
                "price": 420.0,
                "date": "2024-01-05",
            },
            {
                "id": "T002",
                "symbol": "AAPL",
                "action": "BUY",
                "quantity": 50,
                "price": 170.0,
                "date": "2024-01-10",
            },
        ]
        self._theses: dict[str, EntryThesisDTO] = {
            "NVDA": {
                "thesis": ["AI 需求強勁", "資料中心成長", "護城河深"],
                "date": "2024-01-05",
                "price": 420.0,
            },
            "AAPL": {
                "thesis": ["服務收入成長", "生態系黏性", "現金流強勁"],
                "date": "2024-01-10",
                "price": 170.0,
            },
        }
        self._closed_trades: list[TradeRecordDTO] = []

    def set_trades(self, trades: list[TradeRecordDTO]) -> None:
        """設定交易紀錄 (測試用)"""
        self._trades = trades

    def set_thesis(self, symbol: str, thesis: EntryThesisDTO) -> None:
        """設定買入理由 (測試用)"""
        self._theses[symbol] = thesis

    def get_trade(self, trade_id: str) -> TradeRecordDTO | None:
        """取得特定交易紀錄"""
        for trade in self._trades:
            if trade.get("id") == trade_id:
                return trade
        return None

    def get_trades_by_symbol(self, symbol: str) -> list[TradeRecordDTO]:
        """取得特定標的的所有交易"""
        return [t for t in self._trades if t.get("symbol") == symbol]

    def get_trades_by_period(
        self, start_date: str, end_date: str
    ) -> list[TradeRecordDTO]:
        """取得指定期間的交易"""
        return [
            t for t in self._trades if start_date <= (t.get("date") or "") <= end_date
        ]

    def get_entry_thesis(self, symbol: str) -> EntryThesisDTO | None:
        """取得買入理由"""
        return self._theses.get(symbol)

    def record_trade(self, trade: TradeRecordDTO) -> str:
        """記錄交易"""
        trade_id = f"T{len(self._trades) + 1:03d}"
        trade["id"] = trade_id
        self._trades.append(trade)
        return trade_id

    def set_closed_trades(self, trades: list[TradeRecordDTO]) -> None:
        """設定已平倉交易"""
        self._closed_trades = trades

    def get_closed_trades(self, period: str = "monthly") -> list[TradeRecordDTO]:
        """取得已平倉交易"""
        return self._closed_trades


# 別名
TradingJournalFakeAdapter = TradingJournalRepositoryFakeAdapter
