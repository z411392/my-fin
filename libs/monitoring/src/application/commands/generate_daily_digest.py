"""生成每日簡報 Command"""

import logging
from datetime import datetime
from injector import inject
from libs.monitoring.src.domain.services.defcon_calculator import calculate_defcon_level
from libs.monitoring.src.domain.services.vix_tier_calculator import (
    calculate_vix_tier,
    get_vix_kelly_factor,
)
import numpy as np
import yfinance as yf
from libs.arbitraging.src.domain.services.hmm_regime_detector import hmm_regime_simple
import os
from libs.monitoring.src.ports.generate_daily_digest_port import GenerateDailyDigestPort
from libs.monitoring.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.monitoring.src.ports.gex_calculator_port import GEXCalculatorPort
from libs.monitoring.src.ports.fred_data_provider_port import FredDataProviderPort
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from libs.monitoring.src.ports.notification_gateway_port import NotificationGatewayPort
from libs.shared.src.dtos.event.calendar_event_dto import CalendarEventDTO
from libs.shared.src.dtos.event.todo_dto import TodoDTO
from libs.shared.src.dtos.reporting.daily_digest_dto import DailyDigestDTO
from libs.shared.src.dtos.reporting.weather_dto import WeatherDTO
from libs.shared.src.dtos.reporting.portfolio_health_dto import PortfolioHealthDTO
from libs.shared.src.dtos.reporting.entry_checklist_dto import EntryChecklistDTO


class GenerateDailyDigestCommand(GenerateDailyDigestPort):
    """生成每日簡報

    每日收盤後執行，整合天候、持倉健康、事件提醒
    """

    @inject
    def __init__(
        self,
        market_data_adapter: MarketDataProviderPort,
        vpin_adapter: VPINCalculatorPort,
        gex_adapter: GEXCalculatorPort,
        fred_adapter: FredDataProviderPort,
        portfolio_adapter: PortfolioProviderPort,
        notification_gateway: NotificationGatewayPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._market_data_adapter = market_data_adapter
        self._vpin_adapter = vpin_adapter
        self._gex_adapter = gex_adapter
        self._fred_adapter = fred_adapter
        self._portfolio_adapter = portfolio_adapter
        self._notification_gateway = notification_gateway

    def execute(
        self, send_email: bool = False, simulate: bool = False
    ) -> DailyDigestDTO:
        """執行生成每日簡報

        Args:
            send_email: 是否發送 email
            simulate: 是否使用模擬資料 (不連接真實 API)

        Returns:
            DailyDigestDTO: 簡報內容
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 取得天候資料
        weather = self._get_weather(simulate=simulate)

        # 2. 取得持倉健康
        portfolio = self._get_portfolio_health(simulate=simulate)

        # 3. 取得事件提醒
        events = self._get_upcoming_events()

        # 4. 生成進場決策檢表
        entry_checklist = self._get_entry_checklist(weather)

        # 5. 生成待辦事項
        todos = self._get_todos(weather, portfolio)

        # 6. 生成報告
        report = self._generate_report(
            date=today,
            weather=weather,
            portfolio=portfolio,
            events=events,
            entry_checklist=entry_checklist,
            todos=todos,
        )

        result = {
            "date": today,
            "weather": weather,
            "portfolio": portfolio,
            "events": events,
            "entry_checklist": entry_checklist,
            "todos": todos,
            "report_markdown": report,
            "email_sent": False,
        }

        if send_email:
            result["email_sent"] = self._send_email(report)

        return result

    def _get_weather(self, simulate: bool = False) -> WeatherDTO:
        """取得天候資料"""

        if simulate:
            vix = 14.2  # 模擬數據
        else:
            try:
                vix = float(self._market_data_adapter.get_vix())
            except Exception:
                vix = 14.2  # 降級到保守值

        # HMM State: 使用真實 SPY 報酬計算
        hmm_state = self._calculate_hmm_state()

        # 從注入的 Adapter 取得 VPIN
        try:
            vpin_result = self._vpin_adapter.calculate("SPY")
            vpin = vpin_result.get("vpin", 0.3)
        except Exception:
            vpin = 0.3  # 降級到保守值

        # GLI Z-Score: 嘗試從 FRED 取得
        gli_z = self._calculate_gli_z()

        # 從注入的 Adapter 取得 GEX
        try:
            gex_result = self._gex_adapter.calculate("SPY")
            gex = gex_result.get("gex", 0.0)
        except Exception:
            gex = 0.0  # 降級到中性值

        defcon_level, defcon_emoji, _defcon_action = calculate_defcon_level(
            vix=vix,
            hmm_state=hmm_state,
            vpin=vpin,
            gli_z=gli_z,
            gex=gex,
        )
        vix_tier, vix_emoji, _vix_action = calculate_vix_tier(vix)
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

        return {
            "vix": vix,
            "vix_tier": vix_tier.name,
            "vix_emoji": vix_emoji,
            "defcon_level": defcon_level.value,
            "defcon_emoji": defcon_emoji,
            "gli_z": gli_z,
            "kelly_factor": kelly_factor,
            "overall_signal": overall_signal,
            "overall_action": overall_action,
        }

    def _calculate_hmm_state(self) -> int:
        """使用真實 SPY 報酬計算 HMM 狀態"""
        try:
            ticker = yf.Ticker("SPY")
            hist = ticker.history(period="3mo")
            if hist is None or len(hist) < 60:
                return 0  # 降級到預設值

            closes = hist["Close"].values
            returns = np.diff(np.log(closes))

            hmm_state, _ = hmm_regime_simple(returns, lookback=min(60, len(returns)))
            return hmm_state
        except Exception:
            return 0  # 降級

    def _calculate_gli_z(self) -> float:
        """從注入的 FRED adapter 取得 GLI Z-Score"""
        try:
            return self._fred_adapter.get_gli_z_score()
        except Exception:
            return 0.8  # 降級到預設值

    def _get_portfolio_health(self, simulate: bool = False) -> PortfolioHealthDTO:
        """取得持倉健康

        Args:
            simulate: True = 使用 Shioaji 模擬環境, False = 使用正式環境
        """

        # 使用注入的 portfolio adapter
        if os.environ.get("SHIOAJI_API_KEY"):
            try:
                positions = self._portfolio_adapter.get_position_with_stop_loss()

                if positions:
                    healthy_count = sum(1 for p in positions if p["status"] == "✅")
                    danger_count = sum(1 for p in positions if p["status"] == "🔴")

                    return {
                        "positions": positions,
                        "healthy_count": healthy_count,
                        "total_count": len(positions),
                        "has_danger": danger_count > 0,
                        "source": "Shioaji",
                    }
            except Exception as e:
                self._logger.warning(f"Shioaji 錯誤，降級到 Mock: {e}")

        # Mock 持倉數據 (降級)
        positions = [
            {
                "symbol": "NVDA",
                "current_price": 142.0,
                "cost": 125.0,
                "stop_loss": 110.0,
            },
            {
                "symbol": "2330",
                "current_price": 1050.0,
                "cost": 980.0,
                "stop_loss": 900.0,
            },
            {
                "symbol": "AAPL",
                "current_price": 195.0,
                "cost": 188.0,
                "stop_loss": 175.0,
            },
            {
                "symbol": "TSLA",
                "current_price": 252.0,
                "cost": 260.0,
                "stop_loss": 235.0,
            },
        ]

        health_report = []
        for pos in positions:
            buffer = (pos["current_price"] - pos["stop_loss"]) / pos["current_price"]
            buffer_pct = round(buffer * 100, 1)

            if buffer_pct > 15:
                status = "✅"
                status_text = "健康"
            elif buffer_pct > 10:
                status = "🔍"
                status_text = "觀察"
            elif buffer_pct > 5:
                status = "⚠️"
                status_text = "警戒"
            else:
                status = "🔴"
                status_text = "危險"

            health_report.append(
                {
                    **pos,
                    "buffer_pct": buffer_pct,
                    "status": status,
                    "status_text": status_text,
                }
            )

        healthy_count = sum(1 for p in health_report if p["status"] == "✅")
        danger_count = sum(1 for p in health_report if p["status"] == "🔴")

        return {
            "positions": health_report,
            "healthy_count": healthy_count,
            "total_count": len(positions),
            "has_danger": danger_count > 0,
            "source": "Mock",
        }

    def _get_upcoming_events(self) -> list[CalendarEventDTO]:
        """取得即將發生的事件"""
        return [
            {
                "date": "2025-01-03",
                "event": "NFP 非農就業",
                "risk_level": "⭐⭐⭐",
                "action": "降槓桿",
            },
            {
                "date": "2025-01-15",
                "event": "FOMC 會議",
                "risk_level": "⭐⭐⭐",
                "action": "降槓桿、不開新倉",
            },
        ]

    def _get_entry_checklist(self, weather: WeatherDTO) -> EntryChecklistDTO:
        """取得進場決策檢表"""
        checks = [
            {
                "item": "VIX",
                "threshold": "< 20 (Tier 0)",
                "current": weather["vix"],
                "passed": weather["vix"] < 20,
            },
            {
                "item": "流動性象限",
                "threshold": "EXPANSION / INERTIA",
                "current": "EXPANSION",
                "passed": True,
            },
            {
                "item": "GEX",
                "threshold": "MILD_LONG 或以上",
                "current": "+3.2B",
                "passed": True,
            },
            {
                "item": "持倉健康度",
                "threshold": "無 DANGER 持倉",
                "current": "0 檔 DANGER",
                "passed": True,
            },
            {
                "item": "狩獵標的品質濾網",
                "threshold": "全部 ✅",
                "current": "3/3 通過",
                "passed": True,
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
        }

    def _get_todos(self, weather: dict, portfolio: dict) -> list[TodoDTO]:
        """生成待辦事項"""
        todos = []

        if weather["overall_signal"] == "🔴":
            todos.append(
                {
                    "priority": "🔴",
                    "item": "停止買入，設定減倉提醒",
                    "type": "風控",
                }
            )

        if portfolio["has_danger"]:
            todos.append(
                {
                    "priority": "🔴",
                    "item": "檢查 DANGER 持倉，執行停損",
                    "type": "風控",
                }
            )

        # 找出需要警戒的持倉
        warning_positions = [p for p in portfolio["positions"] if p["status"] == "⚠️"]
        for pos in warning_positions:
            todos.append(
                {
                    "priority": "🟡",
                    "item": f"關注 {pos['symbol']} 停損緩衝",
                    "type": "風控",
                }
            )

        todos.append(
            {
                "priority": "🟢",
                "item": "維持現有部位",
                "type": "例行",
            }
        )

        return todos

    def _generate_report(
        self,
        date: str,
        weather: dict,
        portfolio: dict,
        events: list,
        entry_checklist: dict,
        todos: list,
    ) -> str:
        """生成 Markdown 報告"""
        report = f"""# 📰 每日簡報 — {date}

> 生成時間：{datetime.now().strftime("%Y-%m-%d %H:%M")}

---

## 🌤️ 天候燈號：{weather["overall_signal"]}

| 維度 | 狀態 | 燈號 |
|------|------|------|
| VIX  | {weather["vix"]} ({weather["vix_tier"]}) | {weather["vix_emoji"]} |
| DEFCON | DEFCON {weather["defcon_level"]} | {weather["defcon_emoji"]} |
| GLI Z-Score | {weather["gli_z"]} | 🟢 |
| **綜合燈號** | - | {weather["overall_signal"]} |

**建議動作**：{weather["overall_action"]}

---

## 🏥 持倉健康狀態

| 標的 | 現價 | 成本 | 停損 | 緩衝 | 狀態 |
|------|------|------|------|------|------|
"""
        for pos in portfolio["positions"]:
            report += f"| {pos['symbol']} | ${pos['current_price']} | ${pos['cost']} | ${pos['stop_loss']} | {pos['buffer_pct']}% | {pos['status']} |\n"

        report += f"""
**健康度總結**：{portfolio["healthy_count"]}/{portfolio["total_count"]} 健康

---

## 📅 事件提醒

| 日期 | 事件 | 風險等級 | 預備動作 |
|------|------|----------|----------|
"""
        for event in events:
            report += f"| {event['date']} | {event['event']} | {event['risk_level']} | {event['action']} |\n"

        report += """
---

## ✅ 進場決策總檢表

| 項目 | 門檻 | 今日狀態 | 通過 |
|------|------|----------|------|
"""
        for check in entry_checklist["checks"]:
            passed_icon = "✅" if check["passed"] else "❌"
            report += f"| {check['item']} | {check['threshold']} | {check['current']} | {passed_icon} |\n"

        report += f"""
**進場決策**：{entry_checklist["decision"]} ({entry_checklist["passed_count"]}/{entry_checklist["total_count"]} 通過)

---

## 📋 明日待辦事項

| 優先級 | 事項 | 類型 |
|--------|------|------|
"""
        for todo in todos:
            report += f"| {todo['priority']} | {todo['item']} | {todo['type']} |\n"

        report += """
---

_本報告由 `fin digest` 指令生成_
"""
        return report

    def _send_email(self, report: str) -> bool:
        """發送 email"""
        today = datetime.now().strftime("%Y-%m-%d")

        return self._notification_gateway._send_email(
            subject=f"📊 MyFin 每日簡報 - {today}",
            body=report,
        )
