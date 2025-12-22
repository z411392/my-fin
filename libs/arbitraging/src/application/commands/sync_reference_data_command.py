"""同步參考資料 Command

負責更新 data/ 目錄下的靜態參考資料。
"""

import logging

from injector import inject
import json
from calendar import monthcalendar
from datetime import datetime, date, timedelta
from pathlib import Path


from libs.arbitraging.src.ports.sync_reference_data_port import SyncReferenceDataPort
from libs.shared.src.dtos.event.event_command_result_dto import (
    ReferenceDataSyncResultDTO,
)
from libs.shared.src.dtos.arbitraging.file_sync_status_dto import FileSyncStatusDTO


class SyncReferenceDataCommand(SyncReferenceDataPort):
    """同步參考資料 (經濟日曆)

    從 Investing.com 剪貼板同步重大經濟事件到 data/economic_calendar.json
    """

    @inject
    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._data_dir = Path(__file__).parents[5] / "data"

    def execute(
        self, scope: str = "all", force: bool = False
    ) -> ReferenceDataSyncResultDTO:
        """執行資料同步

        Args:
            scope: 同步範圍
                - "all": 全部資料 (目前僅經濟日曆)
                - "calendar": 僅經濟日曆
            force: 強制更新 (即使資料已存在)

        Returns:
            ReferenceDataSyncResultDTO: 同步結果報告
        """
        results = {
            "timestamp": datetime.now().isoformat(),
            "scope": scope,
            "force": force,
            "files": [],
        }

        if scope in ("all", "calendar"):
            results["files"].append(self._sync_economic_calendar(force))

        return results

    def _sync_economic_calendar(self, force: bool = False) -> FileSyncStatusDTO:
        """同步經濟日曆 - 自動生成未來年度"""
        file_path = self._data_dir / "economic_calendar.json"

        try:
            with open(file_path) as f:
                data = json.load(f)

            now = datetime.now()
            current_year = now.year
            # 如果離年末不到 7 天，直接抓明年和後年
            days_until_year_end = (datetime(current_year + 1, 1, 1) - now).days
            if days_until_year_end < 7:
                years_to_sync = [current_year + 1, current_year + 2]
            else:
                years_to_sync = [current_year, current_year + 1]

            updated = False

            # 檢查並生成缺失的年度資料
            for year in years_to_sync:
                if force or f"fomc_{year}" not in data:
                    data[f"fomc_{year}"] = self._generate_fomc_dates(year)
                    updated = True
                if force or f"cpi_{year}" not in data:
                    data[f"cpi_{year}"] = self._generate_cpi_dates(year)
                    updated = True
                if force or f"nfp_{year}" not in data:
                    data[f"nfp_{year}"] = self._generate_nfp_dates(year)
                    updated = True

                # Dynamic generation for "previously manual" events
                if force or f"witching_{year}" not in data:
                    data[f"witching_{year}"] = self._generate_witching_dates(year)
                    updated = True
                if force or f"futures_tw_{year}" not in data:
                    data[f"futures_tw_{year}"] = self._generate_tw_futures_dates(year)
                    updated = True
                if force or f"13f_{year}" not in data:
                    data[f"13f_{year}"] = self._generate_13f_dates(year)
                    updated = True
                if force or f"msci_qir_{year}" not in data:
                    data[f"msci_qir_{year}"] = self._generate_msci_dates(
                        year, types="qir"
                    )
                    updated = True
                if force or f"msci_sair_{year}" not in data:
                    data[f"msci_sair_{year}"] = self._generate_msci_dates(
                        year, types="sair"
                    )
                    updated = True
                if force or f"cbc_{year}" not in data:
                    data[f"cbc_{year}"] = self._generate_cbc_dates(year)
                    updated = True

                # Heuristic Events (Entities)
                if force or f"tsmc_{year}" not in data:
                    data[f"tsmc_{year}"] = self._generate_tsmc_dates(year)
                    updated = True
                if force or f"apple_{year}" not in data:
                    data[f"apple_{year}"] = self._generate_apple_dates(year)
                    updated = True
                if force or f"computex_{year}" not in data:
                    data[f"computex_{year}"] = self._generate_computex_dates(year)
                    updated = True

                # Heuristic Events (ETFs)
                # 0056 (Jun/Dec), 00878 (May/Nov), 00940 (May/Nov)
                if force or f"etf_0056_{year}" not in data:
                    data[f"etf_0056_{year}"] = self._generate_semiannual_dates(
                        year, [6, 12], 15
                    )
                    updated = True
                if force or f"etf_00878_{year}" not in data:
                    data[f"etf_00878_{year}"] = self._generate_semiannual_dates(
                        year, [5, 11], 15
                    )
                    updated = True
                if force or f"etf_00940_{year}" not in data:
                    data[f"etf_00940_{year}"] = self._generate_semiannual_dates(
                        year, [5, 11], 15
                    )
                    updated = True

            if updated:
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=4)

            return {
                "file": "economic_calendar.json",
                "status": "updated" if updated else "valid",
                "years": years_to_sync,
                "message": f"已更新 {years_to_sync[0]}-{years_to_sync[1]} 年度"
                if updated
                else "資料已是最新",
            }
        except Exception as e:
            return {
                "file": "economic_calendar.json",
                "status": "error",
                "error": str(e),
            }

    def _generate_fomc_dates(self, year: int) -> list[str]:
        """生成 FOMC 會議日期 (約每 6 週，1/3/5/6/7/9/11/12 月)"""
        fomc_months = [1, 3, 5, 6, 7, 9, 11, 12]
        dates = []
        for month in fomc_months:
            cal = monthcalendar(year, month)
            week3 = cal[2] if len(cal) > 2 else cal[1]
            wed = week3[2]
            if wed == 0:
                wed = cal[3][2] if len(cal) > 3 else cal[2][2]
            dates.append(f"{year}-{month:02d}-{wed:02d}")
        return dates

    def _generate_cpi_dates(self, year: int) -> list[str]:
        """生成 CPI 公布日期 (每月第二週週三或週四)"""
        dates = []
        for month in range(1, 13):
            cal = monthcalendar(year, month)
            week2 = cal[1] if len(cal) > 1 else cal[0]
            day = week2[2] if week2[2] != 0 else week2[3]
            if day == 0:
                day = cal[2][2] if cal[2][2] != 0 else cal[2][3]
            dates.append(f"{year}-{month:02d}-{max(10, day):02d}")
        return dates

    def _generate_nfp_dates(self, year: int) -> list[str]:
        """生成 NFP 公布日期 (每月第一個週五)"""
        dates = []
        for month in range(1, 13):
            cal = monthcalendar(year, month)
            for week in cal:
                if week[4] != 0:
                    dates.append(f"{year}-{month:02d}-{week[4]:02d}")
                    break
        return dates

    def _generate_witching_dates(self, year: int) -> list[str]:
        """四巫日: 3/6/9/12 月的第三個週五"""
        months = [3, 6, 9, 12]
        dates = []
        for m in months:
            d = self._get_nth_weekday_of_month(year, m, 4, 3)  # 4=Friday, 3=3rd
            dates.append(d.isoformat())
        return dates

    def _generate_tw_futures_dates(self, year: int) -> list[str]:
        """台指期結算: 每月第三個週三"""
        dates = []
        for m in range(1, 13):
            d = self._get_nth_weekday_of_month(year, m, 2, 3)  # 2=Wednesday, 3=3rd
            dates.append(d.isoformat())
        return dates

    def _generate_13f_dates(self, year: int) -> list[str]:
        """13F 報告截止: 季度結束後 45 天 (2/14, 5/15, 8/14, 11/14)"""
        deadlines = [
            date(year, 2, 14),
            date(year, 5, 15),
            date(year, 8, 14),
            date(year, 11, 14),
        ]
        final_dates = []
        for d in deadlines:
            if d.weekday() == 5:  # Sat -> Mon
                d += timedelta(days=2)
            elif d.weekday() == 6:  # Sun -> Mon
                d += timedelta(days=1)
            final_dates.append(d.isoformat())
        return final_dates

    def _generate_msci_dates(self, year: int, types: str) -> list[str]:
        """MSCI 調整: QIR (Quarterly) in Feb/Aug, SAIR (Semi-Annual) in May/Nov"""
        if types == "qir":
            months = [2, 8]
        else:
            months = [5, 11]

        dates = []
        for m in months:
            if m == 12:
                next_month = date(year + 1, 1, 1)
            else:
                next_month = date(year, m + 1, 1)
            last_day = next_month - timedelta(days=1)

            while last_day.weekday() > 4:
                last_day -= timedelta(days=1)
            dates.append(last_day.isoformat())
        return dates

    def _generate_cbc_dates(self, year: int) -> list[str]:
        """台灣央行理監事會: 3/6/9/12 月，通常是 FOMC 後的週四"""
        months = [3, 6, 9, 12]
        dates = []
        for m in months:
            d = self._get_nth_weekday_of_month(year, m, 3, 3)
            dates.append(d.isoformat())
        return dates

    def _generate_tsmc_dates(self, year: int) -> list[str]:
        """TSMC 法說會: 1/4/7/10 月中旬 (通常是第 2 或第 3 個週四)"""
        months = [1, 4, 7, 10]
        dates = []
        for m in months:
            d = self._get_nth_weekday_of_month(year, m, 3, 3)
            dates.append(d.isoformat())
        return dates

    def _generate_apple_dates(self, year: int) -> list[str]:
        """Apple Events"""
        sept_event = self._get_nth_weekday_of_month(year, 9, 1, 2)
        return [sept_event.isoformat()]

    def _generate_computex_dates(self, year: int) -> list[str]:
        """Computex: Late May / Early June (Tuesday start)"""
        d = self._get_nth_weekday_of_month(year, 6, 1, 1)
        return [d.isoformat()]

    def _generate_semiannual_dates(
        self, year: int, months: list[int], day: int
    ) -> list[str]:
        """Generic semiannual/periodic fixed-day events (like ETF rebalance)"""
        dates = []
        for m in months:
            d = date(year, m, day)
            if d.weekday() == 5:
                d += timedelta(days=2)
            elif d.weekday() == 6:
                d += timedelta(days=1)
            dates.append(d.isoformat())
        return dates

    def _get_nth_weekday_of_month(
        self, year: int, month: int, weekday: int, n: int
    ) -> date:
        """Get the nth occurrence of a specific weekday in a month."""
        count = 0
        cal = monthcalendar(year, month)
        for week in cal:
            day = week[weekday]
            if day != 0:
                count += 1
                if count == n:
                    return date(year, month, day)
        return date(year, month, 1)
