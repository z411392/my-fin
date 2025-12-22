"""Account Balance DTO"""

from typing import TypedDict, NotRequired


class AccountBalanceDTO(TypedDict):
    """Account Balance

    Corresponds to PortfolioProviderPort.get_account_balance() return value
    """

    cash: float
    """Cash Balance"""

    margin: NotRequired[float]
    """Margin Available"""

    equity: NotRequired[float]
    """Total Equity"""

    unrealized_pnl: NotRequired[float]
    """Unrealized PnL"""

    buying_power: NotRequired[float]
    """Buying Power"""
