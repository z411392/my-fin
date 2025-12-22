"""
PortfolioProviderPort - Driven Port

實作者: ShioajiPortfolioAdapter
"""

from typing import Protocol

from libs.shared.src.dtos.portfolio.position_dto import PositionDTO
from libs.shared.src.dtos.portfolio.account_balance_dto import AccountBalanceDTO


class PortfolioProviderPort(Protocol):
    """持倉查詢 Driven Port"""

    def connect(self) -> bool:
        """連線至券商 API"""
        ...

    def disconnect(self) -> None:
        """斷線"""
        ...

    def get_positions(self) -> list[PositionDTO]:
        """取得所有持倉"""
        ...

    def get_account_balance(self) -> AccountBalanceDTO:
        """取得帳戶餘額"""
        ...
