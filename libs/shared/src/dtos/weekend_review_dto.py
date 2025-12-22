"""Weekend Review Result DTO

Corresponds to GenerateWeekendReviewCommand.execute() return structure
"""

from typing import TypedDict

from libs.shared.src.dtos.hunting.candidate_stock_dto import CandidateStockDTO
from libs.shared.src.dtos.event.calendar_event_dto import CalendarEventDTO
from libs.shared.src.dtos.event.todo_dto import TodoDTO


class AdvisorStatusDTO(TypedDict):
    """Advisor status"""

    status: str  # "Attack" | "Watch" | "Defend"
    advice: str  # Advice description


class FourAdvisorsDTO(TypedDict):
    """Four advisors diagnosis result"""

    engineer: AdvisorStatusDTO  # Engineer: liquidity/structure
    biologist: AdvisorStatusDTO  # Biologist: industry ecology
    psychologist: AdvisorStatusDTO  # Psychologist: market sentiment
    strategist: AdvisorStatusDTO  # Strategist: win rate/odds
    consensus: str  # "🟢 Attack" | "🟡 Watch" | "🔴 Defend"
    allocation: str  # Recommended allocation
    attack_count: int  # Attack count


class HaltCheckItemDTO(TypedDict):
    """HALT check item"""

    question: str
    answer: str


class HaltCheckDTO(TypedDict):
    """HALT self-check result"""

    hungry: HaltCheckItemDTO
    angry: HaltCheckItemDTO
    lonely: HaltCheckItemDTO
    tired: HaltCheckItemDTO
    can_trade: bool


class WeekendRegimeDTO(TypedDict):
    """Weekend regime assessment result"""

    hurst: float
    hmm_bull_prob: float
    vix: float
    name: str
    market_type: str
    recommended_strategy: str
    kelly_factor: float


class WeekendReviewResultDTO(TypedDict):
    """Weekend review complete result"""

    date: str
    regime: WeekendRegimeDTO
    advisors: FourAdvisorsDTO
    momentum_candidates: list[CandidateStockDTO]
    halt_check: HaltCheckDTO
    upcoming_events: list[CalendarEventDTO]
    next_week_plan: list[TodoDTO]
    total_scanned: int
    report_markdown: str
