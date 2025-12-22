"""板塊限額過濾器

Alpha-Core V4.0: 軟性板塊限額 ≤ 30%
"""

from libs.shared.src.dtos.hunting.candidate_stock_dto import CandidateStockDTO
from libs.shared.src.dtos.hunting.sector_exposure_dto import SectorExposure


def apply_sector_cap(
    candidates: list[CandidateStockDTO],
    cap_pct: float = 0.30,
    sector_key: str = "sector",
) -> tuple[list[CandidateStockDTO], dict[str, int]]:
    """
    應用板塊限額過濾

    規則：同一板塊的候選股不得超過總數的 cap_pct
    超額時，剔除該板塊中動能分數較低者

    Args:
        candidates: 候選股列表，需包含 sector 和 momentum 欄位
        cap_pct: 板塊上限百分比 (預設 30%)
        sector_key: 板塊欄位名稱

    Returns:
        tuple: (過濾後列表, 板塊統計 {sector: count})
    """
    if not candidates:
        return [], {}

    # 統計各板塊數量
    sector_counts: dict[str, list[CandidateStockDTO]] = {}
    for c in candidates:
        sector = c.get(sector_key) or "Unknown"
        if sector not in sector_counts:
            sector_counts[sector] = []
        sector_counts[sector].append(c)

    # 計算每個板塊的上限
    total = len(candidates)
    max_per_sector = max(1, int(total * cap_pct))

    # 過濾：保留每個板塊中動能最高的 N 檔
    filtered = []
    sector_stats = {}

    for sector, stocks in sector_counts.items():
        # 按動能排序 (高到低)
        sorted_stocks = sorted(
            stocks, key=lambda x: x.get("momentum") or 0, reverse=True
        )
        # 保留前 N 檔
        kept = sorted_stocks[:max_per_sector]
        filtered.extend(kept)
        sector_stats[sector] = len(kept)

    # 按原始動能重新排序
    filtered.sort(key=lambda x: x.get("momentum") or 0, reverse=True)

    return filtered, sector_stats


def get_sector_exposure(
    candidates: list[CandidateStockDTO],
    sector_key: str = "sector",
) -> SectorExposure:
    """
    計算各板塊曝險百分比

    Args:
        candidates: 候選股列表
        sector_key: 板塊欄位名稱

    Returns:
        dict: {sector: percentage}
    """
    if not candidates:
        return {}

    total = len(candidates)
    sector_counts: dict[str, int] = {}

    for c in candidates:
        sector = c.get(sector_key) or "Unknown"
        sector_counts[sector] = sector_counts.get(sector, 0) + 1

    return {
        sector: round(count / total * 100, 1) for sector, count in sector_counts.items()
    }
