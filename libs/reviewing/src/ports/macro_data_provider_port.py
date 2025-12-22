"""宏觀數據提供者 Port"""

from typing import Protocol


class MacroDataProviderPort(Protocol):
    """宏觀數據提供者介面"""

    def get_vix(self) -> float:
        """取得 VIX 指數"""
        ...

    def get_fed_balance_sheet_trend(self) -> str:
        """取得 Fed 資產負債表趨勢 (EXPANDING | CONTRACTING)"""
        ...

    def get_m2_yoy(self) -> float:
        """取得 M2 年增率"""
        ...
