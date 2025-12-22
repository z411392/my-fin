"""Maintaining App 生命週期管理

Apps 層的 DI 配置，組合 libs 的能力
"""

import logging
from libs.maintaining.src.lifespan import get_injector as get_lib_injector

from injector import Injector


_injector: Injector | None = None


def startup() -> Injector:
    """啟動 DI 容器"""
    global _injector
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    # Use the lib's injector directly since it has all dependencies configured
    _injector = get_lib_injector()
    return _injector


def get_injector() -> Injector:
    """取得 DI 容器，若未初始化則自動啟動"""
    global _injector
    if _injector is None:
        startup()
    return _injector
