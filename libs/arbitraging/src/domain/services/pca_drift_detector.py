"""PCA Structural Drift Detector

Corresponds to algorithms.md §1.3.3
Compares cosine similarity of PCA loading vectors between two periods
"""

import numpy as np
from sklearn.decomposition import PCA


def calculate_pca_cosine_similarity(
    returns_old: np.ndarray,
    returns_new: np.ndarray,
    n_components: int = 3,
) -> float:
    """
    Calculate cosine similarity of PCA loading vectors between two periods

    S < 0.8: Structural break warning

    Args:
        returns_old: Old period return matrix (samples × assets)
        returns_new: New period return matrix (samples × assets)
        n_components: Number of PCA components

    Returns:
        float: Cosine similarity (0-1)
    """
    if returns_old.shape[1] != returns_new.shape[1]:
        return 0.0

    if returns_old.shape[0] < n_components or returns_new.shape[0] < n_components:
        return 1.0  # Insufficient data, assume no structural change

    try:
        pca_old = PCA(n_components=n_components)
        pca_new = PCA(n_components=n_components)

        pca_old.fit(returns_old)
        pca_new.fit(returns_new)

        # Compare first principal component
        v1 = pca_old.components_[0]
        v2 = pca_new.components_[0]

        # Cosine similarity
        cosine = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        return abs(float(cosine))

    except Exception:
        return 1.0


def detect_structural_break(cosine_similarity: float, threshold: float = 0.8) -> bool:
    """Detect if structural break occurred"""
    return cosine_similarity < threshold
