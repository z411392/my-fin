"""Scanning App 生命週期管理

Apps 層的 DI 配置，組合 libs 的能力
管理瀏覽器生命週期：startup_async 創建 → shutdown_async 銷毀
信號處理：graceful shutdown on Ctrl+C
"""

import logging

from injector import Injector, Module, provider, singleton
from playwright.async_api import async_playwright, Browser, BrowserContext, Playwright

# Libs
from libs.hunting.src.lifespan import configure as configure_alpha_hunter
from libs.linking.src.lifespan import configure as configure_supply_chain
from libs.reporting.src.lifespan import configure as configure_reporting

# Libs Ports
from libs.scanning.src.ports.run_daily_scan_port import RunDailyScanPort

# Libs Commands
from libs.scanning.src.application.commands.run_daily_scan_command import (
    RunDailyScanCommand,
)

# Libs Ports
from libs.hunting.src.ports.scan_residual_momentum_port import (
    ScanResidualMomentumPort,
)

# Monitoring Ports & Adapters
from libs.monitoring.src.ports.get_monitor_port import GetMonitorPort
from libs.monitoring.src.application.queries.get_monitor import GetMonitorQuery
from libs.monitoring.src.ports.market_data_provider_port import (
    MarketDataProviderPort as MonitoringMarketDataPort,
)
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.monitoring.src.ports.gex_calculator_port import GEXCalculatorPort
from libs.monitoring.src.adapters.driven.yahoo.market_data_adapter import (
    YahooMarketDataAdapter,
)
from libs.monitoring.src.adapters.driven.yahoo.vpin_yahoo_adapter import (
    VPINYahooAdapter,
)
from libs.monitoring.src.adapters.driven.yahoo.gex_yahoo_adapter import (
    GEXYahooAdapter,
)


_injector: Injector | None = None


class ScanningModule(Module):
    """Scanning App DI 配置"""

    def __init__(
        self,
        playwright: Playwright | None = None,
        browser: Browser | None = None,
        browser_context: BrowserContext | None = None,
    ):
        self._playwright = playwright
        self._browser = browser
        self._browser_context = browser_context

    @singleton
    @provider
    def provide_run_daily_scan(
        self, scan_residual: ScanResidualMomentumPort
    ) -> RunDailyScanPort:
        return RunDailyScanCommand(scan_residual=scan_residual)

    # Monitoring bindings
    @singleton
    @provider
    def provide_monitoring_market_data(self) -> MonitoringMarketDataPort:
        return YahooMarketDataAdapter()

    @singleton
    @provider
    def provide_vpin_calculator(self) -> VPINCalculatorPort:
        return VPINYahooAdapter()

    @singleton
    @provider
    def provide_gex_calculator(self) -> GEXCalculatorPort:
        return GEXYahooAdapter()

    @singleton
    @provider
    def provide_get_monitor(
        self,
        market_data: MonitoringMarketDataPort,
        vpin: VPINCalculatorPort,
        gex: GEXCalculatorPort,
    ) -> GetMonitorPort:
        return GetMonitorQuery(
            market_data_adapter=market_data,
            vpin_adapter=vpin,
            gex_adapter=gex,
        )

    @singleton
    @provider
    def provide_playwright(self) -> Playwright:
        """提供 Playwright 實例"""
        if self._playwright is None:
            raise RuntimeError("Playwright not initialized.")
        return self._playwright

    @singleton
    @provider
    def provide_browser(self) -> Browser:
        """提供 Browser 實例"""
        if self._browser is None:
            raise RuntimeError("Browser not initialized.")
        return self._browser

    @singleton
    @provider
    def provide_browser_context(self) -> BrowserContext:
        """提供 BrowserContext 實例"""
        if self._browser_context is None:
            raise RuntimeError("BrowserContext not initialized.")
        return self._browser_context


async def startup_async() -> Injector:
    """啟動 DI 容器（async 版本，管理瀏覽器生命週期）"""
    global _injector

    # 抑制第三方套件的噪音 logger（必須在 basicConfig 之前）
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    logging.getLogger("asyncio").setLevel(logging.CRITICAL)
    logging.getLogger("playwright").setLevel(logging.CRITICAL)
    # 抑制 cached_fundamental_adapter 的 log，避免打斷 progress bar
    logging.getLogger(
        "libs.hunting.src.adapters.driven.cache.cached_fundamental_adapter"
    ).setLevel(logging.WARNING)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # 創建瀏覽器
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    browser_context = await browser.new_context()

    # 創建 injector，將瀏覽器資源註冊
    scanning_module = ScanningModule(
        playwright=playwright,
        browser=browser,
        browser_context=browser_context,
    )

    _injector = Injector(
        [
            # scanning_module 必須放在最前面，因為它提供 BrowserContext
            # 而 configure_alpha_hunter (HuntingModule) 需要 BrowserContext
            scanning_module,
            configure_alpha_hunter,
            configure_supply_chain,
            configure_reporting,
        ]
    )

    return _injector


async def shutdown_async() -> None:
    """關閉 DI 容器和瀏覽器（按創建的反序銷毀）"""
    global _injector

    if _injector is None:
        return

    # 按反序銷毀：browser_context → browser → playwright
    try:
        browser_context = _injector.get(BrowserContext)
        if browser_context:
            await browser_context.close()
    except Exception:
        pass  # 靜默處理關閉錯誤

    try:
        browser = _injector.get(Browser)
        if browser:
            await browser.close()
    except Exception:
        pass  # 靜默處理關閉錯誤

    try:
        playwright = _injector.get(Playwright)
        if playwright:
            await playwright.stop()
    except Exception:
        pass  # 靜默處理關閉錯誤

    _injector = None


def startup() -> Injector:
    """啟動 DI 容器（同步版本，向後相容，不啟動瀏覽器）"""
    global _injector
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    _injector = Injector(
        [
            configure_alpha_hunter,
            configure_supply_chain,
            configure_reporting,
            ScanningModule(),
        ]
    )
    return _injector


def get_injector() -> Injector:
    """取得 DI 容器"""
    global _injector
    if _injector is None:
        raise RuntimeError("Injector not initialized. Call startup_async() first.")
    return _injector
