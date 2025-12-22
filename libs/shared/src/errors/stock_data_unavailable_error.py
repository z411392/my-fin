"""Stock Data Unavailable Error"""

from libs.shared.src.errors.domain_error import DomainError


class StockDataUnavailableError(DomainError):
    """Stock data unavailable error

    Raised when stock data cannot be retrieved (e.g., emerging market stocks, delisted stocks, etc.)
    """

    def __init__(self, symbol: str, reason: str | None = None) -> None:
        message = f"Unable to retrieve data for stock {symbol}"
        if reason:
            message += f": {reason}"
        super().__init__(message, code="STOCK_DATA_UNAVAILABLE")
        self.symbol = symbol
        self.reason = reason
