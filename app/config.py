import os

# Crypto watchlist — Kraken base asset names
# These map to USD pairs (XBTUSD, ETHUSD, etc.)
WATCHLIST = os.getenv(
    "WATCHLIST",
    "XBT,ETH,SOL,ADA,DOT,LINK,AVAX"
).split(",")

# Kraken internal pair map (base asset → Kraken pair name)
PAIR_MAP = {
    "XBT":   "XBTUSD",
    "ETH":   "ETHUSD",
    "SOL":   "SOLUSD",
    "ADA":   "ADAUSD",
    "DOT":   "DOTUSD",
    "LINK":  "LINKUSD",
    "AVAX":  "AVAXUSD",
    "MATIC": "MATICUSD",
}

# Position sizing
TRADE_SIZE_PCT = float(os.getenv("TRADE_SIZE_PCT", "0.20"))   # 20% of USD balance
MAX_TRADE_SIZE = float(os.getenv("MAX_TRADE_SIZE", "500"))     # hard cap per trade
MAX_POSITIONS  = int(os.getenv("MAX_POSITIONS", "3"))
MIN_TRADE_USD  = float(os.getenv("MIN_TRADE_USD", "10"))       # Kraken minimum order floor

# Risk management
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.04"))     # 4% stop loss
# Note: take profit is handled by the SELL signal (trend reversal) rather than
# a fixed % target — crypto trends run longer than stocks

# Indicator settings
EMA_SHORT          = int(os.getenv("EMA_SHORT",            "20"))
EMA_LONG           = int(os.getenv("EMA_LONG",             "50"))
RSI_PERIOD         = int(os.getenv("RSI_PERIOD",           "14"))
RSI_BUY_THRESHOLD  = float(os.getenv("RSI_BUY_THRESHOLD",  "55"))
RSI_SELL_THRESHOLD = float(os.getenv("RSI_SELL_THRESHOLD", "45"))

# 120 calendar days ≈ 84 trading days — comfortable headroom above EMA_LONG default of 50
BARS_TO_FETCH = int(os.getenv("BARS_TO_FETCH", "120"))

# Scan time — crypto is 24/7 so we pick a consistent daily time
SCAN_HOUR   = int(os.getenv("SCAN_HOUR",   "9"))
SCAN_MINUTE = int(os.getenv("SCAN_MINUTE", "35"))

# Logging
OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "")
