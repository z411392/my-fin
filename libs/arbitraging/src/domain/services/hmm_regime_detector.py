"""HMM Regime Detector

Corresponds to algorithms.md §1.3.2
HMM 2-state Regime Identification (Simplified Version)
"""

import numpy as np


def hmm_regime_simple(
    returns: np.ndarray,
    lookback: int = 60,
    vol_threshold: float = 1.5,
) -> tuple[int, float]:
    """
    Simplified HMM Regime Identification

    Determines regime based on volatility changes, no hmmlearn dependency

    State 0: Low volatility (usually bull market)
    State 1: High volatility (usually bear market)

    Args:
        returns: Return series
        lookback: Lookback period
        vol_threshold: Volatility threshold multiplier

    Returns:
        tuple: (current_state, bull_probability)
    """
    if len(returns) < lookback:
        return 0, 0.5

    recent_returns = returns[-lookback:]

    # Calculate recent volatility
    recent_vol = np.std(recent_returns)

    # Calculate long-term volatility (if enough data)
    if len(returns) >= lookback * 2:
        long_term_vol = np.std(returns[-lookback * 2 : -lookback])
    else:
        long_term_vol = recent_vol

    # Determine regime
    vol_ratio = recent_vol / (long_term_vol + 1e-8)

    if vol_ratio > vol_threshold:
        # High volatility regime
        current_state = 1
        bull_prob = 0.3
    elif vol_ratio < 1 / vol_threshold:
        # Low volatility regime
        current_state = 0
        bull_prob = 0.8
    else:
        # Intermediate state
        current_state = 0
        bull_prob = 0.5 + (1 - vol_ratio) * 0.3

    # Adjust based on return direction
    recent_return = np.mean(recent_returns)
    if recent_return > 0:
        bull_prob = min(1.0, bull_prob + 0.1)
    else:
        bull_prob = max(0.0, bull_prob - 0.1)

    return current_state, float(bull_prob)


def interpret_hmm_regime(state: int, bull_prob: float) -> tuple[str, str]:
    """Interpret HMM regime"""
    if bull_prob > 0.7:
        return "Bull Market", "Residual momentum strategy"
    elif bull_prob > 0.5:
        return "Neutral Bullish", "Standard allocation"
    elif bull_prob > 0.3:
        return "Neutral Bearish", "Reduce and observe"
    else:
        return "Bear Market", "Defensive strategy"


def combine_regime_signals(
    hurst: float,
    hmm_bull_prob: float,
    pca_cosine: float,
) -> tuple[str, float]:
    """
    Combine regime signals

    Args:
        hurst: Hurst exponent
        hmm_bull_prob: HMM bull probability
        pca_cosine: PCA cosine similarity

    Returns:
        tuple: (regime determination, Kelly factor)
    """
    # Structural break takes priority
    if pca_cosine < 0.8:
        return "Structural Break", 0.0

    # Combine three indicators
    if hurst > 0.55 and hmm_bull_prob > 0.7:
        return "Trending Bull", 0.5
    elif hurst < 0.45:
        return "Range-bound", 0.25
    elif hmm_bull_prob < 0.3:
        return "Panic Bear", 0.0
    else:
        return "Neutral", 0.25
