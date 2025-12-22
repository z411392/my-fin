"""取得週末總覽 Query (Read Model: WeekendReviewDTO)"""

import logging

from injector import inject
import numpy as np

from libs.hunting.src.domain.services.residual_momentum_calculator import (
    calculate_momentum_score,
)
from libs.hunting.src.ports.residual_momentum_market_data_provider_port import (
    ResidualMomentumMarketDataProviderPort,
)
from libs.reviewing.src.ports.macro_data_provider_port import (
    MacroDataProviderPort,
)
from libs.shared.src.dtos.weekend_review_dto import WeekendReviewResultDTO
from libs.shared.src.enums.market_regime_quadrant import MarketRegimeQuadrant
from libs.hunting.src.ports.get_weekend_review_port import GetWeekendReviewPort


class GetWeekendReviewQuery(GetWeekendReviewPort):
    """
    取得週末總覽視圖

    整合:
    - 本週績效
    - 市場體制定位
    - 狩獵清單
    - 配置建議
    """

    VIX_HIGH_THRESHOLD = 25.0

    @inject
    def __init__(
        self,
        market_provider: ResidualMomentumMarketDataProviderPort,
        macro_provider: MacroDataProviderPort,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._market = market_provider
        self._macro = macro_provider

    def execute(self, watchlist: list[str]) -> WeekendReviewResultDTO:
        """
        取得週末總覽

        Args:
            watchlist: 觀察名單

        Returns:
            WeekendReviewDTO: 週末總覽視圖
        """
        # 取得宏觀資料
        vix = self._macro.get_vix()
        fed_trend = self._macro.get_fed_balance_sheet_trend()

        # 判定市場體制
        regime = self._determine_regime(vix, fed_trend)

        # 計算狩獵清單動能
        hunting_targets = []
        for symbol in watchlist:
            returns = self._market.get_daily_returns(symbol, 60)
            benchmark = self._market.get_benchmark_returns("SPY", 60)

            if not returns or not benchmark:
                continue

            # 簡單殘差計算
            returns_arr = np.array(returns)
            benchmark_arr = np.array(benchmark)

            if len(returns_arr) > 0 and len(benchmark_arr) > 0:
                min_len = min(len(returns_arr), len(benchmark_arr))
                residuals = returns_arr[:min_len] - benchmark_arr[:min_len]
                score = calculate_momentum_score(residuals)

                if score > 0.5:  # 正動能
                    hunting_targets.append(
                        {
                            "symbol": symbol,
                            "momentum_score": score,
                            "beta": 1.0,  # 簡化
                        }
                    )

        # 排序
        hunting_targets.sort(key=lambda x: x["momentum_score"], reverse=True)

        return {
            "date": "",  # 由呼叫端填入
            "regime": {
                "hurst": 0.5,
                "hmm_bull_prob": 0.5,
                "vix": 15.0,
                "name": regime.value,
                "market_type": "中性",
                "recommended_strategy": self._get_strategy(regime),
                "kelly_factor": 0.5,
            },
            "advisors": {
                "engineer": {"status": "觀望", "advice": ""},
                "biologist": {"status": "觀望", "advice": ""},
                "psychologist": {"status": "觀望", "advice": ""},
                "strategist": {"status": "觀望", "advice": ""},
                "consensus": "🟡 觀望",
                "allocation": "股票 30%",
                "attack_count": 0,
            },
            "momentum_candidates": hunting_targets[:10],
            "halt_check": {
                "hungry": {"question": "", "answer": "否"},
                "angry": {"question": "", "answer": "否"},
                "lonely": {"question": "", "answer": "否"},
                "tired": {"question": "", "answer": "否"},
                "can_trade": True,
            },
            "upcoming_events": [],
            "next_week_plan": [],
            "total_scanned": len(hunting_targets),
            "report_markdown": "",
        }

    def _determine_regime(self, vix: float, fed_trend: str) -> MarketRegimeQuadrant:
        """判定市場體制"""
        is_high_vol = vix >= self.VIX_HIGH_THRESHOLD
        is_bullish = fed_trend == "EXPANDING"

        if not is_high_vol and is_bullish:
            return MarketRegimeQuadrant.CALM_BULL
        elif is_high_vol and is_bullish:
            return MarketRegimeQuadrant.VOLATILE_BULL
        elif not is_high_vol and not is_bullish:
            return MarketRegimeQuadrant.CALM_BEAR
        else:
            return MarketRegimeQuadrant.VOLATILE_BEAR

    def _get_strategy(self, regime: MarketRegimeQuadrant) -> str:
        """取得推薦策略"""
        strategies = {
            MarketRegimeQuadrant.CALM_BULL: "進攻配置，動能策略",
            MarketRegimeQuadrant.VOLATILE_BULL: "謹慎進攻，設停損",
            MarketRegimeQuadrant.CALM_BEAR: "防守配置，均值回歸",
            MarketRegimeQuadrant.VOLATILE_BEAR: "減倉觀望，持有現金",
        }
        return strategies.get(regime, "觀望")
