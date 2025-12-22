"""交易日誌資料庫 Port"""

from typing import Protocol

from libs.shared.src.dtos.trading_journal.trade_record_dto import TradeRecordDTO
from libs.shared.src.dtos.trading_journal.entry_thesis_dto import EntryThesisDTO


class TradingJournalRepositoryPort(Protocol):
    """交易日誌資料庫 Port

    提供交易日誌的讀取與寫入
    """

    def get_trade(self, trade_id: str) -> TradeRecordDTO | None:
        """取得特定交易紀錄

        Args:
            trade_id: 交易 ID

        Returns:
            TradeRecordDTO | None: 交易紀錄
        """
        ...

    def get_trades_by_symbol(self, symbol: str) -> list[TradeRecordDTO]:
        """取得特定標的的所有交易

        Args:
            symbol: 股票代碼

        Returns:
            list[TradeRecordDTO]: 交易紀錄列表
        """
        ...

    def get_trades_by_period(
        self, start_date: str, end_date: str
    ) -> list[TradeRecordDTO]:
        """取得指定期間的交易

        Args:
            start_date: 開始日期 (YYYY-MM-DD)
            end_date: 結束日期 (YYYY-MM-DD)

        Returns:
            list[TradeRecordDTO]: 交易紀錄列表
        """
        ...

    def get_entry_thesis(self, symbol: str) -> EntryThesisDTO | None:
        """取得買入理由

        Args:
            symbol: 股票代碼

        Returns:
            EntryThesisDTO | None: 買入理由
        """
        ...

    def record_trade(self, trade: TradeRecordDTO) -> str:
        """記錄交易

        Args:
            trade: 交易資料

        Returns:
            str: 交易 ID
        """
        ...
