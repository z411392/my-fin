"""Stock Data Builder Service

共用的資料建構服務，供 make retain 和 make scan 使用
確保推送到 Google Sheets 的資料結構一致
"""

from libs.shared.src.dtos.stock_scan.market_data import MarketData
from libs.shared.src.dtos.stock_scan.momentum_data import MomentumData
from libs.shared.src.dtos.stock_scan.pricing_data import PricingData
from libs.shared.src.dtos.stock_scan.alpha_beta_data import AlphaBetaData
from libs.shared.src.dtos.stock_scan.quality_data import QualityData
from libs.shared.src.dtos.stock_scan.lifecycle_data import LifecycleData
from libs.shared.src.dtos.stock_scan.exit_signals_data import ExitSignalsData
from libs.shared.src.dtos.stock_scan.statementdog_data import StatementDogData
from libs.shared.src.dtos.stock_scan.stock_scan_result import StockScanResult
from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO


def build_market_data(result: ScanResultRowDTO) -> MarketData:
    """建構 market_data 區塊"""
    return {
        "name": result.get("name"),
        "sector": result.get("sector"),
        "open": result.get("open"),
        "high": result.get("high"),
        "low": result.get("low"),
        "close": result.get("close"),
        "prev_close": result.get("prev_close"),
        "volume": result.get("volume"),
        "daily_return": result.get("daily_return"),
    }


def build_momentum(result: ScanResultRowDTO) -> MomentumData:
    """建構 momentum 區塊

    注意：momentum (SNDZ 標準化) 和 signal 在 CSV 產出時才計算
    這裡只存原始值和個股品質濾網指標

    個股獨立欄位 (Per-Stock):
    - raw_momentum, betas, ivol, max_ret
    - 品質濾網: id_score, amihud_illiq, overnight_return, intraday_return, overnight_pass
    - EEMD 趨勢: eemd_slope, eemd_days, eemd_confirmed
    """
    return {
        # 動能原始值 (momentum 欄位移到 CSV 產出時以 SNDZ 標準化計算)
        "raw_momentum": result.get("raw_momentum"),
        "global_beta": result.get("global_beta"),
        "local_beta": result.get("local_beta"),
        "sector_beta": result.get("sector_beta"),
        "ivol": result.get("ivol"),
        "max_ret": result.get("max_ret"),
        # 品質濾網 (Alpha-Core V4.0)
        "id_score": result.get("id_score"),
        "id_pass": result.get("id_pass"),
        "amihud_illiq": result.get("amihud_illiq"),
        "overnight_return": result.get("overnight_return"),
        "intraday_return": result.get("intraday_return"),
        "overnight_pass": result.get("overnight_pass"),
        # EEMD 趨勢確認
        "eemd_slope": result.get("eemd_slope"),
        "eemd_days": result.get("eemd_days"),
        "eemd_confirmed": result.get("eemd_confirmed"),
        # P2 新增欄位
        "residual_source": result.get("residual_source", "ols"),
    }


def build_pricing(result: ScanResultRowDTO) -> PricingData:
    """建構 pricing 區塊

    注意：signal, ivol_decision, ivol_reason 依賴跨截面計算
    在 CSV 產出時才計算
    """
    return {
        "theo_price": result.get("theo_price"),
        "remaining_alpha": result.get("remaining_alpha"),
        "theoretical_price_deviation_pct": result.get(
            "theoretical_price_deviation_pct"
        ),
        # OU 邊界 (plan.md P1)
        "ou_upper_band": result.get("ou_upper_band"),
        "ou_lower_band": result.get("ou_lower_band"),
        # signal, ivol_decision, ivol_reason 移到 CSV 產出時計算
    }


def build_alpha_beta(result: ScanResultRowDTO) -> AlphaBetaData:
    """建構 alpha_beta 區塊 (Alpha/Beta 貢獻度分解)

    對應 plan.md P0 項目: Alpha/Beta Decomposition

    Args:
        result: 股票評估結果，應包含 alpha_beta_decomposition 子結構

    Returns:
        標準化的 alpha_beta 字典
    """
    ab = result.get("alpha_beta_decomposition") or {}

    return {
        "alpha": ab.get("alpha"),
        "beta": ab.get("beta"),
        "alpha_contribution_pct": ab.get("alpha_contribution_pct"),
        "beta_contribution_pct": ab.get("beta_contribution_pct"),
        "total_return": ab.get("total_return"),
        "alpha_return": ab.get("alpha_return"),
        "beta_return": ab.get("beta_return"),
        "r_squared": ab.get("r_squared"),
        "is_all_weather": ab.get("is_all_weather"),
    }


def build_quality(result: ScanResultRowDTO) -> QualityData:
    """建構 quality 區塊 (Alpha-Core V4.0 品質濾網)

    對應 strategy.md 的個股健檢判定標準和選股品質濾網。

    Args:
        result: 股票評估結果

    Returns:
        標準化的 quality 字典
    """
    return {
        # 資訊離散度 (FIP 效應): ID ≤ 0 為連續小漲，高品質
        "id_score": result.get("id_score"),
        "id_pass": result.get("id_pass"),
        # Amihud 非流動性: 值越高表示流動性越差
        "amihud_illiq": result.get("amihud_illiq"),
        # 隔夜確認: ON/ID > 0.5 表示機構主導
        "overnight_return": result.get("overnight_return"),
        "intraday_return": result.get("intraday_return"),
        "overnight_pass": result.get("overnight_pass"),
        # EEMD 趨勢: slope > 0 且 ≥ 3 天 = 趨勢確認
        "eemd_slope": result.get("eemd_slope"),
        "eemd_days": result.get("eemd_days"),
        "eemd_confirmed": result.get("eemd_confirmed"),
        # 均值回歸半衰期
        "half_life": result.get("half_life"),
        # 個股與大盤相關係數 (Alpha 消失預警: ρ > 0.7)
        "correlation_20d": result.get("correlation_20d"),
    }


def build_lifecycle(result: ScanResultRowDTO) -> LifecycleData:
    """建構 lifecycle 區塊 (動能生命週期)

    對應 plan.md P0 項目: 動能生命週期指標

    Args:
        result: 股票評估結果

    Returns:
        lifecycle 字典
    """
    return {
        "signal_age_days": result.get("signal_age_days"),
        "remaining_meat_ratio": result.get("remaining_meat_ratio"),
        "residual_rsi": result.get("residual_rsi"),
        "rsi_divergence": result.get("rsi_divergence"),
        "frog_in_pan_id": result.get("frog_in_pan_id"),
        "theoretical_price": result.get("theoretical_price"),
    }


def build_exit_signals(result: ScanResultRowDTO) -> ExitSignalsData:
    """建構 exit_signals 區塊 (出場訊號)

    對應 plan.md P0 項目: 出場機制指標

    Args:
        result: 股票評估結果

    Returns:
        exit_signals 字典
    """
    return {
        "stop_loss_triggered": result.get("stop_loss_triggered"),
        "beta_change_pct": result.get("beta_change_pct"),
        "beta_spike_alert": result.get("beta_spike_alert"),
        "atr_trailing_stop": result.get("atr_trailing_stop"),
        # P1 新增欄位
        "volatility_expansion_flag": result.get("volatility_expansion_flag"),
        "correlation_drift": result.get("correlation_drift"),
        "short_term_reversal": result.get("short_term_reversal"),
        "rolling_beta_60d": result.get("rolling_beta_60d"),
    }


def build_statementdog(
    sd: StatementDogData | None, close: float | None = None
) -> StatementDogData:
    """
    建構 statementdog 區塊

    Args:
        sd: 財報狗資料字典 (可能為 None 或空字典)
        close: 收盤價 (用於計算 PE)

    Returns:
        標準化的 statementdog 字典，包含 PE 和 DEBT_RATIO
    """
    sd = sd or {}

    # 計算 PE (Price to Earnings)
    ttm_eps = sd.get("ttm_eps")
    pe = round(close / ttm_eps, 2) if close and ttm_eps and ttm_eps != 0 else None

    # 計算 DEBT_RATIO
    total_debt = sd.get("total_debt") or 0
    equity = sd.get("equity") or 0
    debt_ratio = (
        round(total_debt / (total_debt + equity) * 100, 2)
        if (total_debt + equity) != 0
        else None
    )

    return {
        "rev_yoy": sd.get("rev_yoy"),
        "rev_mom": sd.get("rev_mom"),
        "cfo_ratio": sd.get("cfo_ratio"),
        "accrual_ratio": sd.get("accrual_ratio"),
        "pb": sd.get("pb"),
        "f_score": sd.get("f_score"),
        "gross_margin": sd.get("gross_margin"),
        "operating_margin": sd.get("operating_margin"),
        "net_margin": sd.get("net_margin"),
        "roe": sd.get("roe"),
        "roa": sd.get("roa"),
        # 衍生欄位 (原由 spreadsheet 公式計算)
        "pe": pe,
        "debt_ratio": debt_ratio,
        # 原始數據
        "ttm_eps": ttm_eps,
        "total_debt": sd.get("total_debt"),
        "equity": sd.get("equity"),
    }


def build_full_push_data(
    result: ScanResultRowDTO,
    statementdog_data: StatementDogData | None = None,
) -> StockScanResult:
    """
    建構完整的推送資料

    Args:
        result: 股票評估結果 (來自 evaluate_single_stock 或 merged_stream)
        statementdog_data: 財報狗資料 (如果是頂層資料) 或 None (從 result 中讀取)

    Returns:
        符合 GAS v3.3 格式的完整資料字典
    """
    # 如果沒有傳入 statementdog_data，嘗試從 result 中讀取
    if statementdog_data is None:
        statementdog_data = result.get("statementdog")

    # 取得 close 用於計算 PE
    close = result.get("close")

    return {
        "market_data": build_market_data(result),
        "momentum": build_momentum(result),
        "pricing": build_pricing(result),
        "alpha_beta": build_alpha_beta(result),
        "lifecycle": build_lifecycle(result),
        "exit_signals": build_exit_signals(result),
        "statementdog": build_statementdog(statementdog_data, close=close),
    }
