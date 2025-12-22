"""取得診斷報告 Query

實作 DiagnoseStockPort Driving Port
使用 Yahoo Finance 取得真實財務數據
"""

import logging

from injector import inject

from libs.diagnosing.src.ports.get_diagnosis_port import GetDiagnosisPort
from libs.diagnosing.src.ports.financial_data_provider_port import (
    FinancialDataProviderPort,
)
from libs.shared.src.dtos.analysis.diagnosis_result_dto import DiagnosisResultDTO


class GetDiagnosisQuery(GetDiagnosisPort):
    """取得診斷報告

    整合財務數據並生成四顧問共識
    """

    @inject
    def __init__(
        self,
        financial_adapter: FinancialDataProviderPort,
    ) -> None:
        """初始化 Query

        Args:
            financial_adapter: 財務數據提供者
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._financial_adapter = financial_adapter

    def execute(self, symbol: str) -> DiagnosisResultDTO:
        """取得診斷報告"""
        # 確保 symbol 為字串
        symbol = str(symbol)

        # 自動為台股代號加上 .TW 後綴
        yahoo_symbol = symbol
        if symbol.isdigit():
            yahoo_symbol = f"{symbol}.TW"

        # 1. 取得真實財務數據
        financial = self._financial_adapter.get_financial_info(yahoo_symbol)

        # 2. 基本面評分 (使用真實 ROE)
        roe = financial.get("roe", 0)
        if roe > 20:
            grade = "A"
        elif roe > 15:
            grade = "B"
        elif roe > 10:
            grade = "C"
        elif roe > 0:
            grade = "D"
        else:
            grade = "F"

        # 3. 四顧問共識（簡化版本，僅依據基本面）
        if grade in ["A", "B"]:
            consensus = "進攻"
        elif grade in ["C"]:
            consensus = "分歧"
        else:
            consensus = "防守"

        # 4. 推薦動作（依據基本面判斷）
        if grade in ["A", "B"]:
            verdict = "HOLD"
        elif grade in ["C"]:
            verdict = "OBSERVE"
        else:
            verdict = "REDUCE"
        rationale = f"基本面評等 {grade}"

        return {
            "symbol": symbol,
            "name": financial.get("name", symbol),
            "price": financial.get("price", 0),
            "roe": roe,
            "pe_ratio": financial.get("pe_ratio", 0),
            "revenue_growth": financial.get("revenue_growth", 0),
            "fundamental_grade": grade,
            "advisor_consensus": consensus,
            "verdict": verdict,
            "rationale": rationale,
        }
