"""HRP Hierarchical Risk Parity Allocation

Alpha-Core V4.0: Replaces inverse volatility weighting
Uses hierarchical clustering + risk parity allocation
"""

import numpy as np
from scipy.cluster.hierarchy import linkage, leaves_list
from scipy.spatial.distance import squareform

from libs.shared.src.dtos.hunting.allocation_weights_dto import AllocationWeights


def hrp_allocate(
    returns_matrix: np.ndarray,
    symbols: list[str],
) -> AllocationWeights:
    """
    Hierarchical Risk Parity Allocation

    Steps:
    1. Calculate correlation matrix
    2. Hierarchical clustering
    3. Recursive risk parity allocation

    Args:
        returns_matrix: Return matrix (T x N), each column is a stock's return series
        symbols: Stock symbol list (length N)

    Returns:
        dict: {symbol: weight}, weights sum to 1
    """
    n_assets = len(symbols)

    if n_assets == 0:
        return {}

    if n_assets == 1:
        return {symbols[0]: 1.0}

    if returns_matrix.shape[1] != n_assets:
        raise ValueError(
            f"returns_matrix columns ({returns_matrix.shape[1]}) does not match symbols length ({n_assets})"
        )

    # 1. Calculate correlation matrix and covariance matrix
    cov_matrix = np.cov(returns_matrix, rowvar=False)

    # Handle single asset or NaN
    if np.isnan(cov_matrix).any():
        # Fallback: Equal weights
        return {s: 1.0 / n_assets for s in symbols}

    # Ensure covariance matrix is 2D
    if cov_matrix.ndim == 0:
        return {symbols[0]: 1.0}

    # Check if any asset has zero variance (causes corrcoef RuntimeWarning)
    variances = np.diag(cov_matrix)
    if np.any(variances < 1e-10):
        # Has constant return assets, fallback to equal weights
        return {s: 1.0 / n_assets for s in symbols}

    corr_matrix = np.corrcoef(returns_matrix, rowvar=False)

    # Handle NaN from corrcoef (when stddev=0)
    if np.isnan(corr_matrix).any():
        return {s: 1.0 / n_assets for s in symbols}

    # 2. Convert correlation matrix to distance matrix (distance = sqrt(0.5 * (1 - corr)))
    dist_matrix = np.sqrt(0.5 * (1 - corr_matrix))
    np.fill_diagonal(dist_matrix, 0)

    # 3. Hierarchical clustering
    try:
        dist_condensed = squareform(dist_matrix, checks=False)
        link = linkage(dist_condensed, method="single")
        sort_ix = leaves_list(link)
    except Exception:
        # Fallback: Original order
        sort_ix = list(range(n_assets))

    # 4. Recursive risk parity
    weights = _recursive_bisection(cov_matrix, sort_ix)

    # 5. Map to symbols
    result = {}
    for i, w in enumerate(weights):
        result[symbols[i]] = round(w, 4)

    return result


def _recursive_bisection(
    cov_matrix: np.ndarray,
    sort_ix: list[int] | np.ndarray,
) -> np.ndarray:
    """
    Recursive bisection + risk parity

    Args:
        cov_matrix: Covariance matrix
        sort_ix: Sorted indices

    Returns:
        Weight array
    """
    n = len(sort_ix)
    weights = np.ones(n)

    # Recursive bisection
    clusters = [list(sort_ix)]

    while len(clusters) > 0:
        clusters_new = []
        for cluster in clusters:
            if len(cluster) <= 1:
                continue

            # Bisect
            mid = len(cluster) // 2
            left = cluster[:mid]
            right = cluster[mid:]

            # Calculate variance of each sub-cluster
            var_left = _cluster_variance(cov_matrix, left)
            var_right = _cluster_variance(cov_matrix, right)

            # Risk parity weights
            total_var = var_left + var_right
            if total_var > 0:
                alpha = 1 - var_left / total_var
            else:
                alpha = 0.5

            # Update weights
            for i in left:
                weights[i] *= alpha
            for i in right:
                weights[i] *= 1 - alpha

            # Add to next round
            if len(left) > 1:
                clusters_new.append(left)
            if len(right) > 1:
                clusters_new.append(right)

        clusters = clusters_new

    # Normalize
    total = weights.sum()
    if total > 0:
        weights /= total

    return weights


def _cluster_variance(cov_matrix: np.ndarray, indices: list[int]) -> float:
    """Calculate sub-cluster variance (equal weight assumption)"""
    if len(indices) == 0:
        return 0.0

    if len(indices) == 1:
        return cov_matrix[indices[0], indices[0]]

    # Portfolio variance with equal weights
    sub_cov = cov_matrix[np.ix_(indices, indices)]
    n = len(indices)
    weights = np.ones(n) / n
    return float(weights @ sub_cov @ weights)


def inverse_volatility_weights(
    returns_matrix: np.ndarray,
    symbols: list[str],
) -> AllocationWeights:
    """
    Inverse volatility weighting (traditional method, as backup)

    Args:
        returns_matrix: Return matrix (T x N)
        symbols: Stock symbol list

    Returns:
        dict: {symbol: weight}
    """
    n_assets = len(symbols)

    if n_assets == 0:
        return {}

    if n_assets == 1:
        return {symbols[0]: 1.0}

    # Calculate volatility of each asset
    vols = np.std(returns_matrix, axis=0, ddof=1)

    # Avoid division by zero
    vols = np.where(vols == 0, 0.01, vols)

    # Inverse volatility
    inv_vols = 1.0 / vols

    # Normalize
    weights = inv_vols / inv_vols.sum()

    return {s: round(w, 4) for s, w in zip(symbols, weights)}
