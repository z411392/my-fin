"""掃描殘差動能 Query

實作 ScanResidualMomentumPort Driving Port
使用真實 Yahoo Finance 數據

SOTA 升級:
- 三層因子剝離 (全球/本地市場/產業)
- Kalman Filter 動態 Beta
- HMM Factor Timing (體制識別調整權重)
"""

from injector import inject
import asyncio
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

import numpy as np
import yfinance as yf
from aiostream import stream
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

if TYPE_CHECKING:
    import pandas as pd

    from libs.hunting.src.ports.stock_list_provider_port import StockListProviderPort
    from libs.hunting.src.ports.i_fundamental_data_port import IFundamentalDataPort
    from libs.hunting.src.ports.fama_french_factor_provider_port import (
        FamaFrenchFactorProviderPort,
    )
    from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort
    from libs.hunting.src.ports.sector_benchmark_provider_port import (
        SectorBenchmarkProviderPort,
    )
    from libs.hunting.src.ports.local_summary_storage_port import (
        LocalSummaryStoragePort,
    )

from libs.arbitraging.src.domain.services.hmm_regime_detector import hmm_regime_simple
from libs.arbitraging.src.domain.services.hurst_calculator import (
    calculate_hurst_exponent,
)
from libs.hunting.src.domain.services.quality_filters import (
    calculate_ivol,
    calculate_max_return,
    calculate_information_discreteness,
    calculate_amihud_illiq,
    calculate_overnight_confirmation,
)
from libs.hunting.src.domain.services.momentum_lifecycle_calculator import (
    calculate_signal_age,
    calculate_remaining_meat,
    calculate_residual_rsi,
    detect_rsi_divergence,
    calculate_frog_in_pan_id,
)
from libs.hunting.src.domain.services.half_life_calculator import (
    calculate_half_life,
)
from libs.hunting.src.domain.services.exit_signal_detector import (
    calculate_stop_loss_triggered,
    calculate_beta_change_pct,
    calculate_beta_spike_alert,
    calculate_atr_trailing_stop,
    calculate_rolling_beta,
)
from libs.hunting.src.domain.services.volatility_expansion_detector import (
    calculate_volatility_expansion_flag,
    detect_correlation_drift,
    calculate_short_term_reversal,
)
from libs.hunting.src.domain.services.eemd_trend_decomposer import (
    eemd_trend_simple,
    confirm_eemd_trend,
)
from libs.hunting.src.domain.services.residual_momentum_calculator import (
    calculate_momentum_score,
)
from libs.hunting.src.domain.services.stock_data_builder import build_full_push_data
from libs.hunting.src.domain.services.theoretical_price_calculator import (
    calculate_remaining_alpha,
    calculate_theoretical_price,
    calculate_ou_bounds,
)
from libs.linking.src.domain.services.kalman_beta_estimator import kalman_beta_simple

from libs.monitoring.src.domain.services.defcon_calculator import (
    calculate_defcon_level,
)
from libs.shared.src.constants.yfinance_settings import YFINANCE_DELAY_SECONDS
from libs.hunting.src.domain.services.synthetic_benchmark_calculator import (
    get_synthetic_sector_benchmark,
)
from libs.hunting.src.ports.scan_residual_momentum_port import ScanResidualMomentumPort
from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO
from libs.shared.src.dtos.hunting.residual_momentum_scan_result_dto import (
    ResidualMomentumScanResultDTO,
)
from libs.shared.src.dtos.hunting.stock_evaluation_dto import StockEvaluationResultDTO


class ScanResidualMomentumQuery(ScanResidualMomentumPort):
    """掃描殘差動能標的 (三層因子剝離版)"""

    @inject
    def __init__(
        self,
        stock_list_provider: "StockListProviderPort | None" = None,
        local_storage: "LocalSummaryStoragePort | None" = None,
        fundamental_provider: "IFundamentalDataPort | None" = None,
        fama_french_provider: "FamaFrenchFactorProviderPort | None" = None,
        market_data_provider: "MarketDataProviderPort | None" = None,
        sector_benchmark_provider: "SectorBenchmarkProviderPort | None" = None,
    ):
        """Initialize Query

        Args:
            stock_list_provider: Stock list provider (Shioaji)
            local_storage: Local JSON storage
            fundamental_provider: StatementDog fundamental provider (Optional)
            fama_french_provider: Fama-French factor provider (Optional, for US stocks)
            market_data_provider: Market data provider (Yahoo, VIX, etc.)
            sector_benchmark_provider: Sector benchmark provider (Optional)
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._stock_list_provider = stock_list_provider
        self._local_storage = local_storage
        self._fundamental_provider = fundamental_provider
        self._fama_french_provider = fama_french_provider
        self._market_data_provider = market_data_provider
        self._sector_benchmark_provider = sector_benchmark_provider
        # Cache market data
        self._returns_cache: dict[str, np.ndarray] = {}
        # Cache full history DataFrame (reduce yfinance API calls)
        self._hist_cache: dict[str, "pd.DataFrame"] = {}
        # Cache synthetic sector index
        self._synthetic_cache: dict[str, np.ndarray] = {}
        # Cache Fama-French factors (for US stocks)
        self._ff3_cache: dict[str, np.ndarray] | None = None

    def _get_shioaji_targets(self, market: str) -> list[str]:
        """Get TW stock dynamic list via Shioaji Adapter"""
        if self._stock_list_provider is None:
            self._logger.warning(
                "StockListProvider not injected, cannot get stock list"
            )
            return []

        self._logger.info(f"Fetching {market} list via Shioaji...")
        try:
            include_otc = market == "tw_otc"
            return self._stock_list_provider.get_all_stocks(include_otc=include_otc)
        except Exception as e:
            self._logger.warning(f"Shioaji fetch failed: {e}")
            return []

    def _get_us_full_targets(self) -> list[str]:
        """Get US stock full list (filtered via Shioaji)"""
        if self._stock_list_provider is None:
            self._logger.warning(
                "StockListProvider not injected, cannot get US stock list"
            )
            return []

        try:
            base_list = self._stock_list_provider.get_us_stock_list()
        except Exception as e:
            self._logger.warning(f"Failed to get US stock list: {e}")
            return []

        try:
            tradable_us = set(self._stock_list_provider.get_us_tradable_stocks())

            if not tradable_us:
                return base_list

            final_list = [s for s in base_list if s in tradable_us]

            if len(final_list) < len(base_list) * 0.5:
                self._logger.warning(
                    "Shioaji US stock list abnormally small, using original list"
                )
                return base_list

            return final_list
        except Exception as e:
            self._logger.warning(
                f"Shioaji US stock validation failed: {e}, using original list"
            )
            return base_list

    async def execute(
        self,
        top_n: int = 10,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """掃描殘差動能標的 (Async 版本)

        這是 retain 和 scan 共用的核心執行方法。
        - scan: 不傳 stocks，自動取得市場清單
        - retain: 傳入 stocks=[symbol]，處理單一標的

        Args:
            top_n: 返回前/後 N 名
            market: 市場 (tw, tw_shioaji, us, us_full, auto)
            stocks: 自訂股票清單 (若提供則跳過自動取得)
            start_from: 從指定 SYMBOL 開始掃描 (斷點續掃)
        """

        loop = asyncio.get_running_loop()

        # 1. 取得目標清單
        if stocks is not None:
            # 使用傳入的自訂清單 (retain 模式)
            pass  # stocks 已經有值
        elif market == "us_full":
            stocks = await loop.run_in_executor(None, self._get_us_full_targets)
        elif market in ("tw_all", "tw_shioaji", "tw_otc"):
            stocks = await loop.run_in_executor(None, self._get_shioaji_targets, market)
        else:
            # 使用 StockListProvider 取得股票清單
            if self._stock_list_provider is None:
                self._logger.warning("StockListProvider 未注入，無法取得股票清單")
                stocks = []
            elif market == "tw":
                stocks = self._stock_list_provider.get_all_stocks(include_otc=True)
            elif market == "us":
                stocks = self._stock_list_provider.get_us_stock_list()
            else:
                stocks = self._stock_list_provider.get_all_stocks(include_otc=True)

        # 1.5 處理 start_from: 從指定 SYMBOL 開始掃描 (斷點續掃)
        if start_from and stocks:
            # 嘗試找到 start_from 在清單中的位置
            try:
                idx = stocks.index(start_from)
                original_len = len(stocks)
                stocks = stocks[idx:]
                self._logger.info(
                    f"Starting from {start_from} (skipped first {idx} files, remaining {len(stocks)}/{original_len})"
                )
            except ValueError:
                self._logger.warning(
                    f"Cannot find {start_from}, starting from beginning"
                )

        # 預先載入指數資料
        if market == "tw" or market.startswith("tw_"):
            local_symbol = "0050.TW"
        else:
            local_symbol = "SPY"

        # 載入全球因子 (同步操作)
        spy_returns = await loop.run_in_executor(None, self._get_returns, "SPY")
        sox_returns = await loop.run_in_executor(None, self._get_returns, "SOXX")
        local_returns = await loop.run_in_executor(
            None, self._get_returns, local_symbol
        )

        # 載入 Fama-French 因子 (僅美股)
        is_us_market = market in ("us", "us_full")
        if is_us_market and self._fama_french_provider is not None:
            try:
                ff3_df = await loop.run_in_executor(
                    None, self._fama_french_provider.get_ff3_daily
                )
                # FF3 因子單位為百分比，需除以 100 對齊日報酬
                self._ff3_cache = {
                    "Mkt-RF": ff3_df["Mkt-RF"].values / 100,
                    "SMB": ff3_df["SMB"].values / 100,
                    "HML": ff3_df["HML"].values / 100,
                }
                self._logger.info(f"Loaded FF3 factors ({len(ff3_df)} days)")
            except Exception as e:
                self._logger.warning(
                    f"FF3 factor loading failed: {e}, degrading to SPY"
                )
                self._ff3_cache = None
        else:
            self._ff3_cache = None

        # HMM Factor Timing: 計算當前體制
        _, bull_prob = hmm_regime_simple(local_returns)

        # 計算交易日 (凌晨 0-6 點算前一天，避免跨天問題)
        now = datetime.now()
        if now.hour < 6:
            trade_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            trade_date = now.strftime("%Y-%m-%d")
        today = trade_date
        total = len(stocks)
        completed_count = 0
        save_success_count = 0
        fundamental_count = 0

        # ================================================================
        # aiostream Pipeline: eval_stream + fundamental_stream → merge → join → save
        # ================================================================

        # 基礎變數
        results_list: list[ScanResultRowDTO] = []
        local_storage = self._local_storage
        fundamental_provider = self._fundamental_provider
        is_tw_market = market == "tw" or market.startswith("tw_")

        # 過濾已快取的標的
        if local_storage:
            cached_symbols = set(local_storage.list_symbols(today))
            original_len = len(stocks)

            # 統一格式：去除 .TW/.TWO 後綴再比對
            # Shioaji 返回 "1101.TW"，快取檔名是 "1101"
            def normalize_symbol(s: str) -> str:
                return s.replace(".TW", "").replace(".TWO", "")

            stocks = [s for s in stocks if normalize_symbol(s) not in cached_symbols]
            skipped = original_len - len(stocks)
            if skipped > 0:
                self._logger.info(
                    f"📁 已快取 {skipped} 檔，剩餘 {len(stocks)} 檔待處理"
                )
            total = len(stocks)

        # 配置並發數 (減少以避免 yfinance 401 rate limit)
        EVAL_WORKERS = 3  # 降低 yfinance 並發 (原 5)
        FUNDAMENTAL_CONCURRENT = 12  # 提高財報狗並發以加速
        SAVE_WORKERS = 3  # 並行 Save workers

        # Progress 進度條 (在 with block 外定義給 nested function 用)
        # 注意：TimeRemainingColumn 的時間估算基於 advance() 呼叫間隔
        # 當兩個串流同時執行但速度不同時，估算可能不準確
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(elapsed_when_finished=True),
            refresh_per_second=4,  # 提高刷新率以獲得更準確的時間估算
        )
        eval_progress_task = None
        fundamental_progress_task = None

        # Merge buffers: 等兩邊都有資料才往下送
        eval_buffer: dict[str, dict] = {}
        fundamental_buffer: dict[str, dict] = {}

        async def eval_stream():
            """Eval 串流：每完成一檔就 yield"""
            nonlocal completed_count

            async def evaluate_one(symbol: str):
                yf_symbol = symbol
                if is_tw_market and symbol.isdigit():
                    yf_symbol = f"{symbol}.TW"

                result = await loop.run_in_executor(
                    None,
                    self._evaluate_stock_multi_factor,
                    yf_symbol,
                    market if not market.startswith("tw_") else "tw",
                    spy_returns,
                    sox_returns,
                    local_returns,
                    bull_prob,
                    0.08,
                    0.30,
                )
                await asyncio.sleep(YFINANCE_DELAY_SECONDS)  # Rate limit (使用統一常數)
                return symbol, result

            # 並行評估 (限制並發數)
            semaphore = asyncio.Semaphore(EVAL_WORKERS)

            async def limited_eval(symbol):
                async with semaphore:
                    return await evaluate_one(symbol)

            tasks = [asyncio.create_task(limited_eval(s)) for s in stocks]
            for coro in asyncio.as_completed(tasks):
                symbol, result = await coro
                completed_count += 1
                if eval_progress_task is not None:
                    progress.advance(eval_progress_task, 1)
                if result:
                    yield ("eval", symbol, result)

        async def fundamental_stream():
            """財報狗串流：每完成一檔就 yield"""
            nonlocal fundamental_count

            if not (
                fundamental_provider
                and hasattr(fundamental_provider, "batch_get_summaries_async")
            ):
                return

            # 財報狗同時支援台股和美股

            # 使用 on_progress callback 實現串流
            result_queue: asyncio.Queue = asyncio.Queue()

            def on_complete(symbol: str, data: dict):
                """財報狗單筆完成回調"""
                result_queue.put_nowait((symbol, data))
                if fundamental_progress_task is not None:
                    progress.advance(fundamental_progress_task, 1)

            # 啟動批次處理 (背景執行)
            async def run_batch():
                try:
                    await fundamental_provider.batch_get_summaries_async(
                        symbols=stocks,
                        max_concurrent=FUNDAMENTAL_CONCURRENT,
                        on_progress=on_complete,
                    )
                finally:
                    result_queue.put_nowait(None)  # 結束信號

            batch_task = asyncio.create_task(run_batch())

            while True:
                item = await result_queue.get()
                if item is None:
                    break
                symbol, data = item
                if data and not data.get("error"):
                    fundamental_count += 1
                    formatted = self._format_statementdog_data(data)
                    yield ("fundamental", symbol, formatted)

            await batch_task

        async def merged_stream():
            """合併兩個串流，當同一 symbol 兩邊都有資料時 yield"""
            async with stream.merge(
                eval_stream(), fundamental_stream()
            ).stream() as merged:
                async for source, symbol, data in merged:
                    if source == "eval":
                        eval_buffer[symbol] = data
                    else:  # fundamental
                        fundamental_buffer[symbol] = data

                    # 檢查是否可以合流
                    if symbol in eval_buffer and symbol in fundamental_buffer:
                        merged_data = {**eval_buffer[symbol]}
                        merged_data["statementdog"] = fundamental_buffer[symbol]
                        results_list.append(merged_data)
                        yield merged_data
                        # 清理 buffer
                        del eval_buffer[symbol]
                        del fundamental_buffer[symbol]

            # 處理未配對的 eval 結果 (沒有財報狗資料的股票)
            for symbol, data in eval_buffer.items():
                data["statementdog"] = None
                results_list.append(data)
                yield data

        async def save_one(target: dict) -> bool:
            """儲存單筆資料到本地 JSON"""
            nonlocal save_success_count
            symbol = target.get("symbol", "")
            if not symbol:
                return False

            # 使用共用 builder 建構儲存資料
            save_data = build_full_push_data(target)
            save_data["updated"] = today

            try:
                if local_storage:
                    local_storage.save(today, symbol, save_data)
                save_success_count += 1
                return True
            except Exception as e:
                error_type = type(e).__name__
                self._logger.error(f"Save {symbol} failed: [{error_type}] {e}")
                return False

        async def save_stream():
            """儲存串流 (並行 Save)"""

            # 使用 aiostream.stream.map 實現並行儲存
            save_mapper = stream.map(
                stream.iterate(merged_stream()),
                save_one,
                task_limit=SAVE_WORKERS,  # 並行數限制
            )
            async with save_mapper.stream() as s:
                async for _ in s:
                    pass  # 消費串流，實際儲存在 save_one 中完成

        with progress:
            eval_progress_task = progress.add_task("[cyan]動能評估", total=total)
            fundamental_progress_task = progress.add_task(
                "[yellow]財報狗爬蟲", total=total
            )

            if local_storage:
                await save_stream()
            else:
                # 沒有 local_storage，只跑合併流
                async with stream.iterate(merged_stream()).stream() as s:
                    async for _ in s:
                        pass

            self._logger.info(f"Saved {save_success_count} records to local JSON")
            self._logger.info(
                f"✅ Successfully evaluated {len(results_list)}/{total} files, saved {save_success_count} records"
            )

        # ========================================
        # 跨截面標準化和訊號計算延遲到 CSV 產出時
        # ========================================
        # JSON 只存 raw_momentum，momentum/signal/sector_cap 在 export CSV 時計算
        # 這樣可以使用 SNDZ 標準化而非簡單 Z-Score

        # 按 raw_momentum 排序用於回傳結果 (高到低)
        results_list.sort(key=lambda x: x.get("raw_momentum") or -999, reverse=True)

        capped_results = results_list
        sector_stats = {}

        regime_label = (
            "牛市" if bull_prob > 0.6 else ("熊市" if bull_prob < 0.4 else "中性")
        )

        result = {
            "market": market,
            "trade_date": today,
            "regime": regime_label,
            "bull_prob": round(bull_prob, 2),
            "scanned": len(stocks),
            "qualified": len(capped_results),
            "sector_stats": sector_stats,
            "targets": capped_results,
            "top_targets": capped_results[:top_n],
            "bottom_targets": capped_results[-top_n:]
            if len(capped_results) > top_n
            else [],
        }

        return result

    def _format_statementdog_data(self, summary: dict) -> ScanResultRowDTO:
        """將財報狗摘要轉換為原始資料格式

        保留所有可用欄位供日後擴充
        PE 和 DebtRatio 由 spreadsheet 公式計算 (Close/TTM_EPS, TotalDebt/(TotalDebt+Equity))
        """
        revenue = summary.get("revenue_momentum", {})
        quality = summary.get("earnings_quality", {})
        f_score = summary.get("f_score", {})
        river_chart = summary.get("river_chart", {})
        profit_margins = summary.get("profit_margins", {})
        financial_ratios = summary.get("financial_ratios", {})

        return {
            # 營收動能
            "rev_yoy": revenue.get("current_yoy"),
            "rev_mom": revenue.get("short_term_yoy"),
            # 獲利品質
            "cfo_ratio": quality.get("cfo_ni_ratio"),
            "accrual_ratio": quality.get("accrual_ratio"),
            # 評價 (PB 直接用，PE 由 spreadsheet 計算)
            "pb": river_chart.get("current_pb"),
            # F-Score
            "f_score": f_score.get("score") if isinstance(f_score, dict) else f_score,
            # 利潤率 (profit-margin 頁)
            "gross_margin": profit_margins.get("gross_margin"),
            "operating_margin": profit_margins.get("operating_margin"),
            "net_margin": profit_margins.get("net_margin"),
            # 財務比率 (roe-roa 頁)
            "roe": financial_ratios.get("roe"),
            "roa": financial_ratios.get("roa"),
            # 原始數據 (供 spreadsheet 公式計算 PE 和 DebtRatio)
            "ttm_eps": financial_ratios.get("ttm_eps"),
            "total_debt": financial_ratios.get("total_debt"),
            "equity": financial_ratios.get("equity"),
        }

    def _calculate_regime_data(
        self,
        local_returns: np.ndarray,
        regime_state: int,
        bull_prob: float,
    ) -> ScanResultRowDTO:
        """計算體制識別資料 (全局，非個股)

        整合：
        - Hurst 指數 (趨勢持久性)
        - HMM 狀態與牛市機率
        - DEFCON 等級

        Returns:
            RegimeData TypedDict
        """
        try:
            # 計算 Hurst 指數
            try:
                ticker = yf.Ticker("SPY")
                hist = ticker.history(period="6mo")
                if hist is not None and len(hist) > 100:
                    hurst = calculate_hurst_exponent(hist["Close"].values)
                else:
                    hurst = 0.5
            except Exception:
                hurst = 0.5

            # 取得 VIX
            try:
                if self._market_data_provider:
                    vix = float(self._market_data_provider.get_current_price("^VIX"))
                else:
                    vix = 20.0  # 預設中性值
            except Exception:
                vix = 20.0  # 預設中性值

            # 計算 DEFCON
            defcon_level, _, _ = calculate_defcon_level(
                vix=vix,
                hmm_state=regime_state,
                vpin=0.0,  # 暫無 VPIN 資料
                gli_z=0.0,
            )

            # 決定體制標籤
            if hurst > 0.55 and regime_state == 1:
                regime = "趨勢牛市"
            elif hurst > 0.55 and regime_state == 0:
                regime = "趨勢熊市"
            elif hurst < 0.45:
                regime = "均值回歸"
            else:
                regime = "震盪區間"

            return {
                "regime": regime,
                "defcon": defcon_level.value,
                "hurst": round(hurst, 3),
                "hmm_prob": round(bull_prob * 100, 1),
            }
        except Exception as e:
            self._logger.warning(f"計算體制資料失敗: {e}")
            return {
                "regime": "未知",
                "defcon": 3,
                "hurst": 0.5,
                "hmm_prob": 50.0,
            }

    def evaluate_single_stock(
        self, symbol: str, market: str = "auto"
    ) -> StockEvaluationResultDTO | None:
        """評估單一股票動能 (無需全掃描)

        Args:
            symbol: 股票代碼
            market: 市場 ("tw", "us", "auto")

        Returns:
            dict: 動能評估結果
        """
        # 確保 symbol 是字串
        symbol = str(symbol)

        # 自動判斷市場
        if market == "auto":
            market = "us" if symbol.isalpha() else "tw"

        # 處理台股代號
        if market == "tw" and not symbol.endswith(".TW") and symbol.isdigit():
            yf_symbol = f"{symbol}.TW"
        else:
            yf_symbol = symbol

        # 準備指數數據
        if market == "tw":
            local_symbol = "0050.TW"
        else:
            local_symbol = "SPY"

        spy_returns = self._get_returns("SPY")
        sox_returns = self._get_returns("SOXX")
        local_returns = self._get_returns(local_symbol)

        if len(local_returns) < 60:
            return None

        # HMM 體制
        _, bull_prob = hmm_regime_simple(local_returns)

        # 閾值 (單一檢查時稍微寬鬆一點，讓數據能呈現)
        ivol_threshold = 1.0  # 不過濾
        max_ret_threshold = 1.0  # 不過濾

        result = self._evaluate_stock_multi_factor(
            symbol=yf_symbol,
            market=market,
            spy_returns=spy_returns,
            sox_returns=sox_returns,
            local_returns=local_returns,
            _bull_prob=bull_prob,
            _ivol_threshold=ivol_threshold,
            _max_ret_threshold=max_ret_threshold,
        )

        if result:
            result["bull_prob"] = bull_prob

        return result

    def _get_hist(self, symbol: str, lookback: int = 120) -> "pd.DataFrame | None":
        """取得完整歷史資料 (帶快取)

        優化：將 DataFrame 快取起來，避免在同一股票多次呼叫 ticker.history()
        """
        if symbol in self._hist_cache:
            return self._hist_cache[symbol]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1y")
                if hist is not None and len(hist) >= lookback:
                    self._hist_cache[symbol] = hist
                    return hist
                return None
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                is_rate_limit = (
                    "Too Many Requests" in error_msg
                    or "Rate limited" in error_msg
                    or "429" in error_msg
                    or (error_type == "TypeError" and "NoneType" in error_msg)
                    or error_type == "KeyError"
                )
                if is_rate_limit and attempt < max_retries - 1:
                    wait_time = 30 * (attempt + 1)
                    self._logger.warning(
                        f"⏸️ Rate Limited! 全域冷卻 {wait_time} 秒後繼續... ({symbol})"
                    )
                    time.sleep(wait_time)
                    continue
                return None
        return None

    def _get_returns(self, symbol: str, lookback: int = 120) -> np.ndarray:
        """取得指數報酬 (帶快取和 retry)

        優化：使用 _get_hist 取得快取的 DataFrame，避免重複呼叫 yfinance API
        """
        if symbol in self._returns_cache:
            return self._returns_cache[symbol]

        hist = self._get_hist(symbol, lookback)
        if hist is None or len(hist) < lookback:
            if not hasattr(self, "_returns_debug_shown"):
                actual_len = len(hist) if hist is not None else 0
                self._logger.debug(
                    f"_get_returns: {symbol} 資料不足 ({actual_len}/{lookback})"
                )
                self._returns_debug_shown = True
            return np.array([])

        closes = hist["Close"].values[-lookback:]
        returns = np.diff(np.log(closes))
        self._returns_cache[symbol] = returns
        return returns

    def _evaluate_stock_multi_factor(
        self,
        symbol: str,
        market: str,
        spy_returns: np.ndarray,
        sox_returns: np.ndarray,
        local_returns: np.ndarray,
        _bull_prob: float,
        _ivol_threshold: float,
        _max_ret_threshold: float,
        lookback: int = 120,
    ) -> StockEvaluationResultDTO | None:
        """
        評估單一股票 (三層因子剝離)

        Step 1: 剝離全球因子 (SPY + SOX)
        Step 2: 剝離本地市場因子 (0050 / SPY)
        Step 3: 剝離產業因子 (產業 ETF)
        """
        try:
            # 1. 取得個股報酬 (使用統一的獲取方法，支援 mock 和快取)
            stock_returns = self._get_returns(symbol, lookback)
            if len(stock_returns) == 0:
                # Debug: 顯示第一個失敗的原因
                if not hasattr(self, "_debug_shown"):
                    self._logger.debug(f"{symbol} 無法取得報酬資料")
                    self._debug_shown = True
                return None

            # 2. 取得產業 benchmark 報酬
            if self._sector_benchmark_provider is None:
                # Fallback: 使用本地市場指數作為 benchmark
                sector_benchmark = "SPY" if market in ("us", "us_full") else "0050.TW"
                sector_symbol = sector_benchmark
                sector_returns = self._get_returns(sector_symbol)
            else:
                sector_benchmark = self._sector_benchmark_provider.get_sector_benchmark(
                    symbol, market
                )

                # 判斷是 ETF 還是合成指數
                if sector_benchmark.startswith("synthetic:"):
                    # 合成指數：用快取或計算
                    industry = sector_benchmark.split(":")[1]
                    if industry not in self._synthetic_cache:
                        proxies = self._sector_benchmark_provider.get_sector_proxies(
                            industry
                        )
                        self._synthetic_cache[industry] = (
                            get_synthetic_sector_benchmark(proxies, ".TW")
                        )
                    sector_returns = self._synthetic_cache[industry]
                    sector_symbol = f"synthetic:{industry}"
                else:
                    # ETF：直接取報酬
                    sector_symbol = sector_benchmark
                    sector_returns = self._get_returns(sector_symbol)

            # 3. 對齊所有序列長度
            min_len = min(
                len(stock_returns),
                len(spy_returns),
                len(sox_returns),
                len(local_returns),
                len(sector_returns) if len(sector_returns) > 0 else 999,
            )

            if min_len < 60:
                return None

            stock_aligned = stock_returns[-min_len:]
            spy_aligned = spy_returns[-min_len:]
            sox_aligned = sox_returns[-min_len:]
            local_aligned = local_returns[-min_len:]
            sector_aligned = (
                sector_returns[-min_len:]
                if len(sector_returns) >= min_len
                else local_aligned
            )

            # ========================================
            # 三層因子剝離 (使用 Kalman Filter)
            # ========================================

            # 分支：美股使用 FF3 因子，台股使用原有 SPY+Local 方法
            use_ff3 = (
                market in ("us", "us_full")
                and self._ff3_cache is not None
                and len(self._ff3_cache.get("Mkt-RF", [])) >= min_len
            )

            if use_ff3:
                # ========== 美股 FF3 因子剝離 ==========
                # Step 1: 使用 MKT-RF 剝離市場因子 (取代 SPY)
                mkt_rf = self._ff3_cache["Mkt-RF"][-min_len:]
                smb = self._ff3_cache["SMB"][-min_len:]
                hml = self._ff3_cache["HML"][-min_len:]

                global_beta = kalman_beta_simple(mkt_rf, stock_aligned)
                residual_1 = stock_aligned - global_beta * mkt_rf

                # Step 2: 使用 SMB (Size) 剝離規模因子
                smb_beta = kalman_beta_simple(smb, residual_1)
                residual_2_smb = residual_1 - smb_beta * smb

                # Step 2.5: 使用 HML (Value) 剝離價值因子
                hml_beta = kalman_beta_simple(hml, residual_2_smb)
                residual_2 = residual_2_smb - hml_beta * hml

                # Step 3: 剝離產業因子 (使用 Sector ETF)
                sector_for_step3 = sector_aligned
                if len(sector_for_step3) != len(residual_2):
                    sector_for_step3 = sector_for_step3[-len(residual_2) :]

                sector_beta = kalman_beta_simple(sector_for_step3, residual_2)
                final_residual = residual_2 - sector_beta * sector_for_step3

                # 為相容性保留 local_beta (使用 SMB_beta 作為代理)
                local_beta = smb_beta
                sox_beta = hml_beta  # 借用欄位顯示 HML beta

            else:
                # ========== 台股/降級 原有方法 ==========
                # Step 1: 剝離全球因子 (SPY)
                # 台股 T 對應美股 T-1 (時差)
                if market == "tw" and min_len > 1:
                    spy_lagged = spy_aligned[:-1]
                    sox_lagged = sox_aligned[:-1]
                    stock_for_global = stock_aligned[1:]
                    local_aligned = local_aligned[1:]  # Align local for later steps
                    sector_aligned = sector_aligned[1:]  # Align sector for later steps
                else:
                    spy_lagged = spy_aligned
                    sox_lagged = sox_aligned
                    stock_for_global = stock_aligned

                global_beta = kalman_beta_simple(spy_lagged, stock_for_global)
                residual_1 = stock_for_global - global_beta * spy_lagged

                # Step 1.5: 剝離全球半導體因子 (SOX) - 特別針對台股電子權值
                sox_beta = kalman_beta_simple(sox_lagged, residual_1)
                residual_1_5 = residual_1 - sox_beta * sox_lagged

                # Step 2: 剝離本地市場因子
                # 注意: local_aligned 已經在上一步對齊過 (若是 tw)
                local_for_step2 = local_aligned
                # 確保長度一致 (可能會有 1 unit mismatch if not careful)
                if len(local_for_step2) != len(residual_1_5):
                    local_for_step2 = local_for_step2[-len(residual_1_5) :]

                local_beta = kalman_beta_simple(local_for_step2, residual_1_5)
                residual_2 = residual_1_5 - local_beta * local_for_step2

                # Step 3: 剝離產業因子
                sector_for_step3 = sector_aligned
                if len(sector_for_step3) != len(residual_2):
                    sector_for_step3 = sector_for_step3[-len(residual_2) :]

                sector_beta = kalman_beta_simple(sector_for_step3, residual_2)
                final_residual = residual_2 - sector_beta * sector_for_step3

            # ========================================
            # 計算動能指標
            # ========================================

            # 殘差動能分數
            momentum_score = calculate_momentum_score(final_residual)
            raw_momentum = (
                float(np.sum(final_residual)) if len(final_residual) > 0 else 0.0
            )

            # 特質波動率 (IVOL)
            ivol = calculate_ivol(final_residual) if len(final_residual) > 0 else 0.0

            # 最大單日報酬
            max_ret = (
                calculate_max_return(stock_aligned) if len(stock_aligned) > 0 else 0.0
            )

            # ========================================
            # 品質濾網指標 (Alpha-Core V4.0)
            # ========================================

            # ID (FIP) - 資訊離散度
            id_score = (
                calculate_information_discreteness(stock_aligned)
                if len(stock_aligned) > 0
                else 0.0
            )
            id_pass = id_score <= 0  # ID <= 0 為連續小漲（高品質）

            # Amihud 非流動性 - 需要 volume 資料
            # 這裡先設為 None，待取得 OHLCV 後計算
            amihud_illiq = None

            # 隔夜確認 - 需要 open/close 資料
            # 這裡先設為 None，待取得 OHLCV 後計算
            overnight_return = None
            intraday_return = None
            overnight_pass = True  # 預設通過

            # EEMD 趨勢 - 使用累積殘差
            cumulative_residual = (
                np.cumsum(final_residual) if len(final_residual) > 0 else np.array([])
            )
            if len(cumulative_residual) > 30:
                _trend_signal, eemd_slope, eemd_days = eemd_trend_simple(
                    cumulative_residual
                )
                eemd_confirmed = confirm_eemd_trend(eemd_slope, eemd_days, min_days=3)
            else:
                eemd_slope = 0.0
                eemd_days = 0
                eemd_confirmed = False

            # ========================================
            # 動能生命週期指標 (plan.md P0)
            # ========================================
            # 動態計算半衰期 (OU 過程估計)
            half_life_value, _lambda_param = calculate_half_life(final_residual)
            # 如果半衰期無效 (inf), 使用預設值 180 天
            half_life_for_calc = half_life_value if half_life_value < 1000 else 180.0

            signal_age_days = calculate_signal_age(cumulative_residual, threshold=1.0)
            remaining_meat_ratio = calculate_remaining_meat(
                signal_age_days, half_life=half_life_for_calc
            )
            residual_rsi = calculate_residual_rsi(cumulative_residual, period=14)
            frog_in_pan_id = calculate_frog_in_pan_id(stock_aligned, lookback=60)

            # 與大盤 20 日相關係數 (Alpha 消失預警: ρ > 0.7)
            correlation_20d = None
            if len(stock_aligned) >= 20 and len(local_aligned) >= 20:
                try:
                    s20, l20 = stock_aligned[-20:], local_aligned[-20:]
                    # 防止 stddev=0 導致 RuntimeWarning
                    if np.std(s20) > 1e-10 and np.std(l20) > 1e-10:
                        result = np.corrcoef(s20, l20)[0, 1]
                        correlation_20d = (
                            float(result) if not np.isnan(result) else None
                        )
                except Exception:
                    correlation_20d = None

            # ========================================
            # 抓取 OHLCV 原始資料 (使用快取的 DataFrame)
            # ========================================
            try:
                # 優化：使用快取的 1 年資料，從中切片取得所需資料
                hist_full = self._get_hist(symbol)
                ticker = yf.Ticker(symbol)
                info = ticker.info  # 只有 info 需要額外 API 呼叫

                if hist_full is not None and len(hist_full) > 0:
                    # 從快取的 1 年資料切片
                    hist = hist_full.tail(2)  # 取最近 2 天
                    hist_30d = hist_full.tail(30)  # 取最近 30 天

                    latest = hist_full.iloc[-1]
                    open_price = float(latest.get("Open", 0))
                    high_price = float(latest.get("High", 0))
                    low_price = float(latest.get("Low", 0))
                    close_price = float(latest.get("Close", 0))
                    volume = int(latest.get("Volume", 0))

                    # 計算日報酬
                    if len(hist) >= 2:
                        prev_close = float(hist.iloc[-2].get("Close", 0))
                        daily_return = (
                            ((close_price - prev_close) / prev_close * 100)
                            if prev_close > 0
                            else None
                        )
                    else:
                        prev_close = info.get("previousClose", 0)
                        daily_return = (
                            ((close_price - prev_close) / prev_close * 100)
                            if prev_close > 0
                            else None
                        )
                else:
                    open_price = high_price = low_price = close_price = 0
                    volume = 0
                    prev_close = 0
                    daily_return = None
                    hist = None
                    hist_30d = None

                # 股票名稱
                stock_name = info.get("shortName") or info.get("longName") or symbol

                # ========================================
                # 完成品質濾網計算 (需要 OHLCV 資料)
                # ========================================

                # Amihud 非流動性 (使用快取的歷史 volume 資料)
                try:
                    if hist_30d is not None and len(hist_30d) > 10:
                        volumes_arr = hist_30d["Volume"].values
                        daily_rets = np.diff(np.log(hist_30d["Close"].values + 1e-8))
                        amihud_illiq = calculate_amihud_illiq(
                            daily_rets, volumes_arr[1:]
                        )
                except Exception:
                    amihud_illiq = None

                # 隔夜確認 (使用最近 2 天的 open/close)
                try:
                    if hist is not None and len(hist) >= 2:
                        opens = hist["Open"].values
                        closes = hist["Close"].values
                        overnight_return, intraday_return, should_exclude = (
                            calculate_overnight_confirmation(opens, closes)
                        )
                        overnight_pass = not should_exclude
                except Exception:
                    overnight_return = None
                    intraday_return = None
                    overnight_pass = True

            except Exception:
                open_price = high_price = low_price = close_price = 0
                volume = 0
                prev_close = 0
                daily_return = None
                stock_name = symbol
                amihud_illiq = None
                overnight_return = None
                intraday_return = None
                overnight_pass = True

            # ========================================
            # 計算理論價格與剩餘 Alpha
            # ========================================
            daily_vol = np.std(stock_aligned) if len(stock_aligned) > 0 else 0.02
            if close_price > 0 and daily_vol > 0:
                theo_price, expected_move_pct = calculate_theoretical_price(
                    current_price=close_price,
                    momentum_zscore=momentum_score,
                    daily_volatility=daily_vol,
                    holding_period=16,
                )
                remaining_alpha, _signal = calculate_remaining_alpha(
                    target_price=theo_price,
                    current_price=close_price,
                    expected_move=expected_move_pct * close_price,
                )
            else:
                theo_price = close_price
                expected_move_pct = 0.0
                remaining_alpha = 0.0

            # 計算理論價格偏離度 (plan.md P0)
            # (market_price - theoretical_price) / theoretical_price
            if theo_price and theo_price > 0 and close_price > 0:
                theoretical_price_deviation_pct = (
                    (close_price - theo_price) / theo_price
                ) * 100
            else:
                theoretical_price_deviation_pct = None

            # ========================================
            # 出場訊號指標 (plan.md P0)
            # ========================================
            # 止損觸發 (使用前面已切片的 hist_30d)
            try:
                if hist_30d is not None and len(hist_30d) > 5:
                    high_prices = hist_30d["High"].values
                    low_prices = hist_30d["Low"].values
                    close_prices = hist_30d["Close"].values
                    stop_loss_triggered = calculate_stop_loss_triggered(
                        close_price, high_prices, lookback=20, threshold=0.10
                    )
                    atr_trailing_stop = calculate_atr_trailing_stop(
                        close_price,
                        high_prices,
                        low_prices,
                        close_prices,
                        multiplier=2.0,
                        period=14,
                    )
                else:
                    stop_loss_triggered = False
                    atr_trailing_stop = None
            except Exception:
                stop_loss_triggered = False
                atr_trailing_stop = None

            # Beta 變化計算 (需要前一期 Beta)
            if len(local_beta) >= 2:
                current_beta_val = float(local_beta[-1])
                prev_beta_val = float(local_beta[-2])
                beta_change_pct = calculate_beta_change_pct(
                    current_beta_val, prev_beta_val
                )
                beta_spike_alert = calculate_beta_spike_alert(
                    beta_change_pct, threshold=50.0
                )
            else:
                beta_change_pct = 0.0
                beta_spike_alert = False

            # RSI 背離偵測 (需要價格序列)
            try:
                if hist_30d is not None and len(hist_30d) > 20:
                    price_series = hist_30d["Close"].values
                    # 計算 RSI 序列
                    rsi_series = np.array(
                        [
                            calculate_residual_rsi(
                                cumulative_residual[: i + 1], period=14
                            )
                            for i in range(len(cumulative_residual))
                        ]
                    )
                    rsi_divergence = detect_rsi_divergence(
                        price_series[-20:], rsi_series[-20:], lookback=20
                    )
                else:
                    rsi_divergence = "none"
            except Exception:
                rsi_divergence = "none"

            # ========================================
            # P1 新增指標
            # ========================================
            # OU 邊界 (plan.md P1)
            try:
                residual_std = (
                    np.std(final_residual) * close_price
                    if len(final_residual) > 0
                    else 0
                )
                current_residual_price = (
                    final_residual[-1] * close_price if len(final_residual) > 0 else 0
                )
                ou_bounds = calculate_ou_bounds(
                    current_price=close_price,
                    fair_price_model=theo_price,
                    residual_std=residual_std,
                    current_residual=current_residual_price,
                )
                ou_upper_band = ou_bounds.get("sell_high")
                ou_lower_band = ou_bounds.get("buy_lower")
            except Exception:
                ou_upper_band = None
                ou_lower_band = None

            # 波動率擴張旗標 (plan.md P1)
            try:
                if len(cumulative_residual) >= 60:
                    ivol_series = np.array(
                        [
                            calculate_ivol(final_residual[: i + 1])
                            for i in range(len(final_residual))
                        ]
                    )
                    volatility_expansion_flag = calculate_volatility_expansion_flag(
                        cumulative_residual, ivol_series, lookback=60
                    )
                else:
                    volatility_expansion_flag = False
            except Exception:
                volatility_expansion_flag = False

            # 滾動 60 日 Beta (plan.md P1)
            try:
                rolling_betas = calculate_rolling_beta(
                    stock_aligned, local_aligned, window=60
                )
                rolling_beta_60d = (
                    float(rolling_betas[-1])
                    if len(rolling_betas) > 0 and not np.isnan(rolling_betas[-1])
                    else None
                )
            except Exception:
                rolling_beta_60d = None

            # 相關性漂移 (plan.md P1)
            try:
                if len(stock_aligned) >= 40 and len(local_aligned) >= 40:
                    # 安全的滾動相關係數計算 (避免 stddev=0 警告)
                    corr_values = []
                    for i in range(20, len(stock_aligned)):
                        s_slice = stock_aligned[max(0, i - 20) : i]
                        l_slice = local_aligned[max(0, i - 20) : i]
                        if np.std(s_slice) > 1e-10 and np.std(l_slice) > 1e-10:
                            c = np.corrcoef(s_slice, l_slice)[0, 1]
                            corr_values.append(c if not np.isnan(c) else 0.0)
                        else:
                            corr_values.append(0.0)
                    corr_series = np.array(corr_values)
                    correlation_drift = detect_correlation_drift(
                        corr_series, low_threshold=0.3, high_threshold=0.7
                    )
                else:
                    correlation_drift = False
            except Exception:
                correlation_drift = False

            # 短期反轉 (plan.md P1)
            try:
                short_term_reversal = calculate_short_term_reversal(
                    stock_aligned, lookback=22
                )
            except Exception:
                short_term_reversal = None

            # IVOL × F-Score 決策矩陣 (Alpha-Core V4.0)
            # Note: ivol_percentile 和 signal 移到 CSV 階段計算 (跨截面)

            return {
                # Market Data
                "symbol": symbol.replace(".TW", ""),
                "name": stock_name,
                "sector": sector_symbol.replace(".TW", ""),
                "open": round(open_price, 2) if open_price > 0 else None,
                "high": round(high_price, 2) if high_price > 0 else None,
                "low": round(low_price, 2) if low_price > 0 else None,
                "close": round(close_price, 2) if close_price > 0 else None,
                "prev_close": round(prev_close, 2) if prev_close > 0 else None,
                "volume": volume if volume > 0 else None,
                "daily_return": round(daily_return, 2)
                if daily_return is not None
                else None,
                # Momentum (momentum 移到 CSV 階段以 SNDZ 計算)
                "raw_momentum": round(raw_momentum, 6) if raw_momentum else None,
                # Beta values are numpy arrays, extract last value
                "global_beta": round(float(global_beta[-1]), 4)
                if len(global_beta) > 0
                else None,
                "local_beta": round(float(local_beta[-1]), 4)
                if len(local_beta) > 0
                else None,
                "sector_beta": round(float(sector_beta[-1]), 4)
                if len(sector_beta) > 0
                else None,
                "ivol": round(ivol, 6) if ivol else None,
                # ivol_percentile 移到 CSV 階段計算 (跨截面排名)
                "max_ret": round(max_ret, 4) if max_ret else None,
                # Quality Filters (Alpha-Core V4.0)
                "id_score": round(id_score, 4) if id_score else None,
                "id_pass": id_pass,
                "amihud_illiq": round(amihud_illiq, 8) if amihud_illiq else None,
                "overnight_return": round(overnight_return, 4)
                if overnight_return is not None
                else None,
                "intraday_return": round(intraday_return, 4)
                if intraday_return is not None
                else None,
                "overnight_pass": overnight_pass,
                # EEMD Trend (Alpha-Core V4.0)
                "eemd_slope": round(eemd_slope, 6) if eemd_slope else None,
                "eemd_days": eemd_days,
                "eemd_confirmed": eemd_confirmed,
                # Pricing (signal 移到 CSV 階段計算，依賴 SNDZ 和 IVOL_PERCENTILE)
                "theo_price": round(theo_price, 2)
                if theo_price and theo_price > 0
                else None,
                "remaining_alpha": round(remaining_alpha, 4)
                if remaining_alpha
                else None,
                "theoretical_price": round(theo_price, 2)
                if theo_price and theo_price > 0
                else None,
                "theoretical_price_deviation_pct": round(
                    theoretical_price_deviation_pct, 2
                )
                if theoretical_price_deviation_pct is not None
                else None,
                # Lifecycle (plan.md P0)
                "signal_age_days": signal_age_days if signal_age_days >= 0 else None,
                "remaining_meat_ratio": round(remaining_meat_ratio, 4)
                if remaining_meat_ratio >= 0
                else None,
                "residual_rsi": round(residual_rsi, 2) if residual_rsi else None,
                "rsi_divergence": rsi_divergence,
                "frog_in_pan_id": round(frog_in_pan_id, 4) if frog_in_pan_id else None,
                # Quality Metrics (P0)
                "half_life": round(half_life_value, 2)
                if half_life_value and half_life_value < 1000
                else None,
                "correlation_20d": round(correlation_20d, 4)
                if correlation_20d is not None
                else None,
                # Exit Signals (plan.md P0)
                "stop_loss_triggered": stop_loss_triggered,
                "beta_change_pct": round(beta_change_pct, 2)
                if beta_change_pct
                else None,
                "beta_spike_alert": beta_spike_alert,
                "atr_trailing_stop": round(atr_trailing_stop, 2)
                if atr_trailing_stop
                else None,
                # P1 新增欄位
                "ou_upper_band": round(ou_upper_band, 2) if ou_upper_band else None,
                "ou_lower_band": round(ou_lower_band, 2) if ou_lower_band else None,
                "volatility_expansion_flag": volatility_expansion_flag,
                "rolling_beta_60d": round(rolling_beta_60d, 4)
                if rolling_beta_60d
                else None,
                "correlation_drift": correlation_drift,
                "short_term_reversal": round(short_term_reversal, 6)
                if short_term_reversal
                else None,
                # P2 新增欄位
                "residual_source": "ols",  # 目前只使用 OLS 殘差，未來可擴展 PLS
            }

        except Exception as e:
            self._logger.error(f"Error in evaluate_stock_multi_factor: {e}")

            traceback.print_exc()
            return None

    # ========================================
    # 新增：分離式執行方法
    # ========================================

    async def execute_momentum(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """只執行動能評估階段 (不含財報狗)

        Args:
            market: 市場 (tw, tw_shioaji, us, us_full)
            stocks: 自訂股票清單 (retain 模式)
            start_from: 從指定 SYMBOL 開始掃描

        Returns:
            dict: 包含 targets 列表 (無 statementdog 欄位)
        """
        loop = asyncio.get_running_loop()

        # 1. 取得目標清單 (與 execute 相同邏輯)
        if stocks is not None:
            pass
        elif market == "us_full":
            stocks = await loop.run_in_executor(None, self._get_us_full_targets)
        elif market in ("tw_all", "tw_shioaji", "tw_otc"):
            stocks = await loop.run_in_executor(None, self._get_shioaji_targets, market)
        else:
            if self._stock_list_provider is None:
                stocks = []
            elif market == "tw":
                stocks = self._stock_list_provider.get_all_stocks(include_otc=True)
            elif market == "us":
                stocks = self._stock_list_provider.get_us_stock_list()
            else:
                stocks = self._stock_list_provider.get_all_stocks(include_otc=True)

        # 處理 start_from
        if start_from and stocks:
            try:
                idx = stocks.index(start_from)
                stocks = stocks[idx:]
                self._logger.info(f"從 {start_from} 開始掃描 (剩餘 {len(stocks)} 檔)")
            except ValueError:
                self._logger.warning(f"找不到 {start_from}，從頭開始掃描")

        # 載入指數資料
        if market == "tw" or market.startswith("tw_"):
            local_symbol = "0050.TW"
        else:
            local_symbol = "SPY"

        spy_returns = await loop.run_in_executor(None, self._get_returns, "SPY")
        sox_returns = await loop.run_in_executor(None, self._get_returns, "SOXX")
        local_returns = await loop.run_in_executor(
            None, self._get_returns, local_symbol
        )

        # HMM 體制
        _, bull_prob = hmm_regime_simple(local_returns)

        # 計算交易日
        now = datetime.now()
        if now.hour < 6:
            trade_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            trade_date = now.strftime("%Y-%m-%d")
        today = trade_date

        # 過濾已快取的標的
        local_storage = self._local_storage
        if local_storage:
            cached_symbols = set(local_storage.list_symbols(today))
            original_len = len(stocks)

            # 統一格式：去除 .TW/.TWO 後綴再比對
            def normalize_symbol(s: str) -> str:
                return s.replace(".TW", "").replace(".TWO", "")

            stocks = [s for s in stocks if normalize_symbol(s) not in cached_symbols]
            skipped = original_len - len(stocks)
            if skipped > 0:
                self._logger.info(
                    f"📁 已快取 {skipped} 檔，剩餘 {len(stocks)} 檔待處理"
                )

        total = len(stocks)
        if total == 0:
            self._logger.info("✅ 無待處理標的")
            return {"market": market, "trade_date": today, "scanned": 0, "targets": []}

        is_tw_market = market == "tw" or market.startswith("tw_")
        EVAL_WORKERS = 3
        completed_count = 0
        results_list: list[ScanResultRowDTO] = []

        # 單一進度條 (只有動能評估)
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(elapsed_when_finished=True),
            refresh_per_second=4,
        )

        async def evaluate_one(symbol: str):
            yf_symbol = symbol
            if is_tw_market and symbol.isdigit():
                yf_symbol = f"{symbol}.TW"

            result = await loop.run_in_executor(
                None,
                self._evaluate_stock_multi_factor,
                yf_symbol,
                market if not market.startswith("tw_") else "tw",
                spy_returns,
                sox_returns,
                local_returns,
                bull_prob,
                0.08,
                0.30,
            )
            await asyncio.sleep(YFINANCE_DELAY_SECONDS)
            return symbol, result

        semaphore = asyncio.Semaphore(EVAL_WORKERS)

        async def limited_eval(symbol):
            async with semaphore:
                return await evaluate_one(symbol)

        with progress:
            task_id = progress.add_task("[cyan]動能評估", total=total)

            tasks = [asyncio.create_task(limited_eval(s)) for s in stocks]
            for coro in asyncio.as_completed(tasks):
                symbol, result = await coro
                completed_count += 1
                progress.advance(task_id, 1)

                if result:
                    result["statementdog"] = None  # 明確標記未取得財報狗
                    results_list.append(result)

                    # 儲存到 JSON
                    if local_storage:
                        save_data = build_full_push_data(result)
                        save_data["updated"] = today
                        try:
                            local_storage.save(today, symbol, save_data)
                        except Exception as e:
                            self._logger.error(f"儲存 {symbol} 失敗: {e}")

        self._logger.info(f"✅ 動能評估完成: {len(results_list)}/{total} 檔")

        return {
            "market": market,
            "trade_date": today,
            "scanned": total,
            "qualified": len(results_list),
            "targets": results_list,
        }

    async def execute_fundamental(
        self,
        market: str = "tw",
        stocks: list[str] | None = None,
        start_from: str = "",
    ) -> ResidualMomentumScanResultDTO:
        """執行財報狗爬蟲階段 (獨立儲存於 data/fundamental)

        重構說明：
        - 財報狗資料現在獨立於動能資料儲存
        - 使用 Shioaji 股票清單（與 execute_momentum 相同）
        - 快取由 CachedFundamentalAdapter 管理，無需依賴 momentum JSON

        Args:
            market: 市場 (tw, tw_shioaji, us, us_full)
            stocks: 自訂股票清單 (若為空則使用 Shioaji 動態清單)
            start_from: 從指定 SYMBOL 開始掃描 (用於斷點續掃)

        Returns:
            dict: 包含更新數量的結果
        """
        loop = asyncio.get_running_loop()

        # 計算交易日
        now = datetime.now()
        if now.hour < 6:
            trade_date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            trade_date = now.strftime("%Y-%m-%d")
        today = trade_date

        fundamental_provider = self._fundamental_provider

        if not fundamental_provider:
            self._logger.error("FundamentalProvider 未注入，無法取得財報狗資料")
            return {"market": market, "trade_date": today, "updated": 0, "targets": []}

        # 取得待處理的 symbols (使用 Shioaji 清單，與 execute_momentum 相同)
        if stocks:
            symbols = stocks
        elif market == "us_full":
            symbols = await loop.run_in_executor(None, self._get_us_full_targets)
        elif market in ("tw_all", "tw_shioaji", "tw_otc"):
            symbols = await loop.run_in_executor(
                None, self._get_shioaji_targets, market
            )
        else:
            if self._stock_list_provider is None:
                self._logger.warning("StockListProvider 未注入，無法取得股票清單")
                symbols = []
            elif market == "tw":
                symbols = self._stock_list_provider.get_all_stocks(include_otc=True)
            elif market == "us":
                symbols = self._stock_list_provider.get_us_stock_list()
            else:
                symbols = self._stock_list_provider.get_all_stocks(include_otc=True)

        if not symbols:
            self._logger.info("⚠️ 無待處理標的")
            return {"market": market, "trade_date": today, "updated": 0, "targets": []}

        # 處理 start_from (斷點續掃)
        if start_from and symbols:
            try:
                idx = symbols.index(start_from)
                skipped = idx
                symbols = symbols[idx:]
                self._logger.info(
                    f"從 {start_from} 開始掃描 (跳過 {skipped} 檔，剩餘 {len(symbols)} 檔)"
                )
            except ValueError:
                self._logger.warning(f"找不到 {start_from}，從頭開始掃描")

        # 過濾已存在快取的 symbols（讓進度條顯示準確的待處理數量）
        from pathlib import Path

        cache_dir = Path("data/fundamental")
        if cache_dir.exists():
            existing_files = {f.stem for f in cache_dir.glob("*.json")}
            original_count = len(symbols)
            # 移除 .TW/.TWO 後綴後與快取檔名比對
            symbols = [
                s
                for s in symbols
                if s.replace(".TW", "").replace(".TWO", "") not in existing_files
            ]
            cached_count = original_count - len(symbols)
            if cached_count > 0:
                self._logger.info(
                    f"📁 已快取 {cached_count} 檔，剩餘 {len(symbols)} 檔待處理"
                )

        if not symbols:
            self._logger.info("✅ 全部快取完成，無待處理標的")
            return {"market": market, "trade_date": today, "updated": 0, "targets": []}

        total = len(symbols)
        self._logger.info(f"🐕 開始財報狗爬蟲: {total} 檔")

        FUNDAMENTAL_CONCURRENT = 12  # 提高財報狗並發以加速
        updated_count = 0

        # 單一進度條 (只有財報狗)
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("•"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TimeRemainingColumn(elapsed_when_finished=True),
            refresh_per_second=4,
        )

        result_queue: asyncio.Queue = asyncio.Queue()

        def on_complete(symbol: str, data: dict) -> None:
            """財報狗單筆完成回調 (CachedFundamentalAdapter 已自動儲存)"""
            result_queue.put_nowait((symbol, data))

        async def run_batch() -> None:
            try:
                await fundamental_provider.batch_get_summaries_async(
                    symbols=symbols,
                    max_concurrent=FUNDAMENTAL_CONCURRENT,
                    on_progress=on_complete,
                )
            finally:
                result_queue.put_nowait(None)

        with progress:
            task_id = progress.add_task("[yellow]財報狗爬蟲", total=total)

            batch_task = asyncio.create_task(run_batch())

            while True:
                item = await result_queue.get()
                if item is None:
                    break

                symbol, data = item
                progress.advance(task_id, 1)

                # CachedFundamentalAdapter 已自動儲存至 data/fundamental/{symbol}.json
                if data and not data.get("error"):
                    updated_count += 1

            await batch_task

        self._logger.info(f"✅ 財報狗爬蟲完成: {updated_count}/{total} 檔更新")

        return {
            "market": market,
            "trade_date": today,
            "updated": updated_count,
            "targets": [],
        }
