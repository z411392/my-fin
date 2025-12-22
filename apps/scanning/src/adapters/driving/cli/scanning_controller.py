"""Scanning CLI Controller

Driving Adapter — 將 CLI 指令轉換為 Use Case 調用
"""

from injector import Injector

from libs.scanning.src.ports.run_daily_scan_port import RunDailyScanPort
from libs.monitoring.src.ports.get_monitor_port import GetMonitorPort


class ScanningController:
    """掃描 CLI 控制器"""

    def __init__(self, injector: Injector) -> None:
        self._injector = injector

    async def scan(
        self, market: str = "all", top_n: int = 20, start_from: str = ""
    ) -> None:
        """執行殘差動能掃描

        Args:
            market: 市場 ("all"=台股+美股, "tw"=台股, "us"=美股)
            top_n: 返回前 N 名
            start_from: 從指定 SYMBOL 開始掃描 (用於斷點續掃)
        """
        # 強制轉型為字串（fire 會將純數字自動轉為 int）
        start_from = str(start_from) if start_from else ""

        # 決定要掃描的市場
        if market == "all":
            # 智慧判斷：根據 start_from 決定掃描順序
            if start_from:
                if start_from.isdigit():
                    # 純數字 = 台股代碼，從台股開始
                    markets = ["tw", "us"]
                elif start_from.isalpha():
                    # 純英文 = 美股代碼，跳過台股直接掃美股
                    markets = ["us"]
                    print(f"💡 偵測到美股代碼 {start_from}，跳過台股掃描")
                else:
                    # 混合格式，保持預設順序
                    markets = ["tw", "us"]
            else:
                markets = ["tw", "us"]
        else:
            markets = [market]

        for mkt in markets:
            msg = f"\n🔍 掃描 {mkt.upper()} 市場..."
            if start_from:
                msg += f" (從 {start_from} 開始)"
            print(msg)

            use_case = self._injector.get(RunDailyScanPort)
            result = await use_case.execute(
                market=mkt, top_n=top_n, start_from=start_from
            )

            # 輸出簡潔摘要
            print("\n" + "=" * 50)
            print(f"📊 {mkt.upper()} 掃描完成摘要")
            print("=" * 50)
            print(f"市場: {result.get('market', mkt)}")
            print(
                f"體制: {result.get('regime', '-')} (牛市機率 {result.get('bull_prob', 0) * 100:.0f}%)"
            )
            print(f"掃描總數: {result.get('scanned', 0)}")
            print(f"合格標的: {result.get('qualified', 0)}")

            # 顯示 Top N
            top_targets = result.get("top_targets", [])
            if top_targets:
                print(f"\n🔥 Top {len(top_targets)} 動能標的:")
                for i, t in enumerate(top_targets[:5], 1):  # 只顯示前 5
                    momentum = t.get("momentum", 0)
                    signal = t.get("signal", "-")
                    print(
                        f"   {i}. {t.get('symbol', '?')} | 動能 {momentum:.2f} | {signal}"
                    )
                if len(top_targets) > 5:
                    print(f"   ... 還有 {len(top_targets) - 5} 檔")

            print("=" * 50 + "\n")

            # 只有第一個市場需要 start_from，之後清空
            start_from = ""

    def monitor(self) -> None:
        """執行即時警報監控

        整合 VPIN/GEX/VIX 監控，輸出當前市場狀態與警報
        """
        print("🔔 執行即時市場監控...")

        try:
            # 委派給 Application 層
            use_case = self._injector.get(GetMonitorPort)
            result = use_case.execute()

            # 解構結果
            vix_data = result.get("vix", {})
            defcon_data = result.get("defcon", {})
            regime_data = result.get("regime", {})

            vix = vix_data.get("value", 0)
            vix_tier = vix_data.get("tier", "UNKNOWN")

            defcon_level = defcon_data.get("level", "?")
            defcon_emoji = defcon_data.get("emoji", "")
            defcon_actions = defcon_data.get("action", [])

            hmm_state = regime_data.get("hmm_state", 0)
            bull_prob = regime_data.get("hmm_bull_prob", 0.5)

            # 輸出監控結果
            print("\n" + "=" * 50)
            print("📊 即時市場監控報告")
            print("=" * 50)
            print(f"\n🌡️  VIX: {vix:.1f} ({vix_tier})")
            print(f"🚦 DEFCON: {defcon_level} {defcon_emoji}")
            print(
                f"🎯 HMM 狀態: {'牛市' if hmm_state == 1 else '熊市'} (機率 {bull_prob * 100:.0f}%)"
            )

            # 顯示建議動作
            if defcon_actions:
                print("\n⚡ 建議動作:")
                if isinstance(defcon_actions, list):
                    for action in defcon_actions:
                        print(f"   • {action}")
                else:
                    print(f"   • {defcon_actions}")

            print("\n" + "=" * 50)

        except Exception as e:
            print(f"❌ 監控失敗: {e}")

    async def retain(self, symbol: str) -> None:
        """掃描單一股票的市場資料並推送到 Google Sheets

        使用與 scan 相同的 execute() 路徑，僅傳入單一股票清單。

        Args:
            symbol: 股票代碼 (例如 2330, NVDA)
        """
        symbol_str = str(symbol)
        print(f"🔍 掃描單一標的: {symbol_str}")

        # 判斷市場
        market = "tw" if symbol_str.isdigit() else "us"

        # 使用與 scan 相同的 execute() 路徑 (DI 注入)
        use_case = self._injector.get(RunDailyScanPort)
        result = await use_case.execute(stocks=[symbol_str], market=market, top_n=1)

        targets = result.get("targets", [])
        if targets:
            target = targets[0]
            # 輸出詳細結果
            print("\n" + "=" * 50)
            print(f"📊 {symbol} 市場資料")
            print("=" * 50)
            print(f"名稱: {target.get('name', '-')}")
            print(f"產業 ETF: {target.get('sector', '-')}")
            print("-" * 50)

            # 安全格式化數值
            open_val = target.get("open") or 0
            high_val = target.get("high") or 0
            low_val = target.get("low") or 0
            close_val = target.get("close") or 0
            prev_close_val = target.get("prev_close") or 0
            volume_val = target.get("volume") or 0
            daily_return_val = target.get("daily_return") or 0

            print(f"開盤: {open_val:.2f}")
            print(f"最高: {high_val:.2f}")
            print(f"最低: {low_val:.2f}")
            print(f"收盤: {close_val:.2f}")
            print(f"前收: {prev_close_val:.2f}")
            print(f"成交量: {volume_val:,}")
            print(f"日報酬: {daily_return_val:.2f}%")
            print("=" * 50)

            # 財報狗摘要
            sd = target.get("statementdog") or {}
            if sd:
                print(f"   F-Score: {sd.get('f_score', '-')}")
                print(f"   ROE: {sd.get('roe', '-')}")
                print(f"   毛利率: {sd.get('gross_margin', '-')}")

            today = result.get("trade_date", "-")
            print(f"✅ 成功推送 {symbol} 到 Google Sheets ({today})")
        else:
            print(f"❌ 無法取得 {symbol} 的資料")

    # ========================================
    # 新增：分離式掃描指令
    # ========================================

    async def scan_momentum(self, market: str = "all", start_from: str = "") -> None:
        """只執行動能評估階段 (不含財報狗)

        Args:
            market: 市場 ("all"=台股+美股, "tw"=台股, "us"=美股)
            start_from: 從指定 SYMBOL 開始掃描 (用於斷點續掃)
        """
        start_from = str(start_from) if start_from else ""

        if market == "all":
            if start_from:
                if start_from.isdigit():
                    markets = ["tw", "us"]
                elif start_from.isalpha():
                    markets = ["us"]
                    print(f"💡 偵測到美股代碼 {start_from}，跳過台股掃描")
                else:
                    markets = ["tw", "us"]
            else:
                markets = ["tw", "us"]
        else:
            markets = [market]

        for mkt in markets:
            msg = f"\n🔍 動能評估 {mkt.upper()} 市場..."
            if start_from:
                msg += f" (從 {start_from} 開始)"
            print(msg)

            use_case = self._injector.get(RunDailyScanPort)
            result = await use_case.execute_momentum(market=mkt, start_from=start_from)

            print(
                f"✅ {mkt.upper()} 完成: {result.get('qualified', 0)}/{result.get('scanned', 0)} 檔"
            )

            start_from = ""

    async def scan_fundamental(self, market: str = "all", start_from: str = "") -> None:
        """只執行財報狗爬蟲階段 (讀取已有 JSON，補上財報狗資料)

        Args:
            market: 市場 ("all"=台股+美股, "tw"=台股, "us"=美股)
            start_from: 從指定 SYMBOL 開始掃描 (用於斷點續掃)
        """
        start_from = str(start_from) if start_from else ""

        if market == "all":
            if start_from:
                if start_from.isdigit():
                    markets = ["tw", "us"]
                elif start_from.isalpha():
                    markets = ["us"]
                    print(f"💡 偵測到美股代碼 {start_from}，跳過台股掃描")
                else:
                    markets = ["tw", "us"]
            else:
                markets = ["tw", "us"]
        else:
            markets = [market]

        for mkt in markets:
            msg = f"\n🐕 財報狗爬蟲 {mkt.upper()} 市場..."
            if start_from:
                msg += f" (從 {start_from} 開始)"
            print(msg)

            use_case = self._injector.get(RunDailyScanPort)
            result = await use_case.execute_fundamental(
                market=mkt, start_from=start_from
            )

            print(f"✅ {mkt.upper()} 完成: {result.get('updated', 0)} 檔更新")

            # 只有第一個市場需要 start_from，之後清空
            start_from = ""

    async def retain_momentum(self, symbol: str) -> None:
        """只執行單一標的的動能評估 (不含財報狗)

        Args:
            symbol: 股票代碼 (例如 2330, NVDA)
        """
        symbol_str = str(symbol)
        print(f"🔍 動能評估單一標的: {symbol_str}")

        market = "tw" if symbol_str.isdigit() else "us"

        use_case = self._injector.get(RunDailyScanPort)
        result = await use_case.execute_momentum(stocks=[symbol_str], market=market)

        targets = result.get("targets", [])
        if targets:
            print(f"✅ {symbol_str} 動能評估完成")
        else:
            print(f"❌ 無法取得 {symbol_str} 的資料")

    async def retain_fundamental(self, symbol: str) -> None:
        """只執行單一標的的財報狗爬蟲 (需先有 JSON 檔案)

        Args:
            symbol: 股票代碼 (例如 2330, NVDA)
        """
        symbol_str = str(symbol)
        print(f"🐕 財報狗爬蟲單一標的: {symbol_str}")

        market = "tw" if symbol_str.isdigit() else "us"

        use_case = self._injector.get(RunDailyScanPort)
        result = await use_case.execute_fundamental(stocks=[symbol_str], market=market)

        if result.get("updated", 0) > 0:
            print(f"✅ {symbol_str} 財報狗資料更新完成")
        else:
            print(f"⚠️ {symbol_str} 無法更新 (可能尚未執行動能評估)")
