"""
Technical Indicators Module
Uses pandas-ta for RSI, MACD, Bollinger Bands calculation
"""

import pandas as pd
import pandas_ta as ta
import logging

logger = logging.getLogger(__name__)


def klines_to_dataframe(klines):
    """Convert Binance klines to pandas DataFrame"""
    df = pd.DataFrame(
        klines,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trades",
            "taker_buy_base",
            "taker_buy_quote",
            "ignore",
        ],
    )

    # Convert to numeric
    df["close"] = pd.to_numeric(df["close"])
    df["high"] = pd.to_numeric(df["high"])
    df["low"] = pd.to_numeric(df["low"])
    df["volume"] = pd.to_numeric(df["volume"])

    return df


def calculate_indicators(df):
    """Calculate RSI, MACD, Bollinger Bands"""
    try:
        # Need at least 20 rows for proper calculations
        if len(df) < 20:
            logger.warning(f"Insufficient data ({len(df)} rows) for indicators")
            return df

        # RSI (14 period)
        rsi_result = ta.rsi(df["close"], length=14)
        if rsi_result is not None:
            df["RSI"] = rsi_result

        # MACD (12, 26, 9)
        macd = ta.macd(df["close"], fast=12, slow=26, signal=9)
        if macd is not None and not macd.empty:
            df["MACD"] = macd["MACD_12_26_9"]
            df["MACD_signal"] = macd["MACDs_12_26_9"]
            df["MACD_hist"] = macd["MACDh_12_26_9"]

        # Bollinger Bands (20 period, 2 std)
        bbands = ta.bbands(df["close"], length=20, std=2)
        if bbands is not None and not bbands.empty:
            # Find the actual column names
            bb_cols = [
                col
                for col in bbands.columns
                if "BBU" in col or "BBM" in col or "BBL" in col
            ]
            if len(bb_cols) >= 3:
                df["BB_upper"] = bbands[bb_cols[0]]
                df["BB_middle"] = bbands[bb_cols[1]]
                df["BB_lower"] = bbands[bb_cols[2]]

        # Volume moving average
        df["volume_ma"] = df["volume"].rolling(20).mean()

        return df
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        return df


def analyze_trend(df):
    """Analyze overall trend from dataframe"""
    if df.empty or len(df) < 2:
        return "UNKNOWN"

    first_close = df["close"].iloc[0]
    last_close = df["close"].iloc[-1]

    change_pct = ((last_close - first_close) / first_close) * 100

    if change_pct > 1:
        return "UP"
    elif change_pct < -1:
        return "DOWN"
    else:
        return "SIDEWAYS"


def get_latest_indicators(df):
    """Get the most recent indicator values"""
    if df.empty:
        return None

    latest = df.iloc[-1]

    return {
        "close": latest.get("close", 0),
        "RSI": latest.get("RSI", 50),
        "MACD": latest.get("MACD", 0),
        "MACD_signal": latest.get("MACD_signal", 0),
        "BB_upper": latest.get("BB_upper", 0),
        "BB_middle": latest.get("BB_middle", 0),
        "BB_lower": latest.get("BB_lower", 0),
        "volume": latest.get("volume", 0),
        "volume_ma": latest.get("volume_ma", 0),
    }
