"""Reporting App 生命週期管理

Apps 層的 DI 配置，組合 libs 的能力
"""

import logging
from injector import Injector, Module, provider, singleton

# Libs Modules
from libs.reporting.src.lifespan import ReportGeneratorModule
from libs.hunting.src.lifespan import HuntingModule
from libs.linking.src.lifespan import LinkingModule
from libs.arbitraging.src.lifespan import ArbitragingModule

# Monitoring Driven Ports (這些在 monitoring lib 沒有統一 Module，需要直接綁定)
from libs.monitoring.src.ports.notification_gateway_port import NotificationGatewayPort
from libs.monitoring.src.ports.fred_data_provider_port import FredDataProviderPort
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort

# Monitoring Driven Adapters
from libs.monitoring.src.adapters.driven.gmail.gmail_notification_adapter import (
    GmailNotificationAdapter,
)
from libs.monitoring.src.adapters.driven.fred.fred_data_adapter import FredDataAdapter
from libs.monitoring.src.adapters.driven.yahoo.vpin_yahoo_adapter import (
    VPINYahooAdapter,
)

# Reviewing Driven Ports (Portfolio)
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.reviewing.src.adapters.driven.shioaji.shioaji_portfolio_adapter import (
    ShioajiPortfolioAdapter,
)

# Shioaji Client (needed for Portfolio)
from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient

# MarketData Port (hunting 的 Port，需用 monitoring 的 Adapter 覆蓋以取得 get_vix)
from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.monitoring.src.adapters.driven.yahoo.market_data_adapter import (
    YahooMarketDataAdapter,
)


class ReportingAppModule(Module):
    """Reporting App DI 配置，補齊 monitoring 等 libs 未提供的依賴

    Note: GenerateDailyReportPort 和 GenerateWeeklyReportPort
    直接由 ReportGeneratorModule 提供，不再需要 App 層轉換。
    """

    @singleton
    @provider
    def provide_notification_gateway(self) -> NotificationGatewayPort:
        return GmailNotificationAdapter()

    @singleton
    @provider
    def provide_fred_data(self) -> FredDataProviderPort:
        return FredDataAdapter()

    @singleton
    @provider
    def provide_vpin_calculator(self) -> VPINCalculatorPort:
        return VPINYahooAdapter()

    @singleton
    @provider
    def provide_shioaji_client(self) -> ShioajiClient:
        return ShioajiClient(simulation=False)

    @singleton
    @provider
    def provide_portfolio(self, client: ShioajiClient) -> PortfolioProviderPort:
        return ShioajiPortfolioAdapter(client=client)

    @singleton
    @provider
    def provide_market_data(self) -> MarketDataProviderPort:
        """覆蓋 hunting 的 MarketDataProviderPort，使用 monitoring 的 YahooMarketDataAdapter

        該 Adapter 有 get_vix() 方法，hunting 的 Adapter 沒有
        """
        return YahooMarketDataAdapter()


_injector: Injector | None = None


def startup() -> Injector:
    """啟動 DI 容器，組合所有必要的 Modules"""
    global _injector

    # 抑制噪音 logger
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 組合所有 Modules
    _injector = Injector(
        [
            HuntingModule(),
            LinkingModule(),
            ArbitragingModule(),
            ReportGeneratorModule(),
            ReportingAppModule(),
        ]
    )
    return _injector


def get_injector() -> Injector:
    """取得 DI 容器，若未初始化則自動啟動"""
    global _injector
    if _injector is None:
        startup()
    return _injector
