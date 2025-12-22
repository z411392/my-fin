"""執行每小時掃描 Command"""

import logging

from injector import inject
from datetime import datetime
from libs.monitoring.src.domain.services.defcon_calculator import calculate_defcon_level
from libs.monitoring.src.domain.services.vix_tier_calculator import calculate_vix_tier
from libs.monitoring.src.ports.run_hourly_scan_port import RunHourlyScanPort
from libs.monitoring.src.ports.market_data_provider_port import (
    MarketDataProviderPort,
)
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.monitoring.src.ports.gex_calculator_port import GEXCalculatorPort
from libs.shared.src.dtos.event.alert_dto import AlertDTO
from libs.shared.src.dtos.reviewing.scan_result_dto import HourlyScanResultDTO


class RunHourlyScanCommand(RunHourlyScanPort):
    """每小時掃描

    掃描風險與機會觸發條件
    """

    @inject
    def __init__(
        self,
        market_data_adapter: MarketDataProviderPort,
        vpin_adapter: VPINCalculatorPort,
        gex_adapter: GEXCalculatorPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._market_data_adapter = market_data_adapter
        self._vpin_adapter = vpin_adapter
        self._gex_adapter = gex_adapter

    def execute(self) -> HourlyScanResultDTO:
        """執行完整的每小時掃描流程

        Returns:
            HourlyScanResultDTO: 掃描結果
        """

        # 從真實 API 取得 VIX
        try:
            vix = float(self._market_data_adapter.get_vix())
        except Exception:
            vix = 18.5  # 降級到保守值

        # 從真實 Adapter 取得 VPIN
        try:
            vpin_result = self._vpin_adapter.calculate("SPY")
            vpin = vpin_result.get("vpin", 0.3)
        except Exception:
            vpin = 0.3

        # 從真實 Adapter 取得 GEX
        try:
            gex_result = self._gex_adapter.calculate("SPY")
            gex = gex_result.get("gex", 0.0)
        except Exception:
            gex = 0.0

        # 計算 DEFCON
        defcon_level, defcon_emoji, _defcon_action = calculate_defcon_level(
            vix=vix,
            hmm_state=0,  # 待整合 HMM
            vpin=vpin,
            gli_z=0.5,  # 待整合 FRED
            gex=gex,
        )
        vix_tier, _vix_emoji, _vix_action = calculate_vix_tier(vix)

        # 生成警報
        alerts = self._generate_alerts(vix, vpin, defcon_level.value)

        return {
            "timestamp": datetime.now().isoformat(),
            "vix": vix,
            "vpin": vpin,
            "gex": gex,
            "defcon_level": defcon_level.value,
            "defcon_emoji": defcon_emoji,
            "vix_tier": vix_tier.name,
            "alerts": alerts,
            "notifications_sent": len([a for a in alerts if a["severity"] == "HIGH"]),
        }

    def _generate_alerts(self, vix: float, vpin: float, defcon: int) -> list[AlertDTO]:
        """生成警報"""
        alerts = []

        if vix > 25:
            alerts.append(
                {
                    "type": "VIX_HIGH",
                    "message": f"VIX 超過 25: {vix}",
                    "severity": "HIGH",
                }
            )

        if vpin > 0.9:
            alerts.append(
                {
                    "type": "VPIN_HIGH",
                    "message": f"VPIN 超過 0.9: {vpin}",
                    "severity": "HIGH",
                }
            )

        if defcon <= 3:
            alerts.append(
                {
                    "type": "DEFCON_WARNING",
                    "message": f"DEFCON 等級降至 {defcon}",
                    "severity": "MEDIUM",
                }
            )

        return alerts
