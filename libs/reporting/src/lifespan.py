"""報告生成服務 生命週期管理

遵循 P&A 架構
"""

import logging

from injector import Injector, Module, provider, singleton

# Driving Ports
from libs.reporting.src.ports.generate_daily_report_port import (
    GenerateDailyReportPort,
)
from libs.reporting.src.ports.generate_weekly_report_port import (
    GenerateWeeklyReportPort,
)
from libs.reporting.src.ports.export_daily_summary_port import ExportDailySummaryPort
from libs.reporting.src.ports.get_stock_row_port import GetStockRowPort

# Driven Ports (from other libs - GenerateDailyReportCommand dependencies)
from libs.monitoring.src.ports.notification_gateway_port import NotificationGatewayPort
from libs.monitoring.src.ports.fred_data_provider_port import FredDataProviderPort
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.arbitraging.src.ports.economic_calendar_provider_port import (
    EconomicCalendarProviderPort,
)
from libs.hunting.src.ports.scan_pairs_port import ScanPairsPort
from libs.linking.src.ports.get_supply_chain_link_port import GetSupplyChainLinkPort
from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort

# Application Services
from libs.reporting.src.application.commands.generate_daily_report import (
    GenerateDailyReportCommand,
)
from libs.reporting.src.application.commands.generate_weekly_report import (
    GenerateWeeklyReportCommand,
)
from libs.reporting.src.application.commands.export_daily_summary_command import (
    ExportDailySummaryCommand,
)
from libs.reporting.src.application.queries.get_stock_row import GetStockRowQuery

# Driven Adapters
from libs.hunting.src.adapters.driven.file.local_summary_file_adapter import (
    LocalSummaryFileAdapter,
)
from libs.hunting.src.ports.local_summary_storage_port import LocalSummaryStoragePort


class ReportGeneratorModule(Module):
    """報告生成服務 依賴注入模組"""

    @singleton
    @provider
    def provide_local_storage(self) -> LocalSummaryStoragePort:
        return LocalSummaryFileAdapter(base_dir="data/momentum")

    @singleton
    @provider
    def provide_export_daily_summary(
        self, local_storage: LocalSummaryStoragePort
    ) -> ExportDailySummaryPort:
        return ExportDailySummaryCommand(local_storage=local_storage)

    @singleton
    @provider
    def provide_get_stock_row(self) -> GetStockRowPort:
        return GetStockRowQuery()

    @singleton
    @provider
    def provide_generate_daily_report(
        self,
        notification_gateway: NotificationGatewayPort,
        market_data_adapter: MarketDataProviderPort,
        vpin_adapter: VPINCalculatorPort,
        fred_adapter: FredDataProviderPort,
        portfolio_adapter: PortfolioProviderPort,
        calendar_adapter: EconomicCalendarProviderPort,
        pairs_query: ScanPairsPort,
        supply_chain_query: GetSupplyChainLinkPort,
    ) -> GenerateDailyReportPort:
        return GenerateDailyReportCommand(
            notification_gateway=notification_gateway,
            market_data_adapter=market_data_adapter,
            vpin_adapter=vpin_adapter,
            fred_adapter=fred_adapter,
            portfolio_adapter=portfolio_adapter,
            calendar_adapter=calendar_adapter,
            pairs_query=pairs_query,
            supply_chain_query=supply_chain_query,
        )

    @singleton
    @provider
    def provide_generate_weekly_report(
        self,
        notification_gateway: NotificationGatewayPort,
        portfolio_provider: PortfolioProviderPort,
    ) -> GenerateWeeklyReportPort:
        return GenerateWeeklyReportCommand(
            notification_gateway=notification_gateway,
            portfolio_provider=portfolio_provider,
        )


_injector: Injector | None = None


def startup() -> Injector:
    """啟動依賴注入容器"""
    global _injector
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    _injector = Injector([ReportGeneratorModule()])
    return _injector


def shutdown() -> None:
    """關閉並釋放資源"""
    global _injector
    _injector = None


def get_injector() -> Injector:
    """取得依賴注入容器，若未初始化則自動啟動"""
    global _injector
    if _injector is None:
        startup()
    return _injector


def configure(binder) -> None:
    """Injector 配置函式（供其他 apps 組合使用）"""
    module = ReportGeneratorModule()
    binder.install(module)
