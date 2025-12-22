"""VPIN Calculator

Corresponds to algorithms.md §1.5
Volume-Synchronized Probability of Informed Trading
"""

import numpy as np
import pandas as pd

from libs.shared.src.enums.vpin_level import VPINLevel
from libs.shared.src.constants.vpin_thresholds import (
    VPIN_ELEVATED,
    VPIN_HIGH,
    VPIN_WARNING,
    VPIN_DEFCON2_TRIGGER,
)


def calculate_vpin(
    trades: pd.DataFrame,
    bucket_size: int = 50,
    lookback_buckets: int = 50,
) -> float:
    """
    Calculate VPIN using Bulk Classification method

    Args:
        trades: Trade data DataFrame, must contain 'volume' and 'price_change' columns
        bucket_size: Volume per bucket
        lookback_buckets: Number of buckets to look back for VPIN calculation

    Returns:
        float: VPIN value (0-1)
    """
    if trades.empty or "volume" not in trades.columns:
        return 0.0

    # Infer buy/sell direction (Bulk Classification)
    if "price_change" in trades.columns:
        signed_volume = trades["volume"] * np.sign(trades["price_change"])
    else:
        signed_volume = trades["volume"]

    # Calculate total volume
    total_volume = trades["volume"].sum()
    if total_volume == 0:
        return 0.0

    n_buckets = int(total_volume / bucket_size)
    if n_buckets < 2:
        return 0.0

    imbalances = []
    cumulative_volume = 0
    bucket_buy = 0
    bucket_sell = 0

    for _, row in trades.iterrows():
        vol = row["volume"]
        signed = signed_volume.loc[row.name] if row.name in signed_volume.index else vol

        if signed > 0:
            bucket_buy += abs(vol)
        else:
            bucket_sell += abs(vol)

        cumulative_volume += vol

        if cumulative_volume >= bucket_size:
            total_bucket = bucket_buy + bucket_sell
            if total_bucket > 0:
                imbalance = abs(bucket_buy - bucket_sell) / total_bucket
                imbalances.append(imbalance)

            bucket_buy = 0
            bucket_sell = 0
            cumulative_volume = 0

    if not imbalances:
        return 0.0

    # Take average of most recent N buckets
    recent_imbalances = imbalances[-lookback_buckets:]
    return float(np.mean(recent_imbalances))


def classify_vpin(vpin: float) -> tuple[VPINLevel, str]:
    """Classify based on VPIN percentile"""

    if vpin >= VPIN_DEFCON2_TRIGGER:
        return VPINLevel.CRITICAL, "Defensive mode (DEFCON 2)"
    elif vpin >= VPIN_WARNING:
        return VPINLevel.CRITICAL, "Halt trading (Warning)"
    elif vpin >= VPIN_HIGH:
        return VPINLevel.HIGH, "Reduce position size"
    elif vpin >= VPIN_ELEVATED:
        return VPINLevel.ELEVATED, "Monitor liquidity"
    else:
        return VPINLevel.NORMAL, "Normal trading"
