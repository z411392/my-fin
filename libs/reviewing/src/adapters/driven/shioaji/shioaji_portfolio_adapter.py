"""Shioaji 持倉 Adapter

實作 PortfolioProviderPort，用於查詢永豐金帳戶持倉
"""

from libs.shared.src.clients.shioaji.shioaji_client import ShioajiClient
from libs.shared.src.dtos.portfolio.position_dto import PositionDTO
from libs.shared.src.dtos.portfolio.trade_dto import TradeDTO
from libs.shared.src.dtos.portfolio.profit_loss_dto import ProfitLossDTO
from libs.shared.src.dtos.portfolio.account_balance_dto import AccountBalanceDTO
import logging
import os
from libs.reviewing.src.ports.portfolio_provider_port import PortfolioProviderPort
from datetime import datetime, timedelta


class ShioajiPortfolioAdapter(PortfolioProviderPort):
    """Shioaji 持倉查詢 Adapter"""

    def __init__(self, client: ShioajiClient) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)
        self._client = client

    def connect(self) -> bool:
        """連線"""
        return self._client.connect()

    def disconnect(self) -> None:
        """斷線"""
        self._client.disconnect()

    def get_positions(self) -> list[PositionDTO]:
        """取得所有持倉"""
        if not self._client.connected:
            if not self.connect():
                return []

        try:
            api = self._client.api
            accounts = api.list_accounts()
            if not accounts:
                return []

            stock_account = None
            for acc in accounts:
                if "StockAccount" in type(acc).__name__:
                    stock_account = acc
                    break

            if not stock_account:
                stock_account = getattr(api, "stock_account", accounts[0])

            positions = api.list_positions(stock_account)

            result = []
            for pos in positions:
                pnl_percent = (
                    (pos.pnl / (pos.quantity * pos.price)) * 100
                    if pos.quantity > 0 and pos.price > 0
                    else 0
                )

                result.append(
                    {
                        "symbol": pos.code,
                        "name": getattr(pos, "name", pos.code),
                        "quantity": pos.quantity,
                        "cost": float(pos.price),
                        "current_price": float(pos.last_price),
                        "pnl": float(pos.pnl),
                        "pnl_percent": round(pnl_percent, 2),
                    }
                )

            return result
        except Exception:
            return []

    def get_position_with_stop_loss(
        self, stop_loss_map: dict[str, float] | None = None
    ) -> list[PositionDTO]:
        """取得持倉並計算停損緩衝"""
        positions = self.get_positions()
        stop_loss_map = stop_loss_map or {}

        for pos in positions:
            symbol = pos["symbol"]
            current_price = pos["current_price"]

            stop_loss = stop_loss_map.get(symbol, pos["cost"] * 0.9)
            pos["stop_loss"] = stop_loss

            if current_price > 0:
                buffer = (current_price - stop_loss) / current_price * 100
                pos["buffer_pct"] = round(buffer, 1)
            else:
                pos["buffer_pct"] = 0

            if pos["buffer_pct"] > 15:
                pos["status"] = "✅"
                pos["status_text"] = "健康"
            elif pos["buffer_pct"] > 10:
                pos["status"] = "🔍"
                pos["status_text"] = "觀察"
            elif pos["buffer_pct"] > 5:
                pos["status"] = "⚠️"
                pos["status_text"] = "警戒"
            else:
                pos["status"] = "🔴"
                pos["status_text"] = "危險"

        return positions

    def get_account_balance(self) -> AccountBalanceDTO:
        """取得帳戶餘額"""
        if not self._client.connected:
            if not self.connect():
                return {}

        try:
            api = self._client.api
            balance = api.account_balance()
            return {
                "available": float(balance.acc_balance),
            }
        except Exception:
            return {}

    def get_trades(self) -> list[TradeDTO]:
        """取得交易記錄 (Journal)

        Returns:
            list[TradeDTO]: 交易記錄列表，每筆包含:
                - order_id: 訂單編號
                - symbol: 股票代號
                - name: 股票名稱
                - action: 買/賣
                - price: 成交價格
                - quantity: 成交數量
                - status: 訂單狀態
                - order_time: 下單時間
                - deals: 成交明細
        """

        if not self._client.connected:
            if not self.connect():
                return []

        try:
            # 嘗試啟用 CA 憑證 (查詢交易記錄需要)
            ca_path = os.environ.get("SHIOAJI_CA_PATH")
            if ca_path:
                ca_activated = self._client.activate_ca()
                if not ca_activated:
                    self._logger.warning("️ CA 憑證啟用失敗，可能無法取得完整交易記錄")

            api = self._client.api

            # 取得股票帳戶
            accounts = api.list_accounts()
            stock_account = None
            for acc in accounts:
                if "StockAccount" in type(acc).__name__:
                    stock_account = acc
                    break

            if not stock_account:
                stock_account = getattr(
                    api, "stock_account", accounts[0] if accounts else None
                )

            if not stock_account:
                return []

            # 更新訂單狀態
            api.update_status(stock_account)

            # 取得交易記錄
            trades = api.list_trades()

            result = []
            for trade in trades:
                # 解析成交明細
                deals = []
                if hasattr(trade, "status") and hasattr(trade.status, "deals"):
                    for deal in trade.status.deals:
                        deals.append(
                            {
                                "seq": getattr(deal, "seq", ""),
                                "price": float(getattr(deal, "price", 0)),
                                "quantity": int(getattr(deal, "quantity", 0)),
                                "timestamp": getattr(deal, "ts", 0),
                            }
                        )

                # 建構交易記錄
                order_time = None
                if hasattr(trade, "status") and hasattr(trade.status, "order_datetime"):
                    order_time = (
                        trade.status.order_datetime.isoformat()
                        if trade.status.order_datetime
                        else None
                    )

                result.append(
                    {
                        "order_id": getattr(trade.order, "id", "")
                        if hasattr(trade, "order")
                        else "",
                        "symbol": getattr(trade.contract, "code", "")
                        if hasattr(trade, "contract")
                        else "",
                        "name": getattr(trade.contract, "name", "")
                        if hasattr(trade, "contract")
                        else "",
                        "action": trade.order.action.value
                        if hasattr(trade, "order") and hasattr(trade.order, "action")
                        else "",
                        "price": float(trade.order.price)
                        if hasattr(trade, "order") and hasattr(trade.order, "price")
                        else 0,
                        "quantity": int(trade.order.quantity)
                        if hasattr(trade, "order") and hasattr(trade.order, "quantity")
                        else 0,
                        "status": trade.status.status.value
                        if hasattr(trade, "status") and hasattr(trade.status, "status")
                        else "",
                        "order_time": order_time,
                        "deals": deals,
                        "total_filled": sum(d["quantity"] for d in deals),
                        "avg_price": (
                            sum(d["price"] * d["quantity"] for d in deals)
                            / sum(d["quantity"] for d in deals)
                            if deals and sum(d["quantity"] for d in deals) > 0
                            else 0
                        ),
                    }
                )

            return result
        except Exception as e:
            self._logger.warning(f"取得交易記錄失敗: {e}")
            return []

    def get_profit_loss_history(
        self, begin_date: str | None = None, end_date: str | None = None, days: int = 30
    ) -> list[ProfitLossDTO]:
        """取得歷史交易損益記錄

        Args:
            begin_date: 開始日期 (格式: YYYY-MM-DD)，預設為 {days} 天前
            end_date: 結束日期 (格式: YYYY-MM-DD)，預設為今天
            days: 若未指定日期，則查詢最近幾天 (預設 30 天)

        Returns:
            list[ProfitLossDTO]: 損益記錄列表，每筆包含:
                - symbol: 股票代號
                - name: 股票名稱
                - action: 買/賣
                - quantity: 數量
                - price: 成交價
                - pnl: 損益金額
                - pnl_percent: 損益百分比
                - date: 交易日期
        """

        if not self._client.connected:
            if not self.connect():
                return []

        try:
            # 嘗試啟用 CA 憑證
            ca_path = os.environ.get("SHIOAJI_CA_PATH")
            if ca_path:
                self._client.activate_ca()

            api = self._client.api

            # 計算日期範圍
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not begin_date:
                begin_dt = datetime.now() - timedelta(days=days)
                begin_date = begin_dt.strftime("%Y-%m-%d")

            # 取得股票帳戶
            accounts = api.list_accounts()
            stock_account = None
            for acc in accounts:
                if "StockAccount" in type(acc).__name__:
                    stock_account = acc
                    break

            if not stock_account:
                stock_account = getattr(
                    api, "stock_account", accounts[0] if accounts else None
                )

            if not stock_account:
                return []

            # 查詢損益記錄
            profit_loss_list = api.list_profit_loss(
                stock_account,
                begin_date=begin_date,
                end_date=end_date,
            )

            result = []
            for pl in profit_loss_list:
                # 計算損益百分比
                cost = getattr(pl, "cost", 0) or 0
                pnl = getattr(pl, "pnl", 0) or 0
                pnl_percent = (pnl / cost * 100) if cost > 0 else 0

                result.append(
                    {
                        "symbol": getattr(pl, "code", ""),
                        "name": getattr(pl, "name", ""),
                        "quantity": int(getattr(pl, "quantity", 0)),
                        "price": float(getattr(pl, "price", 0)),
                        "cost": float(cost),
                        "pnl": float(pnl),
                        "pnl_percent": round(pnl_percent, 2),
                        "date": getattr(pl, "date", ""),
                        "cond": getattr(pl, "cond", ""),  # 交易條件 (現股/融資等)
                    }
                )

            return result
        except Exception as e:
            self._logger.warning(f"取得歷史損益失敗: {e}")
            return []
