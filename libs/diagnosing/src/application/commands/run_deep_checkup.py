"""執行個股深層健檢 Command"""

from injector import inject
import numpy as np
from datetime import datetime
import logging
import asyncio

from sklearn.linear_model import LinearRegression

from libs.shared.src.clients.statementdog.statement_dog_client import StatementDogClient
from libs.hunting.src.ports.scan_residual_momentum_port import (
    ScanResidualMomentumPort,
)
from libs.hunting.src.ports.scan_pairs_port import ScanPairsPort
from libs.linking.src.ports.get_supply_chain_link_port import (
    GetSupplyChainLinkPort,
)
from libs.shared.src.constants.supply_chain_map import SUPPLY_CHAIN_MAP
from libs.hunting.src.domain.services.pairs_detector import detect_pairs_opportunity
from libs.monitoring.src.ports.notification_gateway_port import (
    NotificationGatewayPort,
)
from libs.diagnosing.src.ports.run_deep_checkup_port import RunDeepCheckupPort
from libs.shared.src.dtos.analysis.checkup_result_dto import DeepCheckupResultDTO
from libs.shared.src.dtos.analysis.fetch_data_parallel_result_dto import (
    FetchDataParallelResultDTO,
)


class RunDeepCheckupCommand(RunDeepCheckupPort):
    """執行個股深層健檢

    整合：
    1. 基本面 (StatementDog)
    2. 動能 (Alpha Hunter)
    3. 統計套利 (Pairs)
    4. 供應鏈 (Supply Chain)
    """

    @inject
    def __init__(
        self,
        sd_client: StatementDogClient,
        momentum_query: ScanResidualMomentumPort,
        pairs_query: ScanPairsPort,
        supply_chain_query: GetSupplyChainLinkPort,
        notification_gateway: NotificationGatewayPort,
    ) -> None:
        """初始化 Command

        Args:
            sd_client: StatementDog 客戶端
            momentum_query: 動能掃描 Query
            pairs_query: 配對交易 Query
            supply_chain_query: 供應鏈 Query
            notification_gateway: 通知 Gateway
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._sd_client = sd_client
        self._momentum_query = momentum_query
        self._pairs_query = pairs_query
        self._supply_chain_query = supply_chain_query
        self._notification_gateway = notification_gateway
        self._report_buffer: list[str] = []

    def execute(self, symbol: str, send_email: bool = True) -> DeepCheckupResultDTO:
        """執行健檢並列印報告

        Args:
            symbol: 股票代碼
            send_email: 是否發送 Email (預設 True)

        Returns:
            DeepCheckupResultDTO: 健檢結果
        """

        symbol = str(symbol)  # 確保是字串
        self._report_buffer = []  # 清空 buffer

        self._logger.info(f"開始深層健檢 (並行模式): {symbol}")

        self._log(f"# 💊 個股健檢報告: {symbol}")
        self._log(f"> 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        self._log("\n---")

        # 啟動並行數據抓取
        self._logger.info("正在並行抓取數據 (基本面/動能/供應鏈)...")
        results = asyncio.run(self._fetch_data_parallel(symbol))

        sd_data = results["statementhub"]
        momentum_data = results["momentum"]
        sc_data = results["supply_chain"]

        # 1. 基本面 (StatementDog)
        self._log("\n## 📊 基本面分析 (財報狗)")
        if "error" in sd_data:
            self._log(f"⚠️ 無法取得數據: {sd_data['error']}")
        else:
            self._print_fundamental_summary(sd_data)

        # 2. 動能 (Alpha Hunter)
        self._log("\n## 🚀 殘差動能 (三層因子剝離)")
        if momentum_data:
            self._print_momentum_summary(momentum_data)

            # 3. 統計套利 (Pairs) - 需要動能數據確立 Sector
            self._log("\n## 🔗 統計套利機會 (vs Top/Bottom 20)")
            # Pairs 需要 Top/Bottom 清單，這通常包含在 momentum_query 內，但這裡我們已經有了 momentum_data
            # 不過原本的 _check_pairs_opportunities 內部又呼叫了一次 momentum_query.execute
            # 為了保持簡單，我們先維持同步執行 (因需掃描市場 Top20，可能較久，暫不並行優化此步)
            self._check_pairs_opportunities(symbol, momentum_data.get("sector", ""))
        else:
            self._log("⚠️ 無法計算動能 (可能資料不足)")

        # 4. 供應鏈 (Supply Chain)
        self._log("\n## ⛓️ 供應鏈傳導 (美股對標)")
        if sc_data:
            self._print_supply_chain_result(sc_data["result"], sc_data["is_reverse"])
        else:
            # 如果沒有 sc_data，可能是在 fetch 階段就發現沒有對標，或者發生錯誤
            # 我們可以在 fetch 階段記錄原因，或者這裡簡單 log
            if results.get("sc_msg"):
                self._log(results["sc_msg"])
            else:
                self._log("⚠️ 供應鏈分析失敗或無資料")

        self._log("\n---")
        self._log("\n✅ 健檢完成")

        # 發送 Email (根據參數決定)
        if send_email:
            self._send_email_report(symbol)

        # 返回結果供其他模組使用
        return {
            "symbol": symbol,
            "fundamental": sd_data if "error" not in sd_data else None,
            "momentum": momentum_data,
            "supply_chain": sc_data.get("result") if sc_data else None,
            "report_markdown": "\n".join(self._report_buffer),
        }

    async def _fetch_data_parallel(self, symbol: str) -> FetchDataParallelResultDTO:
        """並行抓取所有需要的數據"""

        # 定義包裝函式以在 Thread 中執行 Blocking I/O
        def fetch_statementdog():
            try:
                # 抓取完整數據
                raw_data = self._sd_client.analyze(symbol)
                summary = self._sd_client.get_fundamental_summary(symbol, data=raw_data)
                summary["raw_data"] = raw_data  # 附加原始數據
                return summary
            except Exception as e:
                return {"error": str(e)}

        def fetch_momentum():
            try:
                return self._momentum_query.evaluate_single_stock(symbol)
            except Exception as e:
                self._logger.warning(f"Momentum error: {e}")
                return None

        def fetch_supply_chain():
            try:
                # 供應鏈邏輯移植
                # 1. 反向查找 TW -> US
                us_target = None
                for us, tw in SUPPLY_CHAIN_MAP.items():
                    if symbol in tw or (symbol + ".TW") in tw:
                        us_target = us
                        break

                # 2. 查找 US -> TW (如果是查美股)
                if not us_target and symbol in SUPPLY_CHAIN_MAP:
                    tw_target = SUPPLY_CHAIN_MAP[symbol]
                    result = self._supply_chain_query.execute(symbol, tw_target)
                    return {"result": result, "is_reverse": False}

                if us_target:
                    result = self._supply_chain_query.execute(us_target, symbol)
                    return {"result": result, "is_reverse": True}

                return {"msg": "無已知的主要供應鏈對標關係 (僅支援主要權值股)"}

            except Exception as e:
                return {"msg": f"供應鏈分析失敗: {e}"}

        # 建立 Task
        loop = asyncio.get_running_loop()

        task_sd = loop.run_in_executor(None, fetch_statementdog)
        task_mom = loop.run_in_executor(None, fetch_momentum)
        task_sc = loop.run_in_executor(None, fetch_supply_chain)

        # 等待所有結果
        sd_res, mom_res, sc_res = await asyncio.gather(task_sd, task_mom, task_sc)

        return {
            "statementhub": sd_res,
            "momentum": mom_res,
            "supply_chain": sc_res if "result" in sc_res else None,
            "sc_msg": sc_res.get("msg"),
        }

    def _log(self, message: str) -> None:
        """紀錄並列印訊息"""
        print(message)
        self._report_buffer.append(message)

    def _send_email_report(self, symbol: str) -> None:
        """發送 Email 報告"""
        try:
            markdown_content = "\n".join(self._report_buffer)

            print("\n📧 正在發送 Email 報告...")
            success = self._notification_gateway.send_markdown_email(
                subject=f"💊 個股健檢報告: {symbol}",
                markdown_content=markdown_content,
            )
            if success:
                self._logger.info("Email 發送成功")
            else:
                self._logger.error("Email 發送失敗")
        except Exception:
            self._logger.error("Email 發送錯誤: {e}")

    def _print_fundamental_summary(self, data: dict) -> None:
        """列印基本面摘要 (完整版)"""
        # 1. 綜合判定
        valid = "**✅ 通過**" if data.get("is_valid") else "**⚠️ 未通過**"
        self._log(f"**綜合判定**: {valid}")
        self._log("")
        self._log("")
        self._log("> ### 📋 綜合判定條件")
        self._log(">")
        self._log("> 需同時滿足以下三項：")
        self._log(">")
        self._log("> | 條件 | 通過標準 | 說明 |")
        self._log("> |------|----------|------|")
        self._log(
            "> | 營收加速 | 短期 YoY > 長期 YoY 且當月 YoY > 0 | 營收成長趨勢向上 |"
        )
        self._log("> | 獲利品質 | CFO/NI > 0.5 或 FCF > 0 | 現金流支撐獲利 |")
        self._log("> | 評價安全 | PE < 歷史 95 百分位 | 估值不貴 |")
        self._log(">")

        # 2. 營收動能
        rev = data.get("revenue_momentum", {})
        acc = "🔥 加速" if rev.get("is_accelerating") else "❄️ 減速"
        self._log("### 📈 營收動能")
        self._log("")
        self._log("| 指標 | 數值 | 判定 |")
        self._log("|------|------|------|")
        self._log(f"| 短期 YoY (3M) | {rev.get('short_term_yoy', 0):.1f}% | - |")
        self._log(f"| 長期 YoY (12M) | {rev.get('long_term_yoy', 0):.1f}% | - |")
        self._log(f"| 最新月 YoY | {rev.get('current_yoy', 0):.1f}% | {acc} |")
        self._log("")

        # 3. 獲利品質
        qual = data.get("earnings_quality", {})
        q_status = "✅ 優良" if qual.get("is_quality") else "⚠️ 轉差"
        cfo = qual.get("cfo", 0)
        ni = qual.get("net_income", 0)
        cfo_ni = qual.get("cfo_ni_ratio", 0)
        fcf = qual.get("fcf_ttm", 0)
        self._log("### 💰 獲利品質")
        self._log("")
        self._log("| 指標 | 數值 | 判定 |")
        self._log("|------|------|------|")
        self._log(f"| 營業現金流 (CFO) | {cfo:,.0f} | - |")
        self._log(f"| 稅後淨利 (NI) | {ni:,.0f} | - |")
        self._log(
            f"| CFO/NI 比率 | {cfo_ni:.2f} | {'✅ >1' if cfo_ni > 1 else '⚠️ <1'} |"
        )
        self._log(
            f"| 自由現金流 (FCF) | {fcf:,.0f} | {'✅ 正' if fcf > 0 else '⚠️ 負'} |"
        )
        self._log(f"| 品質判定 | - | {q_status} |")
        self._log("")

        # 4. 評價水準
        val = data.get("valuation_metrics", {})
        v_status = "✅ 安全" if val.get("is_safe") else "⚠️ 昂貴"
        pe = val.get("current_pe", 0)
        self._log("### 📊 評價水準")
        self._log("")
        self._log("| 指標 | 數值 | 說明 |")
        self._log("|------|------|------|")
        self._log(f"| 當前 PE | {pe:.1f} | - |")
        self._log(f"| 歷史 5% | {val.get('pe_percentile_5', 0):.1f} | 極低估 |")
        self._log(f"| 歷史 25% | {val.get('pe_percentile_25', 0):.1f} | 低估 |")
        self._log(f"| 歷史 50% | {val.get('pe_percentile_50', 0):.1f} | 中位數 |")
        self._log(f"| 歷史 75% | {val.get('pe_percentile_75', 0):.1f} | 高估 |")
        self._log(f"| 歷史 95% | {val.get('pe_percentile_95', 0):.1f} | 極高估 |")
        self._log(f"| 評價判定 | - | {v_status} |")
        self._log("")

        # 5. F-Score
        f_score = data.get("f_score", {})
        score = f_score.get("score", 0)
        f_status = "✅ 健康" if score >= 5 else "🟡 普通" if score >= 3 else "⚠️ 偏弱"
        self._log("### 🏥 Piotroski F-Score")
        self._log("")
        self._log(f"**得分**: {score}/9 ({f_status})")
        self._log("")

        details = f_score.get("details", {})
        if details:
            self._log("| 類別 | 項目 | 判定 |")
            self._log("|------|------|------|")
            # 獲利能力
            self._log(
                f"| 獲利 | ROA 為正 | {'✅' if details.get('roa_positive') else '❌'} |"
            )
            self._log(
                f"| 獲利 | CFO 為正 | {'✅' if details.get('cfo_positive') else '❌'} |"
            )
            self._log(
                f"| 獲利 | ROA 改善 | {'✅' if details.get('roa_improving') else '❌'} |"
            )
            self._log(
                f"| 獲利 | CFO > NI | {'✅' if details.get('accruals_valid') else '❌'} |"
            )
            # 槓桿與流動性
            self._log(
                f"| 槓桿 | 長期負債下降 | {'✅' if details.get('leverage_improving') else '❌'} |"
            )
            self._log(
                f"| 流動 | 流動比率上升 | {'✅' if details.get('liquidity_improving') else '❌'} |"
            )
            self._log(
                f"| 股本 | 未增發股票 | {'✅' if details.get('no_new_shares') else '❌'} |"
            )
            # 營運效率
            self._log(
                f"| 效率 | 毛利率改善 | {'✅' if details.get('margin_improving') else '❌'} |"
            )
            self._log(
                f"| 效率 | 資產周轉改善 | {'✅' if details.get('turnover_improving') else '❌'} |"
            )
            self._log("")

            # F-Score 判準說明
            self._log("")
            self._log("> ### 🏥 Piotroski F-Score 判準說明")
            self._log(">")
            self._log(
                "> F-Score 是由史丹佛教授 Joseph Piotroski 提出的財務健康評分系統，"
            )
            self._log("> 涵蓋獲利、槓桿、效率三個面向，共 9 項指標：")
            self._log(">")
            self._log("> **獲利能力 (4分)**")
            self._log(">")
            self._log("> | 項目 | 通過條件 | 意義 |")
            self._log("> |------|----------|------|")
            self._log("> | ROA 為正 | ROA > 0 | 公司有獲利能力 |")
            self._log("> | CFO 為正 | 營業現金流 > 0 | 獲利有現金支撐 |")
            self._log("> | ROA 改善 | ROA YoY ↑ | 獲利效率提升 |")
            self._log(
                "> | CFO > NI | 營業現金流 > 稅後淨利 | 盈餘品質佳，非應計項目造成 |"
            )
            self._log(">")
            self._log("> **槓桿與流動性 (3分)**")
            self._log(">")
            self._log("> | 項目 | 通過條件 | 意義 |")
            self._log("> |------|----------|------|")
            self._log("> | 長期負債下降 | (LTD/Assets) YoY ↓ | 財務槓桿降低 |")
            self._log("> | 流動比率上升 | Current Ratio YoY ↑ | 短期償債能力改善 |")
            self._log("> | 未增發股票 | 股本 YoY ≤ 0 | 不稀釋股東權益 |")
            self._log(">")
            self._log("> **營運效率 (2分)**")
            self._log(">")
            self._log("> | 項目 | 通過條件 | 意義 |")
            self._log("> |------|----------|------|")
            self._log("> | 毛利率改善 | Gross Margin YoY ↑ | 定價能力或成本控制改善 |")
            self._log("> | 資產周轉改善 | Asset Turnover YoY ↑ | 資產使用效率提升 |")
            self._log(">")
            self._log("> **總分解讀**")
            self._log(">")
            self._log("> | 分數 | 狀態 | 建議 |")
            self._log("> |------|------|------|")
            self._log("> | 8-9 | ✅ 優秀 | 財務體質極佳 |")
            self._log("> | 5-7 | ✅ 健康 | 財務狀況良好 |")
            self._log("> | 3-4 | 🟡 普通 | 需關注弱項 |")
            self._log("> | 0-2 | ⚠️ 偏弱 | 財務風險較高 |")

        # 6. 原始數據完整呈現 (如有)
        raw_data = data.get("raw_data", {})
        if raw_data:
            self._log("### 📝 財報狗完整數據")
            self._log("")

            # 顯示各指標的實際數值 (完整版 - 對應 metrics.md)
            metric_config = {
                # === 財務報表 ===
                "monthly-revenue": ("📅 月營收", "千元"),
                "eps": ("💵 每股盈餘 (EPS)", "元"),
                "bps": ("💰 每股淨值 (BPS)", "元"),
                "income-statement": ("📊 損益表", "千元"),
                "cash-flow-statement": ("💸 現金流量表", "千元"),
                "liabilities-and-equity": ("📋 負債與股東權益", "千元"),
                "dividend-policy": ("🎁 股利政策", "元"),
                # === 獲利能力 ===
                "profit-margin": ("📈 利潤率", "%"),
                "roe-roa": ("🔄 ROE/ROA", "%"),
                "dupont": ("🔬 杜邦分析", "%"),
                "asset-turnover": ("♻️ 資產周轉率", "次"),
                "operating-days": ("📆 營運週轉天數", "天"),
                # === 安全性分析 ===
                "financial-structure-ratio": ("🏛️ 財務結構比率", "%"),
                "liquidity-ratio": ("💧 流動比率", "%"),
                "interest-coverage": ("🛡️ 利息保障倍數", "倍"),
                "cash-flow-analysis": ("💹 現金流量分析", "%"),
                # === 成長力分析 ===
                "revenue-growth-rate": ("📈 營收成長率", "%"),
                "profit-growth-rate": ("📈 獲利成長率", "%"),
                # === 價值評估 ===
                "pe": ("💹 本益比河流圖", "倍"),
                "pb": ("📊 股價淨值比河流圖", "倍"),
                "dividend-yield": ("💰 殖利率", "%"),
                # === 董監與籌碼 ===
                "directors-holders": ("👔 董監持股與籌碼", "%"),
                # === 關鍵指標 ===
                "key-indicator": ("🔑 關鍵指標", "-"),
                "free-cash-flow-yield": ("💎 自由現金流報酬率", "%"),
            }

            for metric_key, (metric_name, unit) in metric_config.items():
                rows = raw_data.get(metric_key, [])
                if isinstance(rows, list) and rows:
                    self._log(f"#### {metric_name}")
                    self._log("")

                    # 取得所有期間 (header)
                    all_periods = set()
                    for row in rows:
                        if isinstance(row, dict) and "values" in row:
                            all_periods.update(row["values"].keys())

                    # 排序期間 (最新在前)
                    sorted_periods = sorted(all_periods, reverse=True)[
                        :8
                    ]  # 只顯示最近 8 期

                    if sorted_periods:
                        # 建立表頭
                        header = "| 指標 | " + " | ".join(sorted_periods) + " |"
                        separator = (
                            "|------|"
                            + "|".join(["------"] * len(sorted_periods))
                            + "|"
                        )
                        self._log(header)
                        self._log(separator)

                        # 建立資料列
                        for row in rows:
                            if isinstance(row, dict):
                                row_name = row.get("name", "")[:10]  # 截短名稱
                                values = row.get("values", {})
                                row_values = []
                                for period in sorted_periods:
                                    val = values.get(period)
                                    if val is None:
                                        row_values.append("-")
                                    elif isinstance(val, (int, float)):
                                        row_values.append(f"{val:.1f}")
                                    else:
                                        row_values.append(str(val)[:8])
                                self._log(
                                    f"| {row_name} | " + " | ".join(row_values) + " |"
                                )
                        self._log("")

        # 判準區塊
        self._log("")
        self._log("> ### 📊 基本面判準 (StatementDog)")
        self._log(">")
        self._log("> | 指標 | 通過條件 | 說明 |")
        self._log("> |------|----------|------|")
        self._log("> | 營收動能 | 短期 YoY > 長期 YoY | 營收加速成長 |")
        self._log("> | 獲利品質 | CFO/NI > 1 或 FCF > 0 | 現金流支撐獲利 |")
        self._log("> | 評價水準 | PE < 歷史 95% | 估值不貴 |")
        self._log("> | F-Score | ≥ 5/9 | 財務體質健康 |")

    def _print_momentum_summary(self, data: dict) -> None:
        """列印動能摘要"""
        mom = data.get("momentum", 0)
        raw = data.get("raw_momentum", 0)
        bull_prob = data.get("bull_prob", 0.5)

        status = (
            "🟢 強勢"
            if mom > 1.5
            else "🟡 觀察"
            if mom > 0.8
            else "⚪ 中性"
            if mom > -0.8
            else "🔴 弱勢"
        )

        self._log("")
        self._log("| 指標 | 數值 | 說明 |")
        self._log("|------|------|------|")
        self._log(f"| **調整後殘差動能** | `{mom:+.2f}σ` | {status} |")
        self._log(f"| 原始殘差動能 | `{raw:+.2f}σ` | 未調整牛熊權重 |")
        self._log(f"| 市場牛市機率 | `{bull_prob:.0%}` | 動態權重因子 |")
        self._log("")
        self._log("**Beta 分解 (三層因子剝離)**")
        self._log("")
        self._log("| 因子 | Beta | 說明 |")
        self._log("|------|------|------|")
        self._log(f"| 全球 | {data.get('global_beta', 0):.3f} | 全球市場暴露 |")
        self._log(f"| 本地 | {data.get('local_beta', 0):.3f} | 本地市場暴露 |")
        self._log(f"| 產業 | {data.get('sector_beta', 0):.3f} | 產業因子暴露 |")
        self._log("")
        self._log("**品質指標 (濾網)**")
        self._log("")
        self._log("| 指標 | 數值 | 門檻 | 判定 |")
        self._log("|------|------|------|------|")
        ivol = data.get("ivol", 0)
        max_ret = data.get("max_ret", 0)
        ivol_ok = "✅" if ivol < 0.03 else "⚠️ 偏高"
        max_ok = "✅" if max_ret < 0.05 else "⚠️ 偏高"
        self._log(f"| IVOL (特異波動) | {ivol:.2%} | <3% | {ivol_ok} |")
        self._log(f"| MAX (極端報酬) | {max_ret:.2%} | <5% | {max_ok} |")
        self._log("")

        # 判準區塊
        self._log("")
        self._log("> ### 🚀 動能判準 (Residual Momentum)")
        self._log(">")
        self._log("> | 動能 (σ) | 狀態 | 說明 |")
        self._log("> |----------|------|------|")
        self._log("> | > +1.5σ | 🟢 強勢 | 動能領先，可考慮進場 |")
        self._log("> | +0.8~1.5σ | 🟡 觀察 | 待確認突破 |")
        self._log("> | -0.8~+0.8σ | ⚪ 中性 | 無明顯動能 |")
        self._log("> | < -0.8σ | 🔴 弱勢 | 動能落後，避免持有 |")

    def _check_pairs_opportunities(self, symbol: str, sector: str) -> None:
        """檢查配對交易機會"""
        # 1. 取得 Top 20 & Bottom 20
        market = "us" if symbol.isalpha() else "tw"
        try:
            # 這裡為了效率，我們假設 ScanResidualMomentumQuery 可以快速取得 Top/Bottom
            # 但原本的 query 會掃描全市場。為了避免太久，我們先掃描該產業，或只取已知清單
            # 這邊為了演示，我們先掃描 top_n=20 的全市場 (可能會稍久，約 10-15 秒)
            self._log("> 正在掃描市場 Top/Bottom 以尋找配對 (需時約 15 秒)...")
            scan_result = self._momentum_query.execute(market=market, top_n=20)

            top_20 = scan_result.get("targets", [])

            targets = top_20
            self._log(f"> 已取得 {len(targets)} 檔強勢股進行配對分析...")

            # 2. 準備數據
            target_symbol = (
                f"{symbol}.TW"
                if market == "tw" and not symbol.endswith(".TW")
                else symbol
            )
            symbols = [target_symbol] + [
                t["symbol"]
                + (".TW" if market == "tw" and not t["symbol"].endswith(".TW") else "")
                for t in targets
            ]

            # 去除重複
            symbols = list(set(symbols))

            # 使用 ScanPairsQuery 內部的 helper 取得數據
            valid_symbols, returns, prices = self._pairs_query._get_historical_data(
                symbols
            )

            if returns is None:
                self._log("⚠️ 無法取得數據進行配對")
                return

            # 3. 尋找 target_symbol 的 index
            try:
                target_idx = valid_symbols.index(target_symbol)
            except ValueError:
                self._log(f"⚠️ 數據中找不到 {target_symbol}")
                return

            # 4. 計算配對

            found_pairs = []

            target_returns = returns[:, target_idx].reshape(-1, 1)
            target_price = prices[:, target_idx]

            for i, other_symbol in enumerate(valid_symbols):
                if i == target_idx:
                    continue

                other_returns = returns[:, i].reshape(-1, 1)
                other_price = prices[:, i]

                # 相關性
                corr = np.corrcoef(target_returns.flatten(), other_returns.flatten())[
                    0, 1
                ]

                if abs(corr) < 0.5:  # 門檻
                    continue

                # 價差 Z-Score (簡化版: Log Price Ratio)
                # Spread = log(A) - beta * log(B)
                log_a = np.log(target_price)
                log_b = np.log(other_price)

                reg = LinearRegression().fit(log_b.reshape(-1, 1), log_a)
                beta = reg.coef_[0]
                spread = log_a - beta * log_b

                zscore = (spread[-1] - spread.mean()) / spread.std()

                # 半衰期
                spread_lag = spread[:-1]
                spread_ret = np.diff(spread)
                reg_ou = LinearRegression().fit(spread_lag.reshape(-1, 1), spread_ret)
                lambda_ou = reg_ou.coef_[0]
                half_life = -np.log(2) / lambda_ou if lambda_ou < 0 else 999

                signal, _ = detect_pairs_opportunity(zscore, half_life)

                if signal != "NONE":
                    found_pairs.append(
                        {
                            "partner": other_symbol,
                            "corr": corr,
                            "zscore": zscore,
                            "signal": signal,
                            "beta": beta,
                        }
                    )

            # 5. 輸出
            if not found_pairs:
                self._log("無顯著配對機會")
            else:
                self._log("| 對手 | 相關性 | Z-Score | 訊號 | 建議 |")
                self._log("|---|---|---|---|---|")
                for p in found_pairs:
                    action = "做多價差" if p["zscore"] < 0 else "做空價差"
                    self._log(
                        f"| {p['partner']} | {p['corr']:.2f} | {p['zscore']:+.2f} | {p['signal']} | {action} |"
                    )

            # 判準區塊
            self._log("")
            self._log("> ### 🔗 配對交易判準")
            self._log(">")
            self._log("> | 相關性 | Z-Score | 訊號 | 說明 |")
            self._log("> |--------|---------|------|------|")
            self._log("> | > 0.5 | > +2.0 | 做空價差 | 偏離大，預期收斂 |")
            self._log("> | > 0.5 | < -2.0 | 做多價差 | 偏離大，預期擴張 |")
            self._log("> | > 0.5 | ±1.5 內 | 觀望 | 正常範圍 |")

        except Exception as e:
            self._log(f"⚠️ 配對分析失敗: {e}")

    def _print_supply_chain_result(self, result: dict, _is_reverse: bool) -> None:
        if result.get("signal") == "NO_DATA":
            self._log("⚠️ 無法取得供應鏈數據")
            return

        us = result["us_symbol"]
        tw = result["tw_symbol"]
        lag = result["lag"]
        corr = result["correlation"]
        exp_move = result["expected_move"]
        signal = result["signal"]

        self._log(f"- 分析: `{us}` -> `{tw}`")
        self._log(f"- 相關性: `{corr:.2f}` | 滯後: `{lag}` 天")
        self._log(f"- 美股影響預期: `{exp_move:+.2%}` ({signal})")
        if signal == "OPPORTUNITY":
            self._log("  - 🔥 **機會**: 美股上漲，預期台股跟漲")
        elif signal == "CAUTION":
            self._log("  - 🛑 **警戒**: 美股下跌，預期台股跟跌")

        # 判準區塊
        self._log("")
        self._log("> ### ⛓️ 供應鏈判準")
        self._log(">")
        self._log("> | 相關性 | 滯後天數 | 訊號 | 說明 |")
        self._log("> |--------|----------|------|------|")
        self._log("> | > 0.5 | 1-5 天 | 有效 | 可作為領先指標 |")
        self._log("> | 0.3~0.5 | - | 中等 | 需搭配其他指標 |")
        self._log("> | < 0.3 | - | 弱 | 參考價值低 |")
