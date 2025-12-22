"""Reporting CLI 入口

遵循 P&A 架構：CLI → Driving Adapter → Application Service
支援 async 方法執行
"""

import asyncio
import inspect

import fire

from apps.reporting.src.lifespan import startup, get_injector
from apps.reporting.src.adapters.driving.cli.reporting_controller import (
    ReportingController,
)


def main() -> None:
    """同步入口，支援 async 方法"""
    startup()

    # 創建並設置 event loop（Python 3.13 需要）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        controller = ReportingController(get_injector())
        result = fire.Fire(controller)

        # 如果結果是 coroutine，需要 await 它
        if inspect.iscoroutine(result):
            loop.run_until_complete(result)
    finally:
        loop.close()


if __name__ == "__main__":
    main()
