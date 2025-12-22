"""Report Generation Result DTO"""

from typing import TypedDict, NotRequired


class ReportResultDTO(TypedDict):
    """Report Generation Result

    Corresponds to GenerateDailyReportPort and GenerateWeeklyReportPort return value
    """

    success: bool
    """Whether successful"""

    message: str
    """Message"""

    report_url: NotRequired[str | None]
    """Report URL (if pushed to Google Sheets)"""

    is_simulated: NotRequired[bool]
    """Whether simulated mode"""

    date: NotRequired[str]
    """Report Date"""

    items_count: NotRequired[int]
    """Report Items Count"""
