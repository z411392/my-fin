"""Catalog Data DTO

Stock catalog raw data structure (loaded from JSON)
"""

from typing import TypedDict, Any


class CatalogDataDTO(TypedDict, total=False):
    """Stock catalog data (Internal Use)

    Raw structure loaded from catalog.json
    """

    tw: dict[str, list[dict[str, Any]]]
    """Taiwan Stock Data"""

    us: dict[str, list[dict[str, Any]]]
    """US Stock Data"""

    industry_to_etf: dict[str, str]
    """Industry to ETF Mapping"""

    tw_sector_proxies: dict[str, list[str]]
    """Taiwan Sector Proxy Stocks"""
