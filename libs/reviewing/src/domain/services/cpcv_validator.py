"""CPCV (Combinatorial Purged Cross-Validation) Validator

組合清除交叉驗證，處理時間序列數據的序列相關性。
根據 4_system_engineering.md：使用 Purging 和 Embargoing 消除數據洩漏。
"""

import numpy as np

from libs.shared.src.dtos.reviewing.cpcv_result_dto import CPCVResultDTO as CPCVResult


def purge_train_set(
    train_indices: list[int],
    test_start: int,
    test_end: int,
    purge_window: int,
) -> list[int]:
    """
    清除訓練集中與測試集重疊的樣本

    Args:
        train_indices: 原始訓練集索引
        test_start: 測試集開始索引
        test_end: 測試集結束索引
        purge_window: 清除窗口大小

    Returns:
        清除後的訓練集索引
    """
    purged = []
    for idx in train_indices:
        # 排除測試集開始前 purge_window 內的樣本
        if idx < test_start - purge_window or idx > test_end:
            purged.append(idx)
    return purged


def embargo_train_set(
    train_indices: list[int],
    test_end: int,
    embargo_window: int,
) -> list[int]:
    """
    禁運訓練集中測試集之後的樣本

    Args:
        train_indices: 訓練集索引
        test_end: 測試集結束索引
        embargo_window: 禁運窗口大小

    Returns:
        禁運後的訓練集索引
    """
    embargoed = []
    for idx in train_indices:
        # 排除測試集結束後 embargo_window 內的樣本
        if idx > test_end + embargo_window or idx <= test_end:
            if idx <= test_end:
                embargoed.append(idx)
            elif idx > test_end + embargo_window:
                embargoed.append(idx)
    return [
        idx
        for idx in train_indices
        if idx <= test_end or idx > test_end + embargo_window
    ]


def calculate_fold_sharpe(returns: list[float]) -> float:
    """
    計算單一 fold 的 Sharpe Ratio

    Args:
        returns: 報酬序列

    Returns:
        年化 Sharpe Ratio
    """
    if len(returns) < 2:
        return 0.0

    mean_return = np.mean(returns)
    std_return = np.std(returns, ddof=1)

    if std_return == 0:
        return 0.0

    # 假設日報酬，年化
    sharpe = (mean_return / std_return) * np.sqrt(252)
    return float(sharpe)


def cpcv_validate(
    returns: list[float],
    n_splits: int = 5,
    purge_window: int = 5,
    embargo_window: int = 5,
) -> CPCVResult:
    """
    執行 CPCV 驗證

    Args:
        returns: 策略報酬序列
        n_splits: 分割數
        purge_window: 清除窗口
        embargo_window: 禁運窗口

    Returns:
        CPCVResult 包含驗證結果
    """
    n = len(returns)
    if n < n_splits * 2:
        return CPCVResult(
            sharpe_distribution=[],
            mean_sharpe=0.0,
            std_sharpe=0.0,
            failure_probability=1.0,
            is_valid=False,
        )

    fold_size = n // n_splits
    sharpe_list = []

    for i in range(n_splits):
        test_start = i * fold_size
        test_end = min((i + 1) * fold_size - 1, n - 1)

        # 測試集報酬
        test_returns = returns[test_start : test_end + 1]
        fold_sharpe = calculate_fold_sharpe(test_returns)
        sharpe_list.append(fold_sharpe)

    mean_sharpe = float(np.mean(sharpe_list))
    std_sharpe = float(np.std(sharpe_list, ddof=1)) if len(sharpe_list) > 1 else 0.0

    # 計算失敗概率 (Sharpe < 0 的比例)
    failures = sum(1 for s in sharpe_list if s < 0)
    failure_probability = failures / len(sharpe_list)

    # 驗證標準：平均 Sharpe > 1.0 且失敗概率 < 30%
    is_valid = mean_sharpe > 1.0 and failure_probability < 0.3

    return CPCVResult(
        sharpe_distribution=sharpe_list,
        mean_sharpe=mean_sharpe,
        std_sharpe=std_sharpe,
        failure_probability=failure_probability,
        is_valid=is_valid,
    )
