"""Stock Symbol Converter

Uses Shioaji format (no suffix) as internal system standard.
Automatically converts to corresponding format when calling Yahoo Finance API.

Format comparison:
- Shioaji (internal standard): "2330", "00631L", "NVDA"
- Yahoo Finance (TW stocks): "2330.TW", "00631L.TW"
- Yahoo Finance (US stocks): "NVDA", "AAPL"
"""


def to_yahoo_symbol(symbol: str) -> str:
    """Convert internal stock symbol to Yahoo Finance format

    Args:
        symbol: Internal standard symbol (Shioaji format)

    Returns:
        Symbol in Yahoo Finance format

    Examples:
        >>> to_yahoo_symbol("2330")
        '2330.TW'
        >>> to_yahoo_symbol("00631L")
        '00631L.TW'
        >>> to_yahoo_symbol("NVDA")
        'NVDA'
        >>> to_yahoo_symbol("2330.TW")  # Already Yahoo format
        '2330.TW'
    """
    # Already in Yahoo format
    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        return symbol

    # TW stock rules:
    # 1. Pure digits (e.g., 2330, 2317)
    # 2. Digit prefix + letters (e.g., 00631L, 6488W)
    # 3. Not US stock format
    if _is_taiwan_stock(symbol):
        return f"{symbol}.TW"

    # US stocks remain unchanged
    return symbol


def to_internal_symbol(symbol: str) -> str:
    """Convert Yahoo Finance format to internal standard symbol (Shioaji format)

    Args:
        symbol: Symbol in Yahoo Finance format

    Returns:
        Internal standard symbol (no suffix)

    Examples:
        >>> to_internal_symbol("2330.TW")
        '2330'
        >>> to_internal_symbol("00631L.TW")
        '00631L'
        >>> to_internal_symbol("NVDA")
        'NVDA'
        >>> to_internal_symbol("2330")  # Already internal format
        '2330'
    """
    # Remove .TW / .TWO suffix
    if symbol.endswith(".TW"):
        return symbol[:-3]
    if symbol.endswith(".TWO"):
        return symbol[:-4]
    return symbol


def _is_taiwan_stock(symbol: str) -> bool:
    """Determine if symbol is TW stock

    TW stock characteristics:
    - Pure digits (e.g., 2330, 2317, 00631L)
    - Digit prefix + possible letter suffix (e.g., 6488W, 00631L)
    - Length typically 4-6 characters

    US stock characteristics:
    - Pure letters (e.g., NVDA, AAPL)
    - Usually 1-5 letters
    """
    # Pure digits: TW stock
    if symbol.isdigit():
        return True

    # Digit prefix: TW stock (e.g., 00631L, 6488W)
    if symbol[0].isdigit():
        return True

    # Pure letters and length 1-5: US stock
    if symbol.isalpha() and 1 <= len(symbol) <= 5:
        return False

    # Default to TW stock for other cases
    return True


def normalize_symbol_list(symbols: list[str]) -> list[str]:
    """Normalize a list of symbols to internal format

    Args:
        symbols: List of symbols in mixed formats

    Returns:
        List of normalized symbols
    """
    return [to_internal_symbol(s) for s in symbols]


def to_yahoo_symbol_list(symbols: list[str]) -> list[str]:
    """Convert a list of symbols to Yahoo Finance format

    Args:
        symbols: List of internal standard symbols

    Returns:
        List of symbols in Yahoo Finance format
    """
    return [to_yahoo_symbol(s) for s in symbols]
