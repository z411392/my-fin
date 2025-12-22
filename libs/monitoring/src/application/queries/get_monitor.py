"""取得監控數據 Query"""

import logging
from datetime import datetime
import numpy as np
from injector import inject
from libs.monitoring.src.domain.services.defcon_calculator import calculate_defcon_level
from libs.monitoring.src.domain.services.vix_tier_calculator import (
    calculate_vix_tier,
    get_vix_kelly_factor,
)
from libs.monitoring.src.ports.get_monitor_port import GetMonitorPort
from libs.arbitraging.src.domain.services.hmm_regime_detector import hmm_regime_simple
from libs.monitoring.src.ports.market_data_provider_port import (
    MarketDataProviderPort,
)
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.monitoring.src.ports.gex_calculator_port import GEXCalculatorPort
from libs.shared.src.dtos.market.monitor_data_dto import MonitorDataDTO


class GetMonitorQuery(GetMonitorPort):
    """取得即時監控數據

    組合多指標即時狀態供 TUI 顯示
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

    def _calculate_hmm_state(self) -> tuple[int, float]:
        """從 SPY 報酬計算 HMM 體制

        Returns:
            tuple: (hmm_state, bull_prob)
        """
        try:
            daily_prices = self._market_data_adapter.get_daily_prices("SPY", days=120)
            if len(daily_prices) < 60:
                return 0, 0.5

            closes = np.array([p["close"] for p in daily_prices])
            returns = np.diff(closes) / closes[:-1]
            return hmm_regime_simple(returns)
        except Exception:
            return 0, 0.5  # 降級到中性

    def execute(self) -> MonitorDataDTO:
        """執行查詢

        Returns:
            MonitorDataDTO: 監控數據
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
            vpin_level = vpin_result.get("level", "NORMAL")
        except Exception:
            vpin = 0.3
            vpin_level = "NORMAL"

        # 從真實 Adapter 取得 GEX
        try:
            gex_result = self._gex_adapter.calculate("SPY")
            gex = gex_result.get("gex", 0.0)
            gex_level = gex_result.get("level", "NEUTRAL")
        except Exception:
            gex = 0.0
            gex_level = "NEUTRAL"

        # HMM 體制識別
        hmm_state, bull_prob = self._calculate_hmm_state()
        gli_z = 0.5  # 待整合 FRED

        defcon_level, emoji, action = calculate_defcon_level(
            vix=vix, hmm_state=hmm_state, vpin=vpin, gli_z=gli_z, gex=gex
        )
        vix_tier, _, _ = calculate_vix_tier(vix)
        kelly_factor = get_vix_kelly_factor(vix_tier)

        return {
            "timestamp": datetime.now().isoformat(),
            "vix": {
                "value": vix,
                "tier": vix_tier.name,
                "kelly_factor": kelly_factor,
            },
            "defcon": {
                "level": defcon_level.value,
                "emoji": emoji,
                "action": action,
            },
            "vpin": {
                "value": vpin,
                "status": vpin_level,
            },
            "gex": {
                "value": gex,
                "status": gex_level,
            },
            "gli": {
                "z_score": gli_z,
                "status": "中性",
            },
            "regime": {
                "hurst": 0.52,
                "hmm_state": hmm_state,
                "hmm_bull_prob": bull_prob,
                "name": "牛市"
                if bull_prob > 0.7
                else "震盪區間"
                if bull_prob > 0.3
                else "熊市",
            },
        }
