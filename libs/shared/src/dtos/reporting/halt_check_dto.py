"""HALT Check DTO

HALT Self-Check Result
"""

from typing import TypedDict


class HaltCheckDTO(TypedDict):
    """HALT Self-Check Result"""

    hungry: bool
    angry: bool
    lonely: bool
    tired: bool
    passed: bool
    message: str
