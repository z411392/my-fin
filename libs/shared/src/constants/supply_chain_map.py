"""供應鏈對應表

美股 -> 台股供應鏈對照表
用於跨市場傳導分析
"""

# 美股 -> 台股供應鏈對應表
SUPPLY_CHAIN_MAP: dict[str, str] = {
    "NVDA": "2330.TW",  # NVIDIA -> 台積電
    "AAPL": "2317.TW",  # Apple -> 鴻海
    "TSM": "2330.TW",  # 台積電 ADR -> 台積電
    "AMD": "3034.TW",  # AMD -> 聯詠
    "AVGO": "2454.TW",  # Broadcom -> 聯發科
    "QCOM": "2379.TW",  # Qualcomm -> 瑞昱
    "INTC": "2303.TW",  # Intel -> 聯電
}
