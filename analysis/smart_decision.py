"""
Smart Trading Decision Module
Determines buy/sell signals based on technical indicators
"""

import logging
from config.settings import (
    RSI_OVERSOLD,
    RSI_OVERBOUGHT,
    MIN_VOLUME_MULTIPLIER,
    APP_MODE,
)

logger = logging.getLogger(__name__)


# Global ML Engine instance (will be injected)
ml_engine = None


def set_ml_engine(engine):
    global ml_engine
    ml_engine = engine


def should_buy(indicators, trend_24h, ml_confidence=0.0):
    """
    Return True if buy conditions are met
    """
    if not indicators:
        return False

    rsi = indicators.get("RSI", 50)
    macd = indicators.get("MACD", 0)
    macd_signal = indicators.get("MACD_signal", 0)
    price = indicators.get("close", 0)
    bb_lower = indicators.get("BB_lower", 0)
    volume = indicators.get("volume", 0)
    volume_ma = indicators.get("volume_ma", 0)

    if APP_MODE == "dev":
        # DEV MODE: Relaxed conditions for testing
        conditions = {
            "rsi_oversold": rsi < RSI_OVERSOLD,
            "trend_up": trend_24h == "UP",
        }

        buy_signal = all(conditions.values())

        if buy_signal:
            logger.info(
                f"[BUY SIGNAL] DEV MODE - RSI oversold + Trend UP! (ML Conf: {ml_confidence:.2%})"
            )

    else:
        # PROD MODE: All 5 strict conditions + ML Confidence
        from config.settings import MODEL_MODE, ML_CONFIDENCE_THRESHOLD

        conditions = {
            "rsi_oversold": rsi < RSI_OVERSOLD,
            "macd_bullish": macd > macd_signal,
            "near_bb_lower": price <= bb_lower * 1.02 if bb_lower > 0 else False,
            "trend_up": trend_24h == "UP",
            "volume_high": (
                volume > volume_ma * MIN_VOLUME_MULTIPLIER if volume_ma > 0 else True
            ),
        }

        technical_signal = all(conditions.values())

        # ML Validation (only if enabled and trained)
        ml_pass = True
        if MODEL_MODE != "off" and ml_engine and ml_engine.is_trained:
            ml_pass = ml_confidence >= ML_CONFIDENCE_THRESHOLD
            if technical_signal:
                logger.info(
                    f"[ML CHECK] Confidence: {ml_confidence:.2%} >= {ML_CONFIDENCE_THRESHOLD:.2%}? {'[YES]' if ml_pass else '[NO]'}"
                )
        elif MODEL_MODE == "off":
            # ML is disabled, pass through technical signal only
            ml_pass = True

        buy_signal = technical_signal and ml_pass

        if any(conditions.values()):
            status = []
            status.append(
                f"RSI={rsi:.1f}<{RSI_OVERSOLD}? {'[Y]' if conditions['rsi_oversold'] else '[N]'}"
            )
            status.append(
                f"MACD={macd:.2f}>{macd_signal:.2f}? {'[Y]' if conditions['macd_bullish'] else '[N]'}"
            )
            status.append(
                f"BB_lower? {'[Y]' if conditions['near_bb_lower'] else '[N]'}"
            )
            status.append(f"Trend=UP? {'[Y]' if conditions['trend_up'] else '[N]'}")
            status.append(f"Volume? {'[Y]' if conditions['volume_high'] else '[N]'}")
            logger.info(f"[PROD BUY CHECK] {' | '.join(status)}")

        if buy_signal:
            logger.info(f"[BUY SIGNAL] PROD MODE - TECHNICAL + ML VALIDATED!")

    return buy_signal


def should_sell(indicators, entry_price, current_price, tp_pct, sl_pct):
    """
    Return True if ANY sell condition is met

    Conditions:
    1. RSI > RSI_OVERBOUGHT (default 70) - overbought
    2. Profit >= TAKE_PROFIT_PERCENT
    3. Loss >= STOP_LOSS_PERCENT
    4. MACD bearish crossover
    """
    if not indicators:
        return False, "NO_DATA"

    rsi = indicators.get("RSI", 50)
    macd = indicators.get("MACD", 0)
    macd_signal = indicators.get("MACD_signal", 0)

    profit_pct = ((current_price - entry_price) / entry_price) * 100

    # Check each sell condition
    if rsi > RSI_OVERBOUGHT:
        logger.info(f"[SELL SIGNAL] RSI overbought: {rsi:.1f}")
        return True, "RSI_OVERBOUGHT"

    if profit_pct >= tp_pct:
        logger.info(f"[SELL SIGNAL] Take profit hit: {profit_pct:.2f}%")
        return True, "TAKE_PROFIT"

    if profit_pct <= -sl_pct:
        logger.info(f"[SELL SIGNAL] Stop loss hit: {profit_pct:.2f}%")
        return True, "STOP_LOSS"

    if macd < macd_signal:
        logger.info(f"[SELL SIGNAL] MACD bearish crossover")
        return True, "MACD_BEARISH"

    return False, "HOLD"


def calculate_trade_score(indicators, trend_24h):
    """Calculate a score (0-100) for how good the trade setup is"""
    if not indicators:
        return 0

    score = 0
    rsi = indicators.get("RSI", 50)
    macd = indicators.get("MACD", 0)
    macd_signal = indicators.get("MACD_signal", 0)

    # RSI score (0-30 points)
    if rsi < 30:
        score += 30
    elif rsi < RSI_OVERSOLD:
        score += 20
    elif rsi < 50:
        score += 10

    # MACD score (0-30 points)
    macd_diff = macd - macd_signal
    if macd_diff > 0:
        score += min(30, int(macd_diff * 10))

    # Trend score (0-40 points)
    if trend_24h == "UP":
        score += 40
    elif trend_24h == "SIDEWAYS":
        score += 20

    return min(100, score)
