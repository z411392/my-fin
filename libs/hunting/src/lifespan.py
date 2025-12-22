"""
Hunting Context Lifecycle Management

Provides dependency injection startup and shutdown
Follows P&A architecture: Driving Port → Application Service
"""

import logging

from injector import Injector, Module, provider, singleton
from playwright.async_api import BrowserContext

# Clients
from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient
from libs.shared.src.clients.statementdog.statement_dog_client import StatementDogClient

# Driving Ports
from libs.hunting.src.ports.scan_residual_momentum_port import (
    ScanResidualMomentumPort,
)
from libs.hunting.src.ports.calculate_kelly_position_port import (
    CalculateKellyPositionPort,
)
from libs.hunting.src.ports.scan_pairs_port import ScanPairsPort

# Application Services
from libs.hunting.src.application.queries.scan_residual_momentum import (
    ScanResidualMomentumQuery,
)
from libs.hunting.src.application.queries.calculate_kelly_position import (
    CalculateKellyPositionQuery,
)
from libs.hunting.src.application.queries.scan_pairs import ScanPairsQuery

# Driven Ports
from libs.hunting.src.ports.i_fundamental_data_port import IFundamentalDataPort
from libs.hunting.src.ports.stock_list_provider_port import StockListProviderPort
from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.hunting.src.ports.local_summary_storage_port import LocalSummaryStoragePort


from libs.hunting.src.adapters.driven.shioaji.shioaji_stock_list_adapter import (
    ShioajiStockListAdapter,
)
from libs.hunting.src.adapters.driven.statementdog.statement_dog_fundamental_adapter import (
    StatementDogFundamentalAdapter,
)
from libs.hunting.src.adapters.driven.datareader.fama_french_adapter import (
    DatareaderFamaFrenchAdapter,
)
from libs.hunting.src.ports.fama_french_factor_provider_port import (
    FamaFrenchFactorProviderPort,
)
from libs.hunting.src.ports.sector_benchmark_provider_port import (
    SectorBenchmarkProviderPort,
)
from libs.hunting.src.adapters.driven.yahoo.market_data_adapter import (
    AlphaHunterMarketDataAdapter,
)
from libs.hunting.src.adapters.driven.static.catalog_sector_benchmark_adapter import (
    CatalogSectorBenchmarkAdapter,
)
from libs.hunting.src.adapters.driven.cache.cached_fundamental_adapter import (
    CachedFundamentalAdapter,
)
from libs.hunting.src.adapters.driven.file.local_summary_file_adapter import (
    LocalSummaryFileAdapter,
)


class HuntingModule(Module):
    """Hunting dependency injection module"""

    @singleton
    @provider
    def provide_scan_residual_momentum(
        self,
        stock_list_provider: StockListProviderPort,
        local_storage: LocalSummaryStoragePort,
        fundamental_provider: IFundamentalDataPort,
        fama_french_provider: FamaFrenchFactorProviderPort,
        market_data: MarketDataProviderPort,
        sector_benchmark: SectorBenchmarkProviderPort,
    ) -> ScanResidualMomentumPort:
        return ScanResidualMomentumQuery(
            stock_list_provider=stock_list_provider,
            local_storage=local_storage,
            fundamental_provider=fundamental_provider,
            fama_french_provider=fama_french_provider,
            market_data_provider=market_data,
            sector_benchmark_provider=sector_benchmark,
        )

    @singleton
    @provider
    def provide_market_data(self) -> MarketDataProviderPort:
        return AlphaHunterMarketDataAdapter()

    @singleton
    @provider
    def provide_calculate_kelly_position(
        self,
        market_data: MarketDataProviderPort,
    ) -> CalculateKellyPositionPort:
        return CalculateKellyPositionQuery(market_data_provider=market_data)

    @singleton
    @provider
    def provide_scan_pairs(self) -> ScanPairsPort:
        return ScanPairsQuery()

    # ============================================
    # Driven Ports → Real Adapters
    # ============================================

    @singleton
    @provider
    def provide_shioaji_client(self) -> ShioajiClient:
        return ShioajiClient(simulation=True)

    @singleton
    @provider
    def provide_statementdog_client(
        self, browser_context: BrowserContext
    ) -> StatementDogClient:
        return StatementDogClient(browser_provider=browser_context)

    @singleton
    @provider
    def provide_fundamental_data(
        self, client: StatementDogClient
    ) -> IFundamentalDataPort:
        """Provide cached StatementDog adapter (event-driven invalidation)"""
        inner = StatementDogFundamentalAdapter(client=client)
        return CachedFundamentalAdapter(inner=inner)

    @singleton
    @provider
    def provide_stock_list(self, client: ShioajiClient) -> StockListProviderPort:
        return ShioajiStockListAdapter(client=client)

    @singleton
    @provider
    def provide_local_storage(self) -> LocalSummaryStoragePort:
        return LocalSummaryFileAdapter(base_dir="data/momentum")

    @singleton
    @provider
    def provide_fama_french(self) -> FamaFrenchFactorProviderPort:
        return DatareaderFamaFrenchAdapter()

    @singleton
    @provider
    def provide_sector_benchmark(self) -> SectorBenchmarkProviderPort:
        return CatalogSectorBenchmarkAdapter()


_injector: Injector | None = None


def startup() -> Injector:
    """Start dependency injection container"""
    global _injector

    # Suppress noisy third-party loggers (arch.md R13)
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    _injector = Injector([HuntingModule()])
    return _injector


def shutdown() -> None:
    """Shutdown and release resources"""
    global _injector
    _injector = None


def get_injector() -> Injector:
    """Get dependency injection container"""
    if _injector is None:
        raise RuntimeError("Injector not initialized. Call startup() first.")
    return _injector


# Alias for libs composition
configure = HuntingModule()
