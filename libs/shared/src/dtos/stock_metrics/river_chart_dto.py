"""River Chart DTO"""

from typing import TypedDict


class RiverChartDTO(TypedDict):
    """River Chart (PE/PB Bands) analysis result"""

    symbol: str
    current_pe: float | None
    current_pb: float | None
    # PE River Bands (High/Low/Median based on history)
    pe_high_avg: float | None
    pe_low_avg: float | None
    pe_median: float | None
    pe_zone: str  # "Cheap", "Fair", "Expensive", "N/A"
    # PB River Bands
    pb_high_avg: float | None
    pb_low_avg: float | None
    pb_median: float | None
    pb_zone: str  # "Cheap", "Fair", "Expensive", "N/A"
    # Raw data points (optional, for plotting if needed)
    pe_history: list[float]
    pb_history: list[float]
