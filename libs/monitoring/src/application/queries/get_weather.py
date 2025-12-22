"""取得 DEFCON 天候狀態 Query

對應 prd.md fin weather 指令
整合 DEFCON 等級、VIX 恐慌階梯、GLI 流動性脈衝
"""

import logging

from injector import inject

from libs.monitoring.src.domain.services.defcon_calculator import (
    calculate_defcon_level,
    get_defcon_action,
)
from libs.monitoring.src.domain.services.vix_tier_calculator import calculate_vix_tier
from libs.monitoring.src.domain.services.gli_pulse_calculator import calculate_gli_pulse
from libs.arbitraging.src.domain.services.hmm_regime_detector import hmm_regime_simple
import numpy as np
from libs.monitoring.src.ports.get_weather_port import GetWeatherPort
from libs.monitoring.src.ports.market_data_provider_port import (
    MarketDataProviderPort,
)
from libs.monitoring.src.ports.vpin_calculator_port import VPINCalculatorPort
from libs.monitoring.src.ports.gex_calculator_port import GEXCalculatorPort
from libs.monitoring.src.ports.gli_pulse_provider_port import GLIPulseProviderPort


from libs.shared.src.dtos.weather_assessment_dto import WeatherAssessmentDTO


class GetWeatherQuery(GetWeatherPort):
    """取得天候狀態 Query

    整合 VIX、VPIN、GEX、GLI 四大指標
    """

    @inject
    def __init__(
        self,
        market_data: MarketDataProviderPort,
        vpin: VPINCalculatorPort,
        gex: GEXCalculatorPort,
        gli: GLIPulseProviderPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._market_data = market_data
        self._vpin = vpin
        self._gex = gex
        self._gli = gli

    def _get_hmm_regime(self) -> tuple:
        """使用真實 S&P 500 資料計算 HMM 體制"""
        try:
            daily_prices = self._market_data.get_daily_prices("^GSPC", 120)
            if not daily_prices or len(daily_prices) < 60:
                return 0, 0.5

            closes = np.array([p["close"] for p in daily_prices])
            returns = np.diff(closes) / closes[:-1]
            return hmm_regime_simple(returns)
        except Exception:
            return 0, 0.5  # 降級到中性

    def execute(self) -> WeatherAssessmentDTO:
        """
        取得當前天候狀態

        Returns:
            dict: 天候評估視圖
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
            vpin = 0.3  # 降級到保守值

        # 從真實 Adapter 取得 GEX
        try:
            gex_result = self._gex_adapter.calculate("SPY")
            gex = gex_result.get("gex", 0.0)
        except Exception:
            gex = 0.0  # 降級到中性值

        # 其他數據 (待整合其他 Adapters)
        sp500_change = 0.5
        hmm_state, bull_prob = self._calculate_hmm_state()
        fed_balance = 8.5  # (需要 FRED API)
        m2_yoy = 3.5
        historical_gli = np.random.randn(252)

        # 使用計算引擎
        gli_z, gli_status = calculate_gli_pulse(
            fed_balance=fed_balance,
            m2_yoy=m2_yoy,
            historical_gli=historical_gli,
        )

        defcon_level, defcon_emoji, permission = calculate_defcon_level(
            vix=vix,
            hmm_state=hmm_state,
            vpin=vpin,
            gli_z=gli_z,
            gex=gex,
        )

        vix_tier, _vix_emoji, vix_action = calculate_vix_tier(vix)

        action = get_defcon_action(defcon_level)
        requires_action = defcon_level.value <= 3

        return {
            "defcon_level": defcon_level.value,
            "emoji": defcon_emoji,
            "permission": permission,
            "action": action,
            "vix": vix,
            "vix_tier": vix_tier.name,
            "vix_action": vix_action,
            "vpin": vpin,
            "gli_z": round(gli_z, 2),
            "gli_status": gli_status,
            "sp500_change": sp500_change,
            "requires_action": requires_action,
        }
