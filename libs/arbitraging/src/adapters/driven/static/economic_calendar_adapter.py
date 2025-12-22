"""經濟事件日曆 Adapter

從 data/economic_calendar.json 讀取事件，
並整合動態計算的四巫日與台指期結算日。
"""

import json
from datetime import date, timedelta
from pathlib import Path

from libs.arbitraging.src.domain.services.quad_witching_calculator import (
    calculate_quad_witching_dates,
)
from libs.arbitraging.src.domain.services.futures_settlement_calculator import (
    calculate_tw_futures_settlement_dates,
)
from libs.arbitraging.src.ports.economic_calendar_provider_port import (
    EconomicCalendarProviderPort,
)
from libs.shared.src.dtos.catalog.event_type_map_dto import EventTypeMap
from libs.shared.src.dtos.event.economic_event_dto import EconomicEventDTO
from libs.shared.src.dtos.event.calendar_raw_data_dto import CalendarRawDataDTO


# 事件類型對應風險等級
EVENT_RISK_LEVELS = {
    "fomc": "HIGH",
    "fomc_sep": "HIGH",
    "cpi": "MEDIUM",
    "nfp": "MEDIUM",
    "cbc": "MEDIUM",
    "msci_sair": "HIGH",
    "msci_qir": "MEDIUM",
    "witching": "HIGH",
    "futures_tw": "MEDIUM",
    "13f": "LOW",
    "tsmc": "MEDIUM",
    "apple": "MEDIUM",
    "etf_00878": "LOW",
    "etf_00919": "LOW",
    "etf_00929": "LOW",
    "etf_00939": "LOW",
    "etf_00940": "LOW",
}

# 事件類型對應顯示名稱
EVENT_NAMES = {
    "fomc": "FOMC 會議",
    "fomc_sep": "FOMC SEP (點陣圖)",
    "cpi": "美國 CPI",
    "nfp": "非農就業",
    "cbc": "台灣央行會議",
    "msci_sair": "MSCI 半年度調整",
    "msci_qir": "MSCI 季度調整",
    "witching": "四巫日",
    "futures_tw": "台指期結算",
    "13f": "SEC 13F 截止",
    "tsmc": "台積電法說",
    "apple": "Apple 發表會",
    "etf_00878": "00878 換股",
    "etf_00919": "00919 換股",
    "etf_00929": "00929 換股",
    "etf_00939": "00939 換股",
    "etf_00940": "00940 換股",
}


class StaticEconomicCalendarAdapter(EconomicCalendarProviderPort):
    """從靜態 JSON 檔案讀取經濟日曆"""

    def __init__(self) -> None:
        self.data_path = Path(__file__).parents[5] / "data" / "economic_calendar.json"

    def _load_calendar_data(self) -> CalendarRawDataDTO:
        """從 JSON 載入日曆資料"""
        with open(self.data_path, encoding="utf-8") as f:
            return json.load(f)

    def _parse_date(self, date_str: str) -> date:
        """解析日期字串"""
        return date.fromisoformat(date_str)

    def _get_event_type_from_key(self, key: str) -> str:
        """從 JSON key 取得事件類型"""
        for suffix in ["_2025", "_2026", "_2027"]:
            if key.endswith(suffix):
                return key.replace(suffix, "")
        return key

    def get_all_events(self, event_type: str | None = None) -> list[EconomicEventDTO]:
        """取得所有經濟事件 (含動態計算的四巫日與台指期結算)"""
        events = []
        data = self._load_calendar_data()

        # 處理所有靜態事件
        for key, dates in data.items():
            if key == "event_types":
                continue
            if not isinstance(dates, list):
                continue

            evt_type = self._get_event_type_from_key(key)

            # 過濾事件類型
            if event_type:
                if event_type == "etf" and not evt_type.startswith("etf_"):
                    continue
                elif event_type == "msci" and evt_type not in ("msci_sair", "msci_qir"):
                    continue
                elif event_type not in ("etf", "msci") and not evt_type.startswith(
                    event_type
                ):
                    continue

            risk = EVENT_RISK_LEVELS.get(evt_type, "LOW")
            name = EVENT_NAMES.get(evt_type, evt_type)

            for date_str in dates:
                try:
                    events.append(
                        {
                            "date": self._parse_date(date_str),
                            "name": name,
                            "type": evt_type.upper(),
                            "risk": risk,
                        }
                    )
                except ValueError:
                    continue

        # 四巫日 - 動態計算
        if event_type is None or event_type in ("witching", "derivatives"):
            for year in [2025, 2026]:
                for d in calculate_quad_witching_dates(year):
                    events.append(
                        {
                            "date": d,
                            "name": "四巫日",
                            "type": "WITCHING",
                            "risk": "HIGH",
                        }
                    )

        # 台指期結算 - 動態計算
        if event_type is None or event_type in ("futures", "futures_tw", "derivatives"):
            for year in [2025, 2026]:
                for d in calculate_tw_futures_settlement_dates(year):
                    events.append(
                        {
                            "date": d,
                            "name": "台指期結算",
                            "type": "FUTURES_TW",
                            "risk": "MEDIUM",
                        }
                    )

        # 按日期排序並去重
        events.sort(key=lambda x: (x["date"], x["name"]))

        seen = set()
        unique_events = []
        for e in events:
            key = (e["date"], e["name"])
            if key not in seen:
                seen.add(key)
                unique_events.append(e)

        return unique_events

    def get_upcoming_events(
        self, days: int = 30, event_type: str | None = None
    ) -> list[EconomicEventDTO]:
        """取得未來 N 天內的事件"""
        today = date.today()
        end = today + timedelta(days=days)

        all_events = self.get_all_events(event_type)
        return [e for e in all_events if today <= e["date"] <= end]

    def get_event_types(self) -> EventTypeMap:
        """取得所有事件類型及其說明"""
        return EVENT_NAMES.copy()
