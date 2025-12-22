"""FDR (False Discovery Rate) Controller

Benjamini-Hochberg FDR 控制，用於多重測試調整。
根據 4_system_engineering.md：在測試數千個策略時控制偽陽性。
"""

from libs.shared.src.dtos.reviewing.fdr_result_dto import FDRResultDTO as FDRResult


def benjamini_hochberg(
    pvalues: list[float],
    alpha: float = 0.05,
) -> list[int]:
    """
    Benjamini-Hochberg FDR 控制

    Args:
        pvalues: P 值列表
        alpha: FDR 控制水準 (預設 0.05)

    Returns:
        顯著結果的索引列表
    """
    if len(pvalues) == 0:
        return []

    m = len(pvalues)

    # 排序 p-values 並保留原始索引
    indexed_pvalues = [(p, i) for i, p in enumerate(pvalues)]
    indexed_pvalues.sort(key=lambda x: x[0])

    # 找到最大的 k 使得 p_(k) <= k/m * alpha
    max_k = 0
    for k, (p, _) in enumerate(indexed_pvalues, 1):
        threshold = (k / m) * alpha
        if p <= threshold:
            max_k = k

    # 返回前 max_k 個顯著結果的原始索引
    significant_indices = [indexed_pvalues[i][1] for i in range(max_k)]
    return sorted(significant_indices)


def adjust_pvalues_bh(pvalues: list[float]) -> list[float]:
    """
    計算 Benjamini-Hochberg 調整後的 p-values

    Args:
        pvalues: 原始 P 值列表

    Returns:
        調整後的 P 值列表 (與原始順序對應)
    """
    if len(pvalues) == 0:
        return []

    m = len(pvalues)

    # 排序 p-values 並保留原始索引
    indexed_pvalues = [(p, i) for i, p in enumerate(pvalues)]
    indexed_pvalues.sort(key=lambda x: x[0])

    # 計算調整後的 p-values
    adjusted = [0.0] * m
    cummin = float("inf")

    for k in range(m - 1, -1, -1):
        p, original_idx = indexed_pvalues[k]
        rank = k + 1
        adjusted_p = (m / rank) * p
        cummin = min(cummin, adjusted_p)
        adjusted[original_idx] = min(cummin, 1.0)

    return adjusted


def control_fdr(
    pvalues: list[float],
    alpha: float = 0.05,
) -> FDRResult:
    """
    完整 FDR 控制流程

    Args:
        pvalues: P 值列表
        alpha: FDR 控制水準

    Returns:
        FDRResult 包含完整結果
    """
    significant_indices = benjamini_hochberg(pvalues, alpha)
    adjusted_pvalues = adjust_pvalues_bh(pvalues)

    return FDRResult(
        n_tested=len(pvalues),
        n_discoveries=len(significant_indices),
        fdr_threshold=alpha,
        adjusted_pvalues=adjusted_pvalues,
        significant_indices=significant_indices,
    )


def filter_strategies(
    strategy_pvalues: dict[str, float],
    alpha: float = 0.05,
) -> list[str]:
    """
    根據 FDR 控制過濾策略

    Args:
        strategy_pvalues: 策略名稱 -> P 值 的字典
        alpha: FDR 控制水準

    Returns:
        通過 FDR 控制的策略名稱列表
    """
    if len(strategy_pvalues) == 0:
        return []

    names = list(strategy_pvalues.keys())
    pvalues = [strategy_pvalues[name] for name in names]

    significant_indices = benjamini_hochberg(pvalues, alpha)
    return [names[i] for i in significant_indices]
