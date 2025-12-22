"""Export Daily Summary Command — 匯出每日摘要至 CSV"""

import csv
import json
import logging
from pathlib import Path

import numpy as np

from libs.hunting.src.domain.services.quality_filters import is_value_trap
from libs.hunting.src.domain.services.sector_constraint import apply_sector_cap
from libs.hunting.src.domain.services.sndz_standardizer import standardize_sndz
from libs.hunting.src.ports.local_summary_storage_port import LocalSummaryStoragePort
from libs.reporting.src.ports.export_daily_summary_port import ExportDailySummaryPort
from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO
from libs.shared.src.dtos.reporting.fundamental_formatted_dto import (
    FundamentalFormattedDTO,
)
from libs.shared.src.dtos.reporting.flattened_data_dto import FlattenedDataDTO


# CSV 欄位順序
CSV_COLUMNS = [
    "SYMBOL",
    "UPDATED",
    "NAME",
    "SECTOR",
    "OPEN",
    "HIGH",
    "LOW",
    "CLOSE",
    "PREV_CLOSE",
    "VOLUME",
    "DAILY_RETURN",
    "MOMENTUM",
    "RAW_MOMENTUM",
    "GLOBAL_BETA",
    "LOCAL_BETA",
    "SECTOR_BETA",
    "IVOL",
    "IVOL_PERCENTILE",
    "IVOL_DECILE",
    "IVOL_DECISION",
    "MAX_RET",
    # 品質濾網 (Alpha-Core V4.0)
    "ID_SCORE",
    "ID_PASS",
    "AMIHUD_ILLIQ",
    "OVERNIGHT_RETURN",
    "INTRADAY_RETURN",
    "OVERNIGHT_PASS",
    "VALUE_TRAP_FLAG",  # 價值陷阱標記
    # EEMD 趨勢確認
    "EEMD_SLOPE",
    "EEMD_DAYS",
    "EEMD_CONFIRMED",
    "RESIDUAL_SOURCE",  # P2 新增
    # 品質指標 (P0)
    "HALF_LIFE",
    "CORRELATION_20D",
    "AMIHUD_PERCENTILE",
    "MOMENTUM_PERCENTILE",  # P1 新增
    # 動能生命週期 (plan.md P0)
    "SIGNAL_AGE_DAYS",
    "REMAINING_MEAT_RATIO",
    "RESIDUAL_RSI",
    "RSI_DIVERGENCE",
    "FROG_IN_PAN_ID",
    # 出場訊號 (plan.md P0)
    "STOP_LOSS_TRIGGERED",
    "BETA_CHANGE_PCT",
    "BETA_SPIKE_ALERT",
    "ATR_TRAILING_STOP",
    # P1 新增欄位
    "OU_UPPER_BAND",
    "OU_LOWER_BAND",
    "VOLATILITY_EXPANSION_FLAG",
    "ROLLING_BETA_60D",
    "CORRELATION_DRIFT",
    "SHORT_TERM_REVERSAL",
    # P2 進階欄位
    "OU_MEAN_REVERSION_SPEED",
    "REMAINING_ALPHA_PCT",
    "INDUSTRY_NEUTRAL_SCORE",
    "GROSS_MARGIN_STABILITY",
    "PAIRWISE_CORRELATION",
    "HRP_WEIGHT",
    "REGIME_ADJUSTED_WEIGHT",
    "HMM_STATE_PROB",
    # P1 跨截面計算
    "COMPOSITE_SCORE",
    "VALUE_MOMENTUM_INTERACTION",
    "SECTOR_RELATIVE_SCORE",
    "MARKET_STATE",
    "ACTION_SIGNAL",
    "CROWDING_SCORE",
    "SECTOR_WEIGHT_PCT",
    "SECTOR_CONSTRAINT_FLAG",
    "RECOMMENDATION",
    # P1 SNDZ 標準化欄位
    "F_SCORE_SNDZ",
    "IVOL_SNDZ",
    # P1 行業內 Z-Score
    "VALUE_Z_SCORE",
    "MOMENTUM_Z_SCORE",
    "QUALITY_Z_SCORE",
    "RISK_Z_SCORE",
    # P3 報表整合欄位
    "VIX_TIER",
    "DEFCON_LEVEL",
    "KELLY_WEIGHT",
    # 定價
    "THEO_PRICE",
    "PRICE_DEVIATION_PCT",
    "REMAINING_ALPHA",
    "SIGNAL",
    "ENTRY_SIGNAL",
    "ALPHA_DECAY_STATUS",
    # Alpha/Beta 貢獻度 (plan.md P0)
    "ALPHA_CONTRIBUTION_PCT",
    "BETA_CONTRIBUTION_PCT",
    "IS_ALL_WEATHER",
    # 財報狗基本面
    "REV_YOY",
    "REV_MOM",
    "CFO_RATIO",
    "ACCRUAL",
    "PE",
    "PB",
    "F_SCORE",
    "GROSS_MARGIN",
    "OPERATING_MARGIN",
    "NET_MARGIN",
    "ROE",
    "ROA",
    "DEBT_RATIO",
    "TTM_EPS",
    "TOTAL_DEBT",
    "EQUITY",
]


class ExportDailySummaryCommand(ExportDailySummaryPort):
    """匯出每日摘要至 CSV"""

    def __init__(self, local_storage: LocalSummaryStoragePort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._local_storage = local_storage

    def execute(self, date: str) -> str:
        """匯出指定日期的摘要至 CSV

        重構說明：
        - 動能資料來自: data/momentum/[date]/[symbol].json (via local_storage)
        - 財報狗資料來自: data/fundamental/[symbol].json (獨立儲存)
        - 在此階段合併兩者

        Args:
            date: 日期 (YYYY-MM-DD)

        Returns:
            產生的 CSV 檔案路徑
        """
        symbols = self._local_storage.list_symbols(date)
        if not symbols:
            self._logger.warning(f"找不到 {date} 的任何動能資料")
            return ""

        rows = []
        skipped_no_fundamental = 0

        # 財報狗快取路徑
        fundamental_cache_dir = Path("data/fundamental")

        for symbol in symbols:
            data = self._local_storage.load(date, symbol)
            if not data:
                continue

            # 嘗試從獨立快取載入財報狗資料
            if not data.get("statementdog"):
                # 移除 .TW 後綴取得檔名
                filename = symbol.replace(".TW", "").replace(".TWO", "") + ".json"
                fundamental_path = fundamental_cache_dir / filename

                if fundamental_path.exists():
                    try:
                        with open(fundamental_path, "r", encoding="utf-8") as f:
                            fundamental_cache = json.load(f)
                        # 快取格式: {"data": {...}, "created_at": ..., "invalidate_after": ...}
                        if fundamental_cache.get("data"):
                            data["statementdog"] = self._format_fundamental_data(
                                fundamental_cache["data"]
                            )
                    except Exception as e:
                        self._logger.warning(f"載入 {symbol} 財報狗快取失敗: {e}")

            # 跳過沒有財報狗資料的記錄
            if not data.get("statementdog"):
                skipped_no_fundamental += 1
                continue

            row = self._flatten_data(symbol, data)
            rows.append(row)

        if skipped_no_fundamental > 0:
            self._logger.info(
                f"跳過 {skipped_no_fundamental} 筆 (無財報狗資料，請先執行 make scan-fundamental)"
            )
            self._logger.warning(f"跳過 {skipped_no_fundamental} 筆 (無財報狗資料)")

        if not rows:
            self._logger.warning(
                f"{date} 無有效資料 (可能需要執行 make scan-fundamental)"
            )
            return ""

        # ========================================
        # 跨截面標準化 (Cross-Sectional Normalization)
        # ========================================
        self._apply_cross_sectional_normalization(rows)

        # 依 MOMENTUM 排序 (高到低)
        rows.sort(key=lambda r: r.get("MOMENTUM") or -999, reverse=True)

        # ========================================
        # 板塊限額過濾 (Alpha-Core V4.0)
        # ========================================
        # 單一板塊不超過 30%，優先保留動能高者
        # 轉換為 apply_sector_cap 需要的格式
        rows_for_cap = [
            {"sector": r.get("SECTOR"), "momentum": r.get("MOMENTUM"), **r}
            for r in rows
        ]
        capped_results, sector_stats = apply_sector_cap(
            rows_for_cap,
            cap_pct=0.30,
            sector_key="sector",
        )

        # 轉回原格式，移除 apply_sector_cap 用的臨時欄位
        rows = [
            {k: v for k, v in r.items() if k not in ("sector", "momentum")}
            for r in capped_results
        ]

        self._logger.info(
            f"板塊限額過濾: {len(rows_for_cap)} → {len(rows)} 檔, sectors={sector_stats}"
        )

        # 寫入 CSV
        csv_path = Path("data/summaries") / f"{date}.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)

        self._logger.info(f"已匯出 {len(rows)} 筆至 {csv_path}")

        return str(csv_path)

    def _apply_cross_sectional_normalization(
        self, rows: list[ScanResultRowDTO]
    ) -> None:
        """應用跨截面標準化

        包含：
        1. IVOL 百分位排名
        2. SNDZ 標準化 RAW_MOMENTUM → MOMENTUM
        3. SIGNAL 重新計算
        4. ALPHA_DECAY_STATUS 判定
        """
        # ========================================
        # 1. IVOL 百分位排名
        # ========================================
        ivols = [(i, r.get("IVOL")) for i, r in enumerate(rows) if r.get("IVOL")]
        if ivols:
            ivol_values = sorted([v for _, v in ivols])
            for idx, ivol in ivols:
                rank = ivol_values.index(ivol) + 1
                ivol_pct = round(rank / len(ivol_values) * 100, 1)
                rows[idx]["IVOL_PERCENTILE"] = ivol_pct
                # IVOL_DECILE: 十分位 1-10
                rows[idx]["IVOL_DECILE"] = min(10, int(ivol_pct / 10) + 1)

        # ========================================
        # 1.5 AMIHUD_PERCENTILE 跨截面排名 (P0)
        # ========================================
        amihuds = [
            (i, r.get("AMIHUD_ILLIQ"))
            for i, r in enumerate(rows)
            if r.get("AMIHUD_ILLIQ")
        ]
        if amihuds:
            amihud_values = sorted([v for _, v in amihuds])
            for idx, amihud in amihuds:
                rank = amihud_values.index(amihud) + 1
                rows[idx]["AMIHUD_PERCENTILE"] = round(
                    rank / len(amihud_values) * 100, 1
                )

        # ========================================
        # 1.6 PE_PERCENTILE 和 VALUE_TRAP_FLAG (P1)
        # ========================================
        pe_data = [
            (i, r.get("PE"))
            for i, r in enumerate(rows)
            if r.get("PE") and r.get("PE") > 0
        ]
        pe_percentiles: dict[int, float] = {}
        if pe_data:
            pe_values = sorted([v for _, v in pe_data])
            for idx, pe in pe_data:
                rank = pe_values.index(pe) + 1
                pe_percentiles[idx] = round(rank / len(pe_values) * 100, 1)

        # 價值陷阱過濾
        for i, r in enumerate(rows):
            pe = r.get("PE")
            pe_pct = pe_percentiles.get(i)
            accrual = r.get("ACCRUAL")
            is_trap, _reason = is_value_trap(pe, pe_pct, accrual)
            r["VALUE_TRAP_FLAG"] = is_trap

        # ========================================
        # 2. SNDZ 標準化 RAW_MOMENTUM
        # ========================================
        valid_indices = []
        raw_moms = []
        for i, r in enumerate(rows):
            raw_mom = r.get("RAW_MOMENTUM")
            if raw_mom is not None:
                valid_indices.append(i)
                raw_moms.append(raw_mom)

        if len(raw_moms) > 1:
            raw_mom_array = np.array(raw_moms, dtype=float)
            sndz_scores = standardize_sndz(raw_mom_array)

            for j, idx in enumerate(valid_indices):
                rows[idx]["MOMENTUM"] = round(float(sndz_scores[j]), 4)

            self._logger.info(
                f"SNDZ 標準化完成: {len(valid_indices)} 筆, "
                f"mean={np.mean(sndz_scores):.4f}, std={np.std(sndz_scores):.4f}"
            )

        # ========================================
        # 2.5 P1 新增：MOMENTUM_PERCENTILE 跨截面排名
        # ========================================
        momentums = [
            (i, r.get("MOMENTUM"))
            for i, r in enumerate(rows)
            if r.get("MOMENTUM") is not None
        ]
        if momentums:
            mom_values = sorted([v for _, v in momentums])
            for idx, mom in momentums:
                rank = mom_values.index(mom) + 1
                rows[idx]["MOMENTUM_PERCENTILE"] = round(
                    rank / len(mom_values) * 100, 1
                )

        # ========================================
        # 2.6 P1 新增：F_SCORE_SNDZ 和 IVOL_SNDZ 標準化
        # ========================================
        # F_SCORE SNDZ
        f_scores = [
            (i, r.get("F_SCORE"))
            for i, r in enumerate(rows)
            if r.get("F_SCORE") is not None
        ]
        if len(f_scores) > 1:
            f_array = np.array([v for _, v in f_scores], dtype=float)
            f_sndz = standardize_sndz(f_array)
            for j, (idx, _) in enumerate(f_scores):
                rows[idx]["F_SCORE_SNDZ"] = round(float(f_sndz[j]), 4)

        # IVOL SNDZ (負向：高 IVOL = 負 SNDZ)
        ivol_data = [
            (i, r.get("IVOL")) for i, r in enumerate(rows) if r.get("IVOL") is not None
        ]
        if len(ivol_data) > 1:
            ivol_array = np.array([v for _, v in ivol_data], dtype=float)
            # 取負數使高 IVOL 成為負 SNDZ（高風險）
            ivol_sndz = standardize_sndz(-ivol_array)
            for j, (idx, _) in enumerate(ivol_data):
                rows[idx]["IVOL_SNDZ"] = round(float(ivol_sndz[j]), 4)

        # ========================================
        # 2.7 P1 新增：行業內 Z-Score (VALUE, MOMENTUM, QUALITY, RISK)
        # ========================================
        self._calculate_industry_z_scores(rows)

        # ========================================
        # 3. IVOL_DECISION + SIGNAL + ALPHA_DECAY_STATUS + ENTRY_SIGNAL
        # ========================================
        for r in rows:
            momentum = r.get("MOMENTUM", 0) or 0
            ivol_pct = r.get("IVOL_PERCENTILE", 50) or 50
            f_score = r.get("F_SCORE")
            close = r.get("CLOSE")
            theo_price = r.get("THEO_PRICE")

            # IVOL_DECISION (P0): IVOL × F-Score 矩陣決策類型
            r["IVOL_DECISION"] = self._calculate_ivol_decision(ivol_pct, f_score)

            # PRICE_DEVIATION_PCT (P0): 理論價格偏離度
            if close and theo_price and theo_price > 0:
                r["PRICE_DEVIATION_PCT"] = round(
                    (close - theo_price) / theo_price * 100, 2
                )
            else:
                r["PRICE_DEVIATION_PCT"] = None

            # SIGNAL 計算 (根據 methodology.md IVOL × F-Score 矩陣)
            r["SIGNAL"] = self._calculate_signal(momentum, ivol_pct, f_score)

            # ENTRY_SIGNAL (P0): 做多/做空/觀望
            r["ENTRY_SIGNAL"] = self._calculate_entry_signal(
                momentum, r.get("PRICE_DEVIATION_PCT"), r["IVOL_DECISION"]
            )

            # ALPHA_DECAY_STATUS 判定
            r["ALPHA_DECAY_STATUS"] = self._calculate_alpha_decay_status(momentum)

            # ========================================
            # 4. P1 跨截面計算
            # ========================================
            # COMPOSITE_SCORE: 多因子複合評分
            r["COMPOSITE_SCORE"] = self._calculate_composite_score(r)

            # MARKET_STATE: 市場狀態
            r["MARKET_STATE"] = self._calculate_market_state(r)

            # ACTION_SIGNAL: 操作訊號
            r["ACTION_SIGNAL"] = self._calculate_action_signal(r)

            # CROWDING_SCORE: 擁擠度評分
            r["CROWDING_SCORE"] = self._calculate_crowding_score(r)

            # RECOMMENDATION: 最終推薦
            r["RECOMMENDATION"] = self._calculate_recommendation(r)

        # ========================================
        # 5. SECTOR_WEIGHT_PCT 跨截面計算
        # ========================================
        sector_counts: dict[str, int] = {}
        for r in rows:
            sector = r.get("SECTOR")
            if sector:
                sector_counts[sector] = sector_counts.get(sector, 0) + 1
        total = len(rows)
        for r in rows:
            sector = r.get("SECTOR")
            if sector and total > 0:
                weight_pct = sector_counts[sector] / total * 100
                r["SECTOR_WEIGHT_PCT"] = round(weight_pct, 2)
                # SECTOR_CONSTRAINT_FLAG: 行業權重超過 25% 閾值
                r["SECTOR_CONSTRAINT_FLAG"] = weight_pct > 25.0
            else:
                r["SECTOR_WEIGHT_PCT"] = None
                r["SECTOR_CONSTRAINT_FLAG"] = False

        # ========================================
        # 6. INDUSTRY_NEUTRAL_SCORE 跨截面計算
        # ========================================
        # 按行業分組計算 Z-Score
        sector_scores: dict[str, list[tuple[int, float]]] = {}
        for i, r in enumerate(rows):
            sector = r.get("SECTOR")
            composite = r.get("COMPOSITE_SCORE")
            if sector and composite is not None:
                if sector not in sector_scores:
                    sector_scores[sector] = []
                sector_scores[sector].append((i, composite))

        # 計算行業內 Z-Score
        for sector, scores in sector_scores.items():
            if len(scores) < 2:
                for idx, _ in scores:
                    rows[idx]["INDUSTRY_NEUTRAL_SCORE"] = 0.0
                continue
            values = [s[1] for s in scores]
            mean_val = sum(values) / len(values)
            std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
            for idx, val in scores:
                if std_val > 0:
                    rows[idx]["INDUSTRY_NEUTRAL_SCORE"] = round(
                        (val - mean_val) / std_val, 4
                    )
                else:
                    rows[idx]["INDUSTRY_NEUTRAL_SCORE"] = 0.0

        # ========================================
        # 7. P2 進階計算
        # ========================================
        # PAIRWISE_CORRELATION: 使用 CORRELATION_20D 作為代理
        # (完整版需計算 N×N 殘差相關矩陣)
        for r in rows:
            corr = r.get("CORRELATION_20D")
            if corr is not None:
                r["PAIRWISE_CORRELATION"] = round(corr, 4)

        # HRP_WEIGHT: 簡化版等風險權重 (1 / IVOL)
        total_inv_vol = 0.0
        for r in rows:
            ivol = r.get("IVOL")
            if ivol and ivol > 0:
                total_inv_vol += 1.0 / ivol
        for r in rows:
            ivol = r.get("IVOL")
            if ivol and ivol > 0 and total_inv_vol > 0:
                r["HRP_WEIGHT"] = round((1.0 / ivol) / total_inv_vol * 100, 4)
            else:
                r["HRP_WEIGHT"] = None

        # REGIME_ADJUSTED_WEIGHT: HRP 權重 × 市場狀態調整
        for r in rows:
            hrp = r.get("HRP_WEIGHT")
            state = r.get("MARKET_STATE")
            if hrp is not None:
                # 趨勢啟動/確認 = 加碼，過熱/老化 = 減碼
                if state in ["趨勢啟動", "趨勢確認"]:
                    r["REGIME_ADJUSTED_WEIGHT"] = round(hrp * 1.2, 4)
                elif state in ["動能過熱", "動能老化", "動能崩潰"]:
                    r["REGIME_ADJUSTED_WEIGHT"] = round(hrp * 0.5, 4)
                else:
                    r["REGIME_ADJUSTED_WEIGHT"] = hrp

        # HMM_STATE_PROB: 使用 composite_score 標準化為 0-1 機率
        composite_scores = [
            r.get("COMPOSITE_SCORE")
            for r in rows
            if r.get("COMPOSITE_SCORE") is not None
        ]
        if composite_scores:
            min_c = min(composite_scores)
            max_c = max(composite_scores)
            range_c = max_c - min_c if max_c != min_c else 1.0
            for r in rows:
                cs = r.get("COMPOSITE_SCORE")
                if cs is not None:
                    # 標準化為 0-1，代表「牛市狀態機率」
                    r["HMM_STATE_PROB"] = round((cs - min_c) / range_c, 4)
                else:
                    r["HMM_STATE_PROB"] = None

        # ========================================
        # 8. P1 新增: VALUE_MOMENTUM_INTERACTION (價值 × 動能交互項)
        # ========================================
        # 公式: value_z × momentum_z
        # value_z 使用 (1/PE) 標準化，因為低 PE = 高價值
        pe_values = [
            (i, 1.0 / r.get("PE"))
            for i, r in enumerate(rows)
            if r.get("PE") and r.get("PE") > 0
        ]
        if len(pe_values) > 1:
            pe_list = [v for _, v in pe_values]
            pe_mean = sum(pe_list) / len(pe_list)
            pe_std = (sum((v - pe_mean) ** 2 for v in pe_list) / len(pe_list)) ** 0.5
            for idx, pe_inv in pe_values:
                if pe_std > 0:
                    value_z = (pe_inv - pe_mean) / pe_std
                else:
                    value_z = 0.0
                momentum = rows[idx].get("MOMENTUM")
                if momentum is not None:
                    rows[idx]["VALUE_MOMENTUM_INTERACTION"] = round(
                        value_z * momentum, 4
                    )
                else:
                    rows[idx]["VALUE_MOMENTUM_INTERACTION"] = None
        else:
            for r in rows:
                r["VALUE_MOMENTUM_INTERACTION"] = None

        # ========================================
        # 9. P1 新增: SECTOR_RELATIVE_SCORE (行業相對分數)
        # ========================================
        # 公式: MOMENTUM 在同行業內的 Z-Score
        sector_momentums: dict[str, list[tuple[int, float]]] = {}
        for i, r in enumerate(rows):
            sector = r.get("SECTOR")
            momentum = r.get("MOMENTUM")
            if sector and momentum is not None:
                if sector not in sector_momentums:
                    sector_momentums[sector] = []
                sector_momentums[sector].append((i, momentum))

        for sector, moms in sector_momentums.items():
            if len(moms) < 2:
                for idx, _ in moms:
                    rows[idx]["SECTOR_RELATIVE_SCORE"] = 0.0
                continue
            values = [m[1] for m in moms]
            mean_val = sum(values) / len(values)
            std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
            for idx, val in moms:
                if std_val > 0:
                    rows[idx]["SECTOR_RELATIVE_SCORE"] = round(
                        (val - mean_val) / std_val, 4
                    )
                else:
                    rows[idx]["SECTOR_RELATIVE_SCORE"] = 0.0

        # ========================================
        # 10. P3 報表整合: VIX_TIER, DEFCON_LEVEL, KELLY_WEIGHT
        # ========================================
        # 這些是全域欄位，對所有股票相同
        # VIX_TIER 和 DEFCON_LEVEL 需要從外部取得，這裡設為 placeholder
        # KELLY_WEIGHT 可以從 HRP_WEIGHT 和勝率估算

        for r in rows:
            # VIX_TIER: 假設正常模式下為 Tier-0（VIX < 20）
            # 實際值應從天候模組取得
            r["VIX_TIER"] = r.get("VIX_TIER") if "VIX_TIER" in r else "TIER_0"

            # DEFCON_LEVEL: 根據綜合風險計算
            # 簡化版：根據 CROWDING_SCORE 和 IVOL 判斷
            crowding = r.get("CROWDING_SCORE") or 0
            ivol_pct = r.get("IVOL_PERCENTILE") or 50
            if crowding > 70 or ivol_pct > 80:
                r["DEFCON_LEVEL"] = "DEFCON_3"
            elif crowding > 50 or ivol_pct > 60:
                r["DEFCON_LEVEL"] = "DEFCON_4"
            else:
                r["DEFCON_LEVEL"] = "DEFCON_5"

            # KELLY_WEIGHT: 凱利公式建議倉位
            # 簡化公式: Kelly = (win_rate - (1-win_rate)/win_loss_ratio)
            # 這裡使用 composite_score 估算勝率
            composite = r.get("COMPOSITE_SCORE")
            hrp = r.get("HRP_WEIGHT")
            if composite is not None and hrp is not None:
                # 假設 composite_score > 0 時勝率較高
                # 勝率估算: 50% + composite * 5%，上限 70%
                win_rate = min(0.70, max(0.30, 0.50 + composite * 0.05))
                # 假設盈虧比為 1.5
                win_loss_ratio = 1.5
                kelly_fraction = win_rate - (1 - win_rate) / win_loss_ratio
                kelly_fraction = max(0, min(0.25, kelly_fraction))  # 上限 25%
                # 與 HRP 權重結合
                r["KELLY_WEIGHT"] = round(hrp * kelly_fraction * 4, 4)  # 4x 調整因子
            else:
                r["KELLY_WEIGHT"] = None

    def _calculate_signal(
        self, momentum: float, ivol_pct: float, f_score: int | None
    ) -> str:
        """根據 SNDZ + IVOL + F-Score 決策矩陣計算訊號

        基於 methodology.md 的 IVOL × F-Score 矩陣：
        - 高 IVOL + 高 F-Score (≥7): 錯殺機會，積極買入
        - 高 IVOL + 低 F-Score (≤4): 彩票股，剔除
        - 其他: 標準門檻

        買入區間: 0.5 < Z < 3.0 (methodology.md)
        """
        is_high_ivol = ivol_pct > 80
        is_low_fcore = f_score is not None and f_score <= 4
        is_high_fscore = f_score is not None and f_score >= 7

        # 高 IVOL + 低 F-Score = ABORT
        if is_high_ivol and is_low_fcore:
            return "ABORT"

        # 高 IVOL + 高 F-Score = 錯殺機會，降低門檻
        if is_high_ivol and is_high_fscore:
            if momentum > 0.5:
                return "EXECUTE"
            elif momentum > 0:
                return "REDUCE"
            else:
                return "ABORT"

        # 高 IVOL + 中 F-Score = 觀察，提高門檻
        if is_high_ivol:
            if momentum > 1.0:
                return "EXECUTE"
            elif momentum > 0.5:
                return "REDUCE"
            else:
                return "ABORT"

        # 標準門檻 (methodology.md: 0.5 < Z < 3.0)
        if 0.5 < momentum < 3.0:
            return "EXECUTE"
        elif 0 < momentum <= 0.5:
            return "REDUCE"
        else:
            return "ABORT"

    def _calculate_alpha_decay_status(self, momentum: float) -> str:
        """根據 SNDZ 分數判定 Alpha 衰減狀態

        基於 methodology.md 的 Alpha 衰減模型：
        - 剩餘 Alpha >= 60%: FRESH
        - 40% <= 剩餘 Alpha < 60%: ACTIVE
        - 剩餘 Alpha < 40%: FADING/EXHAUSTED
        """
        if momentum > 1.5:
            return "FRESH"
        elif momentum > 0.5:
            return "ACTIVE"
        elif momentum > 0:
            return "FADING"
        else:
            return "EXHAUSTED"

    def _calculate_ivol_decision(self, ivol_pct: float, f_score: int | None) -> str:
        """IVOL × F-Score 矩陣決策類型

        基於 prd.md 的決策矩陣：
        - 高 IVOL + 高 F-Score (≥7): OPPORTUNITY (錯殺機會)
        - 高 IVOL + 中 F-Score (5-6): WATCH (觀察)
        - 高 IVOL + 低 F-Score (≤4): LOTTERY (彩票股，剔除)
        - 中/低 IVOL + F-Score ≥5: STANDARD (標準候選)
        - 中/低 IVOL + F-Score ≤4: EXCLUDE (剔除)
        """
        is_high_ivol = ivol_pct > 80

        if f_score is None:
            return "UNKNOWN"

        if is_high_ivol:
            if f_score >= 7:
                return "OPPORTUNITY"
            elif f_score >= 5:
                return "WATCH"
            else:
                return "LOTTERY"
        else:
            if f_score >= 5:
                return "STANDARD"
            else:
                return "EXCLUDE"

    def _calculate_entry_signal(
        self,
        momentum: float,
        price_deviation_pct: float | None,
        ivol_decision: str,
    ) -> str:
        """綜合進場訊號

        基於 plan.md 的做多/做空訊號：
        - 做多: 市場價格 < 理論價格 (deviation < 0) + 正動能
        - 做空: 市場價格 > 理論價格 × 1.3 (deviation > 30%) + LOTTERY
        - 觀望: 其他情況
        """
        # 彩票股 + 高估值 = 做空候選
        if (
            ivol_decision == "LOTTERY"
            and price_deviation_pct
            and price_deviation_pct > 30
        ):
            return "SHORT"

        # EXCLUDE 類型直接跳過
        if ivol_decision in ["LOTTERY", "EXCLUDE"]:
            return "SKIP"

        # 正動能 + 低估 = 做多
        if (
            momentum > 0.5
            and price_deviation_pct is not None
            and price_deviation_pct < 0
        ):
            return "LONG"

        # 正動能但高估 = 觀望
        if momentum > 0.5:
            return "HOLD"

        return "SKIP"

    def _calculate_composite_score(self, row: dict) -> float | None:
        """計算多因子複合評分 (P1)

        基於 plan.md 的複合評分公式：
        composite = w_M × Momentum + w_Q × Quality - w_R × Risk

        權重:
        - Momentum (SNDZ): 0.4
        - Quality (F_SCORE): 0.3
        - Risk (-IVOL): 0.3
        """
        momentum = row.get("MOMENTUM")
        f_score = row.get("F_SCORE")
        ivol_pct = row.get("IVOL_PERCENTILE")

        if momentum is None:
            return None

        # Quality Z-Score (F_SCORE 標準化為 0-1 範圍)
        quality_z = (f_score - 5) / 2 if f_score is not None else 0

        # Risk Z-Score (IVOL 越高風險越大，取負)
        risk_z = (ivol_pct - 50) / 25 if ivol_pct is not None else 0

        # 複合評分
        composite = 0.4 * momentum + 0.3 * quality_z - 0.3 * risk_z

        return round(composite, 4)

    def _calculate_market_state(self, row: dict) -> str:
        """計算市場狀態 (P1)

        基於 plan.md 的狀態分類：
        - 趨勢啟動: 信號年齡 < 30 天 + 剩餘肉量 > 80%
        - 趨勢確認: 信號年齡 30-60 天 + EEMD 確認
        - 動能過熱: RSI > 70
        - 動能老化: 剩餘肉量 < 40%
        - 動能崩潰: 止損觸發
        - 擁擠警報: 相關性 > 0.7
        """
        signal_age = row.get("SIGNAL_AGE_DAYS")
        remaining_meat = row.get("REMAINING_MEAT_RATIO")
        residual_rsi = row.get("RESIDUAL_RSI")
        eemd_confirmed = row.get("EEMD_CONFIRMED")
        stop_loss = row.get("STOP_LOSS_TRIGGERED")
        correlation = row.get("CORRELATION_20D")

        # 優先判斷：崩潰和警報
        if stop_loss:
            return "動能崩潰"
        if correlation and correlation > 0.7:
            return "擁擠警報"

        # 生命週期狀態
        if signal_age is not None and remaining_meat is not None:
            if signal_age < 30 and remaining_meat > 0.8:
                return "趨勢啟動"
            if 30 <= signal_age <= 60 and eemd_confirmed:
                return "趨勢確認"
            if remaining_meat < 0.4:
                return "動能老化"

        # RSI 過熱
        if residual_rsi and residual_rsi > 70:
            return "動能過熱"

        return "觀察中"

    def _calculate_action_signal(self, row: dict) -> str:
        """計算操作訊號 (P1)

        基於 plan.md 的操作建議：
        - BUY: 趨勢啟動 + EXECUTE 訊號
        - HOLD: 趨勢確認 + 正動能
        - TRIM: 動能過熱 或 剩餘肉量 < 60%
        - EXIT: 動能老化 或 RSI 背離 bearish
        - STOP: 止損觸發
        - LIQUIDATE: 動能崩潰
        """
        market_state = row.get("MARKET_STATE")
        signal = row.get("SIGNAL")
        entry_signal = row.get("ENTRY_SIGNAL")
        rsi_divergence = row.get("RSI_DIVERGENCE")
        remaining_meat = row.get("REMAINING_MEAT_RATIO")

        # 優先判斷：強制動作
        if market_state == "動能崩潰":
            return "LIQUIDATE"
        if row.get("STOP_LOSS_TRIGGERED"):
            return "STOP"

        # 趨勢啟動 + 執行訊號 = 買入
        if market_state == "趨勢啟動" and signal == "EXECUTE":
            return "BUY"

        # 動能過熱 或 剩餘肉量不足 = 減碼
        if market_state == "動能過熱":
            return "TRIM"
        if remaining_meat and remaining_meat < 0.6:
            return "TRIM"

        # RSI 背離 或 動能老化 = 出場
        if rsi_divergence == "bearish":
            return "EXIT"
        if market_state == "動能老化":
            return "EXIT"

        # 趨勢確認 = 持有
        if market_state == "趨勢確認":
            return "HOLD"

        # 其他情況根據 entry_signal
        if entry_signal == "LONG":
            return "BUY"
        if entry_signal == "HOLD":
            return "HOLD"

        return "WAIT"

    def _calculate_crowding_score(self, row: dict) -> float | None:
        """計算擁擠度評分 (P1)

        基於 plan.md 的擁擠度計算：
        - 高相關性 (>0.7) = 高擁擠
        - 相關性漂移 = 擁擠增加
        - 波動率擴張 = 可能擁擠

        評分 0-100，越高越擁擠
        """
        correlation = row.get("CORRELATION_20D")
        corr_drift = row.get("CORRELATION_DRIFT")
        vol_expansion = row.get("VOLATILITY_EXPANSION_FLAG")

        score = 0.0

        # 相關性貢獻 (最大 60 分)
        if correlation is not None:
            score += min(60, max(0, (correlation - 0.3) / 0.5 * 60))

        # 相關性漂移 (20 分)
        if corr_drift:
            score += 20

        # 波動率擴張 (20 分)
        if vol_expansion:
            score += 20

        return round(score, 2)

    def _calculate_recommendation(self, row: dict) -> str:
        """計算最終推薦 (P1)

        基於 plan.md 的推薦邏輯：
        - LONG: 買入訊號 + 低擁擠 + 正動能
        - SHORT: 做空訊號
        - HOLD: 其他
        """
        action = row.get("ACTION_SIGNAL")
        crowding = row.get("CROWDING_SCORE")
        entry = row.get("ENTRY_SIGNAL")
        momentum = row.get("MOMENTUM")

        # 清倉/止損 = 無推薦
        if action in ["LIQUIDATE", "STOP"]:
            return "EXIT"

        # 買入訊號 + 低擁擠
        if action == "BUY" and (crowding is None or crowding < 50):
            return "LONG"

        # 做空訊號
        if entry == "SHORT":
            return "SHORT"

        # 減碼/出場
        if action in ["TRIM", "EXIT"]:
            return "REDUCE"

        # 持有
        if action in ["HOLD", "WAIT"]:
            if momentum is not None and momentum > 0:
                return "HOLD"
            return "NEUTRAL"

        return "NEUTRAL"

    def _calc_mean_reversion_speed(self, half_life: float | None) -> float | None:
        """計算 OU 均值回歸速度 (P2)

        θ = ln(2) / half_life
        """
        import math

        if half_life is None or half_life <= 0:
            return None
        return round(math.log(2) / half_life, 6)

    def _calc_remaining_alpha_pct(self, remaining_alpha: float | None) -> float | None:
        """計算剩餘 Alpha 百分比 (P1)

        remaining_alpha 已經是 0-1 範圍，轉換為百分比顯示
        """
        if remaining_alpha is None:
            return None
        return round(remaining_alpha * 100, 2)

    def _calculate_industry_z_scores(self, rows: list) -> None:
        """計算行業內 Z-Score (P1)

        對每個因子按行業分組，計算行業內標準化分數。
        - VALUE_Z_SCORE: 1/PE 的行業內 Z-Score
        - MOMENTUM_Z_SCORE: MOMENTUM 的行業內 Z-Score
        - QUALITY_Z_SCORE: F_SCORE 的行業內 Z-Score
        - RISK_Z_SCORE: -IVOL 的行業內 Z-Score（負向）
        """
        # 收集各行業的因子值
        sector_data: dict[str, list[tuple[int, dict]]] = {}
        for i, r in enumerate(rows):
            sector = r.get("SECTOR")
            if sector:
                if sector not in sector_data:
                    sector_data[sector] = []
                sector_data[sector].append(
                    (
                        i,
                        {
                            "pe_inv": 1.0 / r["PE"]
                            if r.get("PE") and r["PE"] > 0
                            else None,
                            "momentum": r.get("MOMENTUM"),
                            "f_score": r.get("F_SCORE"),
                            "ivol": r.get("IVOL"),
                        },
                    )
                )

        def calc_z_score(values: list[float]) -> list[float]:
            """計算一組值的 Z-Score"""
            if len(values) < 2:
                return [0.0] * len(values)
            mean_val = sum(values) / len(values)
            std_val = (sum((v - mean_val) ** 2 for v in values) / len(values)) ** 0.5
            if std_val == 0:
                return [0.0] * len(values)
            return [(v - mean_val) / std_val for v in values]

        # 對每個行業計算 Z-Score
        for sector, items in sector_data.items():
            # VALUE_Z_SCORE
            pe_data = [
                (idx, d["pe_inv"]) for idx, d in items if d["pe_inv"] is not None
            ]
            if pe_data:
                z_scores = calc_z_score([v for _, v in pe_data])
                for (idx, _), z in zip(pe_data, z_scores):
                    rows[idx]["VALUE_Z_SCORE"] = round(z, 4)

            # MOMENTUM_Z_SCORE
            mom_data = [
                (idx, d["momentum"]) for idx, d in items if d["momentum"] is not None
            ]
            if mom_data:
                z_scores = calc_z_score([v for _, v in mom_data])
                for (idx, _), z in zip(mom_data, z_scores):
                    rows[idx]["MOMENTUM_Z_SCORE"] = round(z, 4)

            # QUALITY_Z_SCORE
            f_data = [
                (idx, d["f_score"]) for idx, d in items if d["f_score"] is not None
            ]
            if f_data:
                z_scores = calc_z_score([float(v) for _, v in f_data])
                for (idx, _), z in zip(f_data, z_scores):
                    rows[idx]["QUALITY_Z_SCORE"] = round(z, 4)

            # RISK_Z_SCORE (負向：高 IVOL = 負 Z-Score)
            ivol_data = [(idx, -d["ivol"]) for idx, d in items if d["ivol"] is not None]
            if ivol_data:
                z_scores = calc_z_score([v for _, v in ivol_data])
                for (idx, _), z in zip(ivol_data, z_scores):
                    rows[idx]["RISK_Z_SCORE"] = round(z, 4)

    def _format_fundamental_data(self, summary: dict) -> FundamentalFormattedDTO:
        """將財報狗快取資料轉換為 statementdog 欄位格式

        Args:
            summary: 從 data/fundamental/[symbol].json 讀取的 data 欄位

        Returns:
            dict: 與 ScanResidualMomentumQuery._format_statementdog_data 相同格式
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
            # 評價
            "pb": river_chart.get("current_pb"),
            # F-Score
            "f_score": f_score.get("score") if isinstance(f_score, dict) else f_score,
            # 利潤率
            "gross_margin": profit_margins.get("gross_margin"),
            "operating_margin": profit_margins.get("operating_margin"),
            "net_margin": profit_margins.get("net_margin"),
            # 財務比率
            "roe": financial_ratios.get("roe"),
            "roa": financial_ratios.get("roa"),
            # 原始數據
            "ttm_eps": financial_ratios.get("ttm_eps"),
            "total_debt": financial_ratios.get("total_debt"),
            "equity": financial_ratios.get("equity"),
        }

    def _flatten_data(self, symbol: str, data: dict) -> FlattenedDataDTO:
        """將 JSON 資料攤平為 CSV 欄位格式

        注意：以下欄位在 _apply_cross_sectional_normalization 中計算：
        - MOMENTUM (SNDZ 標準化)
        - IVOL_PERCENTILE (跨截面排名)
        - IVOL_DECISION (IVOL × F-Score 矩陣)
        - PRICE_DEVIATION_PCT (理論價格偏離度)
        - SIGNAL (依賴 MOMENTUM 和 IVOL_PERCENTILE)
        - ENTRY_SIGNAL (做多/做空/觀望)
        - ALPHA_DECAY_STATUS (依賴 MOMENTUM)
        """
        market_data = data.get("market_data") or {}
        momentum = data.get("momentum") or {}
        pricing = data.get("pricing") or {}
        lifecycle = data.get("lifecycle") or {}
        exit_signals = data.get("exit_signals") or {}
        alpha_beta = data.get("alpha_beta") or {}
        sd = data.get("statementdog") or {}

        return {
            "SYMBOL": symbol,
            "UPDATED": data.get("updated"),
            "NAME": market_data.get("name"),
            "SECTOR": market_data.get("sector"),
            "OPEN": market_data.get("open"),
            "HIGH": market_data.get("high"),
            "LOW": market_data.get("low"),
            "CLOSE": market_data.get("close"),
            "PREV_CLOSE": market_data.get("prev_close"),
            "VOLUME": market_data.get("volume"),
            "DAILY_RETURN": market_data.get("daily_return"),
            # 跨截面計算欄位 (初始化為 None)
            "MOMENTUM": None,  # SNDZ 標準化
            "RAW_MOMENTUM": momentum.get("raw_momentum"),
            "GLOBAL_BETA": momentum.get("global_beta"),
            "LOCAL_BETA": momentum.get("local_beta"),
            "SECTOR_BETA": momentum.get("sector_beta"),
            "IVOL": momentum.get("ivol"),
            "IVOL_PERCENTILE": None,  # 跨截面排名
            "IVOL_DECILE": None,  # 跨截面十分位 (1-10)
            "IVOL_DECISION": None,  # IVOL × F-Score 矩陣
            "MAX_RET": momentum.get("max_ret"),
            # 品質濾網 (Alpha-Core V4.0) — 從 JSON 讀取
            "ID_SCORE": momentum.get("id_score"),
            "ID_PASS": momentum.get("id_pass"),
            "AMIHUD_ILLIQ": momentum.get("amihud_illiq"),
            "OVERNIGHT_RETURN": momentum.get("overnight_return"),
            "INTRADAY_RETURN": momentum.get("intraday_return"),
            "OVERNIGHT_PASS": momentum.get("overnight_pass"),
            "VALUE_TRAP_FLAG": None,  # 跨截面計算
            # EEMD 趨勢確認 — 從 JSON 讀取
            "EEMD_SLOPE": momentum.get("eemd_slope"),
            "EEMD_DAYS": momentum.get("eemd_days"),
            "EEMD_CONFIRMED": momentum.get("eemd_confirmed"),
            "RESIDUAL_SOURCE": momentum.get("residual_source", "ols"),
            # 品質指標 (P0) — 從 quality 區塊讀取
            "HALF_LIFE": data.get("quality", {}).get("half_life"),
            "CORRELATION_20D": data.get("quality", {}).get("correlation_20d"),
            "AMIHUD_PERCENTILE": None,  # 跨截面排名
            "MOMENTUM_PERCENTILE": None,  # P1 跨截面排名
            # 動能生命週期 (plan.md P0) — 從 JSON 讀取
            "SIGNAL_AGE_DAYS": lifecycle.get("signal_age_days"),
            "REMAINING_MEAT_RATIO": lifecycle.get("remaining_meat_ratio"),
            "RESIDUAL_RSI": lifecycle.get("residual_rsi"),
            "RSI_DIVERGENCE": lifecycle.get("rsi_divergence"),
            "FROG_IN_PAN_ID": lifecycle.get("frog_in_pan_id"),
            # 出場訊號 (plan.md P0) — 從 JSON 讀取
            "STOP_LOSS_TRIGGERED": exit_signals.get("stop_loss_triggered"),
            "BETA_CHANGE_PCT": exit_signals.get("beta_change_pct"),
            "BETA_SPIKE_ALERT": exit_signals.get("beta_spike_alert"),
            "ATR_TRAILING_STOP": exit_signals.get("atr_trailing_stop"),
            # P1 新增欄位 — 從 JSON 讀取
            "OU_UPPER_BAND": pricing.get("ou_upper_band"),
            "OU_LOWER_BAND": pricing.get("ou_lower_band"),
            "VOLATILITY_EXPANSION_FLAG": exit_signals.get("volatility_expansion_flag"),
            "ROLLING_BETA_60D": exit_signals.get("rolling_beta_60d"),
            "CORRELATION_DRIFT": exit_signals.get("correlation_drift"),
            "SHORT_TERM_REVERSAL": exit_signals.get("short_term_reversal"),
            # P2 進階欄位 — 從 half_life 計算
            "OU_MEAN_REVERSION_SPEED": self._calc_mean_reversion_speed(
                lifecycle.get("half_life")
            ),
            # P1/P2 進階欄位
            "REMAINING_ALPHA_PCT": self._calc_remaining_alpha_pct(
                pricing.get("remaining_alpha")
            ),
            "INDUSTRY_NEUTRAL_SCORE": None,  # 跨截面計算
            "GROSS_MARGIN_STABILITY": sd.get("gross_margin_stability"),
            # P2 進階欄位 — 跨截面計算
            "PAIRWISE_CORRELATION": None,
            "HRP_WEIGHT": None,
            "REGIME_ADJUSTED_WEIGHT": None,
            "HMM_STATE_PROB": None,
            # P1 跨截面計算 — 在 _apply_cross_sectional_normalization 中填入
            "COMPOSITE_SCORE": None,
            "VALUE_MOMENTUM_INTERACTION": None,  # P1 跨截面計算
            "SECTOR_RELATIVE_SCORE": None,  # P1 跨截面計算
            "MARKET_STATE": None,
            "ACTION_SIGNAL": None,
            "CROWDING_SCORE": None,
            "SECTOR_WEIGHT_PCT": None,
            "SECTOR_CONSTRAINT_FLAG": None,
            "RECOMMENDATION": None,
            # P1 SNDZ 標準化欄位 — 跨截面計算
            "F_SCORE_SNDZ": None,
            "IVOL_SNDZ": None,
            # P1 行業內 Z-Score — 跨截面計算
            "VALUE_Z_SCORE": None,
            "MOMENTUM_Z_SCORE": None,
            "QUALITY_Z_SCORE": None,
            "RISK_Z_SCORE": None,
            # P3 報表整合欄位
            "VIX_TIER": None,
            "DEFCON_LEVEL": None,
            "KELLY_WEIGHT": None,
            # 定價
            "THEO_PRICE": pricing.get("theo_price"),
            "PRICE_DEVIATION_PCT": None,  # 跨截面計算
            "REMAINING_ALPHA": pricing.get("remaining_alpha"),
            "SIGNAL": None,  # 依賴 MOMENTUM 和 IVOL_PERCENTILE
            "ENTRY_SIGNAL": None,  # 做多/做空/觀望
            "ALPHA_DECAY_STATUS": None,  # 依賴 MOMENTUM
            # Alpha/Beta 貢獻度 (plan.md P0) — 從 alpha_beta 區塊讀取
            "ALPHA_CONTRIBUTION_PCT": alpha_beta.get("alpha_contribution_pct"),
            "BETA_CONTRIBUTION_PCT": alpha_beta.get("beta_contribution_pct"),
            "IS_ALL_WEATHER": alpha_beta.get("is_all_weather"),
            # 財報狗基本面
            "REV_YOY": sd.get("rev_yoy"),
            "REV_MOM": sd.get("rev_mom"),
            "CFO_RATIO": sd.get("cfo_ratio"),
            "ACCRUAL": sd.get("accrual_ratio"),
            "PE": sd.get("pe"),
            "PB": sd.get("pb"),
            "F_SCORE": sd.get("f_score"),
            "GROSS_MARGIN": sd.get("gross_margin"),
            "OPERATING_MARGIN": sd.get("operating_margin"),
            "NET_MARGIN": sd.get("net_margin"),
            "ROE": sd.get("roe"),
            "ROA": sd.get("roa"),
            "DEBT_RATIO": sd.get("debt_ratio"),
            "TTM_EPS": sd.get("ttm_eps"),
            "TOTAL_DEBT": sd.get("total_debt"),
            "EQUITY": sd.get("equity"),
        }
