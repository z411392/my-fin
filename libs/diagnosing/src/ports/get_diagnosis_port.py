"""
GetDiagnosisPort - Driving Port

實作者: GetDiagnosisQuery
"""

from typing import Protocol

from libs.shared.src.dtos.analysis.diagnosis_result_dto import DiagnosisResultDTO


class GetDiagnosisPort(Protocol):
    """Driving Port for GetDiagnosisQuery"""

    def execute(self, symbol: str) -> DiagnosisResultDTO:
        """執行主要操作"""
        ...
