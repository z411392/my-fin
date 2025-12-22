"""Advisor Consensus Result DTO"""

from typing import TypedDict

from libs.shared.src.dtos.analysis.advisor_opinion_dto import AdvisorOpinionDTO


class AdvisorConsensusResultDTO(TypedDict):
    """Advisor Consensus Result"""

    symbol: str
    advisors: list[AdvisorOpinionDTO]
    consensus: str  # All-in Offensive, Majority Offensive, Diverged, Majority Defensive, All-in Defensive
    signal: str  # 🟢🟢, 🟢, 🟡, 🔴, 🔴🔴
    action: str  # Add, Hold/Small Add, Observe, Reduce, Clear
    confidence: float
