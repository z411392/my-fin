"""
Arbitraging Context 生命週期管理

遵循 P&A 架構：Driving Port → Application Service
"""

from injector import Injector, Module, provider, singleton

import logging

# Driving Ports
from libs.arbitraging.src.ports.get_events_port import GetEventsPort
from libs.arbitraging.src.ports.get_regime_port import GetRegimePort
from libs.arbitraging.src.ports.sync_catalog_port import SyncCatalogPort
from libs.arbitraging.src.ports.sync_reference_data_port import SyncReferenceDataPort

# Driven Ports
from libs.arbitraging.src.ports.catalog_provider_port import CatalogProviderPort
from libs.arbitraging.src.ports.us_stock_provider_port import USStockProviderPort
from libs.arbitraging.src.ports.economic_calendar_provider_port import (
    EconomicCalendarProviderPort,
)

# Application Services
from libs.arbitraging.src.application.queries.get_events import GetEventsQuery
from libs.arbitraging.src.application.queries.get_regime import GetRegimeQuery
from libs.arbitraging.src.application.commands.sync_catalog_command import (
    SyncCatalogCommand,
)
from libs.arbitraging.src.application.commands.sync_reference_data_command import (
    SyncReferenceDataCommand,
)

# Driven Adapters
from libs.arbitraging.src.adapters.driven.shioaji.shioaji_catalog_adapter import (
    ShioajiCatalogAdapter,
)
from libs.arbitraging.src.adapters.driven.wikipedia.wikipedia_us_stock_adapter import (
    WikipediaUSStockAdapter,
)
from libs.arbitraging.src.adapters.driven.static.economic_calendar_adapter import (
    StaticEconomicCalendarAdapter,
)


class ArbitragingModule(Module):
    """Arbitraging 依賴注入模組"""

    # ============================================
    # Driving Ports → Application Services
    # ============================================

    @singleton
    @provider
    def provide_get_events(
        self, calendar: EconomicCalendarProviderPort
    ) -> GetEventsPort:
        return GetEventsQuery(calendar)

    @singleton
    @provider
    def provide_get_regime(self) -> GetRegimePort:
        return GetRegimeQuery()

    @singleton
    @provider
    def provide_sync_catalog(
        self,
        catalog_adapter: CatalogProviderPort,
        us_stock_adapter: USStockProviderPort,
    ) -> SyncCatalogPort:
        return SyncCatalogCommand(
            catalog_adapter=catalog_adapter,
            us_stock_adapter=us_stock_adapter,
        )

    @singleton
    @provider
    def provide_sync_reference_data(self) -> SyncReferenceDataPort:
        return SyncReferenceDataCommand()

    # ============================================
    # Driven Ports → Adapters
    # ============================================

    @singleton
    @provider
    def provide_catalog_adapter(self) -> CatalogProviderPort:
        return ShioajiCatalogAdapter()

    @singleton
    @provider
    def provide_us_stock_adapter(self) -> USStockProviderPort:
        return WikipediaUSStockAdapter()

    @singleton
    @provider
    def provide_economic_calendar(
        self,
    ) -> EconomicCalendarProviderPort:
        return StaticEconomicCalendarAdapter()


_injector: Injector | None = None


def startup() -> Injector:
    """啟動依賴注入容器"""
    global _injector
    logging.basicConfig(level=logging.INFO)
    _injector = Injector([ArbitragingModule()])
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
configure = ArbitragingModule()
