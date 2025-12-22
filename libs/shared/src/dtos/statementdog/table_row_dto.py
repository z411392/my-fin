"""StatementDog Table Row Data DTO"""

from typing import TypedDict


class TableRowDTO(TypedDict):
    """StatementDog Table Row Data"""

    name: str
    values: dict[str, float | str | None]
