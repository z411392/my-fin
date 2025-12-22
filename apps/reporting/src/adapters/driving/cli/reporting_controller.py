"""Reporting CLI Controller

Driving Adapter — 將 CLI 指令轉換為 Use Case 調用
"""

from injector import Injector

from libs.reporting.src.ports.generate_daily_report_port import GenerateDailyReportPort
from libs.reporting.src.ports.generate_weekly_report_port import (
    GenerateWeeklyReportPort,
)
from libs.reporting.src.ports.export_daily_summary_port import ExportDailySummaryPort
from libs.reporting.src.ports.get_stock_row_port import GetStockRowPort


class ReportingController:
    """報告生成 CLI 控制器"""

    def __init__(self, injector: Injector) -> None:
        self._injector = injector

    async def daily(self) -> None:
        """生成每日報告 (async)"""
        use_case = self._injector.get(GenerateDailyReportPort)
        await use_case.execute()

    def weekly(self) -> None:
        """生成每週報告"""
        use_case = self._injector.get(GenerateWeeklyReportPort)
        use_case.execute()

    def summary(self, date: str) -> None:
        """匯出指定日期的摘要至 CSV

        Args:
            date: 日期 (YYYY-MM-DD 或 YYYYMMDD)
        """
        date_str = str(date)  # fire 會將純數字自動轉為 int
        print(f"📤 匯出 {date_str} 摘要至 CSV...")

        command = self._injector.get(ExportDailySummaryPort)
        csv_path = command.execute(date_str)

        if not csv_path:
            print(f"❌ {date} 沒有資料")

    async def stock(self, date: str, symbol: str) -> None:
        """取得指定日期的單一股票資料

        Args:
            date: 日期 (YYYY-MM-DD 或 YYYYMMDD)
            symbol: 股票代碼
        """
        date_str = str(date)  # fire 會將純數字自動轉為 int
        symbol_str = str(symbol)
        print(f"📥 取得 {date_str} {symbol_str} 資料...")

        query = self._injector.get(GetStockRowPort)
        row = await query.execute(date_str, symbol_str)

        if not row:
            print(f"❌ 找不到 {date} {symbol_str} 資料")
            return

        print(f"\n📊 {symbol_str} ({date})")
        print("=" * 50)
        for key, value in row.items():
            if value is not None:
                print(f"{key}: {value}")
        print("=" * 50 + "\n")
