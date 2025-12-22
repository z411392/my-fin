"""
財報狗客戶端

使用 Playwright 抓取財報狗 (statementdog.com) 的財務指標資料。
"""

import asyncio
from typing import Any, Callable

from bs4 import BeautifulSoup
from injector import inject

from libs.shared.src.dtos.stock_metrics.contract_liabilities_dto import (
    ContractLiabilitiesDTO,
)
from libs.shared.src.dtos.stock_metrics.f_score_dto import FScoreDTO
from libs.shared.src.dtos.stock_metrics.river_chart_dto import RiverChartDTO
from libs.shared.src.dtos.statementdog.revenue_momentum_dto import RevenueMomentumDTO
from libs.shared.src.dtos.statementdog.earnings_quality_dto import EarningsQualityDTO
from libs.shared.src.dtos.statementdog.valuation_metrics_dto import ValuationMetricsDTO
from libs.shared.src.dtos.statementdog.fundamental_summary_dto import (
    FundamentalSummaryDTO,
)
from libs.shared.src.dtos.statementdog.fundamental_summary_map_dto import (
    FundamentalSummaryMap,
)
from libs.shared.src.dtos.statementdog.latest_and_yoy_dto import LatestAndYoYDTO
from libs.shared.src.dtos.statementdog.table_row_dto import (
    TableRowDTO,
)
from libs.shared.src.dtos.statementdog.parsed_analyze_result_dto import (
    ParsedAnalyzeResultDTO,
)
from libs.shared.src.dtos.statementdog.profit_margins_dto import (
    ProfitMarginsDTO,
)
from libs.shared.src.dtos.statementdog.financial_ratios_dto import (
    FinancialRatiosDTO,
)
from libs.shared.src.errors.stock_data_unavailable_error import (
    StockDataUnavailableError,
)
import logging
import concurrent.futures
import re


class StatementDogClient:
    """財報狗客戶端"""

    BASE_URL = "https://statementdog.com/analysis"

    # 所有可用的指標 slug
    METRICS = [
        # 財務報表
        "income-statement",
        "cash-flow-statement",
        "monthly-revenue",
        "eps",
        "bps",
        "dividend-policy",
        # 獲利能力
        "profit-margin",
        "roe-roa",
        "dupont",
        "asset-turnover",
        "operating-days",
        # 安全性分析
        "financial-structure-ratio",
        "liquidity-ratio",
        "interest-coverage",
        "cash-flow-analysis",
        # 成長力分析
        "revenue-growth-rate",
        "profit-growth-rate",
        # 價值評估
        "pe",
        "pb",
        "dividend-yield",
        # 財務報表細項
        "liabilities-and-equity",
        # 董監與籌碼
        "directors-holders",
        # 關鍵指標
        "key-indicator",
        "free-cash-flow-yield",
    ]

    # 深度健檢必備指標 (只包含免登入可抓取的頁面)
    ESSENTIAL_METRICS = [
        "revenue-growth-rate",  # 營收動能
        "income-statement",  # 獲利品質 (NI, 營收)
        "cash-flow-statement",  # 獲利品質 (CFO, FCF)
        "profit-margin",  # F-Score (毛利率)
        "liabilities-and-equity",  # F-Score (長期負債, 股本, 流動負債)
        "roe-roa",  # F-Score (ROA)
        "pb",  # 評價 (PB 河流圖)
        "eps",  # TTM EPS (供 spreadsheet 計算 PE)
    ]

    @inject
    def __init__(
        self,
        browser_provider: Any = None,
        headless: bool = True,
        delay_seconds: float = 0.3,
    ):
        """
        初始化客戶端

        Args:
            browser_provider: 外部提供的 PlaywrightBrowserProvider (優先使用)
            headless: 是否使用無頭模式 (只在沒提供 browser_provider 時使用)
            delay_seconds: 每次請求之間的延遲秒數
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._browser_provider = browser_provider
        self._headless = headless
        self._delay = delay_seconds

    def analyze(
        self, symbol: str, metrics: list[str] | None = None
    ) -> ParsedAnalyzeResultDTO:
        """
        分析股票，抓取所有財務指標

        Args:
            symbol: 股票代號
            metrics: 指定要抓取的指標列表 (預設抓取全部)

        Returns:
            包含所有指標資料的字典
        """
        # 檢查是否已在運行中的 event loop
        try:
            asyncio.get_running_loop()
            # 如果已經有 event loop，在新的 thread 中運行
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, self._analyze_async(symbol, metrics)
                )
                return future.result()
        except RuntimeError:
            # 沒有 event loop，正常使用 asyncio.run
            return asyncio.run(self._analyze_async(symbol, metrics))

    async def _analyze_async(
        self, symbol: str, metrics: list[str] | None = None
    ) -> ParsedAnalyzeResultDTO:
        """非同步分析實作 (使用注入的 BrowserContext)"""
        # 使用注入的 browser_provider
        if self._browser_provider is None:
            raise RuntimeError("BrowserContext not injected. Please inject via DI.")

        context = self._browser_provider
        page = await context.new_page()
        page.set_default_timeout(30000)

        try:
            # 重用 _analyze_with_page 邏輯
            result = await self._analyze_with_page(page, symbol)
        finally:
            await page.close()

        return result

    def _validate_data_available(
        self, symbol: str, result: ParsedAnalyzeResultDTO, metrics: list[str]
    ) -> None:
        """
        驗證是否成功取得資料

        如果所有指標都無法取得資料，拋出 StockDataUnavailableError。
        這通常發生在興櫃股票、已下市股票、或其他財報狗不支援的股票。

        Args:
            symbol: 股票代號
            result: 爬蟲結果
            metrics: 預期取得的指標列表
        """
        valid_count = 0
        error_messages: list[str] = []

        for metric in metrics:
            data = result.get(metric)
            if data is None:
                continue
            # 檢查是否為錯誤結果
            if isinstance(data, dict) and "error" in data:
                error_messages.append(f"{metric}: {data['error']}")
                continue
            # 檢查是否有有效資料
            if isinstance(data, list) and len(data) > 0:
                valid_count += 1

        if valid_count == 0:
            # 所有指標都無法取得
            reason = "所有指標頁面皆無法取得資料（可能為興櫃股票、已下市股票或其他不支援的股票類型）"
            if error_messages:
                reason += "\n錯誤訊息:\n" + "\n".join(
                    error_messages[:3]
                )  # 只顯示前3個錯誤
            raise StockDataUnavailableError(symbol=symbol, reason=reason)

        # 如果成功取得的指標數量少於一半，發出警告但不拋錯
        if valid_count < len(metrics) / 2:
            self._logger.warning(
                f"[{symbol}] 僅取得 {valid_count}/{len(metrics)} 個指標，資料可能不完整"
            )

    def _parse_table(self, html: str) -> list[TableRowDTO]:
        """解析 HTML 表格"""
        soup = BeautifulSoup(html, "lxml")
        tables = soup.find_all("table")

        if not tables:
            return []

        table = tables[0]
        rows = table.find_all("tr")

        if len(rows) < 2:
            return []

        # 解析表頭
        header_row = rows[0]
        headers = [th.get_text(strip=True) for th in header_row.find_all(["th", "td"])]

        # 解析資料列
        data_rows = []
        for row in rows[1:]:
            cells = row.find_all(["th", "td"])
            if not cells:
                continue

            row_name = cells[0].get_text(strip=True)
            row_data: TableRowDTO = {"name": row_name, "values": {}}

            for i, cell in enumerate(cells[1:], 1):
                if i < len(headers):
                    period = headers[i]
                    value = self._parse_value(cell.get_text(strip=True))
                    row_data["values"][period] = value

            data_rows.append(row_data)

        return data_rows

    def _parse_value(self, text: str) -> float | str | None:
        """解析數值"""
        if not text or text in ["-", "N/A", "--"]:
            return None

        cleaned = text.replace("%", "").replace(",", "").strip()

        try:
            return float(cleaned)
        except ValueError:
            return text

    # ========================================
    # 便捷方法：直接取得結構化數據
    # ========================================

    def get_revenue_momentum(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> RevenueMomentumDTO:
        """
        取得營收動能指標

        Args:
            symbol: 股票代號
            data: 已抓取的數據（可選，避免重複抓取）

        Returns:
            RevenueMomentumDTO 格式的字典
        """
        if data is None:
            data = self.analyze(symbol)

        growth_data = data.get("revenue-growth-rate", [])

        # 預設值
        short_term_yoy = 0.0
        long_term_yoy = 0.0
        current_yoy = 0.0

        # 從 revenue-growth-rate 頁面提取 YoY 數據
        for row in growth_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                values = row.get("values", {})

                if "營收年增率" in name or "Revenue YoY" in name:
                    # 取最新的值作為當月 YoY
                    sorted_periods = sorted(values.keys(), reverse=True)
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            current_yoy = float(val)

                        # 計算近 3 月平均
                        recent_3 = [
                            values[p]
                            for p in sorted_periods[:3]
                            if isinstance(values.get(p), (int, float))
                        ]
                        if recent_3:
                            short_term_yoy = sum(recent_3) / len(recent_3)

                        # 計算近 12 月平均
                        recent_12 = [
                            values[p]
                            for p in sorted_periods[:12]
                            if isinstance(values.get(p), (int, float))
                        ]
                        if recent_12:
                            long_term_yoy = sum(recent_12) / len(recent_12)
                    break

        is_accelerating = short_term_yoy > long_term_yoy and current_yoy > 0

        return {
            "symbol": symbol,
            "short_term_yoy": short_term_yoy,
            "long_term_yoy": long_term_yoy,
            "current_yoy": current_yoy,
            "is_accelerating": is_accelerating,
        }

    def get_earnings_quality(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> EarningsQualityDTO:
        """
        取得獲利品質指標

        Returns:
            EarningsQualityDTO 格式的字典
        """
        if data is None:
            data = self.analyze(symbol)

        cash_flow_data = data.get("cash-flow-statement", [])
        income_data = data.get("income-statement", [])

        cfo = 0.0
        net_income = 0.0
        fcf_ttm = 0.0

        # 從 cash-flow-statement 提取 CFO 和 FCF
        for row in cash_flow_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                values = row.get("values", {})
                sorted_periods = sorted(
                    values.keys(), key=self._parse_period_key, reverse=True
                )

                if "營業現金流" in name or "Operating Cash Flow" in name:
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            cfo = float(val)

                if "自由現金流" in name or "Free Cash Flow" in name:
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            fcf_ttm = float(val)

        # 從 income-statement 提取 Net Income
        for row in income_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                values = row.get("values", {})
                sorted_periods = sorted(
                    values.keys(), key=self._parse_period_key, reverse=True
                )

                if "稅後淨利" in name or "Net Income" in name:
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            net_income = float(val)
                    break

        cfo_ni_ratio = cfo / net_income if net_income != 0 else 0.0
        is_quality = (cfo_ni_ratio > 0.5) or (fcf_ttm > 0)

        # 計算 Accrual Ratio = (NI - CFO) / Total Assets
        # 從 liabilities-and-equity 取得總資產 (總負債 + 股東權益)
        liab_data = data.get("liabilities-and-equity", [])
        total_liabilities = 0.0
        shareholders_equity = 0.0

        for row in liab_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                values = row.get("values", {})
                sorted_periods = sorted(
                    values.keys(), key=self._parse_period_key, reverse=True
                )

                if "總負債" in name or "Total Liabilities" in name:
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            total_liabilities = float(val)

                if "股東權益" in name or "Shareholders" in name:
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            shareholders_equity = float(val)

        total_assets = total_liabilities + shareholders_equity
        accrual_ratio = (net_income - cfo) / total_assets if total_assets > 0 else None

        return {
            "symbol": symbol,
            "cfo": cfo,
            "net_income": net_income,
            "cfo_ni_ratio": cfo_ni_ratio,
            "fcf_ttm": fcf_ttm,
            "is_quality": is_quality,
            "accrual_ratio": round(accrual_ratio, 4)
            if accrual_ratio is not None
            else None,
        }

    def get_valuation_metrics(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> ValuationMetricsDTO:
        """
        取得評價指標

        Returns:
            ValuationMetricsDTO 格式的字典
        """
        if data is None:
            data = self.analyze(symbol)

        pe_data = data.get("pe", [])

        current_pe = 0.0
        pe_values: list[float] = []

        # 從 pe 頁面提取本益比數據
        for row in pe_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                values = row.get("values", {})

                if "本益比" in name or "P/E" in name:
                    sorted_periods = sorted(values.keys(), reverse=True)
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            current_pe = float(val)

                    # 收集所有有效的 PE 值
                    for v in values.values():
                        if isinstance(v, (int, float)) and v > 0:
                            pe_values.append(float(v))
                    break

        # 如果 PE 頁面沒資料，current_pe 維持 0 (讓 spreadsheet 用 Close/EPS 計算)

        # 計算百分位數
        pe_values.sort()
        n = len(pe_values)

        def percentile(p: float) -> float:
            if n == 0:
                return 0.0
            idx = int(p * (n - 1))
            return pe_values[min(idx, n - 1)]

        pe_5th = percentile(0.05)
        pe_25th = percentile(0.25)
        pe_50th = percentile(0.50)
        pe_75th = percentile(0.75)
        pe_95th = percentile(0.95)

        is_safe = current_pe < pe_95th if pe_95th > 0 and current_pe > 0 else False

        return {
            "symbol": symbol,
            "current_pe": current_pe,
            "pe_percentile_5": pe_5th,
            "pe_percentile_25": pe_25th,
            "pe_percentile_50": pe_50th,
            "pe_percentile_75": pe_75th,
            "pe_percentile_95": pe_95th,
            "is_safe": is_safe,
        }

    def _get_ttm_eps(self, data: ParsedAnalyzeResultDTO) -> float | None:
        """從 EPS 頁面取得 TTM EPS (最近 4 季加總)"""
        eps_data = data.get("eps", [])

        for row in eps_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                if "單季EPS" in name or "EPS" in name:
                    values = row.get("values", {})
                    # 取最近 4 季的 EPS
                    sorted_periods = sorted(
                        values.keys(), key=self._parse_period_key, reverse=True
                    )
                    recent_4 = []
                    for p in sorted_periods[:4]:
                        val = values.get(p)
                        if isinstance(val, (int, float)):
                            recent_4.append(float(val))
                    if recent_4:
                        return round(sum(recent_4), 2)
                    break

        return None

    def is_fundamentally_valid(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> bool:
        """
        綜合判斷基本面是否有效

        條件：
        1. 營收加速中
        2. 獲利品質良好
        3. 評價在安全邊際內

        Args:
            symbol: 股票代號
            data: 已抓取的數據（可選）

        Returns:
            是否通過所有基本面濾網
        """
        if data is None:
            data = self.analyze(symbol)

        revenue = self.get_revenue_momentum(symbol, data)
        quality = self.get_earnings_quality(symbol, data)
        valuation = self.get_valuation_metrics(symbol, data)

        return (
            revenue.get("is_accelerating", False)
            and quality.get("is_quality", False)
            and valuation.get("is_safe", False)
        )

    def get_fundamental_summary(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> FundamentalSummaryDTO:
        """
        取得基本面摘要（包含所有濾網結果）

        Returns:
            包含營收動能、獲利品質、評價指標的完整摘要
        """
        if data is None:
            # 使用 essential metrics 加速抓取
            data = self.analyze(symbol, metrics=self.ESSENTIAL_METRICS)

        revenue = self.get_revenue_momentum(symbol, data)
        quality = self.get_earnings_quality(symbol, data)
        valuation = self.get_valuation_metrics(symbol, data)

        # 取得河流圖資料 (PB 可用，PE 需登入)
        river_chart = self.get_river_chart_data(symbol, data)

        # Add F-Score
        f_score_dto = self.get_f_score(symbol, data)
        f_score = {"score": f_score_dto["total_score"], "details": f_score_dto}

        # Get profit margins from profit-margin page
        profit_margins = self._get_profit_margins(data)

        # Get financial ratios from roe-roa and liabilities-and-equity pages
        financial_ratios = self._get_financial_ratios(data)

        return {
            "symbol": symbol,
            "is_valid": self.is_fundamentally_valid(symbol, data),
            "revenue_momentum": revenue,
            "earnings_quality": quality,
            "valuation_metrics": valuation,
            "river_chart": {
                "current_pb": river_chart["current_pb"],
                "pb_zone": river_chart["pb_zone"],
                "pb_median": river_chart["pb_median"],
                "pb_low": river_chart["pb_low_avg"],
                "pb_high": river_chart["pb_high_avg"],
            },
            "f_score": f_score,
            "profit_margins": profit_margins,
            "financial_ratios": financial_ratios,
        }

    def batch_get_fundamental_summaries(
        self,
        symbols: list[str],
        max_concurrent: int = 3,
        on_progress: Callable[[str, FundamentalSummaryDTO], None] | None = None,
    ) -> FundamentalSummaryMap:
        """
        批次並發取得多檔股票的基本面摘要

        Args:
            symbols: 股票代號列表
            max_concurrent: 最大並發分頁數 (預設 3)
            on_progress: 進度回調函數 (symbol, result) -> None

        Returns:
            {symbol: summary} 的字典
        """
        return asyncio.run(
            self._batch_analyze_async(symbols, max_concurrent, on_progress)
        )

    async def _batch_analyze_async(
        self, symbols: list[str], max_concurrent: int, on_progress: Any = None
    ) -> FundamentalSummaryMap:
        """批次並發分析 - 使用注入的 BrowserContext"""
        results: dict[str, FundamentalSummaryDTO] = {}
        semaphore = asyncio.Semaphore(max_concurrent)

        # 使用注入的 browser_provider (BrowserContext)
        if self._browser_provider is None:
            raise RuntimeError("BrowserContext not injected. Please inject via DI.")

        context = self._browser_provider  # BrowserContext
        total = len(symbols)
        completed_count = 0

        async def analyze_one(symbol: str) -> tuple[str, FundamentalSummaryDTO]:
            nonlocal completed_count
            async with semaphore:
                try:
                    # 在共用 context 中開新分頁
                    self._logger.debug(
                        f"[{symbol}] 開始分析 ({completed_count + 1}/{total})..."
                    )
                    page = await context.new_page()
                    page.set_default_timeout(30000)
                    data = await self._analyze_with_page(page, symbol)
                    await page.close()

                    # 使用 get_fundamental_summary 統一建構資料 (重用共同邏輯)
                    result_data = self.get_fundamental_summary(symbol, data)

                    completed_count += 1
                    f_score = result_data.get("f_score", {})
                    score_val = (
                        f_score.get("score") if isinstance(f_score, dict) else f_score
                    )
                    self._logger.debug(
                        f"[{symbol}] 分析完成 (F-Score: {score_val}) - {completed_count}/{total}"
                    )

                    # 觸發回調
                    if on_progress:
                        try:
                            if asyncio.iscoroutinefunction(on_progress):
                                await on_progress(symbol, result_data)
                            else:
                                on_progress(symbol, result_data)
                        except Exception as e:
                            self._logger.debug(f"[{symbol}] Callback failed: {e}")

                    return symbol, result_data
                except Exception as e:
                    self._logger.debug(f"[{symbol}] 分析失敗: {e}")
                    error_data = {"symbol": symbol, "error": str(e)}

                    # 即使失敗也要觸發回調，讓進度條前進
                    if on_progress:
                        try:
                            if asyncio.iscoroutinefunction(on_progress):
                                await on_progress(symbol, error_data)
                            else:
                                on_progress(symbol, error_data)
                        except Exception as cb_e:
                            self._logger.debug(
                                f"[{symbol}] Error Callback failed: {cb_e}"
                            )

                    return symbol, error_data

        tasks = [analyze_one(s) for s in symbols]
        completed = await asyncio.gather(*tasks, return_exceptions=True)

        # 注意：不關閉 context 和 browser，由 lifespan 管理

        for item in completed:
            if isinstance(item, tuple):
                symbol, summary = item
                results[symbol] = summary

        return results

    async def _analyze_with_page(
        self, page: Any, symbol: str
    ) -> ParsedAnalyzeResultDTO:
        """使用指定分頁分析單一股票"""
        # 財報狗 URL 使用純數字代號，移除 .TW 後綴
        clean_symbol = symbol.replace(".TW", "").replace(".TWO", "")
        result: ParsedAnalyzeResultDTO = {"symbol": symbol}

        # 使用類別常數 ESSENTIAL_METRICS (免登入頁面)
        essential_metrics = self.ESSENTIAL_METRICS

        for i, metric in enumerate(essential_metrics, 1):
            url = f"{self.BASE_URL}/{clean_symbol}/{metric}"
            try:
                self._logger.debug(
                    f"[{symbol}]  ➜ 正在抓取 {metric} ({i}/{len(essential_metrics)})..."
                )
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("table", timeout=10000)

                html = await page.content()
                result[metric] = self._parse_table(html)

                await asyncio.sleep(self._delay)

            except Exception as e:
                self._logger.debug(f"[{symbol}]  ⚠️ {metric} 失敗: {e}")
                result[metric] = {"error": str(e)}

        # 驗證是否成功取得資料
        self._validate_data_available(symbol, result, essential_metrics)

        return result

    # ========================================
    # Alpha-Dog 策略相關方法 (F-Score / River Chart / Contract Liabilities)
    # ========================================

    def get_contract_liabilities(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> ContractLiabilitiesDTO:
        """
        取得合約負債趨勢

        Args:
            symbol: 股票代號
            data: 已抓取的數據

        Returns:
            ContractLiabilitiesDTO: 合約負債趨勢分析結果
        """
        if data is None:
            data = self.analyze(symbol)

        liabilities_data = data.get("liabilities-and-equity", [])

        current_val = 0.0
        prev_val = 0.0
        yoy = 0.0
        latest_period = ""
        compare_period = ""

        # 暫存所有合約負債相關數值 {period: total_value}
        cl_map: dict[str, float] = {}

        for row in liabilities_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                values = row.get("values", {})

                if "合約負債" in name or "Contract Liabilities" in name:
                    for period, val in values.items():
                        if isinstance(val, (int, float)):
                            cl_map[period] = cl_map.get(period, 0.0) + float(val)

        if cl_map:
            # 用自訂排序確保正確的時間順序
            sorted_periods = sorted(
                cl_map.keys(), key=self._parse_period_key, reverse=True
            )
            if sorted_periods:
                latest_period = sorted_periods[0]
                current_val = cl_map[latest_period]

                # 找去年同期 (YoY)
                yoy_period = self._find_yoy_period(latest_period, sorted_periods)
                if yoy_period and yoy_period in cl_map:
                    compare_period = yoy_period
                    prev_val = cl_map[yoy_period]
                elif len(sorted_periods) > 1:
                    # Fallback: 使用前一期
                    compare_period = sorted_periods[1]
                    prev_val = cl_map[compare_period]

                if prev_val > 0:
                    yoy = (current_val - prev_val) / prev_val

        return ContractLiabilitiesDTO(
            symbol=symbol,
            current_value=current_val,
            previous_value=prev_val,
            yoy=yoy,
            is_growing=yoy > 0,
            latest_period=latest_period,
            compare_period=compare_period,
        )

    def get_f_score(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> FScoreDTO:
        """
        計算 Piotroski F-Score (0-9 分)

        使用最近一季數據 vs 去年同期 (YoY) 進行比較，以消除季節性影響。

        可用的頁面:
        - roe-roa: ROA (直接使用)
        - profit-margin: 毛利率 (直接使用)
        - income-statement: 稅後淨利, 營收
        - cash-flow-statement: 營業現金流
        - liabilities-and-equity: 長期負債, 總負債, 淨值 (注意: 無資產總計, 無流動資產)

        無法計算的指標 (需登入頁面):
        - Current Ratio (需要 liquidity-ratio 或 流動資產)
        - Asset Turnover (需要 asset-turnover 或 資產總計)
        """
        if data is None:
            data = self.analyze(symbol)

        # 1. 從可用頁面準備數據
        # ROA 直接從 roe-roa 頁面取得
        roa_data = self._get_latest_and_yoy(data, "roe-roa", ["ROA", "資產報酬率"])

        # CFO 從 cash-flow-statement
        cfo_data = self._get_latest_and_yoy(
            data, "cash-flow-statement", ["營業現金流", "Operating Cash Flow"]
        )

        # Net Income 從 income-statement
        ni_data = self._get_latest_and_yoy(
            data, "income-statement", ["稅後淨利", "Net Income"]
        )

        # 營收從 income-statement (用於估算 Asset Turnover 如果有總資產)
        revenue_data = self._get_latest_and_yoy(
            data, "income-statement", ["營收", "營業收入", "Revenue"]
        )

        # 從 liabilities-and-equity 取得負債數據
        ltd_data = self._get_latest_and_yoy(
            data,
            "liabilities-and-equity",
            ["長期負債", "Long-term Liabilities"],
        )
        total_debt_data = self._get_latest_and_yoy(
            data, "liabilities-and-equity", ["總負債", "Total Liabilities"]
        )
        equity_data = self._get_latest_and_yoy(
            data, "liabilities-and-equity", ["淨值", "Equity", "股東權益"]
        )

        # 流動負債 (用於估算流動比例變化)
        current_liab_data = self._get_latest_and_yoy(
            data, "liabilities-and-equity", ["流動負債", "Current Liabilities"]
        )

        # 毛利率從 profit-margin 頁面
        gm_data = self._get_latest_and_yoy(
            data, "profit-margin", ["毛利率", "Gross Margin"]
        )

        # 2. 提取數值
        roa_val = roa_data["current"]
        roa_prev = roa_data["prev"]
        cfo_val = cfo_data["current"]
        ni_val = ni_data["current"]

        # 計算總資產 (Total Assets = Total Debt + Equity)
        total_debt_curr = total_debt_data["current"]
        total_debt_prev = total_debt_data["prev"]
        equity_curr = equity_data["current"]
        equity_prev = equity_data["prev"]
        assets_curr = total_debt_curr + equity_curr
        assets_prev = total_debt_prev + equity_prev

        # 長期負債/總資產 比率
        ltd_curr = ltd_data["current"]
        ltd_prev = ltd_data["prev"]
        lev_curr = ltd_curr / assets_curr if assets_curr > 0 else 0.0
        lev_prev = ltd_prev / assets_prev if assets_prev > 0 else 0.0

        # 流動比率無法計算 (缺少流動資產)，使用流動負債變化作為替代
        # 流動負債下降 = 流動性改善
        cl_curr = current_liab_data["current"]
        cl_prev = current_liab_data["prev"]

        # 毛利率
        gm_curr = gm_data["current"]
        gm_prev = gm_data["prev"]

        # 資產周轉率 = 營收 / 總資產
        rev_curr = revenue_data["current"]
        rev_prev = revenue_data["prev"]
        at_curr = (rev_curr / assets_curr) if assets_curr > 0 else 0.0
        at_prev = (rev_prev / assets_prev) if assets_prev > 0 else 0.0

        # 3. 計算分數
        score = 0

        # --- Profitability (4 分) ---
        # ROA > 0
        roa_positive = roa_val > 0
        if roa_positive:
            score += 1

        # CFO > 0
        cfo_positive = cfo_val > 0
        if cfo_positive:
            score += 1

        # Delta ROA > 0 (YoY)
        roa_improving = roa_val > roa_prev
        if roa_improving:
            score += 1

        # Accruals: CFO > Net Income
        accruals_valid = cfo_val > ni_val
        if accruals_valid:
            score += 1

        # --- Leverage / Liquidity (3 分) ---
        # Delta Leverage < 0 (Long Term Debt / Assets 下降)
        leverage_improving = (
            lev_curr < lev_prev if (assets_curr > 0 and assets_prev > 0) else False
        )
        if leverage_improving:
            score += 1

        # 流動性改善: 流動負債下降 (替代 Current Ratio)
        # 注意: 這是替代指標，原始 F-Score 使用 Current Ratio 上升
        liquidity_improving = (
            cl_curr < cl_prev if (cl_curr > 0 and cl_prev > 0) else False
        )
        if liquidity_improving:
            score += 1

        # No New Shares: 使用總資產變化替代 (無法直接取得股本)
        # 如果淨值增加但非來自增資，認為沒有增發
        # 簡化判斷: 淨值增加幅度 < 獲利增加幅度
        if equity_curr > 0 and equity_prev > 0 and ni_val > 0:
            equity_change_pct = (equity_curr - equity_prev) / equity_prev
            ni_contribution = ni_val / equity_prev  # 預期的淨值增加
            no_new_shares = equity_change_pct <= ni_contribution * 1.2  # 留 20% 容忍度
        else:
            no_new_shares = False
        if no_new_shares:
            score += 1

        # --- Efficiency (2 分) ---
        # Delta Margin > 0 (Gross Margin 改善)
        margin_improving = gm_curr > gm_prev if (gm_curr > 0 or gm_prev > 0) else False
        if margin_improving:
            score += 1

        # Delta Turnover > 0 (Asset Turnover 改善)
        turnover_improving = (
            at_curr > at_prev if (at_curr > 0 or at_prev > 0) else False
        )
        if turnover_improving:
            score += 1

        # 使用 Current Ratio 替代值 (流動負債倒數變化) 作為報告用
        liq_curr = (1 / cl_curr * 1e9) if cl_curr > 0 else 0.0  # 標準化

        return FScoreDTO(
            symbol=symbol,
            total_score=score,
            profitability_score=sum(
                [roa_positive, cfo_positive, roa_improving, accruals_valid]
            ),
            leverage_liquidity_score=sum(
                [leverage_improving, liquidity_improving, no_new_shares]
            ),
            efficiency_score=sum([margin_improving, turnover_improving]),
            roa_positive=roa_positive,
            cfo_positive=cfo_positive,
            roa_improving=roa_improving,
            accruals_valid=accruals_valid,
            leverage_improving=leverage_improving,
            liquidity_improving=liquidity_improving,
            no_new_shares=no_new_shares,
            margin_improving=margin_improving,
            turnover_improving=turnover_improving,
            roa=roa_val,
            cfo=cfo_val,
            net_income=ni_val,
            long_term_debt_ratio=lev_curr,
            current_ratio=liq_curr,
            gross_margin=gm_curr,
            asset_turnover=at_curr,
        )

    def get_river_chart_data(
        self, symbol: str, data: ParsedAnalyzeResultDTO | None = None
    ) -> RiverChartDTO:
        """
        取得河流圖數據 (PE/PB 區間)
        """
        if data is None:
            data = self.analyze(symbol)

        pe_values, current_pe = self._get_historical_values(
            data, "pe", ["本益比", "P/E"]
        )
        pb_values, current_pb = self._get_historical_values(
            data, "pb", ["股價淨值比", "P/B"]
        )

        def calculate_zone(
            val: float | None, high: float | None, low: float | None
        ) -> str:
            if val is None or high is None or low is None:
                return "N/A"
            if val < low:
                return "Cheap"
            if val > high:
                return "Expensive"
            return "Fair"

        # 計算歷史區間 (簡單版：使用 percentile)
        pe_high = None
        pe_low = None
        pe_median = None

        if pe_values:
            pe_values.sort()
            n = len(pe_values)
            pe_low = pe_values[int(n * 0.25)]  # 25th percentile as Low band
            pe_high = pe_values[int(n * 0.75)]  # 75th percentile as High band
            pe_median = pe_values[int(n * 0.5)]

        pb_high = None
        pb_low = None
        pb_median = None

        if pb_values:
            pb_values.sort()
            n = len(pb_values)
            pb_low = pb_values[int(n * 0.25)]
            pb_high = pb_values[int(n * 0.75)]
            pb_median = pb_values[int(n * 0.5)]

        return {
            "symbol": symbol,
            "current_pe": current_pe,
            "current_pb": current_pb,
            "pe_high_avg": pe_high,
            "pe_low_avg": pe_low,
            "pe_median": pe_median,
            "pe_zone": calculate_zone(current_pe, pe_high, pe_low),
            "pb_high_avg": pb_high,
            "pb_low_avg": pb_low,
            "pb_median": pb_median,
            "pb_zone": calculate_zone(current_pb, pb_high, pb_low),
            "pe_history": pe_values,
            "pb_history": pb_values,
        }

    def _get_profit_margins(self, data: ParsedAnalyzeResultDTO) -> ProfitMarginsDTO:
        """
        取得利潤率指標 (從 profit-margin 頁面)

        Returns:
            包含 gross_margin, operating_margin, net_margin 的字典
        """
        gm_data = self._get_latest_and_yoy(
            data, "profit-margin", ["毛利率", "Gross Margin"]
        )
        om_data = self._get_latest_and_yoy(
            data, "profit-margin", ["營業利益率", "Operating Margin"]
        )
        nm_data = self._get_latest_and_yoy(
            data, "profit-margin", ["淨利率", "Net Margin", "稅後淨利率"]
        )

        return {
            "gross_margin": gm_data["current"] if gm_data["current"] != 0 else None,
            "operating_margin": om_data["current"] if om_data["current"] != 0 else None,
            "net_margin": nm_data["current"] if nm_data["current"] != 0 else None,
        }

    def _get_financial_ratios(self, data: ParsedAnalyzeResultDTO) -> FinancialRatiosDTO:
        """
        取得財務比率指標 (從 roe-roa 和 liabilities-and-equity 頁面)

        Returns:
            包含 roe, roa, total_debt, equity, ttm_eps 的字典
            (debt_ratio 和 pe 由 spreadsheet 公式計算)
        """
        # ROE / ROA 從 roe-roa 頁面
        roe_data = self._get_latest_and_yoy(data, "roe-roa", ["ROE", "股東權益報酬率"])
        roa_data = self._get_latest_and_yoy(data, "roe-roa", ["ROA", "資產報酬率"])

        # 總負債和淨值 (供 spreadsheet 計算 DebtRatio)
        total_debt_data = self._get_latest_and_yoy(
            data, "liabilities-and-equity", ["總負債", "Total Liabilities"]
        )
        equity_data = self._get_latest_and_yoy(
            data, "liabilities-and-equity", ["淨值", "股東權益", "Shareholders' Equity"]
        )

        # TTM EPS (供 spreadsheet 計算 PE)
        ttm_eps = self._get_ttm_eps(data)

        return {
            "roe": roe_data["current"] if roe_data["current"] != 0 else None,
            "roa": roa_data["current"] if roa_data["current"] != 0 else None,
            "total_debt": total_debt_data["current"]
            if total_debt_data["current"] != 0
            else None,
            "equity": equity_data["current"] if equity_data["current"] != 0 else None,
            "ttm_eps": ttm_eps,
        }

    # --- Helpers ---

    def _get_latest_and_yoy(
        self, data: dict, page_key: str, keywords: list[str]
    ) -> LatestAndYoYDTO:
        """Helper to extract latest and year-ago values for a metric"""
        page_data = data.get(page_key, [])
        current = 0.0
        prev = 0.0

        for row in page_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                if any(k in name for k in keywords):
                    values = row.get("values", {})
                    # 使用自訂排序確保正確的時間順序
                    sorted_periods = sorted(
                        values.keys(), key=self._parse_period_key, reverse=True
                    )

                    if sorted_periods:
                        latest_period = sorted_periods[0]
                        # Latest
                        val = values[latest_period]
                        if isinstance(val, (int, float)):
                            current = float(val)

                        # Previous (YoY - 去年同期)
                        yoy_period = self._find_yoy_period(
                            latest_period, sorted_periods
                        )
                        if yoy_period:
                            val_prev = values.get(yoy_period)
                            if isinstance(val_prev, (int, float)):
                                prev = float(val_prev)
                        elif len(sorted_periods) > 1:
                            # Fallback: 使用最舊的資料
                            oldest_period = sorted_periods[-1]
                            val_prev = values.get(oldest_period)
                            if isinstance(val_prev, (int, float)):
                                prev = float(val_prev)
                    break

        return {"current": current, "prev": prev}

    def _get_historical_values(
        self, data: dict, page_key: str, keywords: list[str]
    ) -> tuple[list[float], float | None]:
        """Helper to get all historical values and current value"""
        page_data = data.get(page_key, [])
        history = []
        current = None

        for row in page_data:
            if isinstance(row, dict):
                name = row.get("name", "")
                # 有些名稱是 "本益比 (倍)"
                if any(k in name for k in keywords):
                    values = row.get("values", {})

                    # History
                    for v in values.values():
                        if isinstance(v, (int, float)) and v > 0:
                            history.append(float(v))

                    # Current
                    sorted_periods = sorted(values.keys(), reverse=True)
                    if sorted_periods:
                        val = values[sorted_periods[0]]
                        if isinstance(val, (int, float)):
                            current = float(val)
                    break
        return history, current

    def _parse_period_key(self, period: str) -> tuple[int, int]:
        """
        解析期間格式為可排序的 tuple

        支援格式:
        - 季度: "2023Q4", "2024Q1"
        - 年度: "2023", "2024"
        - 月度: "2024/01", "2024-01"

        Returns:
            (year, sub_period): 用於排序的 tuple
        """

        # 季度格式: 2023Q4
        match = re.match(r"(\d{4})Q(\d)", period)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        # 年度格式: 2023
        match = re.match(r"^(\d{4})$", period)
        if match:
            return (int(match.group(1)), 0)

        # 月度格式: 2024/01 or 2024-01
        match = re.match(r"(\d{4})[/-](\d{2})", period)
        if match:
            return (int(match.group(1)), int(match.group(2)))

        # 無法解析，返回 (0, 0) 讓它排在最後
        return (0, 0)

    def _find_yoy_period(
        self, current_period: str, available_periods: list[str]
    ) -> str | None:
        """
        根據當前期間找到去年同期

        Args:
            current_period: 當前期間 (如 "2024Q3")
            available_periods: 所有可用期間列表

        Returns:
            去年同期的字串，如果找不到則返回 None
        """

        # 季度格式: 2023Q4 -> 2022Q4
        match = re.match(r"(\d{4})Q(\d)", current_period)
        if match:
            year = int(match.group(1))
            quarter = match.group(2)
            yoy_period = f"{year - 1}Q{quarter}"
            if yoy_period in available_periods:
                return yoy_period
            return None

        # 年度格式: 2023 -> 2022
        match = re.match(r"^(\d{4})$", current_period)
        if match:
            year = int(match.group(1))
            yoy_period = str(year - 1)
            if yoy_period in available_periods:
                return yoy_period
            return None

        # 月度格式: 2024/01 -> 2023/01
        match = re.match(r"(\d{4})([/-])(\d{2})", current_period)
        if match:
            year = int(match.group(1))
            sep = match.group(2)
            month = match.group(3)
            yoy_period = f"{year - 1}{sep}{month}"
            if yoy_period in available_periods:
                return yoy_period
            return None

        return None
