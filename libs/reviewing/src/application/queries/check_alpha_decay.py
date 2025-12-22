"""檢查 Alpha 衰減 Query

實作 CheckAlphaDecayPort Driving Port
"""

import logging

from injector import inject
from decimal import Decimal

from libs.reviewing.src.ports.stock_price_provider_port import (
    StockPriceProviderPort,
)
from libs.reviewing.src.domain.services.alpha_decay_checker import (
    check_alpha_decay,
    interpret_alpha_decay,
)
from libs.reviewing.src.ports.check_alpha_decay_port import CheckAlphaDecayPort
from libs.shared.src.dtos.reviewing.alpha_decay_result_dto import AlphaDecayResultDTO


class CheckAlphaDecayQuery(CheckAlphaDecayPort):
    """檢查 Alpha 衰減"""

    @inject
    def __init__(self, price_provider: StockPriceProviderPort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._price_provider = price_provider

    def execute(
        self,
        symbol: str,
        entry_price: float,
        target_price: float,
        initial_alpha: float | None = None,
    ) -> AlphaDecayResultDTO:
        """檢查 Alpha 衰減

        Args:
            symbol: 股票代號
            entry_price: 進場價格
            target_price: 目標價格
            initial_alpha: 初始預期 Alpha（可選，若未提供則根據 entry/target 計算）
        """
        # 確保 symbol 是字串（CLI 可能傳入數字類型）
        symbol = str(symbol)

        # 取得當前價格
        current_price_decimal: Decimal = self._price_provider.get_current_price(symbol)
        current_price = float(current_price_decimal)

        if current_price == 0.0:
            return {
                "symbol": symbol,
                "entry_price": entry_price,
                "target_price": target_price,
                "current_price": 0.0,
                "initial_alpha": 0.0,
                "remaining": 0.0,
                "decision": "ABORT",
                "status": "無法取得價格",
                "advice": "請確認股票代號是否正確",
            }

        # 若未提供 initial_alpha，根據進場價與目標價計算
        if initial_alpha is None:
            if entry_price > 0:
                initial_alpha = (target_price - entry_price) / entry_price
            else:
                initial_alpha = 0.0

        decision, remaining = check_alpha_decay(
            initial_alpha=initial_alpha,
            target_price=target_price,
            current_price=current_price,
            entry_price=entry_price,
        )
        status, advice = interpret_alpha_decay(decision, remaining)

        return {
            "symbol": symbol,
            "entry_price": entry_price,
            "target_price": target_price,
            "current_price": current_price,
            "initial_alpha": initial_alpha,
            "remaining": remaining,
            "decision": decision,
            "status": status,
            "advice": advice,
        }
