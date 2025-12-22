"""相關性過濾器

Alpha-Core V4.0: 高相關股票 (ρ > 0.8) 剔除分數較低者
"""

import numpy as np

from libs.shared.src.dtos.hunting.candidate_stock_dto import CandidateStockDTO


def filter_high_correlation(
    candidates: list[CandidateStockDTO],
    returns_data: dict[str, np.ndarray] | None = None,
    threshold: float = 0.8,
    lookback: int = 60,
) -> tuple[list[CandidateStockDTO], list[tuple[str, str, float]]]:
    """
    過濾高相關股票

    規則：若兩檔股票相關性 > threshold，剔除動能較低者

    Args:
        candidates: 候選股列表，需包含 symbol 和 momentum 欄位
        returns_data: 報酬資料 {symbol: returns_array}，若無則跳過過濾
        threshold: 相關性閾值 (預設 0.8)
        lookback: 計算相關性的回望期間

    Returns:
        tuple: (過濾後列表, 剔除的高相關對 [(symbol1, symbol2, corr)])
    """
    if not candidates or len(candidates) < 2:
        return candidates, []

    if returns_data is None:
        # 無報酬資料，無法計算相關性，直接返回
        return candidates, []

    # 按動能排序 (高到低)
    sorted_candidates = sorted(
        candidates, key=lambda x: x.get("momentum") or 0, reverse=True
    )

    # 追蹤已剔除的股票
    removed_symbols: set[str] = set()
    high_corr_pairs: list[tuple[str, str, float]] = []

    # 雙重迴圈檢查相關性
    for i, stock_a in enumerate(sorted_candidates):
        symbol_a = stock_a.get("symbol", "")
        if symbol_a in removed_symbols:
            continue

        returns_a = returns_data.get(symbol_a)
        if returns_a is None or len(returns_a) < lookback:
            continue

        for j in range(i + 1, len(sorted_candidates)):
            stock_b = sorted_candidates[j]
            symbol_b = stock_b.get("symbol", "")
            if symbol_b in removed_symbols:
                continue

            returns_b = returns_data.get(symbol_b)
            if returns_b is None or len(returns_b) < lookback:
                continue

            # 對齊長度
            min_len = min(len(returns_a), len(returns_b), lookback)
            a = returns_a[-min_len:]
            b = returns_b[-min_len:]

            # 計算相關性
            try:
                # 防止 stddev=0 導致 RuntimeWarning
                if np.std(a) < 1e-10 or np.std(b) < 1e-10:
                    continue
                corr = np.corrcoef(a, b)[0, 1]
                if np.isnan(corr):
                    continue

                if abs(corr) > threshold:
                    # 剔除動能較低者 (即 stock_b，因為已按動能排序)
                    removed_symbols.add(symbol_b)
                    high_corr_pairs.append((symbol_a, symbol_b, round(corr, 3)))
            except Exception:
                continue

    # 過濾結果
    filtered = [
        c for c in sorted_candidates if c.get("symbol", "") not in removed_symbols
    ]

    return filtered, high_corr_pairs


def calculate_pairwise_correlation(
    returns_a: np.ndarray,
    returns_b: np.ndarray,
) -> float | None:
    """
    計算兩個報酬序列的相關性

    Args:
        returns_a: 報酬序列 A
        returns_b: 報酬序列 B

    Returns:
        相關係數 (-1 到 1) 或 None (若無法計算)
    """
    if len(returns_a) < 10 or len(returns_b) < 10:
        return None

    min_len = min(len(returns_a), len(returns_b))
    a = returns_a[-min_len:]
    b = returns_b[-min_len:]

    try:
        # 防止 stddev=0 導致 RuntimeWarning
        if np.std(a) < 1e-10 or np.std(b) < 1e-10:
            return None
        corr = np.corrcoef(a, b)[0, 1]
        return float(corr) if not np.isnan(corr) else None
    except Exception:
        return None
