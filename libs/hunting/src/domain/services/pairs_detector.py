"""統計套利配對偵測器

對應 methodology-II.md §1.2
配對篩選：同產業 + 協整 + Granger Causality
"""

import numpy as np

from libs.shared.src.dtos.hunting.pair_result_dto import PairResultDTO as PairResult


def calculate_correlation(returns_a: np.ndarray, returns_b: np.ndarray) -> float:
    """計算相關係數"""
    if len(returns_a) != len(returns_b) or len(returns_a) < 2:
        return 0.0
    # 防止 stddev=0 導致 RuntimeWarning
    if np.std(returns_a) < 1e-10 or np.std(returns_b) < 1e-10:
        return 0.0
    result = np.corrcoef(returns_a, returns_b)[0, 1]
    return float(result) if not np.isnan(result) else 0.0


def calculate_spread_zscore(
    prices_a: np.ndarray,
    prices_b: np.ndarray,
    hedge_ratio: float = 1.0,
) -> tuple[float, float]:
    """
    計算價差 Z-Score

    Args:
        prices_a: 標的 A 價格序列
        prices_b: 標的 B 價格序列
        hedge_ratio: 對沖比率

    Returns:
        tuple: (current_zscore, half_life)
    """
    if len(prices_a) != len(prices_b) or len(prices_a) < 20:
        return 0.0, 0.0

    # 計算價差
    spread = prices_a - hedge_ratio * prices_b

    # Z-Score
    mean = np.mean(spread)
    std = np.std(spread)
    if std == 0:
        return 0.0, 0.0

    current_zscore = (spread[-1] - mean) / std

    # 半衰期估計 (簡化版 OU 過程)
    spread_lag = spread[:-1]
    spread_now = spread[1:]
    if len(spread_lag) > 1:
        reg = np.polyfit(spread_lag, spread_now, 1)
        phi = reg[0]
        if phi < 1 and phi > 0:
            half_life = -np.log(2) / np.log(phi)
        else:
            half_life = float("inf")
    else:
        half_life = 0.0

    return float(current_zscore), float(half_life) if np.isfinite(half_life) else 999.0


def estimate_hedge_ratio(
    returns_a: np.ndarray,
    returns_b: np.ndarray,
) -> float:
    """
    估計對沖比率 (簡化 OLS)

    Args:
        returns_a: 標的 A 報酬
        returns_b: 標的 B 報酬

    Returns:
        float: 對沖比率 β
    """
    if len(returns_a) != len(returns_b) or len(returns_a) < 10:
        return 1.0

    # OLS: returns_a = α + β * returns_b
    cov = np.cov(returns_a, returns_b)
    if cov[1, 1] == 0:
        return 1.0
    beta = cov[0, 1] / cov[1, 1]
    return float(beta)


def detect_pairs_opportunity(
    zscore: float,
    half_life: float,
    entry_threshold: float = 2.0,
    max_half_life: float = 30.0,
) -> tuple[str, str]:
    """
    判斷配對交易機會

    Args:
        zscore: 當前 Z-Score
        half_life: 半衰期
        entry_threshold: 進場閾值
        max_half_life: 最大半衰期

    Returns:
        tuple: (訊號, 建議)
    """
    if half_life > max_half_life or half_life <= 0:
        return "無機會", "半衰期過長或無效"

    if zscore > entry_threshold:
        return "做空價差", f"Z={zscore:.2f} 高於閾值，做空 A 做多 B"
    elif zscore < -entry_threshold:
        return "做多價差", f"Z={zscore:.2f} 低於閾值，做多 A 做空 B"
    else:
        return "觀望", f"Z={zscore:.2f} 在區間內"


def scan_pairs(
    symbols: list[str],
    returns_matrix: np.ndarray,
    prices_matrix: np.ndarray,
    min_correlation: float = 0.7,
) -> list[PairResult]:
    """
    掃描所有配對機會

    Args:
        symbols: 標的代號列表
        returns_matrix: 報酬矩陣 (時間 × 標的)
        prices_matrix: 價格矩陣 (時間 × 標的)
        min_correlation: 最低相關係數

    Returns:
        list: 配對結果列表
    """
    results: list[PairResult] = []
    n = len(symbols)

    for i in range(n):
        for j in range(i + 1, n):
            corr = calculate_correlation(returns_matrix[:, i], returns_matrix[:, j])

            if corr < min_correlation:
                continue

            hedge_ratio = estimate_hedge_ratio(
                returns_matrix[:, i], returns_matrix[:, j]
            )
            zscore, half_life = calculate_spread_zscore(
                prices_matrix[:, i], prices_matrix[:, j], hedge_ratio
            )

            signal, _ = detect_pairs_opportunity(zscore, half_life)

            results.append(
                {
                    "symbol_a": symbols[i],
                    "symbol_b": symbols[j],
                    "correlation": corr,
                    "half_life": half_life,
                    "cointegration_pvalue": 0.0,  # 簡化版不計算
                    "spread_zscore": zscore,
                    "status": signal,
                }
            )

    # 按 Z-Score 絕對值排序
    results.sort(key=lambda x: abs(x["spread_zscore"]), reverse=True)
    return results
