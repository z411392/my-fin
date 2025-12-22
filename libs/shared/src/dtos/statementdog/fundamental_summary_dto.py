"""Fundamental Summary DTO"""

from typing import TypedDict

from libs.shared.src.dtos.statementdog.revenue_momentum_dto import RevenueMomentumDTO
from libs.shared.src.dtos.statementdog.earnings_quality_dto import EarningsQualityDTO
from libs.shared.src.dtos.statementdog.valuation_metrics_dto import ValuationMetricsDTO
from libs.shared.src.dtos.statementdog.river_chart_summary_dto import (
    RiverChartSummaryDTO,
)
from libs.shared.src.dtos.statementdog.f_score_summary_dto import FScoreSummaryDTO


class FundamentalSummaryDTO(TypedDict, total=False):
    """Fundamental Summary"""

    symbol: str
    is_valid: bool  # Whether pass all fundamental filters
    revenue_momentum: RevenueMomentumDTO
    earnings_quality: EarningsQualityDTO
    valuation_metrics: ValuationMetricsDTO
    river_chart: RiverChartSummaryDTO
    f_score: FScoreSummaryDTO
