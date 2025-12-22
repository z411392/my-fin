"""Parsed analyze() Result DTO"""

from typing import TypedDict


class ParsedAnalyzeResultDTO(TypedDict, total=False):
    """Parsed analyze() Result

    Each metric slug (e.g. 'income-statement', 'profit-margin')
    Value is list[TableRowDTO] or {"error": str}
    """

    symbol: str
    # Dynamic metric fields - Cannot be fully defined in TypedDict
    # But mark symbol as required field
