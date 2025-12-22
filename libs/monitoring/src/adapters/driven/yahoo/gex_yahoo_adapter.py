"""GEX 計算器 Yahoo Adapter

使用 yfinance 獲取選擇權數據計算 Gamma Exposure

Note: yfinance 的選擇權數據有限，此實作提供基本估計
"""

import yfinance as yf
from libs.monitoring.src.ports.g_e_x_provider_port import GEXProviderPort
from libs.shared.src.dtos.market.gex_result_dto import GEXResultDTO


class GEXYahooAdapter(GEXProviderPort):
    """GEX 計算器 - Yahoo Finance 實作"""

    def calculate(self, symbol: str) -> GEXResultDTO:
        """計算 Gamma Exposure

        Args:
            symbol: 股票代碼 (如 SPY, QQQ)

        Returns:
            dict: {
                "gex": float (十億美元),
                "level": str (STRONG_SHORT/MILD_SHORT/NEUTRAL/MILD_LONG/STRONG_LONG),
                "put_call_ratio": float,
                "max_pain": float (if available)
            }
        """
        try:
            ticker = yf.Ticker(symbol)

            # 獲取選擇權到期日
            expirations = ticker.options
            if not expirations:
                return self._default_result()

            # 使用最近的到期日
            nearest_exp = expirations[0]

            # 獲取選擇權鏈
            chain = ticker.option_chain(nearest_exp)
            calls = chain.calls
            puts = chain.puts

            if calls.empty or puts.empty:
                return self._default_result()

            # 當前股價
            current_price = ticker.info.get("regularMarketPrice", 100)

            # 計算 GEX
            # GEX = Σ(gamma * OI * contract_size * spot_price)
            # 簡化計算：使用 OI 和價格距離估計

            total_call_gamma = 0
            total_put_gamma = 0

            for _, row in calls.iterrows():
                strike = row["strike"]
                oi = row.get("openInterest", 0) or 0
                # 近價選擇權 gamma 較高
                if abs(strike - current_price) / current_price < 0.1:
                    gamma_weight = 1 - abs(strike - current_price) / current_price / 0.1
                    total_call_gamma += (
                        oi * gamma_weight * 100
                    )  # 100 shares per contract

            for _, row in puts.iterrows():
                strike = row["strike"]
                oi = row.get("openInterest", 0) or 0
                if abs(strike - current_price) / current_price < 0.1:
                    gamma_weight = 1 - abs(strike - current_price) / current_price / 0.1
                    total_put_gamma += oi * gamma_weight * 100

            # Put 的 gamma 對 MM 是相反方向
            net_gex = (
                (total_call_gamma - total_put_gamma) * current_price / 1e9
            )  # 轉為十億美元

            # 計算 Put/Call 比率
            total_call_oi = (
                calls["openInterest"].sum() if "openInterest" in calls.columns else 0
            )
            total_put_oi = (
                puts["openInterest"].sum() if "openInterest" in puts.columns else 0
            )
            pc_ratio = total_put_oi / total_call_oi if total_call_oi > 0 else 1.0

            # 判定 level
            if net_gex > 5:
                level = "STRONG_LONG"
            elif net_gex > 2:
                level = "MILD_LONG"
            elif net_gex < -5:
                level = "STRONG_SHORT"
            elif net_gex < -2:
                level = "MILD_SHORT"
            else:
                level = "NEUTRAL"

            return {
                "gex": round(float(net_gex), 2),
                "level": level,
                "put_call_ratio": round(float(pc_ratio), 2),
                "expiration": nearest_exp,
            }

        except Exception:
            return self._default_result()

    def _default_result(self) -> GEXResultDTO:
        """默認結果 (數據不足時)"""
        return {
            "gex": 0.0,
            "level": "NEUTRAL",
            "put_call_ratio": 1.0,
            "expiration": None,
        }
