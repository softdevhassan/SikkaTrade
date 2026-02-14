import os
from dotenv import load_dotenv

load_dotenv()

# App Mode: dev (simulation) or prod (live trading)
# App Mode: dev (simulation) or prod (live trading)
APP_MODE = os.getenv("APP_MODE", "dev").lower()  # dev or prod
IS_LIVE_MODE = APP_MODE == "prod"  # Only prod uses real Binance trading
MODEL_MODE = os.getenv("MODEL_MODE", "use").lower()  # train/use/off
ML_CONFIDENCE_THRESHOLD = float(os.getenv("ML_CONFIDENCE_THRESHOLD", 0.60))

# ===== API KEYS =====
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")
# CMC_API_KEY = os.getenv("CMC_API_KEY")  # Not used - we only fetch prices from Binance

# ===== TRADING CONFIG =====
COINS = [c.strip().upper() for c in os.getenv("COINS", "").split(",")]

ALLOTED_USDT = float(os.getenv("ALLOTED_USDT", 0))
PARALLEL_TRADES = int(os.getenv("PARALLEL_TRADES", 1))
TRADE_METHOD = os.getenv("TRADE_METHOD", "SPOT").upper()
MIN_SPOT_TRADE_USDT = float(os.getenv("MIN_SPOT_TRADE_USDT", 5))
MAX_SPOT_TRADE_USDT = float(os.getenv("MAX_SPOT_TRADE_USDT", 50))

TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 0.3))
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 0.15))

ANALYSIS_LIVE_SECONDS = int(os.getenv("ANALYSIS_LIVE_SECONDS", 300))
MAX_RUNTIME_SECONDS = int(os.getenv("MAX_RUNTIME_SECONDS", 3600))

# ===== ANALYSIS CONFIG =====
PREV_ANALYSIS_HOURS = [
    int(h.strip()) for h in os.getenv("PREV_ANALYSIS_HOURS", "24,12,6,1").split(",")
]
RSI_OVERSOLD = float(os.getenv("RSI_OVERSOLD", 40))
RSI_OVERBOUGHT = float(os.getenv("RSI_OVERBOUGHT", 70))
MIN_VOLUME_MULTIPLIER = float(os.getenv("MIN_VOLUME_MULTIPLIER", 1.5))
