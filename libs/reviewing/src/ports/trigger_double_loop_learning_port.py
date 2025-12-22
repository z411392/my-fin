"""
TriggerDoubleLoopLearningPort - Driving Port

實作者: TriggerDoubleLoopLearningCommand
"""

from typing import Protocol


class TriggerDoubleLoopLearningPort(Protocol):
    """Driving Port for TriggerDoubleLoopLearningCommand"""

    def execute(self, *_args, **_kwargs):
        """執行主要操作"""
        ...
