"""生成週報 Command

整合各 BC 數據，生成週度覆盤並可選發送 Email
"""

from datetime import datetime, timedelta
from injector import inject
import logging
import numpy as np
import yfinance as yf
from textwrap import dedent

from libs.monitoring.src.ports.notification_gateway_port import (
    NotificationGatewayPort,
)
from libs.reviewing.src.ports.portfolio_provider_port import (
    PortfolioProviderPort,
)
from libs.reviewing.src.domain.services.dsr_calculator import (
    calculate_deflated_sharpe_ratio,
)
from libs.reviewing.src.domain.services.cvar_calculator import assess_tail_risk
from libs.reviewing.src.domain.services.fdr_controller import control_fdr
from libs.reporting.src.ports.generate_weekly_report_port import (
    GenerateWeeklyReportPort,
)
from libs.shared.src.dtos.reporting.report_result_dto import ReportResultDTO
from libs.shared.src.dtos.reporting.performance_dto import PerformanceDTO
from libs.shared.src.dtos.reporting.skill_metrics_dto import SkillMetricsDTO
from libs.shared.src.dtos.reporting.crowding_metrics_dto import CrowdingMetricsDTO
from libs.shared.src.dtos.reporting.decision_quality_dto import DecisionQualityDTO
from libs.shared.src.dtos.reporting.thesis_validation_dto import ThesisValidationDTO
from libs.shared.src.dtos.reporting.strategy_health_dto import StrategyHealthDTO


class GenerateWeeklyReportCommand(GenerateWeeklyReportPort):
    """生成週報

    整合：
    - 績效分析 (performance_reviewer)
    - 技能判定 (performance_reviewer)
    - 策略擁擠度 (performance_reviewer)
    - AI 敘事 (narration)
    """

    @inject
    def __init__(
        self,
        notification_gateway: NotificationGatewayPort,
        portfolio_provider: PortfolioProviderPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._notification_gateway = notification_gateway
        self._portfolio_provider = portfolio_provider

    def execute(self, simulate: bool = False) -> ReportResultDTO:
        """執行生成週報"""

        today = datetime.now()
        period = today.strftime("%Y-W%W")
        self._logger.info(f"開始生成週報: {period}")

        # 1. 取得績效數據
        self._logger.info("步驟 1/6: 取得績效數據...")
        performance = self._get_performance()
        self._logger.info(f"績效數據完成: MTD {performance['mtd_return']:.1%}")

        # 2. 取得技能判定
        self._logger.info("步驟 2/6: 取得技能判定...")
        skill = self._get_skill_metrics()
        self._logger.info(f"技能判定完成: {skill['verdict']}")

        # 3. 取得策略擁擠度
        self._logger.info("步驟 3/6: 取得策略擁擠度...")
        crowding = self._get_crowding_metrics()

        # 4. 取得決策品質
        self._logger.info("步驟 4/6: 取得決策品質...")
        decision_quality = self._get_decision_quality()

        # 5. 取得論點驗證
        self._logger.info("步驟 5/6: 取得論點驗證...")
        thesis_validation = self._get_thesis_validation()

        # 6. 取得策略健康度 (DSR/CVaR/CPCV)
        self._logger.info("步驟 6/6: 取得策略健康度...")
        strategy_health = self._get_strategy_health()
        self._logger.info(f"策略健康度完成: DSR={strategy_health['dsr']:.2f}")

        # 生成 Markdown 報告 (含判準定義)
        self._logger.info("生成 Markdown 報告...")
        report_markdown = self._generate_report(
            period=period,
            performance=performance,
            skill=skill,
            crowding=crowding,
            decision_quality=decision_quality,
            thesis_validation=thesis_validation,
            strategy_health=strategy_health,
        )
        self._logger.info("Markdown 報告完成")

        result = {
            "period": period,
            "performance": performance,
            "skill": skill,
            "crowding": crowding,
            "decision_quality": decision_quality,
            "thesis_validation": thesis_validation,
            "strategy_health": strategy_health,
            "report_markdown": report_markdown,
            "email_sent": False,
        }

        self._logger.info("發送 Email...")
        result["email_sent"] = self._send_email(report_markdown, period)
        self._logger.info(f"Email 發送: {'成功' if result['email_sent'] else '失敗'}")

        self._logger.info("週報生成完成")
        return result

    def _get_performance(self) -> PerformanceDTO:
        """取得績效數據 (從 Shioaji 取得真實交易資料)"""
        try:
            adapter = self._portfolio_provider

            if not adapter.connect():
                return self._default_performance("⚠️ 無法連線 Shioaji")

            # 1. 取得當前持倉 (未實現損益)
            positions = adapter.get_positions()
            unrealized_pnl = (
                sum(pos.get("pnl", 0) for pos in positions) if positions else 0
            )

            # 2. 取得本週交易記錄 (WTD)
            today = datetime.now()
            week_start = today - timedelta(days=today.weekday())  # 本週一
            wtd_trades = adapter.get_profit_loss_history(
                begin_date=week_start.strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )

            # 3. 取得今年交易記錄 (YTD)
            year_start = datetime(today.year, 1, 1)
            ytd_trades = adapter.get_profit_loss_history(
                begin_date=year_start.strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )

            adapter.disconnect()

            # 計算 WTD 報酬
            wtd_pnl = sum(t.get("pnl", 0) for t in wtd_trades)
            wtd_cost = sum(t.get("cost", 0) for t in wtd_trades)
            wtd_return = wtd_pnl / wtd_cost if wtd_cost > 0 else 0

            # 計算 YTD 報酬
            ytd_pnl = sum(t.get("pnl", 0) for t in ytd_trades)
            ytd_cost = sum(t.get("cost", 0) for t in ytd_trades)
            ytd_return = ytd_pnl / ytd_cost if ytd_cost > 0 else 0

            # 計算勝率與盈虧比 (使用 YTD 資料)
            wins = [t for t in ytd_trades if t.get("pnl", 0) > 0]
            losses = [t for t in ytd_trades if t.get("pnl", 0) < 0]
            total_trades = len(wins) + len(losses)

            win_rate = len(wins) / total_trades if total_trades > 0 else 0
            avg_win = sum(t.get("pnl", 0) for t in wins) / len(wins) if wins else 0
            avg_loss = (
                abs(sum(t.get("pnl", 0) for t in losses) / len(losses)) if losses else 0
            )
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0

            # 計算夏普比率 (簡化版：使用每筆交易報酬率)
            if len(ytd_trades) >= 5:
                returns = [
                    t.get("pnl", 0) / t.get("cost", 1)
                    for t in ytd_trades
                    if t.get("cost", 0) > 0
                ]
                if returns:
                    mean_ret = np.mean(returns)
                    std_ret = np.std(returns)
                    # 年化夏普 (假設每月約 10 筆交易)
                    sharpe = (mean_ret / std_ret) * np.sqrt(120) if std_ret > 0 else 0
                else:
                    sharpe = 0
            else:
                sharpe = 0

            # 計算最大回撤 (使用累計損益)
            if ytd_trades:
                cumulative = []
                running = 0
                for t in ytd_trades:
                    running += t.get("pnl", 0)
                    cumulative.append(running)

                peak = cumulative[0]
                max_dd = 0
                for val in cumulative:
                    if val > peak:
                        peak = val
                    dd = (peak - val) / peak if peak > 0 else 0
                    if dd > max_dd:
                        max_dd = dd
            else:
                max_dd = 0

            note = f"✅ 資料來源: Shioaji ({len(ytd_trades)} 筆 YTD 交易)"
            if not ytd_trades:
                note = "⚠️ 今年尚無已實現交易記錄"

            return {
                "mtd_return": round(wtd_return, 4),
                "ytd_return": round(ytd_return, 4),
                "sharpe_ratio": round(sharpe, 2),
                "max_drawdown": round(max_dd, 4),
                "win_rate": round(win_rate, 4),
                "profit_factor": round(profit_factor, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "note": note,
                "total_trades": total_trades,
                "unrealized_pnl": round(unrealized_pnl, 2),
            }
        except Exception as e:
            self._logger.warning(f"績效獲取失敗: {e}")
            return self._default_performance(f"⚠️ 資料獲取失敗: {e}")

    def _default_performance(self, note: str) -> PerformanceDTO:
        """預設績效資料（資料不足時）"""
        return {
            "mtd_return": 0.0,
            "ytd_return": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "win_rate": 0.0,
            "profit_factor": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "note": note,
            "total_trades": 0,
            "unrealized_pnl": 0.0,
        }

    def _get_skill_metrics(self) -> SkillMetricsDTO:
        """取得技能判定（使用真實交易資料計算 DSR/PSR）"""
        try:
            adapter = self._portfolio_provider

            if not adapter.connect():
                return self._default_skill_metrics("⚠️ 無法連線")

            # 取得過去一年的交易紀錄
            today = datetime.now()
            year_ago = today - timedelta(days=365)
            trades = adapter.get_profit_loss_history(
                begin_date=year_ago.strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
            adapter.disconnect()

            if len(trades) < 10:
                return self._default_skill_metrics(
                    f"需累積至少 10 筆交易 (目前 {len(trades)} 筆)"
                )

            # 計算每筆交易報酬率
            returns = [
                t.get("pnl", 0) / t.get("cost", 1)
                for t in trades
                if t.get("cost", 0) > 0
            ]

            if not returns:
                return self._default_skill_metrics("⚠️ 無有效交易資料")

            # 計算夏普比率
            mean_ret = np.mean(returns)
            std_ret = np.std(returns)
            sharpe = (mean_ret / std_ret) * np.sqrt(120) if std_ret > 0 else 0

            # 計算 DSR (Deflated Sharpe Ratio)
            dsr = calculate_deflated_sharpe_ratio(
                sr=sharpe,
                n_trials=5,  # 假設測試過 5 個策略變體
                n_observations=len(returns),
                sr_std=1.0,
            )

            # 計算 PSR (Probabilistic Sharpe Ratio)
            # PSR = Φ((SR - SR_benchmark) * √(n-1) / √(1 - skew*SR + (kurtosis-1)/4 * SR²))
            from scipy import stats

            n = len(returns)
            skew = stats.skew(returns) if n > 2 else 0
            kurtosis = stats.kurtosis(returns) if n > 3 else 3
            sr_benchmark = 0  # 基準夏普 = 0

            denominator = np.sqrt(1 - skew * sharpe + (kurtosis - 1) / 4 * sharpe**2)
            if denominator > 0 and n > 1:
                z_score = (sharpe - sr_benchmark) * np.sqrt(n - 1) / denominator
                psr = stats.norm.cdf(z_score) * 100  # 轉換為百分比
            else:
                psr = 50.0

            # 判定結果 (methodology.md: DSR ≥ 0.95 有效，0.80-0.95 灰色地帶)
            if dsr >= 0.95:
                verdict = "✅ 有效策略"
                confidence = "高"
            elif dsr >= 0.80:
                verdict = "🟡 灰色地帶 (待進一步驗證)"
                confidence = "中"
            else:
                verdict = "⚠️ 偽陽性風險"
                confidence = "低"

            return {
                "dsr": round(dsr, 2),
                "psr": round(psr, 1),
                "verdict": verdict,
                "confidence": confidence,
                "note": f"✅ 資料來源: {len(trades)} 筆交易",
            }
        except Exception as e:
            self._logger.warning(f"技能判定失敗: {e}")
            return self._default_skill_metrics(f"⚠️ 計算失敗: {e}")

    def _default_skill_metrics(self, note: str) -> SkillMetricsDTO:
        """預設技能判定（資料不足時）"""
        return {
            "dsr": 0.0,
            "psr": 0.0,
            "verdict": "N/A (資料不足)",
            "confidence": "無法判定",
            "note": note,
        }

    def _get_crowding_metrics(self) -> CrowdingMetricsDTO:
        """取得策略擁擠度（使用真實持倉資料）

        使用 reviewing/domain/services/crowding_detector.py 計算：
        1. calculate_pairwise_correlation() - 成對相關性
        2. estimate_alpha_half_life() - Alpha 半衰期
        3. calculate_days_to_cover() - 流動性天數
        4. assess_crowding() - 綜合評估
        """
        try:
            from libs.reviewing.src.domain.services.crowding_detector import (
                calculate_pairwise_correlation,
                calculate_days_to_cover,
                estimate_alpha_half_life,
                assess_crowding,
            )

            # 1. 從 Shioaji 取得真實持倉
            adapter = self._portfolio_provider
            if not adapter.connect():
                return self._default_crowding_metrics()

            positions = adapter.get_positions()
            adapter.disconnect()

            if not positions or len(positions) < 2:
                return self._default_crowding_metrics()

            # 2. 取得持倉股票的歷史價格
            symbols = [p["symbol"] + ".TW" for p in positions]
            hist = yf.download(
                symbols,
                period="6mo",
                progress=False,
                auto_adjust=True,
            )

            if hist.empty:
                return self._default_crowding_metrics()

            # 3. 計算報酬矩陣
            if len(symbols) == 1:
                # 單一持倉無法計算成對相關性
                return self._default_crowding_metrics()

            closes = hist["Close"]
            if closes.isna().all().all():
                return self._default_crowding_metrics()

            # 移除全部是 NaN 的欄位，並填補缺失值
            closes = closes.dropna(axis=1, how="all").ffill().bfill()
            if closes.shape[1] < 2:
                return self._default_crowding_metrics()

            returns = np.log(closes).diff().dropna()
            if len(returns) < 30:
                return self._default_crowding_metrics()

            returns_matrix = returns.values

            # 4. 計算成對相關性
            pairwise_corr = calculate_pairwise_correlation(returns_matrix)

            # 5. 估算 Alpha 半衰期 (使用組合報酬均值)
            portfolio_returns = returns.mean(axis=1).values
            alpha_returns = portfolio_returns - np.mean(portfolio_returns)
            half_life = estimate_alpha_half_life(alpha_returns)
            half_life_weeks = half_life / 5.0  # 轉換為週

            # 6. 計算平倉天數 (使用真實持倉價值)
            position_value = sum(
                p.get("current_price", 0) * p.get("quantity", 0) for p in positions
            )

            # 計算平均日成交量
            if "Volume" in hist.columns:
                volumes = hist["Volume"]
                avg_volume = volumes.mean().sum() if not volumes.empty else 0
                avg_daily_volume = avg_volume * float(closes.iloc[-1].mean())
            else:
                avg_daily_volume = position_value * 0.1  # 預設假設日周轉率 10%

            days_to_cover = calculate_days_to_cover(
                position_value=position_value,
                avg_daily_volume=avg_daily_volume if avg_daily_volume > 0 else 1,
            )

            # 7. 綜合評估
            crowding_assessment = assess_crowding(
                pairwise_corr=pairwise_corr,
                days_to_cover=days_to_cover,
                dsr=1.0,  # DSR 在策略健康度區塊計算
                alpha_half_life=half_life,
            )

            return {
                "pairwise_correlation": round(pairwise_corr, 2),
                "days_to_cover": round(days_to_cover, 1),
                "alpha_half_life": round(half_life_weeks, 1),
                "status": crowding_assessment["status"],
                "recommendation": crowding_assessment["action"],
                "note": f"✅ 資料來源: {len(positions)} 檔持倉",
            }
        except Exception as e:
            self._logger.warning(f"擁擠度計算失敗: {e}")
            return self._default_crowding_metrics()

    def _default_crowding_metrics(self) -> CrowdingMetricsDTO:
        """預設擁擠度指標（資料不足時）"""
        return {
            "pairwise_correlation": 0.0,
            "days_to_cover": 0.0,
            "alpha_half_life": 0.0,
            "status": "N/A",
            "recommendation": "尚無足夠數據評估擁擠度",
            "note": "⚠️ 需至少 2 檔持倉才能計算",
        }

    def _get_decision_quality(self) -> DecisionQualityDTO:
        """取得決策品質（從 Shioaji 交易紀錄分析）

        決策品質定義：
        - 好的進場決策：買入後最終獲利
        - 好的出場決策：賣出時 pnl > 0 或停損執行得當
        """
        try:
            adapter = self._portfolio_provider

            if not adapter.connect():
                return self._default_decision_quality("⚠️ 無法連線")

            # 取得今年交易紀錄
            today = datetime.now()
            year_start = datetime(today.year, 1, 1)
            trades = adapter.get_profit_loss_history(
                begin_date=year_start.strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
            adapter.disconnect()

            if not trades:
                return self._default_decision_quality("今年尚無已結算交易")

            # 分析進場決策（買入後最終是否獲利）
            good_entries = sum(1 for t in trades if t.get("pnl", 0) > 0)
            total_entries = len(trades)

            # 分析出場決策
            # 好的出場：獲利出場 或 控制虧損在合理範圍 (< 10%)
            good_exits = sum(
                1
                for t in trades
                if t.get("pnl", 0) > 0 or t.get("pnl_percent", 0) > -10
            )
            total_exits = len(trades)

            # 計算總體好決策率 (加權平均)
            total_good = good_entries + good_exits
            total_decisions = total_entries + total_exits
            good_rate = total_good / total_decisions if total_decisions > 0 else 0

            return {
                "good_decision_rate": round(good_rate, 4),
                "entries": {"good": good_entries, "total": total_entries},
                "exits": {"good": good_exits, "total": total_exits},
                "note": f"✅ 基於 {len(trades)} 筆交易分析",
            }
        except Exception as e:
            self._logger.warning(f"決策品質計算失敗: {e}")
            return self._default_decision_quality(f"⚠️ 計算失敗: {e}")

    def _default_decision_quality(self, note: str) -> DecisionQualityDTO:
        """預設決策品質（資料不足時）"""
        return {
            "good_decision_rate": 0.0,
            "entries": {"good": 0, "total": 0},
            "exits": {"good": 0, "total": 0},
            "note": note,
        }

    def _get_thesis_validation(self) -> ThesisValidationDTO:
        """取得論點驗證 (已停用，回傳空結構)"""
        return {
            "total_theses": 0,
            "valid_theses": 0,
            "validity_rate": 0.0,
            "details": [],
        }

    def _get_strategy_health(self) -> StrategyHealthDTO:
        """取得策略健康度 (DSR/CVaR/CPCV) — 使用真實交易資料

        整合：
        - DSR (Deflated Sharpe Ratio): 調整多重測試偏差的夏普比率
        - CVaR (Conditional VaR): 尾部風險評估
        - WFO (Walk-Forward Optimization): 樣本外夏普
        - CPCV (Combinatorial Purged CV): 夏普分布
        - PBO (Probability of Backtest Overfitting): 過擬合概率
        """
        try:
            from libs.reviewing.src.domain.services.wfo_validator import (
                walk_forward_optimization,
                probability_backtest_overfitting,
            )
            from libs.reviewing.src.domain.services.cpcv_validator import (
                cpcv_validate,
            )

            adapter = self._portfolio_provider

            if not adapter.connect():
                return self._default_strategy_health("⚠️ 無法連線 Shioaji")

            # 取得過去一年的交易紀錄
            today = datetime.now()
            year_ago = today - timedelta(days=365)
            trades = adapter.get_profit_loss_history(
                begin_date=year_ago.strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
            adapter.disconnect()

            if len(trades) < 10:
                return self._default_strategy_health(
                    f"需累積至少 10 筆交易 (目前 {len(trades)} 筆)"
                )

            # 計算每筆交易報酬率
            returns = [
                t.get("pnl", 0) / t.get("cost", 1)
                for t in trades
                if t.get("cost", 0) > 0
            ]

            if not returns:
                return self._default_strategy_health("⚠️ 無有效交易資料")

            # 計算夏普比率 (年化，假設每月約 10 筆交易)
            mean_ret = np.mean(returns)
            std_ret = np.std(returns)
            sharpe_ratio = (mean_ret / std_ret) * np.sqrt(120) if std_ret > 0 else 0

            # 計算 DSR (Deflated Sharpe Ratio)
            dsr = calculate_deflated_sharpe_ratio(
                sr=sharpe_ratio,
                n_trials=5,  # 假設測試過 5 個策略變體
                n_observations=len(returns),
                sr_std=1.0,
            )

            # 計算 CVaR
            cvar_result = assess_tail_risk(returns, confidence_level=0.95)

            # 評估策略健康狀態 (methodology.md DSR 判準)
            if dsr >= 0.95:
                dsr_status = "✅ 有效策略"
                dsr_verdict = "策略有效性高"
            elif dsr >= 0.80:
                dsr_status = "🟡 灰色地帶"
                dsr_verdict = "需進一步驗證"
            else:
                dsr_status = "⚠️ 偽陽性風險"
                dsr_verdict = "考慮棄用此策略"

            # 評估尾部風險
            tail_ratio = cvar_result.get("tail_ratio", 1.0)
            if tail_ratio > 1.5:
                tail_risk = "⚠️ 肥尾 (高風險)"
            elif tail_ratio > 1.2:
                tail_risk = "🟡 略高"
            else:
                tail_risk = "🟢 正常"

            # ===== WFO: 計算真實 OOS 夏普 =====
            returns_array = np.array(returns)
            equity_curve, is_monotonic = walk_forward_optimization(
                returns_array,
                in_sample_pct=0.7,
                n_splits=5,
            )

            if len(equity_curve) > 1:
                # 使用 OOS 權益曲線計算夏普
                oos_returns = np.diff(equity_curve) / (np.abs(equity_curve[:-1]) + 1e-8)
                oos_mean = np.mean(oos_returns)
                oos_std = np.std(oos_returns)
                oos_sharpe = (oos_mean / oos_std) * np.sqrt(120) if oos_std > 0 else 0
            else:
                oos_sharpe = 0

            # ===== CPCV: 計算真實夏普分布 =====
            cpcv_result = cpcv_validate(returns, n_splits=5)
            cpcv_mean = cpcv_result["mean_sharpe"]

            # ===== PBO: 計算過擬合概率 =====
            # 需要 IS/OOS 夏普對，使用 WFO 分割來估算
            n_splits = 5
            if len(returns_array) >= n_splits * 2:
                split_size = len(returns_array) // n_splits
                is_sharpes = []
                oos_sharpes = []

                for i in range(n_splits):
                    start = i * split_size
                    end = start + split_size
                    is_end = int(start + split_size * 0.7)

                    is_data = returns_array[start:is_end]
                    oos_data = returns_array[is_end:end]

                    if len(is_data) > 1 and len(oos_data) > 1:
                        is_sr = (
                            (np.mean(is_data) / np.std(is_data)) * np.sqrt(120)
                            if np.std(is_data) > 0
                            else 0
                        )
                        oos_sr = (
                            (np.mean(oos_data) / np.std(oos_data)) * np.sqrt(120)
                            if np.std(oos_data) > 0
                            else 0
                        )
                        is_sharpes.append(is_sr)
                        oos_sharpes.append(oos_sr)

                if is_sharpes and oos_sharpes:
                    pbo = (
                        probability_backtest_overfitting(
                            np.array(is_sharpes),
                            np.array(oos_sharpes),
                        )
                        * 100
                    )  # 轉換為百分比

                    # ===== FDR: 使用 B-H 方法控制多重測試假陽性 =====
                    # 計算每個 split 的 p-value (雙側 z-test 近似)
                    from scipy import stats

                    pvalues = []
                    for is_sr, oos_sr in zip(is_sharpes, oos_sharpes):
                        # p-value = P(|SR| > observed | H0: SR = 0)
                        z = oos_sr / (1.0 / np.sqrt(split_size) + 1e-8)
                        p = 2 * (1 - stats.norm.cdf(abs(z)))
                        pvalues.append(p)
                    fdr_result = control_fdr(pvalues, alpha=0.05)
                    fdr_discoveries = fdr_result["n_discoveries"]
                    fdr_tested = fdr_result["n_tested"]
                else:
                    pbo = 50.0
                    fdr_discoveries = 0
                    fdr_tested = 0
            else:
                pbo = 50.0
                fdr_discoveries = 0
                fdr_tested = 0

            return {
                "dsr": round(dsr, 2),
                "dsr_status": dsr_status,
                "dsr_verdict": dsr_verdict,
                "sharpe_ratio": round(sharpe_ratio, 2),
                "cvar_95": round(cvar_result.get("cvar", -0.02) * 100, 2),
                "var_95": round(cvar_result.get("var", -0.015) * 100, 2),
                "tail_risk": tail_risk,
                "oos_sharpe": round(oos_sharpe, 2),
                "wfo_monotonic": is_monotonic,
                "pbo": round(pbo, 1),
                "cpcv_mean": round(cpcv_mean, 2),
                "cpcv_valid": cpcv_result["is_valid"],
                "fdr_discoveries": fdr_discoveries,
                "fdr_tested": fdr_tested,
                "note": f"✅ 資料來源: {len(trades)} 筆交易",
            }
        except Exception as e:
            self._logger.warning(f"策略健康度計算失敗: {e}")
            return self._default_strategy_health(f"⚠️ 計算失敗: {e}")

    def _default_strategy_health(self, note: str = "資料不足") -> StrategyHealthDTO:
        """預設策略健康度 (資料不足時)"""
        return {
            "dsr": 0.0,
            "dsr_status": "N/A",
            "dsr_verdict": note,
            "sharpe_ratio": 0.0,
            "cvar_95": 0.0,
            "var_95": 0.0,
            "tail_risk": "N/A",
            "oos_sharpe": 0.0,
            "wfo_monotonic": False,
            "pbo": 0.0,
            "cpcv_mean": 0.0,
            "cpcv_valid": False,
            "fdr_discoveries": 0,
            "fdr_tested": 0,
            "note": note,
        }

    def _generate_narrative(self, _performance: dict, _skill: dict) -> str:
        """生成 AI 敘事 (暫時停用 LLM，待 Gemini Adapter 遷移至 libs/ 後啟用)"""
        # TODO: 待建立 libs/shared/src/adapters/driven/gemini/ 後重新啟用
        return ""

    def _generate_report(
        self,
        period: str,
        performance: dict,
        skill: dict,
        crowding: dict,
        decision_quality: dict,
        thesis_validation: dict,
        strategy_health: dict,
    ) -> str:
        """生成 Markdown 報告 (含判準定義，供 LLM 解讀)"""

        # 績效評語
        mtd_comment = (
            "表現優異"
            if performance["mtd_return"] > 0.02
            else "符合預期"
            if performance["mtd_return"] > 0
            else "待改進"
        )
        sharpe_comment = (
            "優秀"
            if performance["sharpe_ratio"] > 1.5
            else "良好"
            if performance["sharpe_ratio"] > 1
            else "普通"
        )

        report = (
            dedent(f"""
            # 📈 週度覆盤 — {period}

            > 生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}

            ---

            ## 📊 績效總覽

            | 指標 | 數值 | 說明 |
            |------|------|------|
            | 週報酬 (WTD) | {performance["mtd_return"]:.1%} | {mtd_comment}，本週投資組合總報酬 |
            | 年報酬 (YTD) | {performance["ytd_return"]:.1%} | 今年累計報酬 |
            | 夏普比率 | {performance["sharpe_ratio"]:.2f} | {sharpe_comment}，>1 為佳，風險調整後報酬 |
            | 最大回撤 | {performance["max_drawdown"]:.1%} | 期間最大跌幅，愈小愈好 |
            | 勝率 | {performance["win_rate"]:.0%} | 獲利交易的比例 |
            | 盈虧比 | {performance["profit_factor"]:.1f} | 平均獲利/平均虧損，>1.5 為佳 |
        """).strip()
            + "\n\n"
        )

        report += dedent("""
> ### 📊 判準定義 (Performance Metrics)
>
> | 指標 | 優秀 | 良好 | 待改進 |
> |------|------|------|--------|
> | 週報酬 | > 2% | 0~2% | < 0% |
> | 夏普比率 | > 1.5 | 1.0~1.5 | < 1.0 |
> | 最大回撤 | < 5% | 5~10% | > 10% |
> | 勝率 | > 60% | 50~60% | < 50% |
> | 盈虧比 | > 2.0 | 1.5~2.0 | < 1.5 |

---
        """)

        report += (
            dedent(f"""
            ## 🎯 技能判定

            | 指標 | 數值 | 解讀 | 說明 |
            |------|------|------|------|
            | DSR (調整後夏普) | {skill["dsr"]:.2f} | {"優秀" if skill["dsr"] > 0.5 else "普通"} | 扣除運氣成分的夏普，>0.5 有技能 |
            | PSR (機率夏普) | {skill["psr"]:.1f}% | {"有信心" if skill["psr"] > 80 else "待觀察"} | 真實夏普>0 的機率，>95% 可確認 |
            | **判定** | **{skill["verdict"]}** | 信心度: {skill["confidence"]} | 績效來自技能還是運氣？ |

            > 💡 **技能 vs 運氣**：
            > - **技能主導**：可放心繼續執行策略
            > - **可能有技能**：繼續觀察，避免過度自信
            > - **運氣主導**：謹慎評估是否需調整策略
        """).strip()
            + "\n\n"
        )

        report += dedent("""
> ### 🎯 判準定義 (Skill Verdict)
>
> | 指標 | 計算方式 | 門檻 |
> |------|----------|------|
> | DSR (Deflated Sharpe Ratio) | 調整運氣與多重測試 | > 0.5 = 技能 |
> | PSR (Probabilistic Sharpe Ratio) | 真實 SR > 0 的機率 | > 95% = 確認 |
>
> | DSR | PSR | 判定 | 信心 |
> |-----|-----|------|------|
> | > 0.5 | > 95% | 技能主導 | 高 |
> | 0.3~0.5 | 70~95% | 可能有技能 | 中 |
> | < 0.3 | < 70% | 運氣主導 | 低 |

---
        """)

        report += (
            dedent(f"""
            ## 📈 策略擁擠度

            | 指標 | 數值 | 狀態 | 說明 |
            |------|------|------|------|
            | 成對相關性 | {crowding["pairwise_correlation"]:.2f} | {"正常" if crowding["pairwise_correlation"] < 0.7 else "偏高"} | 持倉間的相關性，<0.5 分散良好 |
            | 平倉天數 | {crowding["days_to_cover"]:.1f} | {"安全" if crowding["days_to_cover"] < 5 else "偏長"} | 若需出場，需幾天才能賣完 |
            | Alpha 半衰期 | {crowding["alpha_half_life"]:.1f} 週 | {crowding["status"]} | 超額報酬消失一半的時間 |

            **建議**：{crowding["recommendation"]}

            > 💡 擁擠度高 = 很多人用類似策略，Alpha 可能加速消失
        """).strip()
            + "\n\n"
        )

        report += dedent("""
> ### 🔗 判準定義 (Crowding)
>
> | 指標 | 正常 | 警戒 | 危險 | 說明 |
> |------|------|------|------|------|
> | 成對相關性 | < 0.5 | 0.5~0.7 | > 0.7 | 持倉間相關度 |
> | 平倉天數 | < 3 | 3~5 | > 5 | 若需出場多久能賣完 |
> | Alpha 半衰期 | > 12週 | 8~12週 | < 8週 | 超額報酬消失速度 |

---
        """)

        report += (
            dedent(f"""
            ## ✅ 決策品質審計

            | 指標 | 數值 | 說明 |
            |------|------|------|
            | 好決策率 | {decision_quality["good_decision_rate"]:.0%} | 正確決策的比例，>60% 為佳 |
            | 進場決策 | {decision_quality["entries"]["good"]}/{decision_quality["entries"]["total"]} 正確 | 買入時機是否正確 |
            | 出場決策 | {decision_quality["exits"]["good"]}/{decision_quality["exits"]["total"]} 正確 | 賣出時機是否正確 |

            > 💡 好決策不一定賺錢，但長期來看好決策會帶來好結果
        """).strip()
            + "\n\n"
        )

        report += dedent("""
> ### ✅ 判準定義 (Decision Quality)
>
> | 好決策率 | 評價 | 建議 |
> |----------|------|------|
> | > 70% | 優秀 | 繼續保持現有紀律 |
> | 50~70% | 普通 | 檢視進出場規則 |
> | < 50% | 待加強 | 需調整策略或心態 |

---
        """)

        report += (
            dedent(f"""
            ## 📊 策略健康度

            | 指標 | 數值 | 判準 | 狀態 |
            |------|------|------|------|
            | Deflated Sharpe (DSR) | {strategy_health["dsr"]:.2f} | > 0.95 | {strategy_health["dsr_status"]} |
            | 樣本外夏普 (OOS) | {strategy_health["oos_sharpe"]:.2f} | > 1.0 | {"✅" if strategy_health["oos_sharpe"] > 1.0 else "⚠️"} |
            | 過擬合機率 (PBO) | {strategy_health["pbo"]:.0f}% | < 30% | {"✅" if strategy_health["pbo"] < 30 else "⚠️"} |
            | CPCV 夏普分布 μ | {strategy_health["cpcv_mean"]:.2f} | > 1.0 | {"✅" if strategy_health["cpcv_mean"] > 1.0 else "⚠️"} |
            | FDR 通過 | {strategy_health["fdr_discoveries"]}/{strategy_health["fdr_tested"]} | B-H α=0.05 | {"✅" if strategy_health["fdr_discoveries"] > 0 else "⚠️"} |
            | CVaR 95% | {strategy_health["cvar_95"]:.2f}% | - | {strategy_health["tail_risk"]} |

            **判定**：{strategy_health["dsr_verdict"]}

            > 💡 **策略健康度**：辨別績效來自技能還是運氣，預警 Alpha 衰減風險
        """).strip()
            + "\n\n"
        )

        report += dedent("""
> ### 📊 判準定義 (Strategy Health)
>
> | 指標 | 計算方式 | 通過條件 |
> |------|----------|----------|
> | DSR (Deflated Sharpe) | 調整多重測試偏差 | > 0.95 |
> | OOS Sharpe | 樣本外夏普比率 | > 1.0 |
> | PBO | 過擬合機率 | < 30% |
> | CPCV μ | 交叉驗證夏普平均 | > 1.0 |
> | FDR | Benjamini-Hochberg 控制 | 至少 1 策略通過 |

---
        """)

        report += dedent("""
            ## 📋 論點驗證

            | 標的 | 論點 | 有效 | 說明 |
            |------|------|------|------|
            """)
        for thesis in thesis_validation["details"]:
            valid_icon = "✅" if thesis["valid"] else "❌"
            desc = "論點正確，持續持有" if thesis["valid"] else "論點失效，考慮出場"
            report += (
                f"| {thesis['symbol']} | {thesis['thesis']} | {valid_icon} | {desc} |\n"
            )

        report += (
            dedent(f"""
            **有效率**：{thesis_validation["valid_theses"]}/{thesis_validation["total_theses"]} ({thesis_validation["validity_rate"]:.0%})

            > 💡 論點驗證：確認當初買入的理由是否仍然成立

            ---
        """).strip()
            + "\n\n"
        )

        report += dedent("""
> ### 📋 判準定義 (Thesis Validation)
>
> | 有效率 | 評估 | 建議 |
> |--------|------|------|
> | > 75% | 良好 | 論點品質高 |
> | 50~75% | 普通 | 檢視失效論點 |
> | < 50% | 偏低 | 重新審視投資框架 |

---

_本報告由 `report_generator` 生成，設計供 LLM 解讀使用_
        """)

        return report

    def _send_email(self, report: str, period: str) -> bool:
        """發送 Email (Markdown → HTML)"""
        try:
            adapter = self._notification_gateway
            return adapter.send_markdown_email(
                subject=f"📊 MyFin 週度覆盤 - {period}",
                markdown_content=report,
            )
        except Exception:
            return False
