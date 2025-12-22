"""Maintaining CLI 入口

遵循 P&A 架構：CLI → Driving Adapter → Application Service
"""

import fire

from apps.maintaining.src.lifespan import startup, get_injector
from apps.maintaining.src.adapters.driving.cli.maintaining_controller import (
    MaintainingController,
)


def main() -> None:
    startup()
    controller = MaintainingController(get_injector())
    fire.Fire(controller)


if __name__ == "__main__":
    main()
