"""Industry Code → ETF Mapping Table

Electronics industries use 0052 (Fubon Technology), Financial Insurance uses 0055 (Yuanta Financial).
Other industries without corresponding ETFs will use synthetic benchmark.
"""

INDUSTRY_TO_ETF: dict[str, str] = {
    # Electronics → 0052 (Fubon Technology)
    "24": "0052",  # Semiconductor
    "25": "0052",  # Computer Peripherals
    "26": "0052",  # Optoelectronics
    "27": "0052",  # Communications
    "28": "0052",  # Electronic Components
    "29": "0052",  # Electronic Distribution
    "30": "0052",  # Information Services
    "31": "0052",  # Other Electronics
    # Financial → 0055 (Yuanta Financial)
    "17": "0055",  # Financial Insurance
}
