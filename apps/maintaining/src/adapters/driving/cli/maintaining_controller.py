"""Maintaining CLI Controller

Driving Adapter — 將 CLI 指令轉換為 Use Case 調用
"""

from injector import Injector

from libs.maintaining.src.ports.sync_data_port import SyncDataPort


class MaintainingController:
    """資料維護 CLI 控制器"""

    def __init__(self, injector: Injector) -> None:
        self._injector = injector

    def sync(self, force: bool = False) -> None:
        """同步經濟日曆與股票池"""
        print("同步資料中...")
        use_case = self._injector.get(SyncDataPort)
        use_case.execute(force=force)
        print("✅ 資料同步完成")
