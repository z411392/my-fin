"""Monitor Data DTO"""

from typing import TypedDict


class VIXDataDTO(TypedDict):
    """VIX Data"""

    value: float
    tier: str
    kelly_factor: float


class DEFCONDataDTO(TypedDict):
    """DEFCON Data"""

    level: int
    emoji: str
    action: str


class VPINDataDTO(TypedDict):
    """VPIN Data"""

    value: float
    status: str


class GEXDataDTO(TypedDict):
    """GEX Data"""

    value: float
    status: str


class GLIDataDTO(TypedDict):
    """GLI Data"""

    z_score: float
    status: str


class RegimeDataDTO(TypedDict):
    """Regime Data"""

    hurst: float
    hmm_state: int
    hmm_bull_prob: float
    name: str


class MonitorDataDTO(TypedDict):
    """Complete Monitor Data

    Corresponds to GetMonitorPort.execute() return value
    """

    timestamp: str
    vix: VIXDataDTO
    defcon: DEFCONDataDTO
    vpin: VPINDataDTO
    gex: GEXDataDTO
    gli: GLIDataDTO
    regime: RegimeDataDTO
