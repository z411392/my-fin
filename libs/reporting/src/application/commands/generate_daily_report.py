"""Generate Daily Report Command

Integrates data from various BCs to generate daily briefing with optional email
"""

from datetime import datetime
from injector import inject
import logging
import numpy as np
import yfinance as yf
from datetime import timedelta
from textwrap import dedent
from collections import Counter

from libs.shared.src.dtos.event.alert_dto import AlertDTO
from libs.shared.src.dtos.event.economic_event_dto import EconomicEventDTO
from libs.shared.src.dtos.event.todo_dto import TodoDTO
from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO
from libs.shared.src.dtos.strategy.pair_opportunity_dto import PairOpportunityDTO
from libs.shared.src.dtos.strategy.supply_chain_opportunity_dto import (
    SupplyChainOpportunityDTO,
)

from libs.monitoring.src.domain.services.defcon_calculator import calculate_defcon_level
from libs.monitoring.src.domain.services.vix_tier_calculator import (
    calculate_vix_tier,
    get_vix_kelly_factor,
)
from libs.arbitraging.src.domain.services.hmm_regime_detector import hmm_regime_simple
from libs.arbitraging.src.domain.services.hurst_calculator import (
    calculate_hurst_exponent as hurst_exponent,
)
from libs.arbitraging.src.domain.services.pca_drift_detector import (
    calculate_pca_cosine_similarity,
)
from libs.reviewing.src.domain.services.cvar_calculator import assess_tail_risk
from libs.hunting.src.domain.services.market_impact_calculator import (
    assess_market_impact,
)
from libs.hunting.src.domain.services.regime_weight import get_factor_weights
from libs.hunting.src.domain.services.half_life_calculator import (
    calculate_half_life,
    calculate_signal_age,
    calculate_remaining_meat,
    get_lifecycle_stage,
)
from libs.hunting.src.domain.services.theoretical_price_calculator import (
    calculate_theoretical_price,
    calculate_remaining_alpha,
)
from libs.hunting.src.domain.services.residual_rsi_calculator import (
    calculate_residual_rsi,
    calculate_rsi_series,
    detect_rsi_divergence,
    check_stop_loss,
)
from libs.hunting.src.domain.services.yang_zhang_volatility_calculator import (
    calculate_yang_zhang_volatility,
    check_volatility_expansion,
)
from libs.hunting.src.domain.services.atr_trailing_stop import (
    calculate_atr,
    should_trigger_trailing_stop,
)
from libs.shared.src.dtos.reporting.momentum_lifecycle_dto import MomentumLifecycleDTO
from libs.shared.src.dtos.reporting.exit_signal_dto import ExitSignalDTO
from libs.shared.src.dtos.reporting.four_advisors_dto import FourAdvisorsDTO
from libs.shared.src.dtos.reporting.halt_check_dto import HaltCheckDTO
from libs.shared.src.dtos.reporting.weather_dto import WeatherDTO, LiquidityQuadrantDTO
from libs.shared.src.dtos.reporting.cvar_result_dto import CvarResultDTO
from libs.shared.src.dtos.reporting.regime_weights_dto import RegimeWeightsDTO
from libs.shared.src.dtos.reporting.portfolio_health_dto import PortfolioHealthDTO
from libs.shared.src.dtos.reporting.entry_checklist_dto import EntryChecklistDTO
from libs.shared.src.dtos.reporting.deep_analysis_dto import DeepAnalysisDTO
from libs.shared.src.dtos.reporting.kelly_position_dto import KellyPositionDTO
from libs.shared.src.dtos.reporting.supply_chain_link_dto import SupplyChainLinkDTO
from libs.shared.src.dtos.reporting.sector_stats_dto import SectorStatsDTO
from libs.shared.src.dtos.reporting.stock_diagnosis_dto import StockDiagnosisDTO
from libs.shared.src.dtos.reporting.stock_pairs_dto import StockPairsDTO
from libs.reporting.src.ports.generate_daily_report_port import GenerateDailyReportPort
from libs.monitoring.src.ports.notification_gateway_port import NotificationGatewayPort
from libs.monitoring.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.monitoring.src.ports.fred_data_provider_port import FredDataProviderPort
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.arbitraging.src.ports.economic_calendar_provider_port import (
    EconomicCalendarProviderPort,
)
from libs.hunting.src.ports.scan_pairs_port import ScanPairsPort
from libs.linking.src.ports.get_supply_chain_link_port import GetSupplyChainLinkPort
from libs.shared.src.constants.supply_chain_map import SUPPLY_CHAIN_MAP
from libs.shared.src.dtos.reporting.report_result_dto import ReportResultDTO


class GenerateDailyReportCommand(GenerateDailyReportPort):
    """Generate Daily Report

    Integrates:
    - Weather indicator (risk_sentinel)
    - Portfolio health (performance_reviewer)
    - Event reminders (event_arbitrageur)
    - AI narrative (narration)
    """

    @inject
    def __init__(
        self,
        notification_gateway: NotificationGatewayPort,
        market_data_adapter: MarketDataProviderPort,
        vpin_adapter: VPINCalculatorPort,
        fred_adapter: FredDataProviderPort,
        portfolio_adapter: PortfolioProviderPort,
        calendar_adapter: EconomicCalendarProviderPort,
        pairs_query: ScanPairsPort,
        supply_chain_query: GetSupplyChainLinkPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._notification_gateway = notification_gateway
        self._market_data_adapter = market_data_adapter
        self._vpin_adapter = vpin_adapter
        self._fred_adapter = fred_adapter
        self._portfolio_adapter = portfolio_adapter
        self._calendar_adapter = calendar_adapter
        self._pairs_query = pairs_query
        self._supply_chain_query = supply_chain_query

    async def execute(self, simulate: bool = False) -> ReportResultDTO:
        """Execute daily report generation (integrated weekly report features)"""

        # 凌晨 0-6 點算前一天（與 _get_scan_results_from_sheets 一致）
        now = datetime.now()
        if now.hour < 6:
            today = (now - timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            today = now.strftime("%Y-%m-%d")
        self._logger.info(f"Starting daily report generation: {today}")

        # 1. Get weather data
        self._logger.info("Step 1/13: Getting weather data...")
        weather = self._get_weather()
        self._logger.info(f"Weather data complete: {weather['overall_signal']}")

        # 2. Get regime weights (new)
        self._logger.info("Step 2/13: Getting regime weights...")
        regime_weights = self._get_regime_weights()
        self._logger.info(
            f"Regime weights complete: {regime_weights['regime_emoji']} {regime_weights['regime']}"
        )

        # 3. Four advisors diagnosis (from weekly)
        self._logger.info("Step 3/13: Four advisors diagnosis...")
        advisors = self._get_four_advisors(weather)
        self._logger.info(f"Four advisors consensus: {advisors['consensus']}")

        # 4. Get portfolio health
        self._logger.info("Step 4/13: Getting portfolio health...")
        portfolio = self._get_portfolio_health()
        self._logger.info(
            f"Portfolio health complete: {portfolio['healthy_count']}/{portfolio['total_count']}"
        )

        # 5. Get event reminders
        self._logger.info("Step 5/13: Getting event reminders...")
        events = self._get_upcoming_events()
        self._logger.info(f"Event reminders complete: {len(events)} events")

        # 6. Read scan results from Google Sheets (read first for later steps)
        self._logger.info("Step 6/13: Reading scan results from Google Sheets...")
        scan_results = await self._get_scan_results_from_sheets(today)
        self._logger.info(f"Scan results: {len(scan_results)} records")

        # 7. Get risk alerts (new)
        self._logger.info("Step 7/13: Checking risk alerts...")
        risk_alerts = self._get_risk_alerts(scan_results)
        self._logger.info(f"Risk alerts: {len(risk_alerts)} alerts")

        # 8. Generate entry decision checklist (using scan_results)
        self._logger.info("Step 8/13: Generating entry decision checklist...")
        entry_checklist = self._get_entry_checklist(weather, scan_results)
        self._logger.info(f"Entry checklist complete: {entry_checklist['decision']}")

        # 9. Pairs trading opportunities
        self._logger.info("Step 9/13: Scanning pairs trading opportunities...")
        pairs = self._get_pairs_opportunities()
        self._logger.info(f"Pairs opportunities: {len(pairs)} pairs")

        # 10. Supply chain opportunities
        self._logger.info("Step 10/13: Supply chain opportunities...")
        supply_chain = self._get_supply_chain_opportunities()
        self._logger.info(f"Supply chain opportunities: {len(supply_chain)} items")

        # 11. HALT self-check
        self._logger.info("Step 11/13: HALT self-check...")
        halt = self._get_halt_check()
        self._logger.info(f"HALT self-check: {halt['message']}")

        # 12. Generate todos
        self._logger.info("Step 12/13: Generating todos...")
        todos = self._get_todos(weather, portfolio)

        # 13. Generate Markdown report
        self._logger.info("Step 13/13: Generating Markdown report...")
        report_markdown = self._generate_report(
            date=today,
            weather=weather,
            regime_weights=regime_weights,
            advisors=advisors,
            portfolio=portfolio,
            events=events,
            entry_checklist=entry_checklist,
            scan_results=scan_results,
            risk_alerts=risk_alerts,
            pairs=pairs,
            supply_chain=supply_chain,
            halt=halt,
            todos=todos,
        )
        self._logger.info("Markdown report complete")

        result = {
            "date": today,
            "weather": weather,
            "regime_weights": regime_weights,
            "advisors": advisors,
            "portfolio": portfolio,
            "events": events,
            "entry_checklist": entry_checklist,
            "scan_results": scan_results,
            "risk_alerts": risk_alerts,
            "pairs": pairs,
            "supply_chain": supply_chain,
            "halt": halt,
            "todos": todos,
            "report_markdown": report_markdown,
            "email_sent": False,
        }

        self._logger.info("Sending Email...")
        result["email_sent"] = self._send_email(report_markdown, today)
        self._logger.info(
            f"Email sent: {'success' if result['email_sent'] else 'failed'}"
        )

        self._logger.info("Daily report generation complete")
        return result

    # ===========================================
    # 以下方法從週報遷移 (merged from weekly report)
    # ===========================================

    def _get_four_advisors(self, weather: WeatherDTO) -> FourAdvisorsDTO:
        """四顧問診斷"""
        # 工程師 - 流動性/結構
        engineer = "進攻" if weather["vix"] < 20 else "防守"

        # 生物學家 - 產業生態
        # TODO: 需實作產業廣度指標 (Breadth)
        biologist = "觀望"

        # 心理學家 - 市場情緒
        psychologist = "觀望" if weather["vix"] > 15 else "進攻"

        # 策略家 - 勝率賠率
        hurst = weather.get("hurst", 0.5)
        strategist = "進攻" if hurst > 0.5 else "觀望"

        # 計算共識
        votes = [engineer, biologist, psychologist, strategist]
        attack_count = votes.count("進攻")

        if attack_count >= 4:
            consensus = "🟢🟢 進攻"
            allocation = "股票 60%"
        elif attack_count >= 3:
            consensus = "🟢 進攻"
            allocation = "股票 50%"
        elif attack_count >= 2:
            consensus = "🟡 分歧"
            allocation = "股票 30%"
        else:
            consensus = "🔴 防守"
            allocation = "股票 15%"

        return {
            "engineer": {
                "verdict": engineer,
                "reason": "GLI 擴張中" if engineer == "進攻" else "流動性縮減",
            },
            "biologist": {"verdict": biologist, "reason": "產業廣度待確認"},
            "psychologist": {
                "verdict": psychologist,
                "reason": "情緒指標" if psychologist == "進攻" else "避險情緒",
            },
            "strategist": {
                "verdict": strategist,
                "reason": "動能延續" if strategist == "進攻" else "動能減弱",
            },
            "consensus": consensus,
            "allocation": allocation,
            "attack_count": attack_count,
        }

    def _get_pairs_opportunities(self) -> list[PairOpportunityDTO]:
        """取得配對交易機會 - 使用真實掃描"""
        try:
            pairs = []

            # 掃描多個產業
            sectors = ["金融", "半導體", "航運"]
            for sector in sectors:
                result = self._pairs_query.execute(sector=sector, min_correlation=0.6)
                for p in result.get("pairs", []):
                    if abs(p["spread_zscore"]) > 1.5:  # 只顯示有訊號的
                        signal = "做空價差" if p["spread_zscore"] > 1.5 else "做多價差"
                        pairs.append(
                            {
                                "pair": f"{p['symbol_a']}/{p['symbol_b']}",
                                "correlation": p["correlation"],
                                "z_score": p["spread_zscore"],
                                "half_life": p["half_life"],
                                "signal": signal,
                            }
                        )

            return pairs[:5]
        except Exception as e:
            self._logger.warning(f"配對掃描失敗: {e}")
            return []

    def _get_supply_chain_opportunities(self) -> list[SupplyChainOpportunityDTO]:
        """取得供應鏈機會 (真實掃描)"""
        try:
            opportunities = []

            # 掃描主要標的 (權值股)
            targets = ["NVDA", "AMD", "AAPL", "TSM", "AVGO", "QCOM", "INTC"]

            for us_symbol in targets:
                # 找出該美股對應的台股供應鏈
                tw_symbol = SUPPLY_CHAIN_MAP.get(us_symbol)
                if not tw_symbol:
                    continue

                result = self._supply_chain_query.execute(us_symbol, tw_symbol)
                signal = result.get("signal", "")

                # 根據訊號類型決定是否顯示
                # EXECUTE = 強烈買入機會, REDUCE = 減碼, SHORT = 做空, NEUTRAL = 觀望
                if signal in ["EXECUTE", "REDUCE", "SHORT"]:
                    signal_text = {
                        "EXECUTE": "買入機會",
                        "REDUCE": "減碼觀望",
                        "SHORT": "做空警戒",
                    }.get(signal, signal)

                    opportunities.append(
                        {
                            "us_stock": result["us_symbol"],
                            "tw_stock": result["tw_symbol"],
                            "us_return": f"{result.get('expected_move', 0):.2%}",
                            "signal": signal_text,
                            "beta": result.get("beta", 0),
                            "remaining_alpha": result.get("remaining_alpha", 0),
                        }
                    )
                elif (
                    signal == "NEUTRAL" and abs(result.get("expected_move", 0)) > 0.005
                ):
                    # NEUTRAL 但有一定波動也顯示
                    opportunities.append(
                        {
                            "us_stock": result["us_symbol"],
                            "tw_stock": result["tw_symbol"],
                            "us_return": f"{result.get('expected_move', 0):.2%}",
                            "signal": "等待觀察",
                            "beta": result.get("beta", 0),
                            "remaining_alpha": result.get("remaining_alpha", 0),
                        }
                    )

            return opportunities
        except Exception as e:
            self._logger.warning(f"供應鏈掃描失敗: {e}")
            return []

    def _get_halt_check(self) -> HaltCheckDTO:
        """HALT self-check"""
        return {
            "hungry": False,
            "angry": False,
            "lonely": False,
            "tired": False,
            "passed": True,
            "message": "✅ 全部「否」，可正常交易",
        }

    # ===========================================
    # 以下是原有日報方法
    # ===========================================

    def _generate_narrative(
        self, _weather: dict, _portfolio: dict, _events: list
    ) -> str:
        """Generate AI narrative (temporarily disabled LLM, pending Gemini Adapter migration to libs/)"""
        # TODO: 待建立 libs/shared/src/adapters/driven/gemini/ 後重新啟用
        return ""

    def _get_weather(self) -> WeatherDTO:
        """取得天候數據 (整合多項指標)"""

        try:
            vix = float(self._market_data_adapter.get_vix())
        except Exception:
            # Critical Data Failure -> Return Error State
            return {
                "vix": 0.0,
                "overall_signal": "🔴 (Data Error)",
                "overall_action": "數據源異常，暫停交易",
                "defcon_level": 1,
                "defcon_emoji": "⚠️",
            }

        # HMM State + 牛市機率
        hmm_state, bull_prob = self._calculate_hmm_state_and_prob()

        # Hurst 指數
        hurst = self._calculate_hurst()

        # PCA 結構穩定度
        pca_stability = self._calculate_pca_stability()

        # GLI Z-Score
        gli_z = self._calculate_gli_z()

        # 流動性象限
        liquidity_quadrant = self._get_liquidity_quadrant()

        # VPIN - 從注入的 Adapter 取得
        try:
            vpin_result = self._vpin_adapter.calculate("SPY")
            vpin = vpin_result.get("vpin", 0.3)
        except Exception:
            vpin = 0.3  # 降級到保守值

        defcon_level, defcon_emoji, _ = calculate_defcon_level(
            vix, hmm_state, vpin, gli_z
        )
        vix_tier, vix_emoji, _ = calculate_vix_tier(vix)
        kelly_factor = get_vix_kelly_factor(vix_tier)

        # 綜合燈號
        if defcon_level.value >= 4 and vix < 20 and gli_z > 0:
            overall_signal = "🟢"
            overall_action = "可進攻、可建新倉"
        elif defcon_level.value >= 3 or vix < 25:
            overall_signal = "🟡"
            overall_action = "觀望、只減不加"
        else:
            overall_signal = "🔴"
            overall_action = "避險、減倉、不開新倉"

        # 體制解讀
        if hurst > 0.55 and hmm_state == 1:
            regime = "趨勢牛市"
        elif hurst > 0.55 and hmm_state == 0:
            regime = "趨勢熊市"
        elif hurst < 0.45:
            regime = "均值回歸"
        else:
            regime = "震盪區間"

        # CVaR 風險評估
        cvar_result = self._calculate_portfolio_cvar()

        return {
            "vix": round(vix, 2),
            "vix_tier": vix_tier.name,
            "vix_emoji": vix_emoji,
            "defcon_level": defcon_level.value,
            "defcon_emoji": defcon_emoji,
            "gli_z": round(gli_z, 2),
            "kelly_factor": kelly_factor,
            "overall_signal": overall_signal,
            "overall_action": overall_action,
            # 新增指標
            "hurst": round(hurst, 2),
            "hmm_state": hmm_state,
            "bull_prob": round(bull_prob * 100, 1),
            "pca_stability": round(pca_stability, 2),
            "regime": regime,
            "liquidity_quadrant": liquidity_quadrant,
            # CVaR 風險評估
            "cvar_95": cvar_result["cvar_95"],
            "var_95": cvar_result["var_95"],
            "tail_risk": cvar_result["tail_risk"],
        }

    def _calculate_hmm_state_and_prob(self) -> tuple[int, float]:
        """Calculate HMM state and bull probability"""
        try:
            ticker = yf.Ticker("SPY")
            hist = ticker.history(period="1y")  # Unified to 1y
            if hist is None or len(hist) < 60:
                self._logger.warning("HMM Data Insufficient")
                return 0, 0.5

            closes = hist["Close"].values
            returns = np.diff(np.log(closes))
            hmm_state, bull_prob = hmm_regime_simple(
                returns, lookback=min(60, len(returns))
            )
            return hmm_state, bull_prob
        except Exception as e:
            self._logger.warning(f"HMM Calc Error: {e}")
            return 0, 0.5

    def _calculate_hurst(self) -> float:
        """Calculate Hurst exponent"""
        try:
            ticker = yf.Ticker("SPY")
            hist = ticker.history(period="1y")  # Unified to 1y
            if hist is None or len(hist) < 100:
                return 0.5

            closes = hist["Close"].values
            return hurst_exponent(closes)
        except Exception:
            return 0.5

    def _calculate_pca_stability(self) -> float:
        """Calculate PCA structural stability"""
        try:
            tickers = ["SPY", "QQQ", "IWM", "DIA"]
            data = {}
            for t in tickers:
                ticker = yf.Ticker(t)
                hist = ticker.history(period="6mo")
                if hist is not None and len(hist) > 0:
                    data[t] = hist["Close"].values

            if len(data) < 3:
                return 0.9

            min_len = min(len(v) for v in data.values())
            returns = np.column_stack(
                [np.diff(np.log(data[t][:min_len])) for t in data]
            )

            return calculate_pca_cosine_similarity(returns, returns)
        except Exception:
            return 0.9

    def _get_liquidity_quadrant(self) -> LiquidityQuadrantDTO:
        """取得流動性象限"""
        try:
            fred = self._fred_adapter
            m2_yoy = fred.get_m2_yoy()
            fed_trend = fred.get_fed_balance_sheet_trend()

            if fed_trend == "expanding" and m2_yoy > 0:
                quadrant = "EXPANSION"
                emoji = "🟢"
            elif fed_trend == "expanding" and m2_yoy <= 0:
                quadrant = "TRANSITION"
                emoji = "🟡"
            elif fed_trend == "stable" and m2_yoy > 0:
                quadrant = "INERTIA"
                emoji = "🟢"
            elif fed_trend == "stable" and m2_yoy <= 0:
                quadrant = "NEUTRAL"
                emoji = "🟡"
            elif fed_trend == "contracting" and m2_yoy > 0:
                quadrant = "INERTIA"
                emoji = "🟡"
            else:  # contracting + m2 <= 0
                quadrant = "CONTRACTION"
                emoji = "🔴"

            return {
                "name": quadrant,
                "emoji": emoji,
                "m2_yoy": round(m2_yoy, 2),
                "fed_trend": fed_trend,
            }
        except Exception:
            return {
                "name": "EXPANSION",
                "emoji": "🟢",
                "m2_yoy": 0.0,
                "fed_trend": "unknown",
            }

    def _calculate_gli_z(self) -> float:
        """Calculate GLI Z-Score"""
        try:
            fred = self._fred_adapter
            return fred.get_gli_z_score()
        except Exception:
            return 0.8

    def _calculate_portfolio_cvar(self) -> CvarResultDTO:
        """Calculate portfolio CVaR risk"""
        try:
            ticker = yf.Ticker("SPY")
            hist = ticker.history(period="6mo")
            if hist is None or len(hist) < 30:
                return {"cvar_95": -0.02, "var_95": -0.015, "tail_risk": "正常"}

            closes = hist["Close"].values
            returns = list(np.diff(np.log(closes)))

            result = assess_tail_risk(returns, confidence_level=0.95)

            tail_ratio = result["tail_ratio"]
            if tail_ratio > 1.5:
                tail_risk = "⚠️ 肥尾 (高風險)"
            elif tail_ratio > 1.2:
                tail_risk = "🟡 略高"
            else:
                tail_risk = "🟢 正常"

            return {
                "cvar_95": round(result["cvar"] * 100, 2),
                "var_95": round(result["var"] * 100, 2),
                "tail_risk": tail_risk,
            }
        except Exception:
            return {"cvar_95": -2.0, "var_95": -1.5, "tail_risk": "🟢 正常"}

    # ===========================================
    # 新增方法：動能生命週期與出場機制 (Phase 2)
    # ===========================================

    def _get_regime_weights(self) -> RegimeWeightsDTO:
        """取得當前體制權重（HMM 狀態 + 因子權重建議）

        對應 plan.md Phase 2.1
        """
        hmm_state, bull_prob = self._calculate_hmm_state_and_prob()
        weights = get_factor_weights(hmm_state, bull_prob)
        return {
            "hmm_state": hmm_state,
            "bull_prob": round(bull_prob * 100, 1),
            "regime": weights["regime"],
            "regime_emoji": weights["regime_emoji"],
            "trend_weight": int(weights["trend"] * 100),
            "value_weight": int(weights["value"] * 100),
            "quality_weight": int(weights["quality"] * 100),
        }

    def _get_risk_alerts(
        self, scan_results: list, prev_results: list | None = None
    ) -> list[AlertDTO]:
        """取得風險警示（與前日比對）

        對應 plan.md Phase 2.3

        警報類型：
        1. 滾動 Beta 變化 > 50%
        2. IVOL 超過 80th 百分位
        3. F-Score ≤ 4
        """
        alerts = []

        for stock in scan_results:
            symbol = stock.get("SYMBOL", "")

            # 檢查 IVOL 是否超過 80th 百分位
            ivol_pct = stock.get("IVOL_Percentile", 50)
            if ivol_pct and ivol_pct > 80:
                alerts.append(
                    {
                        "symbol": symbol,
                        "alert_type": "IVOL 高位",
                        "value": f"{ivol_pct:.0f}th 百分位",
                        "severity": "🟡",
                    }
                )

            # 檢查 F-Score (methodology.md: F-Score < 4 剔除)
            f_score = stock.get("FScore", 5)
            if f_score is not None and f_score < 4:
                alerts.append(
                    {
                        "symbol": symbol,
                        "alert_type": "F-Score 過低 (剔除)",
                        "value": f"{f_score}/9",
                        "severity": "🔴",  # F-Score < 4 一律紅色
                    }
                )

            # 與前日比對 Beta 變化
            if prev_results:
                prev_stock = next(
                    (p for p in prev_results if p.get("SYMBOL") == symbol), None
                )
                if prev_stock:
                    curr_beta = stock.get("RollingBeta", 1.0)
                    prev_beta = prev_stock.get("RollingBeta", 1.0)
                    if prev_beta and prev_beta != 0:
                        beta_change = abs(curr_beta - prev_beta) / abs(prev_beta)
                        if beta_change > 0.5:
                            alerts.append(
                                {
                                    "symbol": symbol,
                                    "alert_type": "Beta 劇變",
                                    "value": f"+{beta_change:.0%} vs 昨日",
                                    "severity": "🔴",
                                }
                            )

        return alerts[:10]  # 最多顯示 10 個警報

    def _get_momentum_lifecycle(
        self, symbol: str, price_data: dict
    ) -> MomentumLifecycleDTO:
        """計算動能生命週期指標

        對應 plan.md Phase 2.4
        整合 half_life, theoretical_price, residual_rsi, yang_zhang_volatility
        """
        closes = price_data.get("closes", np.array([]))
        opens = price_data.get("opens", np.array([]))
        highs = price_data.get("highs", np.array([]))
        lows = price_data.get("lows", np.array([]))
        residuals = price_data.get("residuals", np.array([]))
        zscore_series = price_data.get("zscore_series", np.array([]))
        momentum_zscore = price_data.get("momentum_zscore", 0.0)

        # 1. 信號年齡與生命週期
        signal_age = calculate_signal_age(zscore_series, threshold=1.0)
        stage_code, stage_desc = get_lifecycle_stage(signal_age)

        # 2. 半衰期與剩餘肉量
        half_life, _ = calculate_half_life(residuals)
        remaining_meat, meat_rec = calculate_remaining_meat(
            signal_age, half_life if half_life != float("inf") else 130
        )

        # 3. 理論價格與剩餘 Alpha
        current_price = float(closes[-1]) if len(closes) > 0 else 0
        daily_vol = float(np.std(np.diff(np.log(closes)))) if len(closes) > 20 else 0.02
        theo_price, expected_move = calculate_theoretical_price(
            current_price, momentum_zscore, daily_vol, holding_period=16
        )
        remaining_alpha, alpha_signal = calculate_remaining_alpha(
            theo_price, current_price, expected_move * current_price
        )

        # 4. 殘差 RSI
        cumulative_residuals = (
            np.cumsum(residuals) if len(residuals) > 0 else np.array([])
        )
        residual_rsi = calculate_residual_rsi(cumulative_residuals, period=14)
        rsi_series = calculate_rsi_series(cumulative_residuals, period=14)
        divergence_type, _ = detect_rsi_divergence(closes, rsi_series, lookback=20)

        # 5. Yang-Zhang 波動率
        yz_vol = calculate_yang_zhang_volatility(opens, highs, lows, closes, window=20)
        # 建立歷史波動率序列（簡化：用滾動計算）
        historical_vol = np.array([yz_vol])  # 簡化處理
        is_expanding, vol_pct = check_volatility_expansion(
            yz_vol, historical_vol, threshold_percentile=95
        )

        return {
            "signal_age": signal_age,
            "lifecycle_stage": stage_code,
            "lifecycle_emoji": stage_desc.split()[0],  # 取表情符號
            "remaining_meat": round(remaining_meat, 2),
            "meat_recommendation": meat_rec,
            "theoretical_price": round(theo_price, 2),
            "expected_move": round(expected_move, 4),
            "remaining_alpha": round(remaining_alpha, 2),
            "alpha_signal": alpha_signal,
            "residual_rsi": round(residual_rsi, 1),
            "rsi_divergence": divergence_type,
            "yz_volatility": round(yz_vol, 4),
            "vol_expansion": is_expanding,
            "vol_percentile": round(vol_pct, 1),
        }

    def _check_exit_signals(self, position: dict, price_data: dict) -> ExitSignalDTO:
        """檢查出場訊號矩陣

        對應 plan.md Phase 2.5
        5 層出場機制：硬停損、ATR停損、RSI背離、時間止損、波動率擴張
        """
        closes = price_data.get("closes", np.array([]))
        opens = price_data.get("opens", np.array([]))
        highs = price_data.get("highs", np.array([]))
        lows = price_data.get("lows", np.array([]))
        residuals = price_data.get("residuals", np.array([]))
        entry_date = position.get("entry_date")

        current_price = float(closes[-1]) if len(closes) > 0 else 0
        monthly_high = (
            float(np.max(closes[-22:])) if len(closes) >= 22 else current_price
        )

        triggered_signals = []

        # 1. 10% 硬停損
        stop_triggered, drawdown = check_stop_loss(
            current_price, monthly_high, threshold=0.10
        )
        if stop_triggered:
            triggered_signals.append("硬停損")

        # 2. ATR 移動停損
        atr = calculate_atr(highs, lows, closes, window=14)
        max_price = float(np.max(closes)) if len(closes) > 0 else current_price
        atr_triggered, atr_stop_price, atr_buffer = should_trigger_trailing_stop(
            current_price, max_price, atr, multiplier=2.0
        )
        if atr_triggered:
            triggered_signals.append("ATR停損")

        # 3. RSI 頂背離
        cumulative_residuals = (
            np.cumsum(residuals) if len(residuals) > 0 else np.array([])
        )
        rsi_series = calculate_rsi_series(cumulative_residuals, period=14)
        divergence_type, should_exit = detect_rsi_divergence(
            closes, rsi_series, lookback=20
        )
        rsi_triggered = divergence_type == "bearish"
        if rsi_triggered:
            triggered_signals.append("RSI背離")

        # 4. 時間止損（持有超過 12 個月）
        holding_months = 0.0
        time_triggered = False
        if entry_date:
            try:
                from datetime import datetime

                entry_dt = datetime.strptime(str(entry_date), "%Y-%m-%d")
                days_held = (datetime.now() - entry_dt).days
                holding_months = days_held / 30.0
                time_triggered = holding_months > 12
                if time_triggered:
                    triggered_signals.append("時間止損")
            except Exception:
                pass

        # 5. 波動率擴張
        yz_vol = calculate_yang_zhang_volatility(opens, highs, lows, closes, window=20)
        historical_vol = np.array([yz_vol])  # 簡化處理
        vol_triggered, vol_pct = check_volatility_expansion(
            yz_vol, historical_vol, threshold_percentile=95
        )
        if vol_triggered:
            triggered_signals.append("波動率擴張")

        # 綜合建議
        trigger_count = len(triggered_signals)
        if trigger_count >= 2 or stop_triggered:
            exit_recommendation = "EXIT"
        elif trigger_count == 1:
            exit_recommendation = "REDUCE"
        else:
            exit_recommendation = "HOLD"

        return {
            "stop_loss_triggered": stop_triggered,
            "stop_loss_drawdown": round(drawdown, 4),
            "atr_stop_triggered": atr_triggered,
            "atr_stop_price": atr_stop_price,
            "atr_buffer_pct": atr_buffer,
            "rsi_divergence_triggered": rsi_triggered,
            "rsi_divergence_type": divergence_type,
            "time_stop_triggered": time_triggered,
            "holding_months": round(holding_months, 1),
            "vol_expansion_triggered": vol_triggered,
            "vol_percentile": round(vol_pct, 1),
            "exit_recommendation": exit_recommendation,
            "triggered_signals": triggered_signals,
        }

    def _get_portfolio_health(self) -> PortfolioHealthDTO:
        """Get portfolio health (from Shioaji)"""
        try:
            # 嘗試從 Shioaji 取得真實持倉
            adapter = self._portfolio_adapter
            positions = []

            if adapter.connect():
                # 使用 Cost * 0.9 (10% 停損) 作為預設停損規則
                # TODO: 未來可整合 journal.json 取得真實停損設定
                positions = adapter.get_position_with_stop_loss()
                adapter.disconnect()

            if not positions:
                # 若無持倉或連線失敗，返回空狀態，而非 Mock
                return {
                    "positions": [],
                    "healthy_count": 0,
                    "total_count": 0,
                    "has_danger": False,
                    "source": "Shioaji (Empty/Failed)",
                }

            health_report = []
            for pos in positions:
                health_report.append(pos)

            healthy_count = sum(1 for p in health_report if p.get("status") == "✅")
            danger_count = sum(1 for p in health_report if p.get("status") == "🔴")

            return {
                "positions": health_report,
                "healthy_count": healthy_count,
                "total_count": len(positions),
                "has_danger": danger_count > 0,
                "source": "Shioaji",
            }

        except Exception as e:
            self._logger.warning(f"取得持倉失敗: {e}")
            return {
                "positions": [],
                "healthy_count": 0,
                "total_count": 0,
                "has_danger": False,
                "source": "Error",
            }

    def _get_upcoming_events(self, max_events: int = 7) -> list[EconomicEventDTO]:
        """取得即將發生的重要事件"""
        try:
            calendar = self._calendar_adapter
            raw_events = calendar.get_upcoming_events(days=30)

            event_descriptions = {
                "FOMC 會議": "聯準會利率決策，影響美元和股市走向",
                "CPI 公布": "通膨數據，影響聯準會政策預期",
                "非農就業": "美國就業報告，經濟健康指標",
                "四巫日": "期貨選擇權結算日，波動放大",
            }

            events = []
            for e in raw_events[:max_events]:
                event_name = e.get("name", e.get("event", "未知"))
                risk_emoji = "⭐⭐⭐" if e.get("risk") == "HIGH" else "⭐⭐"
                action = "降槓桿、不開新倉" if e.get("risk") == "HIGH" else "關注"
                description = event_descriptions.get(event_name, "重要經濟事件")
                events.append(
                    {
                        "date": str(e["date"]),
                        "event": event_name,
                        "risk_level": risk_emoji,
                        "action": action,
                        "description": description,
                    }
                )
            return events if events else self._default_events()
        except Exception:
            return self._default_events()

    def _default_events(self) -> list[EconomicEventDTO]:
        """預設事件列表"""
        return [
            {
                "date": "2025-01-03",
                "event": "NFP 非農就業",
                "risk_level": "⭐⭐⭐",
                "action": "降槓桿",
                "description": "美國就業報告，經濟健康指標",
            },
            {
                "date": "2025-01-15",
                "event": "FOMC 會議",
                "risk_level": "⭐⭐⭐",
                "action": "降槓桿、不開新倉",
                "description": "聯準會利率決策",
            },
            {
                "date": "2025-01-17",
                "event": "四巫日",
                "risk_level": "⭐⭐⭐",
                "action": "降槓桿",
                "description": "期貨選擇權結算日",
            },
        ]

    def _get_entry_checklist(
        self, weather: WeatherDTO, scan_results: list | None = None
    ) -> EntryChecklistDTO:
        """取得進場決策檢表

        Args:
            weather: 天候資料
            scan_results: 從 Sheets 讀取的掃描結果（可選）
        """
        # 從 scan_results 計算掃描範圍資訊
        if scan_results:
            # 計算有訊號的標的數量
            qualified = sum(
                1 for s in scan_results if s.get("SIGNAL") in ("EXECUTE", "REDUCE")
            )
            scope_info = f"Google Sheets ({len(scan_results)} 筆)"
        else:
            qualified = 0
            scope_info = "無資料 (尚未執行 make scan)"

        checks = [
            {
                "item": "VIX",
                "threshold": "< 20 (Tier 0)",
                "current": weather["vix"],
                "passed": weather["vix"] < 20,
                "description": "恐慌指數，低於 20 代表市場平靜",
            },
            {
                "item": "流動性象限",
                "threshold": "EXPANSION / INERTIA",
                "current": weather.get("liquidity_quadrant", {}).get(
                    "name", "EXPANSION"
                ),
                "passed": weather.get("liquidity_quadrant", {}).get("name", "EXPANSION")
                in ("EXPANSION", "INERTIA"),
                "description": "Fed 印鈔態度，擴張中錢多好做多",
            },
            {
                "item": "GEX",
                "threshold": "MILD_LONG 或以上",
                "current": "+3.2B",  # TODO: 實際 GEX 資料
                "passed": True,
                "description": "造市商 Gamma，正值時跌幅受限",
            },
            {
                "item": "持倉健康度",
                "threshold": "無 DANGER 持倉",
                "current": "0 檔 DANGER",  # TODO: 從 portfolio 取得
                "passed": True,
                "description": "手中持股距離停損的安全距離",
            },
            {
                "item": "狩獵標的品質濾網",
                "threshold": "有訊號標的 > 0",
                "current": f"{qualified}/{len(scan_results or [])} 有訊號",
                "passed": qualified > 0,
                "description": scope_info,
            },
        ]

        passed_count = sum(1 for c in checks if c["passed"])

        if passed_count == 5:
            decision = "🟢🟢 可執行週末狩獵計畫"
        elif passed_count == 4:
            decision = "🟢 可進場，但縮小倉位"
        elif passed_count == 3:
            decision = "🟡 觀望，等待條件改善"
        else:
            decision = "🔴 禁止進場"

        return {
            "checks": checks,
            "passed_count": passed_count,
            "total_count": len(checks),
            "decision": decision,
            "scan_results_count": len(scan_results or []),
            "qualified_count": qualified,
        }

    def _get_deep_analysis(self, entry_checklist: EntryChecklistDTO) -> DeepAnalysisDTO:
        """對通過篩選的股票進行深度分析

        整合：
        - position: 凱利建議倉位
        - pairs: 配對交易 Z-score
        - chains: 供應鏈夥伴
        - diagnose: 健檢分數
        """
        try:
            scan_scope = entry_checklist.get("scan_scope", {})
            tw_candidates = scan_scope.get("tw_candidates", [])
            us_candidates = scan_scope.get("us_candidates", [])

            # 篩選通過的股票 (🟢)
            tw_passed = [c for c in tw_candidates if c.get("signal") == "🟢"]
            us_passed = [c for c in us_candidates if c.get("signal") == "🟢"]

            analysis_results = []

            # 台股分析 (Top 3)
            for stock in tw_passed[:3]:
                analysis = {
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "market": "TW",
                    "kelly_position": self._calc_kelly_for_stock(stock),
                    "supply_chain": self._get_stock_supply_chain(stock["symbol"]),
                    "diagnosis": self._get_stock_diagnosis(stock),
                    "pairs": self._get_stock_pairs(stock["symbol"]),
                }
                analysis_results.append(analysis)

            # 美股分析 (Top 3)
            for stock in us_passed[:3]:
                analysis = {
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "market": "US",
                    "kelly_position": self._calc_kelly_for_stock(stock),
                    "supply_chain": self._get_stock_supply_chain(stock["symbol"]),
                    "diagnosis": self._get_stock_diagnosis(stock),
                    "pairs": self._get_stock_pairs(stock["symbol"]),
                }
                analysis_results.append(analysis)

            return {"stocks": analysis_results, "count": len(analysis_results)}

        except Exception as e:
            self._logger.warning(f"深度分析失敗: {e}")
            return {"stocks": [], "count": 0}

    def _calc_kelly_for_stock(self, stock: ScanResultRowDTO) -> KellyPositionDTO:
        """計算單檔股票的凱利建議（含市場衝擊評估）"""

        momentum = stock.get("momentum", 1.0)
        win_rate = min(0.55 + momentum * 0.05, 0.75)
        win_loss_ratio = 1.5 + momentum * 0.2
        kelly = win_rate - (1 - win_rate) / win_loss_ratio
        kelly = max(0, min(kelly, 0.25))

        # 市場衝擊評估 (假設 100 張訂單)
        expected_alpha = momentum * 0.01  # 預期 Alpha
        impact_result = assess_market_impact(
            order_size=100000,  # 100 張 (假設每股 1000 元)
            adv=5000000,  # 日均量 5M (Mock)
            volatility=0.02,  # 2% 日波動
            expected_alpha=expected_alpha,
        )

        return {
            "win_rate": f"{win_rate:.0%}",
            "win_loss_ratio": f"{win_loss_ratio:.1f}",
            "kelly_fraction": f"{kelly:.1%}",
            "suggested_position": "小量"
            if kelly < 0.10
            else "中量"
            if kelly < 0.20
            else "大量",
            "market_impact": f"{impact_result['estimated_impact']:.2%}",
            "execute_ok": "✅" if impact_result["should_execute"] else "⚠️ 成本過高",
        }

    def _get_stock_supply_chain(self, symbol: str) -> SupplyChainLinkDTO:
        """取得股票的供應鏈資訊"""
        chains = {
            "2330": {"partner": "NVDA/AMD/AAPL", "role": "晶圓代工", "lag": "1-2 天"},
            "2454": {"partner": "QCOM/MTK", "role": "手機晶片", "lag": "2-3 天"},
            "3661": {"partner": "NVDA/AMD", "role": "ASIC 設計", "lag": "1-2 天"},
            "NVDA": {"partner": "2330/3711", "role": "GPU 設計", "lag": "領先"},
            "AMD": {"partner": "2330/3034", "role": "CPU/GPU", "lag": "領先"},
            "AVGO": {"partner": "2454", "role": "網通晶片", "lag": "領先"},
            "MRVL": {"partner": "2330", "role": "雲端晶片", "lag": "領先"},
        }
        return chains.get(symbol, {"partner": "N/A", "role": "獨立", "lag": "N/A"})

    async def _get_scan_results_from_sheets(
        self, date: str | None = None
    ) -> list[ScanResultRowDTO]:
        """讀取當日掃描結果

        優先順序：
        1. 本地 CSV (data/summaries/[date].csv)
        2. Google Sheets API (備援)

        注意：CSV 由 momentum JSON (data/momentum) 和 fundamental JSON (data/fundamental) 合併產生

        Args:
            date: 日期 (YYYY-MM-DD)，預設為今天

        Returns:
            掃描結果列表，每個元素包含完整的股票資料
        """
        import csv
        from pathlib import Path

        if date is None:
            now = datetime.now()
            # 凌晨 0-6 點算前一天
            if now.hour < 6:
                date = (now - timedelta(days=1)).strftime("%Y-%m-%d")
            else:
                date = now.strftime("%Y-%m-%d")

        # === 從本地 CSV 讀取 ===
        csv_path = Path("data/summaries") / f"{date}.csv"
        if csv_path.exists():
            try:
                with open(csv_path, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                self._logger.info(f"從本地 CSV 讀取 {len(rows)} 筆掃描結果 ({date})")
                return rows
            except Exception as e:
                self._logger.warning(f"讀取本地 CSV 失敗: {e}")
                return []
        else:
            self._logger.warning(f"本地 CSV 不存在 ({csv_path})，請先執行 make scan")
            return []

    def _split_scan_by_market(
        self, results: list[ScanResultRowDTO]
    ) -> tuple[list[ScanResultRowDTO], list[ScanResultRowDTO]]:
        """將掃描結果分為台股和美股

        Args:
            results: 掃描結果列表

        Returns:
            (台股列表, 美股列表)
        """
        tw_stocks = []
        us_stocks = []

        for row in results:
            symbol = row.get("SYMBOL", "")
            # 台股: 純數字或 .TW 結尾
            if symbol.isdigit() or symbol.endswith(".TW"):
                tw_stocks.append(row)
            else:
                us_stocks.append(row)

        return tw_stocks, us_stocks

    def _calculate_sector_stats(
        self, results: list[ScanResultRowDTO]
    ) -> SectorStatsDTO:
        """計算板塊分布統計"""
        if not results:
            return {"stats": {}, "alerts": [], "total": 0}

        # 兼容不同大小寫的 key
        sectors = []
        for r in results:
            sector = (
                r.get("SECTOR") or r.get("Sector") or r.get("industry") or "Unknown"
            )
            if sector != "Unknown":
                sectors.append(sector)

        total = len(sectors)
        if total == 0:
            return {"stats": {}, "alerts": [], "total": 0}

        stats = Counter(sectors)
        alerts = []

        # 檢查集中度 (單一板塊 > 30%)
        # 只在樣本數足夠時檢查 (> 5)
        if total > 5:
            for sector, count in stats.items():
                pct = count / total
                if pct > 0.3:
                    alerts.append(f"⚠️ {sector} 佔比 {pct:.0%} (>30%)，集中度過高")

        return {"stats": dict(stats.most_common(5)), "alerts": alerts, "total": total}

    def _enrich_scan_results_with_alpha(
        self, results: list[ScanResultRowDTO]
    ) -> list[ScanResultRowDTO]:
        """豐富掃描結果 (新增 Alpha/Beta 貢獻度)"""
        enriched = []
        market_return_16d = 0.01  # 假設 16 天市場預期回報 1%

        for r in results:
            new_r = r.copy()

            # 取得基礎數據
            close = float(r.get("CLOSE") or 0)
            theo = float(r.get("THEO_PRICE") or 0)
            beta = float(r.get("RollingBeta") or r.get("beta") or 1.0)

            # 計算潛在漲幅 (Alpha Return / Upside)
            # Upside = (Theo - Close) / Close
            if close > 0:
                upside_pct = (theo - close) / close
            else:
                upside_pct = 0.0

            # 分解回報
            # Beta_Return = Beta * Market_Return
            beta_return = beta * market_return_16d

            # Total_Expected = Alpha_Return + Beta_Return
            alpha_return = upside_pct
            total_expected = alpha_return + beta_return

            # 計算 Alpha 貢獻度
            if abs(total_expected) > 0.001:
                alpha_contrib_pct = alpha_return / total_expected
            else:
                alpha_contrib_pct = 0.0

            new_r["ALPHA_RETURN"] = alpha_return
            new_r["BETA_RETURN"] = beta_return
            new_r["TOTAL_EXPECTED"] = total_expected
            new_r["ALPHA_CONTRIB_PCT"] = alpha_contrib_pct
            new_r["UPSIDE"] = upside_pct  # 確保 UPSIDE 存在

            enriched.append(new_r)

        return enriched

    def _format_dashboard_section(self, weather: WeatherDTO) -> str:
        """格式化市場儀表板（狩獵者策略核心）"""
        vix = weather.get("vix", 0)
        gli_z = weather.get("gli_z", 0)
        defcon = weather.get("defcon_level", 5)
        defcon_emoji = weather.get("defcon_emoji", "🟢")
        regime = weather.get("regime", "震盪區間")
        hurst = weather.get("hurst", 0.5)

        # VIX 狀態判斷
        if vix < 20:
            vix_status = "🟢 正常"
        elif vix < 30:
            vix_status = "🟡 警戒"
        elif vix < 40:
            vix_status = "🔴 恐慌"
        else:
            vix_status = "💀 極度恐慌"

        # GLI 狀態判斷
        if gli_z > 0:
            gli_status = "流動性充裕"
        elif gli_z > -1:
            gli_status = "流動性正常"
        elif gli_z > -2:
            gli_status = "⚠️ 流動性緊縮"
        else:
            gli_status = "🔴 流動性枯竭"

        # 梭哈條件判斷
        all_in_ready = vix > 40 and gli_z < -2.0
        all_in_status = "🔴 觸發！準備梭哈" if all_in_ready else "⚪ 持續監控"

        lines = [
            "## 🎯 市場狀態儀表板",
            "",
            "| 指標 | 數值 | 狀態 | 判準 |",
            "|:-----|-----:|:-----|:-----|",
            f"| VIX 恐慌指數 | {vix:.1f} | {vix_status} | < 20 正常, 20-30 警戒, > 40 恐慌 |",
            f"| GLI Z-Score | {gli_z:+.2f} | {gli_status} | > 0 充裕, < -2 枯竭 (買點) |",
            f"| DEFCON 等級 | {defcon_emoji} Lv.{defcon} | {'安全' if defcon >= 4 else '警戒' if defcon >= 3 else '危險'} | 5=安全, 1=最高警戒 |",
            f"| 市場體制 | {regime} | {'趨勢市場' if hurst > 0.55 else '震盪市場'} | Hurst {hurst:.2f} |",
            "",
            f"**梭哈條件**: {all_in_status}",
            "",
            "> 💡 當 VIX > 40 且 GLI < -2.0 時，解鎖 90% 現金分批買入 F-Score ≥ 7 的高 IVOL 權值股",
            "",
            "---",
            "",
        ]
        return "\n".join(lines)

    def _get_oversold_quality_candidates(
        self, scan_results: list[ScanResultRowDTO]
    ) -> list[ScanResultRowDTO]:
        """錯殺候選名單（熊市備戰）"""
        candidates = []
        for r in scan_results:
            f_score = r.get("F_SCORE")
            ivol_pct = r.get("IVOL_Percentile")
            try:
                f_val = int(f_score) if f_score is not None else 0
            except (ValueError, TypeError):
                f_val = 0
            try:
                ivol_val = float(ivol_pct) if ivol_pct is not None else 0
            except (ValueError, TypeError):
                ivol_val = 0
            if f_val >= 7 and ivol_val > 75:
                candidates.append(r)
        return candidates

    def _format_oversold_table(self, candidates: list[ScanResultRowDTO]) -> str:
        """格式化錯殺候選表格"""
        if not candidates:
            return "*目前無符合條件的錯殺候選*\n"
        lines = [
            "| 股票 | F-Score | IVOL Rank | 現價 | 理想買點條件 |",
            "|:-----|--------:|----------:|-----:|:-------------|",
        ]
        for r in candidates[:10]:
            symbol = r.get("SYMBOL", "")
            f_score = r.get("F_SCORE", "-")
            ivol_pct = r.get("IVOL_Percentile", 0)
            close = self._safe_float(r.get("CLOSE"))
            close_str = f"{close:.0f}" if close else "-"
            lines.append(
                f"| {symbol} | {f_score} | {ivol_pct:.0f}% | {close_str} | VIX > 40 時 |"
            )
        return "\n".join(lines)

    def _format_scan_results_table(
        self, results: list[ScanResultRowDTO], top_n: int = 20
    ) -> str:
        """Format scan results table (Markdown) — 殘差動能排行榜

        按 MOMENTUM (殘差動能) 排名，台股/美股各顯示：
        - 🇹🇼 台股動能前 20 + 倒數 20
        - 🇺🇸 美股動能前 20 + 倒數 20

        保留 ENTRY_SIGNAL、IVOL_DECISION、F_SCORE 等判準欄位供參考。


        Args:
            results: 掃描結果列表
            top_n: 每組顯示前 N 名 (預設 20)

        Returns:
            Markdown 表格字串
        """
        if not results:
            return "*今日無掃描資料*"

        # ========================================
        # 1. 預處理：計算潛在漲幅 + 數據品質檢核
        # ========================================
        processed = []
        for row in results:
            close_price = self._safe_float(row.get("CLOSE"))
            theo_price = self._safe_float(row.get("THEO_PRICE"))

            # 計算潛在漲幅
            if close_price and theo_price and close_price > 0:
                upside = (theo_price - close_price) / close_price
            else:
                upside = None

            # 數據品質檢核
            data_quality = "OK"
            if upside is not None and upside < -0.5:
                data_quality = "ANOMALY"
            elif close_price is None or theo_price is None:
                data_quality = "MISSING"

            processed.append({**row, "UPSIDE": upside, "DATA_QUALITY": data_quality})

        valid_data = [r for r in processed if r["DATA_QUALITY"] == "OK"]

        # ========================================
        # 2. 基本篩選：排除彩票股和已觸發停損
        # ========================================
        # - IVOL_DECISION=LOTTERY: 高風險彩票股
        # - STOP_LOSS_TRIGGERED=True: 已觸發停損
        # 注意: CSV 值為字串 'True'/'False'，需正確比較
        base_filtered = [
            r
            for r in valid_data
            if r.get("IVOL_DECISION") != "LOTTERY"
            and r.get("STOP_LOSS_TRIGGERED") != "True"
        ]

        # ========================================
        # 3. 分離台股/美股
        # ========================================
        def is_tw_stock(symbol: str) -> bool:
            return symbol.isdigit() or symbol.endswith(".TW") or symbol.endswith(".TWO")

        tw_stocks = [r for r in base_filtered if is_tw_stock(r.get("SYMBOL", ""))]
        us_stocks = [r for r in base_filtered if not is_tw_stock(r.get("SYMBOL", ""))]

        # ========================================
        # 4. 排序函數：使用 MOMENTUM (殘差動能) 排序
        # ========================================
        def sort_by_momentum(r):
            return self._safe_float(r.get("MOMENTUM")) or -999

        # 動能前 20：MOMENTUM 由高到低
        tw_stocks_top = sorted(tw_stocks, key=sort_by_momentum, reverse=True)
        us_stocks_top = sorted(us_stocks, key=sort_by_momentum, reverse=True)

        # 動能倒數 20：MOMENTUM 由低到高
        tw_stocks_bottom = sorted(tw_stocks, key=sort_by_momentum, reverse=False)
        us_stocks_bottom = sorted(us_stocks, key=sort_by_momentum, reverse=False)

        lines = []

        # ========================================
        # 5. 台股動能前 20
        # ========================================
        lines.append("### 🇹🇼 台股動能前 20（做多候選）")
        lines.append("")
        if tw_stocks_top:
            lines.append(self._format_ranked_table(tw_stocks_top[:top_n]))
        else:
            lines.append("*今日無符合條件的標的*")
        lines.append("")

        # ========================================
        # 6. 台股動能倒數 20
        # ========================================
        lines.append("### 🇹🇼 台股動能倒數 20（避開/做空候選）")
        lines.append("")
        if tw_stocks_bottom:
            lines.append(self._format_ranked_table(tw_stocks_bottom[:top_n]))
        else:
            lines.append("*今日無符合條件的標的*")
        lines.append("")

        # ========================================
        # 7. 美股動能前 20
        # ========================================
        lines.append("### 🇺🇸 美股動能前 20（做多候選）")
        lines.append("")
        if us_stocks_top:
            lines.append(self._format_ranked_table(us_stocks_top[:top_n]))
        else:
            lines.append("*今日無符合條件的標的*")
        lines.append("")

        # ========================================
        # 8. 美股動能倒數 20
        # ========================================
        lines.append("### 🇺🇸 美股動能倒數 20（避開/做空候選）")
        lines.append("")
        if us_stocks_bottom:
            lines.append(self._format_ranked_table(us_stocks_bottom[:top_n]))
        else:
            lines.append("*今日無符合條件的標的*")
        lines.append("")

        # ========================================
        # 9. 統計摘要
        # ========================================
        tw_count = len(tw_stocks)
        us_count = len(us_stocks)
        lines.append(
            f"> 今日共 {len(valid_data)} 筆資料 (台股 {tw_count} / 美股 {us_count})"
        )
        lines.append("")

        # ========================================
        # 10. 欄位說明 (詳細易懂版)
        # ========================================
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("### 欄位說明")
        lines.append("")
        lines.append("**偏離%**：股價與理論價的差距")
        lines.append("- `-5%` = 目前價格比理論價低 5%（低估，是買入機會）")
        lines.append("- `+3%` = 目前價格比理論價高 3%（高估，不宜追高）")
        lines.append("")
        lines.append("**複合分**：綜合動能、品質、風險的總評分")
        lines.append("- `強` (≥1.5)：強力推薦")
        lines.append("- `中` (1.0~1.5)：值得關注")
        lines.append("- `弱` (<1.0)：條件未達")
        lines.append("")
        lines.append("**判準**：進場訊號與依據")
        lines.append("- `LONG(動能=2.3,偏離=-5.4)` = 建議做多，動能分數 2.3，低估 5.4%")
        lines.append("- `HOLD` = 觀望，條件還不夠強")
        lines.append("- `SKIP` = 跳過，不符合篩選條件")
        lines.append("")
        lines.append("**階段**：股票目前所處的動能週期")
        lines.append("- `啟動`：趨勢剛開始，可考慮進場")
        lines.append("- `確認`：趨勢穩定向上，持續持有")
        lines.append("- `過熱`：短期漲多，可能回調")
        lines.append("- `老化`：動能減弱，準備出場")
        lines.append("- `崩潰`：趨勢結束，應已離場")
        lines.append("")
        lines.append("**F Score**：Piotroski 財務品質分數 (0-9 分)")
        lines.append("- `7+優`：財務健康")
        lines.append("- `4-6中`：普通")
        lines.append("- `<4差`：財務有疑慮")
        lines.append("")

        # ========================================
        # 11. 異常數據警告
        # ========================================
        anomalies = [r for r in processed if r["DATA_QUALITY"] == "ANOMALY"]
        if anomalies:
            lines.append(
                f"> ⚠️ **數據品質警示**: {len(anomalies)} 筆數據潛在跌幅超過 50%，已排除。"
            )

        return "\n".join(lines)

    def _format_ranked_table(self, candidates: list[ScanResultRowDTO]) -> str:
        """格式化排名表格（新版：按 COMPOSITE_SCORE 排名，保留判準標籤）

        欄位說明：
        - 代碼: 股票代碼
        - 現價→目標: 現價 / 理論目標價
        - 偏離%: 價格偏離百分比 (負=低估，正=高估)
        - 複合分: 多因子複合評分
        - 判準: ENTRY_SIGNAL + 簡短理由
        - 階段: 市場狀態
        - F Score: Piotroski F-Score
        """
        lines = [
            "| 代碼 | 現價→目標 | 偏離% | 複合分 | 判準 | 階段 | F Score |",
            "|:-----|----------:|------:|-------:|:-----|:----:|--------:|",
        ]

        for row in candidates:
            symbol = row.get("SYMBOL", "")
            close = self._safe_float(row.get("CLOSE"))
            theo = self._safe_float(row.get("THEO_PRICE"))

            # 價格偏離：優先用 REMAINING_ALPHA_PCT，否則用 PRICE_DEVIATION_PCT
            remaining_alpha_pct = self._safe_float(row.get("REMAINING_ALPHA_PCT"))
            price_deviation_pct = self._safe_float(row.get("PRICE_DEVIATION_PCT"))

            if remaining_alpha_pct is not None:
                deviation = remaining_alpha_pct
            elif price_deviation_pct is not None:
                deviation = -price_deviation_pct  # 反轉：原本正值=高估，這裡正值=低估
            else:
                deviation = None

            composite_score = self._safe_float(row.get("COMPOSITE_SCORE"))
            entry_signal = row.get("ENTRY_SIGNAL", "")
            momentum = self._safe_float(row.get("MOMENTUM"))
            f_score = row.get("F_SCORE")

            # 從 CSV 取得或計算市場狀態
            market_state = row.get("MARKET_STATE") or ""
            if not market_state:
                market_state, _ = self._calculate_market_state(row)

            # 格式化: 現價→目標
            if close and theo:
                price_str = f"{close:.0f}→{theo:.0f}"
            else:
                price_str = "-"

            # 價格偏離%
            if deviation is not None:
                if deviation > 0:
                    alpha_str = f"-{abs(deviation):.1f}%"  # 負值=低估=買入機會
                else:
                    alpha_str = f"+{abs(deviation):.1f}%"  # 正值=高估
            else:
                alpha_str = "-"

            # 複合評分 + 判準
            if composite_score is not None:
                if composite_score >= 1.5:
                    comp_str = f"{composite_score:.1f}強"
                elif composite_score >= 1.0:
                    comp_str = f"{composite_score:.1f}中"
                else:
                    comp_str = f"{composite_score:.1f}弱"
            else:
                comp_str = "-"

            # ENTRY_SIGNAL + 判準理由 (用完整中文)
            mom_str = f"動能={momentum:.1f}" if momentum is not None else ""
            dev_str = f"偏離={deviation:.1f}%" if deviation is not None else ""
            reason = ",".join(filter(None, [mom_str, dev_str]))

            if entry_signal == "LONG":
                signal_str = f"LONG({reason})" if reason else "LONG"
            elif entry_signal == "HOLD":
                signal_str = f"HOLD({reason})" if reason else "HOLD"
            elif entry_signal == "SHORT":
                signal_str = f"SHORT({reason})" if reason else "SHORT"
            else:
                signal_str = "SKIP"

            # 市場狀態文字標籤
            state_text = {
                "趨勢啟動": "啟動",
                "趨勢確認": "確認",
                "動能過熱": "過熱",
                "動能老化": "老化",
                "動能崩潰": "崩潰",
                "擁擠警報": "擁擠",
                "觀察中": "觀察",
            }
            state_str = state_text.get(
                market_state, market_state[:2] if market_state else "-"
            )

            # F-Score 文字標籤
            if f_score is not None:
                try:
                    f_val = int(f_score)
                    if f_val >= 7:
                        f_str = f"{f_val}優"
                    elif f_val >= 4:
                        f_str = f"{f_val}中"
                    else:
                        f_str = f"{f_val}差"
                except (ValueError, TypeError):
                    f_str = "-"
            else:
                f_str = "-"

            lines.append(
                f"| {symbol} | {price_str} | {alpha_str} | {comp_str} | "
                f"{signal_str} | {state_str} | {f_str} |"
            )

        return "\n".join(lines)

    def _format_candidate_table(self, candidates: list[ScanResultRowDTO]) -> str:
        """格式化做多候選表格（精簡版）

        欄位說明：
        - 代碼: 股票代碼
        - 現價→目標: 現價 / 理論目標價
        - 剩餘α%: 剩餘 Alpha 空間
        - 複合分: 多因子複合評分
        - 配置: HRP 權重% (擁擠度)
        - 階段: 市場狀態
        - 操作: 操作建議
        - F: Piotroski F-Score 圖示
        """
        lines = [
            "| 代碼 | 現價→目標 | 剩餘α% | 複合分 | 配置 | 階段 | 操作 | F |",
            "|:-----|----------:|-------:|-------:|-----:|:----:|:----:|:-:|",
        ]

        for row in candidates:
            symbol = row.get("SYMBOL", "")
            close = self._safe_float(row.get("CLOSE"))
            theo = self._safe_float(row.get("THEO_PRICE"))

            # 新增欄位
            remaining_alpha_pct = self._safe_float(row.get("REMAINING_ALPHA_PCT"))
            composite_score = self._safe_float(row.get("COMPOSITE_SCORE"))
            hrp_weight = self._safe_float(row.get("HRP_WEIGHT"))
            crowding_score = self._safe_float(row.get("CROWDING_SCORE"))
            f_score = row.get("F_SCORE")

            # 從 CSV 取得或計算市場狀態與操作指令
            market_state = row.get("MARKET_STATE") or ""
            action = row.get("ACTION_SIGNAL") or ""
            if not market_state or not action:
                market_state, action = self._calculate_market_state(row)

            # 格式化: 現價→目標
            if close and theo:
                price_str = f"{close:.0f}→{theo:.0f}"
            else:
                price_str = "-"

            # 剩餘 Alpha %
            if remaining_alpha_pct is not None:
                alpha_str = (
                    f"**{remaining_alpha_pct:.0f}%**"
                    if remaining_alpha_pct > 50
                    else f"{remaining_alpha_pct:.0f}%"
                )
            else:
                alpha_str = "-"

            # 複合評分
            comp_str = f"{composite_score:.1f}" if composite_score is not None else "-"

            # 配置：合併 HRP 權重 + 擁擠度
            if hrp_weight is not None:
                if crowding_score is not None and crowding_score > 70:
                    config_str = f"{hrp_weight:.1f}⚠️"  # 高擁擠警示
                else:
                    config_str = f"{hrp_weight:.1f}"
            else:
                config_str = "-"

            # F-Score 圖示化
            if f_score is not None:
                try:
                    f_val = int(f_score)
                    if f_val >= 7:
                        f_str = "✅"  # 高品質
                    elif f_val >= 4:
                        f_str = "⚠️"  # 中等
                    else:
                        f_str = "❌"  # 低品質
                except (ValueError, TypeError):
                    f_str = "-"
            else:
                f_str = "-"

            # 市場狀態 emoji 映射
            state_emoji = {
                "趨勢啟動": "🌱",
                "趨勢確認": "🚀",
                "動能過熱": "🔥",
                "動能老化": "💀",
                "動能崩潰": "🔴",
                "擁擠警報": "⚠️",
                "觀察中": "👀",
            }
            state_str = state_emoji.get(
                market_state, market_state[:2] if market_state else "-"
            )

            # 操作指令顏色標記
            action_str = f"**{action}**" if action in ("BUY", "STOP") else action

            lines.append(
                f"| {symbol} | {price_str} | {alpha_str} | {comp_str} | "
                f"{config_str} | {state_str} | {action_str} | {f_str} |"
            )

        return "\n".join(lines)

    def _format_watchlist_table(self, candidates: list[ScanResultRowDTO]) -> str:
        """格式化觀察名單表格

        顯示 MARKET_STATE=觀察中 的標的，追蹤動能衰減
        欄位：代碼 | 動能Z | 剩餘肉量% | 訊號天數 | 半衰期 | 操作
        """
        lines = [
            "| 代碼 | 動能Z | 剩餘肉量% | 訊號天數 | 半衰期 | 操作 |",
            "|:-----|------:|----------:|---------:|-------:|:----:|",
        ]

        for row in candidates:
            symbol = row.get("SYMBOL", "")
            momentum = self._safe_float(row.get("MOMENTUM"))
            remaining_meat = self._safe_float(row.get("REMAINING_MEAT_RATIO"))
            signal_age = self._safe_float(row.get("SIGNAL_AGE_DAYS"))
            half_life = self._safe_float(row.get("HALF_LIFE"))
            action = row.get("ACTION_SIGNAL") or "-"

            # 動能 Z-Score
            mom_str = f"{momentum:.2f}" if momentum is not None else "-"

            # 剩餘肉量 (0-100%)
            if remaining_meat is not None:
                meat_str = (
                    f"**{remaining_meat:.0%}**"
                    if remaining_meat > 0.5
                    else f"{remaining_meat:.0%}"
                )
            else:
                meat_str = "-"

            # 訊號天數
            age_str = f"{signal_age:.0f}" if signal_age is not None else "-"

            # 半衰期
            hl_str = f"{half_life:.0f}" if half_life is not None else "-"

            lines.append(
                f"| {symbol} | {mom_str} | {meat_str} | {age_str} | {hl_str} | {action} |"
            )

        return "\n".join(lines)

    def _format_risk_table(self, candidates: list[ScanResultRowDTO]) -> str:
        """格式化風險視角表格

        顯示波動擴張或 Beta 異動的標的
        欄位：代碼 | 風險類型 | Beta變化% | IVOL決策 | 操作
        """
        lines = [
            "| 代碼 | 風險類型 | Beta變化% | IVOL決策 | 操作 |",
            "|:-----|:---------|----------:|:--------:|:----:|",
        ]

        for row in candidates:
            symbol = row.get("SYMBOL", "")
            vol_expansion = row.get("VOLATILITY_EXPANSION_FLAG")
            beta_spike = row.get("BETA_SPIKE_ALERT")
            beta_change = self._safe_float(row.get("BETA_CHANGE_PCT"))
            ivol_decision = row.get("IVOL_DECISION") or "-"
            action = row.get("ACTION_SIGNAL") or "-"

            # 風險類型
            risk_types = []
            if vol_expansion:
                risk_types.append("📈 波動擴張")
            if beta_spike:
                risk_types.append("⚡ Beta劇變")
            risk_str = ", ".join(risk_types) if risk_types else "-"

            # Beta 變化
            if beta_change is not None:
                beta_str = (
                    f"**{beta_change:.0%}**"
                    if abs(beta_change) > 0.5
                    else f"{beta_change:.0%}"
                )
            else:
                beta_str = "-"

            lines.append(
                f"| {symbol} | {risk_str} | {beta_str} | {ivol_decision} | {action} |"
            )

        return "\n".join(lines)

    def _format_short_table(self, candidates: list[ScanResultRowDTO]) -> str:
        """格式化做空候選表格（增強版）

        做空標的特徵：
        - 價格偏離高 (> 理論價)
        - 低 F-Score (≤ 4)
        - 高擁擠度
        """
        lines = [
            "| 代碼 | 現價→目標 | 偏離% | 複合分 | IVOL決策 | F分 | 擁擠 |",
            "|:-----|----------:|------:|-------:|:--------:|:---:|-----:|",
        ]

        for row in candidates:
            symbol = row.get("SYMBOL", "")
            close = self._safe_float(row.get("CLOSE"))
            theo = self._safe_float(row.get("THEO_PRICE"))
            deviation = self._safe_float(row.get("PRICE_DEVIATION_PCT"))
            composite_score = self._safe_float(row.get("COMPOSITE_SCORE"))
            ivol_decision = row.get("IVOL_DECISION", "")
            f_score = row.get("F_SCORE")
            crowding_score = self._safe_float(row.get("CROWDING_SCORE"))

            # 格式化: 現價→目標
            if close and theo:
                price_str = f"{close:.0f}→{theo:.0f}"
            else:
                price_str = "-"

            dev_str = f"+{deviation:.0f}%" if deviation else "-"
            comp_str = f"{composite_score:.1f}" if composite_score is not None else "-"
            f_str = str(f_score) if f_score is not None else "-"

            # 擁擠度警示
            if crowding_score is not None:
                crowd_str = (
                    f"⚠️{crowding_score:.0f}"
                    if crowding_score > 70
                    else f"{crowding_score:.0f}"
                )
            else:
                crowd_str = "-"

            lines.append(
                f"| {symbol} | {price_str} | {dev_str} | {comp_str} | {ivol_decision} | {f_str} | {crowd_str} |"
            )

        return "\n".join(lines)

    def _format_exit_alert_table(self, alerts: list[ScanResultRowDTO]) -> str:
        """格式化出場警示表格"""
        lines = [
            "| 代碼 | 觸發訊號 | 細節 |",
            "|:-----|:---------|:-----|",
        ]

        for row in alerts:
            symbol = row.get("SYMBOL", "")
            triggers = []
            details = []

            if row.get("STOP_LOSS_TRIGGERED"):
                triggers.append("硬停損")
                details.append("月高回落 > 10%")

            if row.get("ATR_TRAILING_STOP"):
                triggers.append("ATR停損")
                atr_price = self._safe_float(row.get("ATR_TRAILING_STOP"))
                if atr_price:
                    details.append(f"停損價 {atr_price:.0f}")

            if row.get("RSI_DIVERGENCE") == "bearish":
                triggers.append("RSI頂背離")
                details.append("動能衰竭")

            if row.get("BETA_SPIKE_ALERT"):
                triggers.append("Beta劇變")
                beta_chg = self._safe_float(row.get("BETA_CHANGE_PCT"))
                if beta_chg:
                    details.append(f"變化 {beta_chg:.0%}")

            trigger_str = ", ".join(triggers) if triggers else "-"
            detail_str = "; ".join(details) if details else "-"

            lines.append(f"| {symbol} | {trigger_str} | {detail_str} |")

        return "\n".join(lines)

    def _safe_float(self, value) -> float | None:
        """安全轉換為 float"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _calculate_market_state(self, row: dict) -> tuple[str, str]:
        """
        根據 Z-Score 和年齡計算市場狀態與操作指令

        依據「凱利公式後交易價格與出場」操作總結表：
        - 趨勢啟動: 0.5 < Z < 1.5, 年齡 < 90 天 → BUY
        - 趨勢確認: 1.5 < Z < 2.5, 年齡 90-270 天 → HOLD
        - 動能過熱: Z > 3.0 → TRIM
        - 動能老化: Z > 1.0, 年齡 > 360 天 → EXIT
        - 動能崩潰: 停損觸發 → STOP
        """
        z_score = self._safe_float(row.get("MOMENTUM"))
        age_days = self._safe_float(row.get("SIGNAL_AGE_DAYS"))
        stop_triggered = row.get("STOP_LOSS_TRIGGERED")

        # 預設值
        if z_score is None:
            return ("⚪ 無資料", "-")

        # 動能崩潰（最高優先級）
        if stop_triggered:
            return ("🔴 崩潰", "STOP")

        # 動能過熱
        if z_score > 3.0:
            return ("🔥 過熱", "TRIM")

        # 動能老化
        if age_days is not None and age_days > 360 and z_score > 1.0:
            return ("💀 老化", "EXIT")

        # 趨勢啟動
        if 0.5 < z_score < 1.5 and (age_days is None or age_days < 90):
            return ("🌱 啟動", "BUY")

        # 趨勢確認
        if 1.5 <= z_score <= 2.5:
            if age_days is None or 90 <= age_days <= 270:
                return ("🚀 確認", "HOLD")

        # 高動能但年齡偏高（觀察）
        if z_score > 2.5 and (age_days is None or age_days > 270):
            return ("🌙 衰退", "TRIM")

        # 低動能或觀望區間
        if z_score < 0.5:
            return ("⏸️ 觀望", "-")

        # 其他情況
        return ("⚪ 觀察", "HOLD")

    def _get_stock_diagnosis(self, stock: ScanResultRowDTO) -> StockDiagnosisDTO:
        """取得股票健檢分數"""
        momentum = stock.get("momentum", 1.0)
        signal = stock.get("signal", "🟡")
        technical_score = min(momentum * 30, 95)
        sentiment_score = 85 if signal == "🟢" else 70
        overall = (technical_score + sentiment_score) / 2
        return {
            "technical": f"{technical_score:.0f}/100",
            "sentiment": f"{sentiment_score:.0f}/100",
            "overall": f"{overall:.0f}/100",
            "grade": "A" if overall >= 85 else "B" if overall >= 70 else "C",
        }

    def _get_stock_pairs(self, symbol: str) -> StockPairsDTO:
        """取得股票的配對交易機會 - 使用真實掃描"""
        try:
            # 判斷市場
            is_tw = symbol.isdigit() or symbol.endswith(".TW")
            sector = "半導體" if is_tw else "科技"

            query = self._get_pairs_query()
            result = query.execute(sector=sector, min_correlation=0.5)

            # 找到包含此股票的配對
            for p in result.get("pairs", []):
                if (
                    p["symbol_a"].replace(".TW", "") == symbol
                    or p["symbol_b"].replace(".TW", "") == symbol
                ):
                    pair_with = (
                        p["symbol_b"]
                        if p["symbol_a"].replace(".TW", "") == symbol
                        else p["symbol_a"]
                    )
                    return {
                        "pair_with": pair_with.replace(".TW", ""),
                        "correlation": p["correlation"],
                        "z_score": p["spread_zscore"],
                    }

            return {"pair_with": "N/A", "correlation": 0, "z_score": 0}
        except Exception:
            return {"pair_with": "N/A", "correlation": 0, "z_score": 0}

    def _get_todos(self, weather: dict, portfolio: dict) -> list[TodoDTO]:
        """生成待辦事項"""
        todos = []

        if weather["overall_signal"] == "🔴":
            todos.append(
                {"priority": "🔴", "item": "停止買入，設定減倉提醒", "type": "風控"}
            )

        if portfolio["has_danger"]:
            todos.append(
                {"priority": "🔴", "item": "檢查 DANGER 持倉，執行停損", "type": "風控"}
            )

        warning_positions = [p for p in portfolio["positions"] if p["status"] == "⚠️"]
        for pos in warning_positions:
            todos.append(
                {
                    "priority": "🟡",
                    "item": f"關注 {pos['symbol']} 停損緩衝",
                    "type": "風控",
                }
            )

        todos.append({"priority": "🟢", "item": "維持現有部位", "type": "例行"})

        return todos

    def _generate_report(
        self,
        date: str,
        weather: dict,
        regime_weights: dict,
        advisors: dict,
        portfolio: dict,
        events: list,
        entry_checklist: dict,
        scan_results: list,
        risk_alerts: list,
        pairs: list,
        supply_chain: list,
        halt: dict,
        todos: list,
    ) -> str:
        """生成 Markdown 報告 (含判準定義，供 LLM 解讀)"""

        # 檢查今天是否為營收開牌日 (每月 10 日)
        today_dt = datetime.now()
        is_revenue_day = today_dt.day == 10
        revenue_alert = ""
        if is_revenue_day:
            revenue_alert = """
> [!IMPORTANT]
> **📊 今天是營收開牌日！** 各公司 11 月營收將於今日公布。等待收盤消化資訊，11 日再評估反應。

"""
        elif today_dt.day == 11:
            revenue_alert = """
> [!NOTE]
> **📈 今天是營收反應日！** 觀察昨日公布營收的市場反應，符合預期可能利多出盡，超預期可追蹤。

"""

        # 1. 數據增強 (Alpha Contribution)
        enriched_results = self._enrich_scan_results_with_alpha(scan_results)

        # 2. 板塊分析 (Sector Distribution)
        sector_info = self._calculate_sector_stats(enriched_results)

        report = (
            dedent(f"""
            # 📰 每日簡報 — {date}

            > 生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}
            {revenue_alert}
            ---
        """).strip()
            + "\n\n"
        )

        # 市場狀態儀表板（狩獵者策略核心）
        report += self._format_dashboard_section(weather)

        report += dedent(f"""
            
            ## 📈 體制識別


            | 指標 | 數值 | 解讀 | 說明 |
            |------|------|------|------|
            | Hurst | {weather.get("hurst", 0.5)} | {"趨勢市場" if weather.get("hurst", 0.5) > 0.55 else "震盪/均值回歸"} | >0.55 跟隨趨勢，<0.45 逢低布局 |
            | HMM 牛市機率 | {weather.get("bull_prob", 50)}% | {"牛市" if weather.get("hmm_state", 0) == 1 else "熊市"} | 機器學習模型判斷的牛熊機率 |
            | PCA 穩定度 | {weather.get("pca_stability", 0.9)} | {"結構穩定" if weather.get("pca_stability", 0.9) > 0.8 else "結構異常"} | 市場結構是否正常 |
            | 凱利係數 | {weather.get("kelly_factor", 1.0)}x | 倉位調整因子 | 建議的倉位縮放比例 |

            **體制結論**：{weather.get("regime", "震盪區間")}

            ---

            ## 📊 體制權重

            | 指標 | 值 |
            |------|-----|
            | HMM 體制 | {regime_weights["regime_emoji"]} {regime_weights["regime"]} ({regime_weights["bull_prob"]}%) |
            | Trend 權重 | {regime_weights["trend_weight"]}% |
            | Value 權重 | {regime_weights["value_weight"]}% |
            | Quality 權重 | {regime_weights["quality_weight"]}% |

            > 💡 牛市偏重 Trend (動能)，熊市偏重 Value/Quality (防禦)

            ---
        """)

        # 風險警示區塊
        if risk_alerts:
            report += "\n## ⚠️ 風險警示\n\n"
            report += "| 股票 | 警示類型 | 說明 | 嚴重度 |\n"
            report += "|------|---------|------|--------|\n"
            for alert in risk_alerts:
                report += f"| {alert['symbol']} | {alert['alert_type']} | {alert['value']} | {alert['severity']} |\n"
            report += "\n> 💡 建議優先處理 🔴 級別警報\n\n---\n"

        report += dedent(f"""

            ## 🧠 四顧問診斷

            | 顧問 | 評估維度 | 判定 | 理由 | 說明 |
            |------|----------|------|------|------|
            | 🔧 工程師 | 流動性/結構 | {advisors["engineer"]["verdict"]} | {advisors["engineer"]["reason"]} | 看資金面與技術結構 |
            | 🌿 生物學家 | 產業生態 | {advisors["biologist"]["verdict"]} | {advisors["biologist"]["reason"]} | 看產業趨勢與競爭格局 |
            | 🧠 心理學家 | 市場情緒 | {advisors["psychologist"]["verdict"]} | {advisors["psychologist"]["reason"]} | 看恐慌貪婪與投資人行為 |
            | ♟️ 策略家 | 勝率賠率 | {advisors["strategist"]["verdict"]} | {advisors["strategist"]["reason"]} | 看風險報酬比 |
            | **共識** | - | **{advisors["consensus"]}** | {advisors["allocation"]} | 四位顧問的綜合意見 |

            > 💡 進攻 ≥3 位 = 可積極做多；分歧 = 觀望為主；防守 = 減倉避險

            ---

            ## 🏥 持倉健康狀態

            | 標的 | 現價 | 成本 | 停損 | 緩衝 | 狀態 | 說明 |
            |------|------|------|------|------|------|------|
        """)
        for pos in portfolio["positions"]:
            buffer_desc = (
                "安全"
                if pos["buffer_pct"] > 15
                else "觀察"
                if pos["buffer_pct"] > 10
                else "緊繃"
            )
            report += f"| {pos['symbol']} | ${pos['current_price']} | ${pos['cost']} | ${pos['stop_loss']} | {pos['buffer_pct']}% | {pos['status']} | {buffer_desc} |\n"

        report += f"""
**健康度總結**：{portfolio["healthy_count"]}/{portfolio["total_count"]} 健康

> ### 💊 判準定義 (Portfolio Health)
>
> | 緩衝 % | 狀態 | 建議 |
> |--------|------|------|
> | > 15% | ✅ 健康 | 可加碼 |
> | 10-15% | 🔍 觀察 | 維持 |
> | 5-10% | ⚠️ 警戒 | 考慮減碼 |
> | < 5% | 🔴 危險 | 立即停損 |
>
> 💡 緩衝 = (現價-停損)/現價

---

## 📅 事件提醒 (近 7 個重要事件)

| 日期 | 事件 | 風險 | 動作 | 說明 |
|------|------|------|------|------|
"""
        for event in events[:7]:
            report += f"| {event['date']} | {event['event']} | {event['risk_level']} | {event['action']} | {event.get('description', '')} |\n"

        report += """
> 💡 ⭐⭐⭐ = 高風險事件，當日應降低槓桿、避免開新倉

---

## ✅ 進場決策總檢表

| 項目 | 門檻 | 今日狀態 | 通過 | 白話說明 |
|------|------|----------|------|----------|
"""
        for check in entry_checklist["checks"]:
            passed_icon = "✅" if check["passed"] else "❌"
            report += f"| {check['item']} | {check['threshold']} | {check['current']} | {passed_icon} | {check.get('description', '')} |\n"

        report += dedent(f"""
            
**進場決策**：{entry_checklist["decision"]} ({entry_checklist["passed_count"]}/{entry_checklist["total_count"]} 通過)

> ### ✅ 判準定義 (Entry Decision)
>
> **五大關卡**
>
> | 項目 | 門檻 | 說明 |
> |------|------|------|
> | VIX | < 25 | 恐慌指數正常 |
> | DEFCON | ≥ 3 | 風險等級中等以上 |
> | 流動性象限 | EXPANSION | 資金擴張中 |
> | GEX | ≥ MILD_LONG | 波動受壓制 |
> | 持倉健康 | 無 DANGER | 現有部位安全 |
>
> **決策矩陣**
>
> | 通過項目 | 決策 |
> |----------|------|
> | 5/5 | 🟢🟢 可執行狩獵計畫 |
> | 4/5 | 🟢 可進場，縮小倉位 |
> | 3/5 | 🟡 觀望 |
> | < 3/5 | 🔴 禁止進場 |
>
> **品質濾網 (剔除條件)**
>
> - IVOL 前 10% 高
> - MAX 前 10% 高
> - ID 前 20% 高
> - Amihud 前 10% 高

---
""")

        # 板塊分布區塊 (新增)
        if sector_info["stats"]:
            report += "## 🏭 板塊分布與集中度\n\n"

            # 顯示前 5 大板塊
            report += "| 板塊 | 數量 | 佔比 |\n"
            report += "|------|------|------|\n"
            total = sector_info["total"]
            for sector, count in sector_info["stats"].items():
                pct = count / total
                bar = "█" * int(pct * 10)
                report += f"| {sector} | {count} | {pct:.0%} {bar} |\n"

            # 顯示警示
            if sector_info["alerts"]:
                report += "\n"
                for alert in sector_info["alerts"]:
                    report += f"> {alert}\n"

            report += "\n---\n\n"

        # 殘差動能掃描結果 - 傳入全部結果，函數內部會分割台股/美股
        scan_table = self._format_scan_results_table(enriched_results, top_n=20)
        report += f"""
## 🚀 殘差動能掃描結果

{scan_table}

> **篩選規則**: 已排除產業超限、價值陷阱、IVOL 剔除標的

---
"""

        report += """
## 🔄 配對交易機會

| 配對 | 相關性 | Z-Score | 訊號 | 說明 |
|------|--------|---------|------|------|
"""
        if pairs:
            for pair in pairs:
                z_desc = (
                    "偏離大，可能回歸" if abs(pair["z_score"]) > 1.5 else "正常範圍"
                )
                report += f"| {pair['pair']} | {pair['correlation']:.2f} | {pair['z_score']:.1f} | {pair['signal']} | {z_desc} |\n"
        else:
            report += "| 無顯著配對機會 | - | - | - | - |\n"

        report += """
> 💡 配對交易：兩檔相關性高的股票，當價差偏離時做反向操作

---

## ⛓️ 供應鏈機會

| 美股 | 台股 | 美股報酬 | 訊號 |
|------|------|----------|------|
"""
        if supply_chain:
            for sc in supply_chain:
                report += f"| {sc['us_stock']} | {sc['tw_stock']} | {sc['us_return']} | {sc['signal']} |\n"
        else:
            report += "| 無顯著供應鏈機會 | - | - | - |\n"

        report += """
> 💡 觀察美股龍頭對台灣供應鏈的傳導效應

---

"""
        # 錯殺候選名單（熊市備戰）
        oversold_candidates = self._get_oversold_quality_candidates(scan_results)
        report += "## 🎯 錯殺候選名單（熊市備戰）\n\n"
        report += self._format_oversold_table(oversold_candidates)
        report += """

> ### 🎯 錯殺判準
> - **F-Score ≥ 7**: Piotroski 財務體質優良
> - **IVOL > 75%**: 近期波動異常高（可能被錯殺）
> - **買點**: 等待 DEFCON 2 (VIX > 40) + GLI 見底

---

## 🧘 HALT 自檢

| 項目 | 問題 | 狀態 | 說明 |
|------|------|------|------|
"""
        report += f"| **H**ungry | 我很急著想賺錢嗎？ | {'是 ⚠️' if halt['hungry'] else '否 ✅'} | 急躁容易追高殺低 |\n"
        report += f"| **A**ngry | 我想對市場「報復」嗎？ | {'是 ⚠️' if halt['angry'] else '否 ✅'} | 報復心態會加倉攤平 |\n"
        report += f"| **L**onely | 我怕落後別人嗎？ | {'是 ⚠️' if halt['lonely'] else '否 ✅'} | FOMO 容易追漲 |\n"
        report += f"| **T**ired | 我精神疲憊嗎？ | {'是 ⚠️' if halt['tired'] else '否 ✅'} | 疲憊時判斷力下降 |\n"

        report += f"""
**結論**：{halt["message"]}

> 💡 任一項為「是」，今日建議暫停交易，先調整心態

---

## 📋 明日待辦事項

| 優先級 | 事項 | 類型 |
|--------|------|------|
"""
        for todo in todos:
            report += f"| {todo['priority']} | {todo['item']} | {todo['type']} |\n"

        report += """
---

_本報告由 `report_generator` 生成，設計供 LLM 解讀使用_
"""
        return report

    def _send_email(self, report: str, date: str) -> bool:
        """發送 Email (Markdown → HTML)"""
        try:
            return self._notification_gateway.send_markdown_email(
                subject=f"📊 MyFin 每日簡報 - {date}",
                markdown_content=report,
            )
        except Exception as e:
            self._logger.warning(f"發送失敗: {e}")
            return False
