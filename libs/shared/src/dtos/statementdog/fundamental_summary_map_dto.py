"""Fundamental Summary Map DTO

Symbol to Fundamental Summary Mapping
"""

from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)

# Type alias for symbol to fundamental summary mapping (dynamic keys)
# Key = stock symbol, Value = fundamental summary
FundamentalSummaryMap = dict[str, FundamentalSummaryDTO]
