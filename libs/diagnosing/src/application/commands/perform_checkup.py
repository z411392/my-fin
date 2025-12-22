"""執行個股健檢 Command"""

import logging

from injector import inject
import numpy as np

import pandas as pd
from libs.diagnosing.src.ports.perform_checkup_port import PerformCheckupPort
from libs.diagnosing.src.ports.financial_data_provider_port import (
    FinancialDataProviderPort,
)
from libs.shared.src.dtos.analysis.dimension_result_dto import DimensionResultDTO

# Importing Domain Services from hunting lib
from libs.hunting.src.domain.services.theoretical_price_calculator import (
    calculate_alpha_decay_price,
    calculate_remaining_alpha,
)
from libs.hunting.src.domain.services.half_life_calculator import (
    calculate_remaining_meat,
)
from libs.hunting.src.domain.services.residual_rsi_calculator import (
    detect_rsi_divergence,
    check_stop_loss,
)
from libs.hunting.src.domain.services.volatility_scaler import (
    scale_position_by_volatility,
)
from libs.hunting.src.domain.services.frog_in_the_pan_calculator import (
    calculate_information_discreteness,
    interpret_id_score,
)
from libs.shared.src.dtos.analysis.checkup_result_dto import CheckupResultDTO
from libs.shared.src.dtos.analysis.advanced_checkup_result_dto import (
    AdvancedCheckupResultDTO,
)
from libs.shared.src.dtos.analysis.stock_analysis_data_dto import StockAnalysisDataDTO


class PerformCheckupCommand(PerformCheckupPort):
    """執行個股健檢

    整合四維度診斷 + 論點驗證
    並包含新的定價模型與出場協議
    """

    @inject
    def __init__(self, data_provider: FinancialDataProviderPort) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._data_provider = data_provider

    def execute(self, symbol: str) -> CheckupResultDTO:
        """執行個股健檢"""

        # 0. 準備資料
        try:
            data = self._fetch_real_data(symbol)
        except Exception as e:
            return {"error": str(e)}

        # 1. 執行新版評估 (Pricing, Meat, Exits)
        checkup_result = self._run_advanced_checkup(symbol, data)

        # 2. 整合舊版維度 (Mocked dimensions)
        dimensions = self._evaluate_legacy_dimensions(symbol)

        # 3. 合併結果
        # 將新版 Checkup 轉換為維度格式加入
        dimensions.extend(checkup_result["dimensions"])

        # 4. 計算綜合分數與判定
        # 根據 Dimensions 的 passed 狀態
        passed_count = sum(1 for d in dimensions if d.get("passed", False))
        total_checks = len(dimensions)

        # 簡單判定邏輯
        if checkup_result["must_exit"]:
            verdict = "SELL"
            action = f"觸發強制出場: {checkup_result['exit_reason']}"
        elif passed_count / total_checks >= 0.8:
            verdict = "KEEP"
            action = "積極持有"
        elif passed_count / total_checks >= 0.5:
            verdict = "HOLD"
            action = "觀察"
        else:
            verdict = "REDUCE"
            action = "減碼"

        return {
            "symbol": symbol,
            "diagnosis": {
                "dimensions": dimensions,
                "score": passed_count,
                "verdict": verdict,
                "action": action,
                "details": checkup_result["details"],
            },
            "timestamp": "2025-01-05T00:00:00",
        }

    def _run_advanced_checkup(
        self, symbol: str, data: StockAnalysisDataDTO
    ) -> AdvancedCheckupResultDTO:
        """執行進階健檢 (Pricing, Meat, Exits)"""

        current_price = data["current_price"]
        prices = data["prices"]  # np.array

        # --- 1. 定價模型檢查 ---
        # 假設我們計算出了 Alpha Decay Price
        alpha_price_res = calculate_alpha_decay_price(
            current_price=current_price,
            alpha_resid_annual=data["alpha"],
            beta_market=1.0,
            market_expected_return=0.08,
        )
        target_price = alpha_price_res["target_price"]

        # 檢查是否有剩餘空間
        remaining_pct, alpha_signal = calculate_remaining_alpha(
            target_price, current_price, alpha_price_res["expected_move_pct"]
        )

        pricing_check = {
            "name": "理論定價",
            "description": f"Target: {target_price:.2f} (Upside: {remaining_pct:.1%})",
            "passed": remaining_pct > 0.03,  # >3% 才有肉
            "value": f"{remaining_pct:.1%}",
        }

        # --- 2. 肉量檢查 (Meat Metrics) ---
        # 計算 ID
        id_score = calculate_information_discreteness(data["returns"])
        id_label, id_desc = interpret_id_score(id_score)

        # 計算 Meat
        # 假設已知 signal_age
        meat_pct, meat_rec = calculate_remaining_meat(data["signal_age"], half_life=130)

        meat_check = {
            "name": "肉量評估",
            "description": f"Meat: {meat_pct:.0%} | ID: {id_score:.2f}",
            "passed": meat_pct > 0.3 and id_score < 0,
            "value": f"{meat_rec} | {id_label}",
        }

        # --- 3. 出場協議 (Exit Protocols) ---
        must_exit = False
        exit_reason = ""

        # 3.1: 10% 硬停損
        should_stop, drawdown = check_stop_loss(current_price, data["monthly_high"])
        if should_stop:
            must_exit = True
            exit_reason = f"觸發 10% 止損 (回撤 {drawdown:.1%})"

        stop_loss_check = {
            "name": "硬性止損",
            "description": "Max Drawdown < 10%",
            "passed": not should_stop,
            "value": f"Drawdown: {drawdown:.1%}",
        }

        # 3.2: 波動率縮放
        vol_res = scale_position_by_volatility(
            base_position_size=1.0,  # 假設滿倉
            current_volatility=data["volatility"],
            target_volatility=0.20,
        )

        # 3.3: RSI 背離
        # 假設我們有 residual rsi data
        div_type, div_exit = detect_rsi_divergence(prices, data["resid_rsi"])
        if div_exit:
            # RSI 背離通常是獲利了結，不一定是恐慌出場，但這裡視為 Exit 訊號
            pass

        rsi_check = {
            "name": "RSI 背離",
            "description": "無頂背離",
            "passed": not div_exit,
            "value": div_type,
        }

        return {
            "dimensions": [pricing_check, meat_check, stop_loss_check, rsi_check],
            "must_exit": must_exit,
            "exit_reason": exit_reason,
            "details": {
                "alpha_decay": alpha_price_res,
                "vol_scaling": vol_res,
                "id_score": id_score,
                "meat_pct": meat_pct,
            },
        }

    def _evaluate_legacy_dimensions(self, symbol: str) -> list[DimensionResultDTO]:
        """評估舊版維度 (Mock)"""
        # ... (保持原有的隨機邏輯或簡化)
        np.random.seed(hash(symbol) % 2**32)
        return [
            {
                "name": "EEMD趨勢",
                "description": "斜率 > 0",
                "passed": True,
                "value": "Positive",
            }
        ]

    def _fetch_real_data(self, symbol: str) -> StockAnalysisDataDTO:
        """從 Provider 取得真實數據並計算指標"""

        # 1. 取得價格資料
        stock_data = self._data_provider.get_daily_prices(symbol, days=252)
        if not stock_data:
            raise ValueError(f"No data for {symbol}")

        # 2. 取得大盤資料 (SPY) 作為基準
        spy_data = self._data_provider.get_daily_prices("SPY", days=252)

        # 3. 轉換為 DataFrame 處理
        df_stock = pd.DataFrame(stock_data)
        df_stock["date"] = pd.to_datetime(df_stock["date"])
        df_stock.set_index("date", inplace=True)

        df_spy = pd.DataFrame(spy_data)
        df_spy["date"] = pd.to_datetime(df_spy["date"])
        df_spy.set_index("date", inplace=True)

        # 對齊資料
        df = pd.concat(
            [df_stock["close"].rename("stock"), df_spy["close"].rename("spy")], axis=1
        ).dropna()

        if len(df) < 30:
            raise ValueError("Insufficient data for analysis")

        prices = df["stock"].values
        current_price = prices[-1]

        # 計算報酬率
        returns = df["stock"].pct_change().dropna().values
        spy_returns = df["spy"].pct_change().dropna().values

        # 確保長度一致
        min_len = min(len(returns), len(spy_returns))
        returns = returns[-min_len:]
        spy_returns = spy_returns[-min_len:]
        # prices[-min_len:] 可用於對應 returns 的價格 (長度差1?)
        # 價格序列長度通常比 return 多 1，這裡是為了計算 RSI，使用原始 prices 比較好
        # 但是 returns 是 diff，所以 returns[i] 對應 prices[i+1]

        # 4. 計算 Alpha (簡單單因子模型)
        # Stock = alpha + beta * Market
        if len(returns) > 10:
            beta, alpha_daily = np.polyfit(spy_returns, returns, 1)
            alpha_annual = alpha_daily * 252
        else:
            alpha_annual = 0.0

        # 5. 計算波動率
        volatility = np.std(returns) * np.sqrt(252)

        # 6. 計算 RSI (Mock Resid RSI for now, or implement real calculation)
        # 這裡簡單用價格 RSI 代替，或隨機 (因為我們還沒搬移 hunting 的完整殘差計算)
        # 為了演示，我們用 50
        resid_rsi = np.full(len(prices), 50.0)

        # 7. 取得基本面 (Optional)
        # info = self._data_provider.get_financial_info(symbol)

        return {
            "current_price": current_price,
            "monthly_high": np.max(prices[-22:]),  # 近一月高點
            "alpha": alpha_annual,
            "volatility": volatility,
            "signal_age": 10,  # 暫時 Mock
            "returns": returns,
            "prices": prices,  # 使用對齊後的價格序列 (包含開頭)
            "resid_rsi": resid_rsi,
        }
