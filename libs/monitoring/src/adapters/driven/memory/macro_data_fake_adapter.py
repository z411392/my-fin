from libs.monitoring.src.ports.macro_data_provider_port import MacroDataProviderPort

"""MacroData Fake Adapter

用於測試時提供 Fake 宏觀數據
"""


class MacroDataFakeAdapter(MacroDataProviderPort):
    """宏觀數據 Fake Adapter"""

    def __init__(self):
        self._vix = 15.0
        self._m2_yoy = 5.0
        self._fed_trend = "EXPANDING"

    def set_vix(self, vix: float) -> None:
        self._vix = vix

    def set_m2_yoy(self, m2_yoy: float) -> None:
        self._m2_yoy = m2_yoy

    def set_fed_balance_sheet_trend(self, trend: str) -> None:
        self._fed_trend = trend

    def get_vix(self) -> float:
        return self._vix

    def get_m2_yoy(self) -> float:
        return self._m2_yoy

    def get_fed_balance_sheet_trend(self) -> str:
        return self._fed_trend
