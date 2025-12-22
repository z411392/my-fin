"""Get Stock Row Query

Read single stock data from local CSV
"""

import csv
import logging
from pathlib import Path

from libs.reporting.src.ports.get_stock_row_port import GetStockRowPort
from libs.shared.src.dtos.scan_result.scan_result_row_dto import ScanResultRowDTO


class GetStockRowQuery(GetStockRowPort):
    """Get single stock data from local CSV"""

    def __init__(self) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, date: str, symbol: str) -> ScanResultRowDTO | None:
        """Get single stock data for specified date

        Prioritize reading from CSV, fallback to JSON if CSV doesn't exist

        Args:
            date: Date (YYYY-MM-DD)
            symbol: Stock symbol

        Returns:
            Stock data, or None if not found
        """
        # Try reading from CSV
        csv_path = Path("data/summaries") / f"{date}.csv"
        if csv_path.exists():
            row = self._read_from_csv(csv_path, symbol)
            if row:
                return row

        # If CSV doesn't exist or not found, try reading from JSON
        json_path = Path("data/momentum") / date / f"{symbol}.json"
        if json_path.exists():
            return self._read_from_json(json_path)

        self._logger.warning(f"Cannot find {date} {symbol} data")
        return None

    def _read_from_csv(self, csv_path: Path, symbol: str) -> ScanResultRowDTO | None:
        """Read single stock data from CSV"""
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("SYMBOL") == symbol:
                        self._logger.info(f"Read {symbol} from CSV")
                        return row  # type: ignore
            return None
        except Exception as e:
            self._logger.error(f"Failed to read CSV: {e}")
            return None

    def _read_from_json(self, json_path: Path) -> ScanResultRowDTO | None:
        """Read single stock data from JSON (raw format, not cross-sectionally standardized)"""
        import json

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._logger.info(f"從 JSON 讀取 {json_path.stem}")

            # 將 JSON 結構攤平為 CSV 格式
            market_data = data.get("market_data") or {}
            momentum = data.get("momentum") or {}
            pricing = data.get("pricing") or {}
            lifecycle = data.get("lifecycle") or {}
            exit_signals = data.get("exit_signals") or {}
            sd = data.get("statementdog") or {}

            return {
                "SYMBOL": json_path.stem,
                "UPDATED": data.get("updated"),
                "NAME": market_data.get("name"),
                "SECTOR": market_data.get("sector"),
                "CLOSE": market_data.get("close"),
                "VOLUME": market_data.get("volume"),
                "RAW_MOMENTUM": momentum.get("raw_momentum"),
                "IVOL": momentum.get("ivol"),
                "THEO_PRICE": pricing.get("theo_price"),
                "REMAINING_ALPHA": pricing.get("remaining_alpha"),
                "F_SCORE": sd.get("f_score"),
                "PE": sd.get("pe"),
                "ROE": sd.get("roe"),
                # Lifecycle
                "SIGNAL_AGE_DAYS": lifecycle.get("signal_age_days"),
                "REMAINING_MEAT_RATIO": lifecycle.get("remaining_meat_ratio"),
                # Exit signals
                "STOP_LOSS_TRIGGERED": exit_signals.get("stop_loss_triggered"),
                # Note: This is raw data not cross-sectionally standardized
                "_SOURCE": "JSON (not standardized)",
            }  # type: ignore

        except Exception as e:
            self._logger.error(f"Failed to read JSON: {e}")
            return None
