"""Scan Result DTO"""

from typing import TypedDict


class HourlyScanResultDTO(TypedDict, total=False):
    """Hourly Scan Result"""

    status: str  # success, failed
    alerts_count: int
    notifications_sent: int
    timestamp: str


class WeeklyReviewResultDTO(TypedDict, total=False):
    """Weekly Review Result"""

    week: int
    year: int
    performance_summary: dict
    skill_verdict: str
    recommendations: list[str]
    report_markdown: str
