"""Scanning CLI 入口

遵循 P&A 架構：CLI → Driving Adapter → Application Service
管理瀏覽器生命週期：startup → fire → shutdown
"""

import asyncio
import inspect

import fire

from apps.scanning.src.lifespan import (
    startup_async,
    shutdown_async,
    get_injector,
)
from apps.scanning.src.adapters.driving.cli.scanning_controller import (
    ScanningController,
)


def main() -> None:
    """同步入口，支援 async 方法"""
    # 創建並設置 event loop（Python 3.13 需要）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        # 啟動瀏覽器
        loop.run_until_complete(startup_async())

        # 使用 fire 執行 CLI
        controller = ScanningController(get_injector())
        result = fire.Fire(controller)

        # 如果結果是 coroutine，需要 await 它
        if inspect.iscoroutine(result):
            loop.run_until_complete(result)
    finally:
        # 關閉瀏覽器
        loop.run_until_complete(shutdown_async())
        loop.close()


if __name__ == "__main__":
    main()
