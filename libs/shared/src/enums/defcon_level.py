"""DEFCON Level Enum"""

from enum import Enum


class DefconLevel(Enum):
    """DEFCON Level (5=Safe, 1=Danger)"""

    DEFCON_5 = 5  # 🟢 Full Auto, Normal Trading
    DEFCON_4 = 4  # 🟡 Full Auto, No Adding Positions
    DEFCON_3 = 3  # 🟠 Restricted, Position <= 50%
    DEFCON_2 = 2  # 🔴 Defensive, Clear Alpha
    DEFCON_1 = 1  # ⬛ Manual Takeover, All Cash
