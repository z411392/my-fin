"""殘差 RSI 計算器

計算殘差 RSI 並偵測背離
對應 diff.md §5.3 殘差 RSI 背離
"""

import numpy as np


def calculate_residual_rsi(
    cumulative_residuals: np.ndarray,
    period: int = 14,
) -> float:
    """
    計算殘差 RSI

    將 RSI 應用於累積殘差曲線，而非原始價格

    Args:
        cumulative_residuals: 累積殘差序列
        period: RSI 週期 (預設 14)

    Returns:
        float: 殘差 RSI (0-100)
    """
    if len(cumulative_residuals) < period + 1:
        return 50.0  # 預設中性值

    # 計算累積殘差的變化
    changes = np.diff(cumulative_residuals)

    if len(changes) < period:
        return 50.0

    # 取最近 period 天的變化
    recent_changes = changes[-period:]

    # 分離漲跌
    gains = np.where(recent_changes > 0, recent_changes, 0)
    losses = np.where(recent_changes < 0, -recent_changes, 0)

    # 計算平均漲跌
    avg_gain = np.mean(gains)
    avg_loss = np.mean(losses)

    # 計算 RSI
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(rsi)


def calculate_rsi_series(
    cumulative_residuals: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """
    計算殘差 RSI 時間序列

    Args:
        cumulative_residuals: 累積殘差序列
        period: RSI 週期

    Returns:
        np.ndarray: RSI 時間序列
    """
    if len(cumulative_residuals) < period + 2:
        return np.array([50.0])

    changes = np.diff(cumulative_residuals)
    rsi_series = []

    for i in range(period, len(changes) + 1):
        window = changes[i - period : i]
        gains = np.where(window > 0, window, 0)
        losses = np.where(window < 0, -window, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            rsi = 100.0
        elif avg_gain == 0:
            rsi = 0.0
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        rsi_series.append(rsi)

    return np.array(rsi_series)


def detect_rsi_divergence(
    prices: np.ndarray,
    residual_rsi: np.ndarray,
    lookback: int = 20,
) -> tuple[str, bool]:
    """
    偵測殘差 RSI 背離

    頂背離 (Bearish): 價格創新高，但殘差 RSI 未創新高
    底背離 (Bullish): 價格創新低，但殘差 RSI 未創新低

    Args:
        prices: 價格序列
        residual_rsi: 殘差 RSI 序列
        lookback: 回顧期 (預設 20)

    Returns:
        tuple: (背離類型, 是否應出場)
    """
    if len(prices) < lookback or len(residual_rsi) < lookback:
        return "none", False

    # 取最近 lookback 天
    recent_prices = prices[-lookback:]
    recent_rsi = residual_rsi[-lookback:]

    # 價格是否創新高 (最後一天是最高點)
    price_new_high = recent_prices[-1] >= np.max(recent_prices[:-1])

    # RSI 是否創新高
    rsi_new_high = recent_rsi[-1] >= np.max(recent_rsi[:-1])

    # 價格是否創新低
    price_new_low = recent_prices[-1] <= np.min(recent_prices[:-1])

    # RSI 是否創新低
    rsi_new_low = recent_rsi[-1] <= np.min(recent_rsi[:-1])

    # 頂背離: 價格新高但 RSI 未新高
    if price_new_high and not rsi_new_high:
        return "bearish", True

    # 底背離: 價格新低但 RSI 未新低
    if price_new_low and not rsi_new_low:
        return "bullish", False

    return "none", False


def check_stop_loss(
    current_price: float,
    monthly_high: float,
    threshold: float = 0.10,
) -> tuple[bool, float]:
    """
    檢查 10% 止損規則

    Args:
        current_price: 當前價格
        monthly_high: 月內最高價
        threshold: 止損閾值 (預設 10%)

    Returns:
        tuple: (是否觸發止損, 下跌幅度)
    """
    if monthly_high <= 0:
        return False, 0.0

    drawdown = (monthly_high - current_price) / monthly_high

    should_stop = drawdown >= threshold

    return should_stop, drawdown


def interpret_divergence(
    divergence_type: str,
    _should_exit: bool,
    rsi_value: float,
) -> str:
    """
    解讀背離狀態

    Args:
        divergence_type: 背離類型
        should_exit: 是否應出場
        rsi_value: 當前 RSI 值

    Returns:
        str: 人類可讀的解釋
    """
    if divergence_type == "bearish":
        return f"⚠️ 殘差 RSI 頂背離 | RSI: {rsi_value:.0f} | 建議獲利了結"
    elif divergence_type == "bullish":
        return f"🟢 殘差 RSI 底背離 | RSI: {rsi_value:.0f} | 可能反轉向上"
    else:
        if rsi_value >= 70:
            return f"🟡 殘差 RSI 偏高 | RSI: {rsi_value:.0f} | 短期可能回調"
        elif rsi_value <= 30:
            return f"🟡 殘差 RSI 偏低 | RSI: {rsi_value:.0f} | 短期可能反彈"
        else:
            return f"🟢 殘差 RSI 正常 | RSI: {rsi_value:.0f}"
