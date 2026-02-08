import time
import logging
from binance.client import Client
from binance.enums import KLINE_INTERVAL_1HOUR
from config.settings import BINANCE_API_KEY, BINANCE_SECRET_KEY

logger = logging.getLogger(__name__)

client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)


def get_klines(symbol, hours=24):
    """Fetch historical candlestick data"""
    try:
        # Calculate how many 1h candles we need
        limit = hours

        klines = client.get_klines(
            symbol=f"{symbol}USDT", interval=KLINE_INTERVAL_1HOUR, limit=limit
        )

        return klines
    except Exception as e:
        logger.error(f"Failed to fetch klines for {symbol}: {e}")
        return []


def get_current_price(symbol, retries=3):
    """Fetch current price with retry logic"""
    for attempt in range(retries):
        try:
            ticker = client.get_symbol_ticker(symbol=f"{symbol}USDT")
            return float(ticker["price"])
        except Exception as e:
            logger.warning(f"Attempt {attempt + 1}/{retries} failed for {symbol}: {e}")
            if attempt < retries - 1:
                time.sleep(2**attempt)  # Exponential backoff
            else:
                raise Exception(
                    f"Failed to fetch price for {symbol} after {retries} attempts"
                )
