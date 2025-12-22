"""
Linking Context 生命週期管理

遵循 P&A 架構：Driving Port → Application Service
"""

import logging
from injector import Injector, Module, provider, singleton

# Driving Ports
from libs.linking.src.ports.get_supply_chain_link_port import (
    GetSupplyChainLinkPort,
)

# Application Services
from libs.linking.src.application.queries.get_supply_chain_link import (
    GetSupplyChainLinkQuery,
)


class LinkingModule(Module):
    """Linking 依賴注入模組"""

    @singleton
    @provider
    def provide_get_supply_chain_link(self) -> GetSupplyChainLinkPort:
        return GetSupplyChainLinkQuery()


_injector: Injector | None = None


def startup() -> Injector:
    """啟動依賴注入容器"""
    global _injector
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    _injector = Injector([LinkingModule()])
    return _injector


def shutdown() -> None:
    """關閉並釋放資源"""
    global _injector
    _injector = None


def get_injector() -> Injector:
    """取得依賴注入容器"""
    if _injector is None:
        raise RuntimeError("Injector not initialized. Call startup() first.")
    return _injector


# Alias for libs composition
configure = LinkingModule()
