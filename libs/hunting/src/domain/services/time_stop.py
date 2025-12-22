"""時間止損機制

Alpha-Core V4.0: 3D 出場機制 — Time Stop
持有 N 日後若 Alpha ≤ 0 → 強制平倉
"""


def should_exit_by_time(
    holding_days: int,
    alpha_contribution: float,
    threshold_days: int = 10,
) -> tuple[bool, str]:
    """
    判斷是否觸發時間止損

    規則：
    - 持有超過 threshold_days 且 Alpha ≤ 0 → 強制平倉
    - 持有超過 2 × threshold_days → 無論 Alpha 強制平倉

    Args:
        holding_days: 已持有天數
        alpha_contribution: Alpha 貢獻 (正值=有效，負值=無效)
        threshold_days: 時間門檻 (預設 10 日)

    Returns:
        tuple: (是否應出場, 原因說明)
    """
    # 強制平倉：持有過久
    if holding_days >= threshold_days * 2:
        return (
            True,
            f"⏰ 強制平倉：持有 {holding_days} 日 > {threshold_days * 2} 日上限",
        )

    # 時間止損：Alpha 無效
    if holding_days >= threshold_days and alpha_contribution <= 0:
        return (
            True,
            f"⏰ 時間止損：持有 {holding_days} 日，Alpha = {alpha_contribution:.2%}",
        )

    # 繼續持有
    remaining = threshold_days - holding_days
    if remaining > 0:
        return False, f"✅ 持有中 ({holding_days}/{threshold_days} 日)"
    else:
        return False, f"⚠️ 觀察期 (Alpha = {alpha_contribution:.2%})"


def calculate_alpha_contribution(
    entry_price: float,
    current_price: float,
    benchmark_return: float,
) -> float:
    """
    計算持倉的 Alpha 貢獻

    Alpha = 實際報酬 - 基準報酬

    Args:
        entry_price: 進場價格
        current_price: 當前價格
        benchmark_return: 同期基準報酬 (如 0050 或 SPY)

    Returns:
        Alpha 貢獻 (正值=優於基準)
    """
    if entry_price <= 0:
        return 0.0

    actual_return = (current_price - entry_price) / entry_price
    return actual_return - benchmark_return
