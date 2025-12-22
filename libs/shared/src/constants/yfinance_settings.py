"""yfinance API Settings

All places calling yfinance must use these constants to avoid Rate Limit (429).
"""

# Delay seconds between each yfinance API request
YFINANCE_DELAY_SECONDS: float = 0.5
