"""Stock Diagnosis Result DTO"""

from typing import TypedDict, NotRequired


class StockDiagnosisDTO(TypedDict):
    """Stock Diagnosis Result

    Corresponds to DiagnoseStockPort.execute() return value
    """

    symbol: str
    """Stock Symbol"""

    name: NotRequired[str]
    """Stock Name"""

    price: NotRequired[float]
    """Current Price"""

    roe: NotRequired[float]
    """ROE"""

    pe_ratio: NotRequired[float]
    """P/E Ratio"""

    revenue_growth: NotRequired[float]
    """Revenue Growth Rate"""

    fundamental_grade: str
    """Fundamental Grade (A/B/C/D/F)"""

    advisor_consensus: str
    """Four Advisor Consensus (Aggressive/Diverged/Defensive)"""

    verdict: str
    """Verdict (HOLD/OBSERVE/REDUCE)"""

    rationale: str
    """Rationale"""
