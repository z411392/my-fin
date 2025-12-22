"""Entry Checklist DTO

Entry Decision Checklist Result
"""

from typing import TypedDict


class EntryChecklistDTO(TypedDict):
    """Entry Decision Checklist Result"""

    decision: str
    weather_pass: bool
    liquidity_pass: bool
    regime_pass: bool
    signal_count: int
    checks: list[str]
    recommendation: str
