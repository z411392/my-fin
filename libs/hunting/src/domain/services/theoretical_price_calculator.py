"""理論價格計算器

對應 diff.md §1.2 理論價格推導公式
根據動能強度與波動率計算統計理論目標價

包含三種模型：
1. Alpha Decay Projection (基於衰減的預期價格)
2. Ornstein-Uhlenbeck Bands (基於均值回歸的統計邊界)
3. LPPL Critical Time (泡沫崩潰預測啟發式)
"""

import math
import numpy as np

from libs.shared.src.dtos.hunting.ou_bounds_dto import OuBoundsDTO
from libs.shared.src.dtos.hunting.lppl_result_dto import LpplResultDTO
from libs.shared.src.dtos.hunting.pricing_result_dto import PricingResultDTO


def calculate_theoretical_price(
    current_price: float,
    momentum_zscore: float,
    daily_volatility: float,
    holding_period: int = 16,
) -> tuple[float, float]:
    """
    計算基礎理論價格 (Legacy/Simple Model)
    (保留用於向後兼容)

    Args:
        current_price: 當前價格 (P₀)
        momentum_zscore: 殘差動能 Z-Score
        daily_volatility: 日波動率
        holding_period: 預期持有期 (天數)

    Returns:
        tuple: (理論目標價, 預期漲幅)
    """
    if current_price <= 0 or daily_volatility <= 0:
        return current_price, 0.0

    expected_move = momentum_zscore * daily_volatility * math.sqrt(holding_period)
    target_price = current_price * (1 + expected_move)

    if target_price <= 0:
        target_price = current_price * 0.01

    return target_price, expected_move


def calculate_alpha_decay_price(
    current_price: float,
    alpha_resid_annual: float,
    beta_market: float,
    market_expected_return: float,
    decay_rate_lambda: float = 0.5,
    holding_period_months: float = 3.0,
) -> PricingResultDTO:
    """
    模型一：基於阿爾法衰減的預期價格投影

    公式: P_target = P_t * (1 + β* Rm)^H * exp(∫ α / (1 + λτ) dτ)

    Args:
        current_price: 當前價格
        alpha_resid_annual: 年化殘差 Alpha (例如 0.20 = 20%)
        beta_market: 市場 Beta
        market_expected_return: 市場預期年化回報 (例如 0.08 = 8%)
        decay_rate_lambda: 衰減參數 (0.5 為標準值)
        holding_period_months: 持有期 (月)

    Returns:
        PricingResult: 定價結果
    """
    if current_price <= 0:
        return {
            "target_price": 0.0,
            "expected_move_pct": 0.0,
            "model_type": "alpha_decay",
            "confidence": 0.0,
            "details": {},
        }

    # 時間轉換為年
    h_years = holding_period_months / 12.0

    # 1. 系統性回報部分 (Systematic Return)
    systematic_return = (1 + beta_market * market_expected_return) ** h_years

    # 2. 殘差 Alpha 貢獻 (Residual Alpha Contribution)
    # 積分 ∫(α / (1 + λτ)) dτ = (α / λ) * ln(1 + λH)
    if decay_rate_lambda > 0.001:
        integral_alpha = (alpha_resid_annual / decay_rate_lambda) * math.log(
            1 + decay_rate_lambda * h_years
        )
    else:
        integral_alpha = alpha_resid_annual * h_years

    residual_contribution = math.exp(integral_alpha)

    # 總目標價
    target_price = current_price * systematic_return * residual_contribution
    expected_move = (target_price - current_price) / current_price

    return {
        "target_price": target_price,
        "expected_move_pct": expected_move,
        "model_type": "alpha_decay",
        "confidence": 0.8,
        "details": {
            "systematic_component": systematic_return,
            "residual_component": residual_contribution,
            "decay_lambda": decay_rate_lambda,
        },
    }


def calculate_ou_bounds(
    current_price: float,
    fair_price_model: float,
    residual_std: float,
    current_residual: float,
    mean_reversion_level: float = 0.0,
) -> OuBoundsDTO:
    """
    模型二：Ornstein-Uhlenbeck 均值回歸帶

    計算買入與賣出的統計邊界
    P_buy/sell ≈ P_model + (μ ± kσ) (這裡以價格偏差形式近似)

    Args:
        current_price: 當前價格
        fair_price_model: 因子模型隱含價格 (或移動平均價格)
        residual_std: 殘差標準差 (價格單位 或 % * P)
        current_residual: 當前殘差值 (價格單位)
        mean_reversion_level: 均值回歸水平 (殘差均值，通常為 0)

    Returns:
        dict: 各個邊界的價格
    """
    # 假設輸入的 residual_std 已經轉換為價格單位
    # 如果 residual_std 是報酬率標準差，應傳入 (std_pct * current_price)

    # 定義 Z-Score 閾值 (參考 methodology.md §3.2)
    k_entry_lower = 0.5
    k_entry_upper = 1.5
    k_exit_high = 2.5
    k_exit_extreme = 3.0

    base = fair_price_model + mean_reversion_level

    return {
        "buy_lower": base + k_entry_lower * residual_std,
        "buy_upper": base + k_entry_upper * residual_std,
        "sell_high": base + k_exit_high * residual_std,
        "sell_extreme": base + k_exit_extreme * residual_std,
        "current_deviation_z": (current_residual - mean_reversion_level) / residual_std
        if residual_std > 0
        else 0,
    }


def calculate_ou_mean_reversion_speed(half_life: float | None) -> float | None:
    """計算 OU 均值回歸速度 (P2)

    θ = ln(2) / half_life
    θ 越大表示回歸速度越快

    Args:
        half_life: 半衰期 (天數)

    Returns:
        均值回歸速度參數 θ
    """
    if half_life is None or half_life <= 0:
        return None

    return round(math.log(2) / half_life, 6)


def estimate_lppl_critical_time(
    prices: np.ndarray, log_prices: bool = True
) -> LpplResultDTO:
    """
    模型三：LPPL 臨界時間估計 (Simplified Heuristic)

    檢測是否存在超指數增長 (Super-exponential growth)
    這是一個簡化的啟發式檢測，非完整 LPPL 擬合 (避免 scipy.optimize 依賴)

    原理：檢查對數價格的加速度是否顯著為正 (凸性)

    Args:
        prices: 價格序列
        log_prices: 是否使用對數價格

    Returns:
        dict: 檢測結果
    """
    if len(prices) < 20:
        return {"is_bubble": 0.0, "critical_time_days": -1.0}

    p = np.log(prices) if log_prices else prices

    # 計算一階差分 (速度)
    velocity = np.diff(p)
    # 計算二階差分 (加速度)
    acceleration = np.diff(velocity)

    # 簡單指標：加速度是否持續為正？
    # 取最近 20 天的一階與二階趨勢
    recent_acc = np.mean(acceleration[-10:])
    recent_vel = np.mean(velocity[-10:])

    # 泡泡特徵：價格上漲 (vel > 0) 且 加速上漲 (acc > 0)
    is_super_exponential = (recent_vel > 0) and (recent_acc > 0)

    # 振盪頻率檢測 (簡單版)：變號次數
    # LPPL 特徵是振盪頻率隨時間增加
    # 這裡僅作簡單標記

    return {
        "is_bubble": 1.0 if is_super_exponential else 0.0,
        "acceleration": float(recent_acc),
        "velocity": float(recent_vel),
    }


def calculate_supply_chain_target(
    tw_prev_close: float,
    tw_open: float,
    us_return: float,
    kalman_beta: float,
) -> tuple[float, float]:
    """
    計算供應鏈傳導的理論目標價 (Legacy)
    Target_TW = P_TW,open + β × R_US × P_TW,close,-1
    """
    if tw_prev_close <= 0:
        return tw_open, 0.0

    expected_transmission = kalman_beta * us_return * tw_prev_close
    target_price = tw_open + expected_transmission

    return target_price, expected_transmission


def calculate_remaining_alpha(
    target_price: float,
    current_price: float,
    expected_move: float,
) -> tuple[float, str]:
    """
    計算剩餘 Alpha 比例 (Legacy)
    """
    if current_price <= 0:
        return 0.0, "ABORT"

    if expected_move <= 0:
        return 0.0, "ABORT"

    remaining_pct = (target_price - current_price) / current_price

    if remaining_pct <= 0:
        return 0.0, "ABORT"

    if remaining_pct >= 0.03:
        signal = "EXECUTE"
    elif remaining_pct >= 0.01:
        signal = "REDUCE"
    else:
        signal = "ABORT"

    return remaining_pct, signal


def interpret_remaining_alpha(remaining: float, signal: str) -> str:
    """人類可讀解釋"""
    pct = remaining * 100
    interpretations = {
        "EXECUTE": f"✅ 剩餘肉量 {pct:.0f}%，可執行交易",
        "REDUCE": f"⚠️ 剩餘肉量 {pct:.0f}%，建議縮減部位 50%",
        "ABORT": f"❌ 剩餘肉量 {pct:.0f}%，放棄交易（魚尾巴留給別人）",
    }
    return interpretations.get(signal, f"未知訊號：{signal}")
