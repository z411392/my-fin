"""DEFCON Level Calculator

Corresponds to methodology.md §5 System Engineering and Data Infrastructure
Integrates multiple indicators into single decision signal, supports rule-based cognition
"""

from libs.shared.src.enums.defcon_level import DefconLevel
from libs.shared.src.constants.gex_thresholds import GEX_FLIP
from libs.shared.src.constants.vix_thresholds import VIX_DEFCON_1
from libs.shared.src.constants.vpin_thresholds import VPIN_DEFCON2_TRIGGER


def calculate_defcon_level(
    vix: float,
    hmm_state: int,
    vpin: float,
    gli_z: float,
    gex: float = 0.0,
) -> tuple[DefconLevel, str, str]:
    """
    Calculate DEFCON level

    Corresponds to methodology.md:
    - DEFCON 5: VIX < 20 and HMM 0/1 → Normal
    - DEFCON 4: VIX > 20 or HMM ≥ 2 → No adding positions
    - DEFCON 3: VIX > 30 → Position ≤ 50%
    - DEFCON 2: VIX > 40 or Negative GEX or VPIN > 0.95 → Clear Alpha
    - DEFCON 1: VIX > 50 → Kill Switch

    Args:
        vix: VIX index value
        hmm_state: HMM regime state (0=Bull, 1=Neutral, 2=Bear)
        vpin: VPIN value (0-1)
        gli_z: GLI Z-Score
        gex: Gamma Exposure value

    Returns:
        tuple: (DefconLevel, emoji, permission description)
    """
    # DEFCON 1: Extreme risk (VIX > 50 or circuit breaker)
    if vix >= VIX_DEFCON_1:
        return DefconLevel.DEFCON_1, "⬛", "Manual takeover"

    # DEFCON 2: Defensive mode
    # VIX > 40 OR GEX < 0 (Negative Gamma) OR VPIN > 0.95
    if vix >= 40 or gex < GEX_FLIP or vpin > VPIN_DEFCON2_TRIGGER:
        return DefconLevel.DEFCON_2, "🔴", "Defensive mode"

    # DEFCON 3: Restricted mode (VIX > 30)
    if vix >= 30:
        return DefconLevel.DEFCON_3, "🟠", "Restricted mode"

    # DEFCON 4: Alert (VIX > 20 or HMM Bear)
    if vix >= 20 or hmm_state >= 2:
        return DefconLevel.DEFCON_4, "🟡", "Full auto"

    # DEFCON 5: Normal
    return DefconLevel.DEFCON_5, "🟢", "Full auto"


def get_defcon_action(level: DefconLevel) -> str:
    """Get recommended action for DEFCON level"""
    actions = {
        DefconLevel.DEFCON_5: "Normal trading",
        DefconLevel.DEFCON_4: "No adding positions, reduce only",
        DefconLevel.DEFCON_3: "Position ≤ 50%, stop opening new positions",
        DefconLevel.DEFCON_2: "Clear Alpha, keep only cash+hedges",
        DefconLevel.DEFCON_1: "Kill Switch, all cash/Treasury bonds",
    }
    return actions.get(level, "Unknown state")
