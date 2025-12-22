"""Thesis Validation DTO

Thesis Validation Result
"""

from typing import TypedDict


class ThesisValidationDTO(TypedDict):
    """Thesis Validation Result"""

    validated_count: int
    invalidated_count: int
    pending_count: int
    validation_rate: float
    details: list[str]
