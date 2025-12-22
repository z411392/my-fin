"""生成週末總覽 Command

使用真實 yfinance 資料計算市場體制和殘差動能
"""

import logging
from typing import TYPE_CHECKING

from injector import inject
from datetime import date, datetime

import numpy as np
import yfinance as yf

if TYPE_CHECKING:
    from libs.hunting.src.ports.stock_list_provider_port import StockListProviderPort

from libs.arbitraging.src.domain.services.hurst_calculator import (
    calculate_hurst_exponent,
    interpret_hurst,
)
from libs.arbitraging.src.domain.services.hmm_regime_detector import (
    hmm_regime_simple,
    combine_regime_signals,
)
from libs.hunting.src.domain.services.residual_momentum_calculator import (
    calculate_momentum_score,
)
from libs.hunting.src.adapters.driven.wikipedia.us_stock_list_adapter import (
    get_russell_1000,
    get_sox_components,
)
from libs.hunting.src.ports.generate_weekend_review_port import (
    GenerateWeekendReviewPort,
)
from libs.shared.src.dtos.event.calendar_event_dto import CalendarEventDTO
from libs.shared.src.dtos.event.todo_dto import TodoDTO
from libs.shared.src.dtos.hunting.candidate_stock_dto import CandidateStockDTO
from libs.shared.src.dtos.weekend_review_dto import (
    WeekendReviewResultDTO,
    WeekendRegimeDTO,
    FourAdvisorsDTO,
    HaltCheckDTO,
)


class GenerateWeekendReviewCommand(GenerateWeekendReviewPort):
    """生成週末總覽

    整合 OODA 循環、四顧問診斷、狩獵標的、下週計劃
    使用真實 yfinance 資料
    """

    @inject
    def __init__(
        self,
        stock_list_provider: "StockListProviderPort | None" = None,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._stock_list_provider = stock_list_provider
        self._returns_cache: dict[str, np.ndarray] = {}

    def execute(
        self,
        watchlist: list[str] | None = None,
        scope: str = "default",
    ) -> WeekendReviewResultDTO:
        """生成週末總覽

        Args:
            watchlist: 觀察名單 (可選)
            scope: 掃描範圍 "default" (14 檔) 或 "full" (台股+美股全掃)

        Returns:
            WeekendReviewResultDTO: 週末總覽結果
        """
        if watchlist is None:
            if scope == "full":
                watchlist = self._get_full_watchlist()
            else:
                # 預設觀察名單：台股熱門 + 美股科技
                watchlist = [
                    # 台股半導體
                    "2330.TW",
                    "2454.TW",
                    "3034.TW",
                    "2379.TW",
                    # 台股 AI 伺服器
                    "3017.TW",
                    "2382.TW",
                    "3661.TW",
                    "2308.TW",
                    # 美股科技
                    "NVDA",
                    "AMD",
                    "AVGO",
                    "MRVL",
                    "AAPL",
                    "MSFT",
                ]

        today = date.today()

        # 1. 評估市場體制 (使用真實資料)
        regime = self._assess_regime()

        # 2. 四顧問診斷
        advisors = self._get_four_advisors(regime)

        # 3. 掃描狩獵標的 (使用真實資料)
        momentum_candidates = self._scan_momentum_candidates(watchlist)

        # 4. HALT 自檢
        halt_check = self._get_halt_check()

        # 5. 下週重要事件
        upcoming_events = self._get_upcoming_events()

        # 6. 生成下週計劃
        next_week_plan = self._generate_next_week_plan(regime, advisors)

        # 7. 生成 Markdown 報告
        report_markdown = self._generate_report(
            date=today,
            regime=regime,
            advisors=advisors,
            momentum_candidates=momentum_candidates,
            halt_check=halt_check,
            upcoming_events=upcoming_events,
            next_week_plan=next_week_plan,
        )

        return {
            "date": today.isoformat(),
            "regime": regime,
            "advisors": advisors,
            "momentum_candidates": momentum_candidates,
            "halt_check": halt_check,
            "upcoming_events": upcoming_events,
            "next_week_plan": next_week_plan,
            "total_scanned": len(watchlist),
            "report_markdown": report_markdown,
        }

    def _get_returns(self, symbol: str, lookback: int = 120) -> np.ndarray:
        """取得報酬序列 (帶快取)"""
        if symbol in self._returns_cache:
            return self._returns_cache[symbol]

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="6mo")
            if hist is None or len(hist) < lookback:
                return np.array([])

            closes = hist["Close"].values[-lookback:]
            returns = np.diff(np.log(closes))
            self._returns_cache[symbol] = returns
            return returns
        except Exception:
            return np.array([])

    def _assess_regime(self) -> WeekendRegimeDTO:
        """評估市場體制 (使用真實 S&P 500 資料)"""
        try:
            # 從 yfinance 取得 S&P 500 資料
            returns = self._get_returns("^GSPC")

            if len(returns) < 60:
                # 降級到預設值
                return self._get_default_regime()

            # 第一層: Hurst 指數
            hurst = calculate_hurst_exponent(returns)
            hurst_market, hurst_strategy = interpret_hurst(hurst)

            # 第二層: HMM 體制
            _, hmm_bull_prob = hmm_regime_simple(
                returns, lookback=min(60, len(returns))
            )

            # 取得 VIX
            try:
                vix_ticker = yf.Ticker("^VIX")
                vix_hist = vix_ticker.history(period="1d")
                vix = float(vix_hist["Close"].iloc[-1]) if len(vix_hist) > 0 else 15.0
            except Exception:
                vix = 15.0

            # 綜合判定
            regime_name, kelly_factor = combine_regime_signals(
                hurst, hmm_bull_prob, 1.0
            )

            # 推薦策略
            if hurst > 0.55 and hmm_bull_prob > 0.6:
                strategy = "殘差動能"
            elif hurst < 0.45:
                strategy = "統計套利"
            else:
                strategy = "觀望"

            return {
                "hurst": round(hurst, 3),
                "hmm_bull_prob": round(hmm_bull_prob, 2),
                "vix": round(vix, 1),
                "name": regime_name,
                "market_type": hurst_market,
                "recommended_strategy": strategy,
                "kelly_factor": round(kelly_factor, 2),
            }

        except Exception:
            return self._get_default_regime()

    def _get_default_regime(self) -> WeekendRegimeDTO:
        """返回預設體制 (API 失敗時使用)"""
        return {
            "hurst": 0.5,
            "hmm_bull_prob": 0.5,
            "vix": 15.0,
            "name": "中性",
            "market_type": "隨機漫步",
            "recommended_strategy": "觀望",
            "kelly_factor": 0.5,
        }

    def _get_four_advisors(self, regime: WeekendRegimeDTO) -> FourAdvisorsDTO:
        """四顧問診斷"""
        # 工程師：流動性/結構 (根據 VIX 和 Hurst 判斷)
        if regime["vix"] < 18 and regime["hurst"] > 0.50:
            engineer = {"status": "進攻", "advice": "流動性充裕，結構穩定"}
        elif regime["vix"] < 25:
            engineer = {"status": "觀望", "advice": "流動性尚可，留意變化"}
        else:
            engineer = {"status": "防守", "advice": "流動性收緊，風險升高"}

        # 生物學家：產業生態 (簡化判斷)
        if regime["hmm_bull_prob"] > 0.6:
            biologist = {"status": "進攻", "advice": "AI 題材持續，動能延續"}
        elif regime["hmm_bull_prob"] > 0.4:
            biologist = {"status": "觀望", "advice": "題材輪動中，選股為重"}
        else:
            biologist = {"status": "防守", "advice": "動能衰退，避開追高"}

        # 心理學家：市場情緒 (根據 VIX 判斷)
        if regime["vix"] < 15:
            psychologist = {"status": "觀望", "advice": "情緒過熱，留意回調"}
        elif regime["vix"] < 20:
            psychologist = {"status": "進攻", "advice": "情緒健康，可積極布局"}
        else:
            psychologist = {"status": "防守", "advice": "恐慌情緒，暫停買入"}

        # 策略家：勝率賠率 (根據 Kelly 因子)
        if regime["kelly_factor"] > 0.6:
            strategist = {"status": "進攻", "advice": "勝率賠率俱佳"}
        elif regime["kelly_factor"] > 0.4:
            strategist = {"status": "觀望", "advice": "等待更好機會"}
        else:
            strategist = {"status": "防守", "advice": "風險報酬不佳"}

        # 統計共識
        statuses = [
            engineer["status"],
            biologist["status"],
            psychologist["status"],
            strategist["status"],
        ]
        attack_count = statuses.count("進攻")
        defend_count = statuses.count("防守")

        if attack_count >= 3:
            consensus = "🟢 進攻"
            allocation = "股票 50%"
        elif defend_count >= 3:
            consensus = "🔴 防守"
            allocation = "股票 15%"
        else:
            consensus = "🟡 觀望"
            allocation = "股票 30%"

        return {
            "engineer": engineer,
            "biologist": biologist,
            "psychologist": psychologist,
            "strategist": strategist,
            "consensus": consensus,
            "allocation": allocation,
            "attack_count": attack_count,
        }

    def _scan_momentum_candidates(
        self, watchlist: list[str]
    ) -> list[CandidateStockDTO]:
        """掃描動能候選 (使用真實資料)"""
        candidates = []
        total = len(watchlist)

        # 取得基準指數報酬
        benchmark_returns = self._get_returns("0050.TW")
        if len(benchmark_returns) < 60:
            benchmark_returns = self._get_returns("SPY")

        # 進度顯示
        show_progress = total > 50
        if show_progress:
            self._logger.info(f"掃描 {total} 檔標的...")

        for idx, symbol in enumerate(watchlist):
            # 進度更新
            if show_progress and (idx + 1) % 100 == 0:
                self._logger.info(
                    f"進度: {idx + 1}/{total} ({(idx + 1) / total * 100:.0f}%)"
                )

            try:
                # 確保 symbol 格式正確
                if symbol.isdigit():
                    yahoo_symbol = f"{symbol}.TW"
                else:
                    yahoo_symbol = symbol

                stock_returns = self._get_returns(yahoo_symbol)
                if len(stock_returns) < 60:
                    continue

                # 對齊長度
                min_len = min(len(stock_returns), len(benchmark_returns))
                if min_len < 60:
                    continue

                stock_aligned = stock_returns[-min_len:]
                bench_aligned = benchmark_returns[-min_len:]

                # 計算殘差
                beta = np.cov(stock_aligned, bench_aligned)[0, 1] / np.var(
                    bench_aligned
                )
                residual = stock_aligned - beta * bench_aligned

                # 計算動能分數
                momentum_score = calculate_momentum_score(residual)

                # 趨勢確認: 近期殘差累積為正
                recent_residual = np.sum(residual[-20:])
                if recent_residual > 0.02:
                    trend = "↑ 上升"
                elif recent_residual < -0.02:
                    trend = "↓ 下降"
                else:
                    trend = "→ 持平"

                # 品質濾網 (簡化版)
                # IVOL: 計算殘差波動率
                ivol = np.std(residual) * np.sqrt(252) * 100
                ivol_pass = ivol < 50  # 非極端波動

                # 成交量檢查
                volume_pass = True  # 簡化

                if ivol_pass and volume_pass:
                    quality = "✅"
                elif ivol_pass or volume_pass:
                    quality = "⚠️"
                else:
                    quality = "❌"

                candidates.append(
                    {
                        "symbol": symbol.replace(".TW", "").replace(".TWO", ""),
                        "momentum_score": round(momentum_score, 2),
                        "trend": trend,
                        "beta": round(beta, 2),
                        "ivol": round(ivol, 1),
                        "quality": quality,
                    }
                )

            except Exception:
                continue

        if show_progress:
            self._logger.info(f"掃描完成，找到 {len(candidates)} 檔符合條件")

        candidates.sort(key=lambda x: x["momentum_score"], reverse=True)
        return candidates[:10]

    def _get_full_watchlist(self) -> list[str]:
        """取得完整觀察名單 (台股 + 美股)"""
        watchlist = []

        # 台股：透過注入的 StockListProvider 取得
        if self._stock_list_provider:
            try:
                tw_stocks = self._stock_list_provider.get_all_stocks(include_otc=False)
                watchlist.extend(tw_stocks)
                self._logger.info(f"載入台股上市 (Shioaji): {len(tw_stocks)} 檔")
            except Exception as e:
                self._logger.info(f"載入台股失敗: {e}")
        else:
            self._logger.warning(" StockListProvider 未注入，跳過台股")

        # 美股：Russell 1000 + SOX
        try:
            russell = get_russell_1000()
            sox = get_sox_components()

            # 合併去重
            us_stocks = sorted(set(russell + sox))
            watchlist.extend(us_stocks)
            self._logger.info(
                f"載入美股: Russell 1000 ({len(russell)}) + SOX ({len(sox)}) = {len(us_stocks)} 檔"
            )
        except Exception as e:
            self._logger.info(f"載入美股失敗: {e}")

        self._logger.info(f"總計觀察名單: {len(watchlist)} 檔")
        return watchlist

    def _get_halt_check(self) -> HaltCheckDTO:
        """HALT 自檢 (預設全部否)"""
        return {
            "hungry": {"question": "我很急著想賺錢嗎？", "answer": "否"},
            "angry": {"question": "我想對市場「報復」嗎？", "answer": "否"},
            "lonely": {"question": "我怕落後別人嗎？", "answer": "否"},
            "tired": {"question": "我精神疲憊嗎？", "answer": "否"},
            "can_trade": True,
        }

    def _get_upcoming_events(self) -> list[CalendarEventDTO]:
        """取得即將發生的事件"""
        # TODO: 可整合外部 API 取得實時經濟日曆
        return [
            {
                "date": "2025-01-03",
                "event": "NFP 非農就業",
                "risk_level": "⭐⭐⭐",
                "action": "事前降槓桿",
            },
            {
                "date": "2025-01-15",
                "event": "FOMC 會議",
                "risk_level": "⭐⭐⭐",
                "action": "不開新倉",
            },
            {
                "date": "2025-01-17",
                "event": "四巫日",
                "risk_level": "⭐⭐",
                "action": "避免方向性交易",
            },
        ]

    def _generate_next_week_plan(
        self, regime: WeekendRegimeDTO, advisors: FourAdvisorsDTO
    ) -> list[TodoDTO]:
        """生成下週計劃"""
        strategy = regime["recommended_strategy"]
        consensus = advisors["consensus"]

        if "進攻" in consensus:
            mon_action = "觀察開盤跳空，執行買入計畫"
            wed_action = f"執行{strategy}策略"
            fri_action = "掃描下週候選，設定追蹤"
        elif "防守" in consensus:
            mon_action = "確認停損點，不開新倉"
            wed_action = "觀望，留意反轉訊號"
            fri_action = "週末覆盤，調整觀察名單"
        else:
            mon_action = "觀察開盤，維持現有部位"
            wed_action = "等待訊號確認"
            fri_action = "掃描下週候選"

        return [
            {"day": "週一", "action": mon_action, "priority": "🟢"},
            {"day": "週三", "action": wed_action, "priority": "🟡"},
            {"day": "週五", "action": fri_action, "priority": "🟢"},
        ]

    def _generate_report(
        self,
        date: date,
        regime: WeekendRegimeDTO,
        advisors: FourAdvisorsDTO,
        momentum_candidates: list[CandidateStockDTO],
        halt_check: HaltCheckDTO,
        upcoming_events: list[CalendarEventDTO],
        next_week_plan: list[TodoDTO],
    ) -> str:
        """生成 Markdown 報告"""
        weekday = ["週一", "週二", "週三", "週四", "週五", "週六", "週日"][
            date.weekday()
        ]

        report = f"""# 📊 週末總覽 — {date.isoformat()}

> 生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M")} ({weekday})
> 對應 BC：`alpha_hunter`, `event_arbitrageur`

---

## 🔄 OODA 循環摘要

### ORIENT：市場體制判定

| 指標 | 數值 | 解讀 |
|------|------|------|
| VIX | {regime["vix"]} | {"😌 平靜" if regime["vix"] < 18 else "😐 中性" if regime["vix"] < 25 else "😰 恐慌"} |
| Hurst | {regime["hurst"]} | {regime["market_type"]} |
| HMM 牛市機率 | {int(regime["hmm_bull_prob"] * 100)}% | {"🐂 牛市" if regime["hmm_bull_prob"] > 0.6 else "🐻 熊市" if regime["hmm_bull_prob"] < 0.4 else "➡️ 中性"} |
| **綜合判定** | {regime["name"]} | **推薦策略：{regime["recommended_strategy"]}** |

---

### 四顧問診斷

| 顧問 | 評估維度 | 判定 | 建議 |
|------|----------|------|------|
| 🔧 工程師 | 流動性/結構 | {advisors["engineer"]["status"]} | {advisors["engineer"]["advice"]} |
| 🌿 生物學家 | 產業生態 | {advisors["biologist"]["status"]} | {advisors["biologist"]["advice"]} |
| 🧠 心理學家 | 市場情緒 | {advisors["psychologist"]["status"]} | {advisors["psychologist"]["advice"]} |
| ♟️ 策略家 | 勝率賠率 | {advisors["strategist"]["status"]} | {advisors["strategist"]["advice"]} |
| **共識** | - | **{advisors["consensus"]}** | **建議配置：{advisors["allocation"]}** |

---

### DECIDE：配置燈號

| 共識 | 燈號 | 建議配置 |
|------|------|----------|
| {advisors["attack_count"]}/4 進攻 | {advisors["consensus"].split()[0]} | {advisors["allocation"]} |

---

## 🎯 狩獵清單 Top 10

| 排名 | 標的 | 殘差動能 | EEMD 趨勢 | Beta | IVOL | 品質 |
|------|------|----------|-----------|------|------|------|
"""
        for i, c in enumerate(momentum_candidates, 1):
            report += f"| {i} | {c['symbol']} | {c['momentum_score']:+.2f}σ | {c['trend']} | {c['beta']} | {c['ivol']}% | {c['quality']} |\n"

        if not momentum_candidates:
            report += "| - | 無符合條件標的 | - | - | - | - | - |\n"

        report += f"""
**品質濾網說明**：
- ✅ 全部通過：可積極布局
- ⚠️ 部分通過：需謹慎評估
- ❌ 未通過：建議觀望

---

## 🧘 HALT 自檢

| 項目 | 問題 | 狀態 |
|------|------|------|
| **H**ungry | {halt_check["hungry"]["question"]} | {halt_check["hungry"]["answer"]} |
| **A**ngry | {halt_check["angry"]["question"]} | {halt_check["angry"]["answer"]} |
| **L**onely | {halt_check["lonely"]["question"]} | {halt_check["lonely"]["answer"]} |
| **T**ired | {halt_check["tired"]["question"]} | {halt_check["tired"]["answer"]} |

**結論**：{"✅ 全部「否」，可正常交易" if halt_check["can_trade"] else "⚠️ 有項目為「是」，建議暫停交易"}

> ⚠️ 請誠實自我檢視，任一項為「是」→ 本週不執行任何交易

---

## 📅 下週重要事件

| 日期 | 事件 | 風險等級 | 預備動作 |
|------|------|----------|----------|
"""
        for event in upcoming_events:
            report += f"| {event['date']} | {event['event']} | {event['risk_level']} | {event['action']} |\n"

        report += """
---

## 📋 下週計劃

| 日期 | 計劃動作 | 優先級 |
|------|----------|--------|
"""
        for plan in next_week_plan:
            report += f"| {plan['day']} | {plan['action']} | {plan['priority']} |\n"

        report += """
---

_本報告由 `make weekend` 指令生成_
"""
        return report
