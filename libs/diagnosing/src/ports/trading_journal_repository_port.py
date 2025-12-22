"""交易日誌資料庫 Port (Stock Checkup)"""

from typing import Protocol

from libs.shared.src.dtos.trading_journal.trade_record_dto import TradeRecordDTO
from libs.shared.src.dtos.trading_journal.entry_thesis_dto import EntryThesisDTO


class TradingJournalRepositoryPort(Protocol):
    """交易日誌資料庫 Port

    提供交易日誌的讀取，用於驗證買入理由
    """

    def get_entry_thesis(self, symbol: str) -> EntryThesisDTO | None:
        """取得買入理由

        Args:
            symbol: 股票代碼

        Returns:
            EntryThesisDTO | None: 買入理由
        """
        ...

    def get_trade_history(self, symbol: str) -> list[TradeRecordDTO]:
        """取得交易歷史

        Args:
            symbol: 股票代碼

        Returns:
            list[TradeRecordDTO]: 交易紀錄列表
        """
        ...

    def get_holding_period(self, symbol: str) -> int:
        """取得持有天數

        Args:
            symbol: 股票代碼

        Returns:
            int: 持有天數
        """
        ...
