"""殘差動能計算器

對應 algorithms.md §2.1
三層階層式因子剝離計算殘差動能
"""

import numpy as np
from sklearn.linear_model import LinearRegression


def hierarchical_residual_momentum(
    tw_returns: np.ndarray,
    spy_returns: np.ndarray,
    sox_returns: np.ndarray,
    taiex_returns: np.ndarray,
    sector_returns: np.ndarray,
    window: int = 60,
) -> tuple[np.ndarray, dict]:
    """
    三層階層式因子剝離

    Step 1: 對 SPY(T-1) + SOX(T-1) 剝離 Global Beta
    Step 2: 對 0050(T) 剝離 Local Beta
    Step 3: 對產業指數(T) 剝離 Sector Beta

    Args:
        tw_returns: 台股標的日報酬
        spy_returns: SPY 日報酬 (T-1)
        sox_returns: SOX 日報酬 (T-1)
        taiex_returns: 台股大盤 (0050) 日報酬
        sector_returns: 產業指數日報酬
        window: Beta 估計視窗

    Returns:
        tuple: (殘差序列, betas dict)
    """
    n = min(
        len(tw_returns) - 1,
        len(spy_returns) - 1,
        len(sox_returns) - 1,
        len(taiex_returns) - 1,
        len(sector_returns) - 1,
    )

    if n < window:
        return np.array([]), {}

    # Align data (TW T corresponds to US T-1)
    y = tw_returns[1 : n + 1]
    X1 = np.column_stack([spy_returns[:n], sox_returns[:n]])
    X2 = taiex_returns[1 : n + 1].reshape(-1, 1)
    X3 = sector_returns[1 : n + 1].reshape(-1, 1)

    # Step 1: 剝離全球因子
    model1 = LinearRegression()
    model1.fit(X1[-window:], y[-window:])
    pred1 = model1.predict(X1)
    residual1 = y - pred1
    global_beta = model1.coef_.tolist()

    # Step 2: 剝離市場因子
    model2 = LinearRegression()
    model2.fit(X2[-window:], residual1[-window:])
    pred2 = model2.predict(X2)
    residual2 = residual1 - pred2
    local_beta = float(model2.coef_[0])

    # Step 3: 剝離產業因子
    model3 = LinearRegression()
    model3.fit(X3[-window:], residual2[-window:])
    pred3 = model3.predict(X3)
    final_residual = residual2 - pred3
    sector_beta = float(model3.coef_[0])

    betas = {
        "global_beta": global_beta,
        "local_beta": local_beta,
        "sector_beta": sector_beta,
    }

    return final_residual, betas


def oos_residual(y: np.ndarray, X: np.ndarray, window: int = 60) -> np.ndarray:
    """
    Out-of-Sample Residual Calculation (avoids look-ahead bias)

    Uses data from T-W to T-1 to estimate Beta, apply to day T

    Args:
        y: Target variable
        X: Explanatory variables
        window: Rolling window

    Returns:
        np.ndarray: OOS residual series
    """
    if len(y) <= window or len(X) <= window:
        return np.array([])

    residuals = np.zeros(len(y) - window)

    for t in range(window, len(y)):
        X_train = X[t - window : t]
        y_train = y[t - window : t]

        model = LinearRegression()
        model.fit(X_train, y_train)

        y_pred = model.predict(X[t : t + 1])
        residuals[t - window] = y[t] - y_pred[0]

    return residuals


def calculate_momentum_score(residuals: np.ndarray) -> float:
    """Calculate momentum score (Z-Score)

    Formula: mean(residuals) / σ(residuals)

    This is a standardized Z-Score, expected values in -3 to +3 range:
    - Buy zone: Z-Score between +0.5 and +1.5
    - Sell zone: Z-Score exceeds +2.5 or +3.0

    See methodology.md §4 (Ornstein-Uhlenbeck process pricing)
    """
    if len(residuals) == 0:
        return 0.0

    std = np.std(residuals)
    if std == 0:
        return 0.0

    return float(np.mean(residuals) / std)
