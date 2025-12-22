"""四巫日計算器

四巫日 (Quad Witching Day) 是每季第三個週五，
股票指數期貨、股票指數選擇權、個股期貨、個股選擇權同時到期的日子。
"""

from datetime import date, timedelta


def calculate_quad_witching_dates(year: int) -> list[date]:
    """計算指定年度的四巫日 (每季第三個週五)

    Args:
        year: 年份

    Returns:
        list[date]: 該年度四個四巫日的日期列表
    """
    witching_dates = []

    # 四巫日在 3, 6, 9, 12 月的第三個週五
    witching_months = [3, 6, 9, 12]

    for month in witching_months:
        # 找出該月第一天
        first_day = date(year, month, 1)

        # 計算該月第一個週五
        # weekday(): 0=Monday, 1=Tuesday, ..., 4=Friday
        days_until_friday = (4 - first_day.weekday()) % 7
        first_friday = first_day + timedelta(days=days_until_friday)

        # 第三個週五 = 第一個週五 + 14 天
        third_friday = first_friday + timedelta(days=14)

        witching_dates.append(third_friday)

    return witching_dates
