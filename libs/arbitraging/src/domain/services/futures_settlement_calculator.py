"""TW Futures Settlement Date Calculator

Calculates the third Wednesday of each month for Taiwan futures settlement.
"""

from datetime import date


def calculate_tw_futures_settlement_dates(year: int) -> list[date]:
    """Calculate TW futures settlement dates (third Wednesday of each month)

    Args:
        year: Year

    Returns:
        list[date]: All settlement dates for the year

    Note:
        TW futures final settlement date is the third Wednesday of each month.
        Settlement price is based on VWAP of TAIEX component stocks from 13:00 to 13:30.
    """
    settlement_dates = []

    for month in range(1, 13):
        # Find what day of week the first day of month is
        first_day = date(year, month, 1)
        first_weekday = first_day.weekday()  # 0=Monday, 2=Wednesday

        # Calculate date of first Wednesday
        days_until_wednesday = (2 - first_weekday) % 7
        first_wednesday = 1 + days_until_wednesday

        # Third Wednesday = first Wednesday + 14
        third_wednesday = first_wednesday + 14

        settlement_dates.append(date(year, month, third_wednesday))

    return settlement_dates
