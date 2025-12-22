"""FDR (False Discovery Rate) Control Result DTO"""

from typing import TypedDict


class FDRResultDTO(TypedDict):
    """FDR Control Result"""

    n_tested: int  # Number of tested hypotheses
    n_discoveries: int  # Number of discoveries (Reject H0)
    fdr_threshold: float  # FDR Threshold used
    adjusted_pvalues: list[float]  # Adjusted p-values
    significant_indices: list[int]  # Indices of significant results
