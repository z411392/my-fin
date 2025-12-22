"""River Chart Summary DTO"""

from typing import TypedDict


class RiverChartSummaryDTO(TypedDict, total=False):
    """River Chart Summary"""

    current_pb: float
    pb_zone: str  # Expensive/High/Fair/Cheap/Very Cheap
    pb_median: float
    pb_low: float
    pb_high: float
