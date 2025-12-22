"""Todo Item Data Structure"""

from typing import TypedDict


class TodoDTO(TypedDict):
    """Todo item

    Used for action recommendations in daily digest
    """

    action: str
    priority: str
    description: str
