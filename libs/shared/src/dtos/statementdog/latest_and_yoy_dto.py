"""_get_latest_and_yoy Return Structure DTO"""

from typing import TypedDict


class LatestAndYoYDTO(TypedDict):
    """_get_latest_and_yoy Return Structure

    current: Latest Value
    prev: Same Period Last Year Value
    """

    current: float
    prev: float
