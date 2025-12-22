"""
UpdateEventCalendarPort - Driving Port

實作者: UpdateEventCalendarCommand
"""

from typing import Protocol


class UpdateEventCalendarPort(Protocol):
    """Driving Port for UpdateEventCalendarCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
