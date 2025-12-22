"""計算凱利部位 Query

實作 CalculateKellyPositionPort Driving Port
"""

import logging

from injector import inject

from libs.hunting.src.domain.services.kelly_position_calculator import (
    calculate_kelly_position,
    get_regime_factor,
    get_vix_factor,
)
from libs.monitoring.src.domain.services.vix_tier_calculator import calculate_vix_tier
from libs.hunting.src.ports.market_data_provider_port import MarketDataProviderPort
from libs.hunting.src.ports.calculate_kelly_position_port import (
    CalculateKellyPositionPort,
)
from libs.shared.src.dtos.portfolio.kelly_position_result_dto import (
    KellyPositionResultDTO,
)


class CalculateKellyPositionQuery(CalculateKellyPositionPort):
    """計算凱利部位大小"""

    @inject
    def __init__(
        self,
        market_data_provider: MarketDataProviderPort,
    ) -> None:
        """初始化 Query

        Args:
            market_data_provider: 市場資料提供者 (由 DI 注入)
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._market_data = market_data_provider

    def execute(
        self,
        symbol: str,
        capital: float = 1000000,
        win_rate: float = 0.55,
        avg_win: float = 0.08,
        avg_loss: float = 0.04,
    ) -> KellyPositionResultDTO:
        """計算凱利部位"""
        vix = float(self._market_data.get_current_price("^VIX"))
        vix_tier, _, _ = calculate_vix_tier(vix)
        vix_factor = get_vix_factor(vix_tier)

        regime = "趨勢牛市"
        regime_factor = get_regime_factor(regime)

        kelly_pct = calculate_kelly_position(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            regime_factor=regime_factor,
            vix_factor=vix_factor,
        )

        position_size = capital * kelly_pct

        # 處理股票代碼格式
        symbol_str = str(symbol)
        if symbol_str.isdigit():
            # 台股代碼 (純數字) -> 加上 .TW
            yahoo_symbol = f"{symbol_str}.TW"
        else:
            yahoo_symbol = symbol_str

        current_price = float(self._market_data.get_current_price(yahoo_symbol))
        shares = int(position_size / current_price) if current_price > 0 else 0

        return {
            "symbol": symbol,
            "vix": vix,
            "vix_tier": vix_tier.name,
            "regime": regime,
            "kelly_pct": kelly_pct,
            "position_size": position_size,
            "shares": shares,
        }
