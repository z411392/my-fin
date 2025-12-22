"""取得天候狀態 Driving Port"""

from typing import Protocol

from libs.shared.src.dtos.weather_assessment_dto import WeatherAssessmentDTO


class GetWeatherPort(Protocol):
    """取得天候狀態

    CLI Entry: fin weather
    """

    def execute(self) -> WeatherAssessmentDTO:
        """
        取得當前天候狀態

        Returns:
            WeatherAssessmentDTO: 天候評估結果，包含 defcon_level, vix, vix_tier, action 等
        """
        ...
