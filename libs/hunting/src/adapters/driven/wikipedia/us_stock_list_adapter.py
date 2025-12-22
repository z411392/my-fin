"""US 股票清單取得器

從 Wikipedia 取得 Russell 1000、SOX 成分股清單
"""

import pandas as pd


def get_sp500() -> list[str]:
    """
    從 Wikipedia 取得 S&P 500 成分股清單

    Returns:
        list[str]: 股票代碼列表
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    try:
        tables = pd.read_html(url)
        df = tables[0]
        symbols = df["Symbol"].tolist()
        # 清理格式 (有些 symbol 包含 . 如 BRK.B)
        symbols = [s.replace(".", "-") for s in symbols]
        return sorted(symbols)
    except Exception:
        return _get_sp500_fallback()


def get_russell_1000() -> list[str]:
    """
    從 Wikipedia 取得 Russell 1000 成分股清單

    Returns:
        list[str]: 股票代碼列表
    """
    url = "https://en.wikipedia.org/wiki/Russell_1000_Index"

    try:
        tables = pd.read_html(url)
        # Russell 1000 表格通常是第二或第三個
        for table in tables:
            if "Ticker" in table.columns:
                symbols = table["Ticker"].dropna().tolist()
                symbols = [str(s).strip() for s in symbols if str(s).strip()]
                if len(symbols) > 100:  # 確認是正確的表格
                    return sorted(symbols)
            elif "Symbol" in table.columns:
                symbols = table["Symbol"].dropna().tolist()
                symbols = [str(s).strip() for s in symbols if str(s).strip()]
                if len(symbols) > 100:
                    return sorted(symbols)

        # 如果找不到，回退到 S&P 500
        return get_sp500()
    except Exception:
        return get_sp500()


def get_sox_components() -> list[str]:
    """
    取得 SOX (費城半導體指數) 成分股清單

    SOX 成分股較固定，使用靜態清單
    Reference: https://www.nasdaq.com/market-activity/index/sox

    Returns:
        list[str]: 股票代碼列表
    """
    # SOX 30 成分股 (2024 年)
    return [
        "AMD",  # Advanced Micro Devices
        "ADI",  # Analog Devices
        "AMAT",  # Applied Materials
        "ASML",  # ASML Holding
        "AVGO",  # Broadcom
        "AZTA",  # Azenta
        "COHR",  # Coherent
        "ENTG",  # Entegris
        "GFS",  # GlobalFoundries
        "INTC",  # Intel
        "IPGP",  # IPG Photonics
        "KLAC",  # KLA Corporation
        "LRCX",  # Lam Research
        "MCHP",  # Microchip Technology
        "MPWR",  # Monolithic Power Systems
        "MU",  # Micron Technology
        "MRVL",  # Marvell Technology
        "NXPI",  # NXP Semiconductors
        "NVDA",  # NVIDIA
        "ON",  # ON Semiconductor
        "QCOM",  # Qualcomm
        "QRVO",  # Qorvo
        "SLAB",  # Silicon Labs
        "SMTC",  # Semtech
        "SWKS",  # Skyworks Solutions
        "TER",  # Teradyne
        "TSM",  # TSMC
        "TXN",  # Texas Instruments
        "WOLF",  # Wolfspeed
    ]


def get_nasdaq_100() -> list[str]:
    """
    從 Wikipedia 取得 NASDAQ 100 成分股清單

    Returns:
        list[str]: 股票代碼列表
    """
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"

    try:
        tables = pd.read_html(url)
        for table in tables:
            if "Ticker" in table.columns:
                symbols = table["Ticker"].dropna().tolist()
                symbols = [str(s).strip() for s in symbols if str(s).strip()]
                if len(symbols) > 50:
                    return sorted(symbols)
            elif "Symbol" in table.columns:
                symbols = table["Symbol"].dropna().tolist()
                symbols = [str(s).strip() for s in symbols if str(s).strip()]
                if len(symbols) > 50:
                    return sorted(symbols)
        return _get_nasdaq100_fallback()
    except Exception:
        return _get_nasdaq100_fallback()


def get_all_us_stocks(
    include_russell: bool = True,
    include_sox: bool = True,
    include_nasdaq: bool = False,
) -> list[str]:
    """
    取得完整美股清單

    Args:
        include_russell: 是否包含 Russell 1000
        include_sox: 是否包含 SOX 成分股
        include_nasdaq: 是否包含 NASDAQ 100

    Returns:
        list[str]: 股票代碼列表
    """
    stocks = set()

    if include_russell:
        stocks.update(get_russell_1000())

    if include_sox:
        stocks.update(get_sox_components())

    if include_nasdaq:
        stocks.update(get_nasdaq_100())

    return sorted(stocks)


def _get_sp500_fallback() -> list[str]:
    """S&P 500 備援清單 (前 100 大)"""
    return [
        "AAPL",
        "ABBV",
        "ABT",
        "ACN",
        "ADBE",
        "AIG",
        "AMD",
        "AMGN",
        "AMZN",
        "AVGO",
        "AXP",
        "BA",
        "BAC",
        "BK",
        "BKNG",
        "BLK",
        "BMY",
        "C",
        "CAT",
        "CHTR",
        "CL",
        "CMCSA",
        "COP",
        "COST",
        "CRM",
        "CSCO",
        "CVS",
        "CVX",
        "DE",
        "DHR",
        "DIS",
        "DOW",
        "DUK",
        "EMR",
        "EXC",
        "F",
        "FDX",
        "GD",
        "GE",
        "GILD",
        "GM",
        "GOOG",
        "GOOGL",
        "GS",
        "HD",
        "HON",
        "IBM",
        "INTC",
        "INTU",
        "ISRG",
        "JNJ",
        "JPM",
        "KHC",
        "KO",
        "LIN",
        "LLY",
        "LMT",
        "LOW",
        "MA",
        "MCD",
        "MDLZ",
        "MDT",
        "MET",
        "META",
        "MMM",
        "MO",
        "MRK",
        "MS",
        "MSFT",
        "NEE",
        "NFLX",
        "NKE",
        "NVDA",
        "ORCL",
        "PEP",
        "PFE",
        "PG",
        "PM",
        "PYPL",
        "QCOM",
        "RTX",
        "SBUX",
        "SCHW",
        "SO",
        "SPG",
        "T",
        "TGT",
        "TMO",
        "TMUS",
        "TSLA",
        "TXN",
        "UNH",
        "UNP",
        "UPS",
        "USB",
        "V",
        "VZ",
        "WBA",
        "WFC",
        "WMT",
    ]


def _get_nasdaq100_fallback() -> list[str]:
    """NASDAQ 100 備援清單"""
    return [
        "AAPL",
        "ABNB",
        "ADBE",
        "ADI",
        "ADP",
        "ADSK",
        "AEP",
        "AMAT",
        "AMD",
        "AMGN",
        "AMZN",
        "ANSS",
        "ASML",
        "AVGO",
        "AZN",
        "BIIB",
        "BKNG",
        "BKR",
        "CDNS",
        "CEG",
        "CHTR",
        "CMCSA",
        "COST",
        "CPRT",
        "CRWD",
        "CSCO",
        "CSGP",
        "CSX",
        "CTAS",
        "CTSH",
        "DDOG",
        "DLTR",
        "DXCM",
        "EA",
        "EBAY",
        "ENPH",
        "EXC",
        "FANG",
        "FAST",
        "FTNT",
        "GEHC",
        "GFS",
        "GILD",
        "GOOG",
        "GOOGL",
        "HON",
        "IDXX",
        "ILMN",
        "INTC",
        "INTU",
        "ISRG",
        "JD",
        "KDP",
        "KHC",
        "KLAC",
        "LRCX",
        "LULU",
        "MAR",
        "MCHP",
        "MDLZ",
        "MELI",
        "META",
        "MNST",
        "MRNA",
        "MRVL",
        "MSFT",
        "MU",
        "NFLX",
        "NVDA",
        "NXPI",
        "ODFL",
        "ON",
        "ORLY",
        "PANW",
        "PAYX",
        "PCAR",
        "PDD",
        "PEP",
        "PYPL",
        "QCOM",
        "REGN",
        "RIVN",
        "ROST",
        "SBUX",
        "SIRI",
        "SNPS",
        "SPLK",
        "TEAM",
        "TMUS",
        "TSLA",
        "TTD",
        "TTWO",
        "TXN",
        "VRSK",
        "VRTX",
        "WBA",
        "WBD",
        "WDAY",
        "XEL",
        "ZS",
    ]
