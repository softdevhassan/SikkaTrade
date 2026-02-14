"""
SikkaTrade Trading Engine with AI-Powered Analysis
Author: Hassan Ali (@softdevhassan)

4-Phase Trading System:
1. Historical Analysis (24h, 12h, 6h, 1h)
2. Live Monitoring
3. Smart Trading with Indicators
4. Auto-Shutdown
"""

import time
import sys
import signal
import logging
import random  # For random trade amounts
from datetime import datetime
from config.settings import (
    COINS,
    ALLOTED_USDT,
    TAKE_PROFIT_PERCENT,
    STOP_LOSS_PERCENT,
    ANALYSIS_LIVE_SECONDS,
    MAX_RUNTIME_SECONDS,
    PREV_ANALYSIS_HOURS,
    APP_MODE,
    IS_LIVE_MODE,
    BINANCE_API_KEY,
    BINANCE_SECRET_KEY,
    PARALLEL_TRADES,
    MIN_SPOT_TRADE_USDT,
    MAX_SPOT_TRADE_USDT,
    TRADE_METHOD,
    MODEL_MODE,
)

from engine.wallet import VirtualWallet, BinanceWallet
from engine.executor import BinanceExecutor
from engine.simulator import TradeSimulator
from data.binance_data import get_current_price, get_klines
from engine.recovery import save_state
from analysis.indicators import (
    klines_to_dataframe,
    calculate_indicators,
    analyze_trend,
    get_latest_indicators,
)
from engine.ml_engine import MLEngine  # New Import
from analysis.smart_decision import (
    should_buy,
    should_sell,
    calculate_trade_score,
    set_ml_engine,
)  # Updated Import

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/sikkatrade.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

# Global variables
wallet = None
simulator = None
executor = None
ml_engine = None  # Global ML Engine
trend_data = {}
shutting_down = False  # Guard for shutdown


def initialize_wallet():
    """Initialize wallet and executor based on APP_MODE"""
    if IS_LIVE_MODE:  # prod mode
        if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
            logger.error(f"[!] APP_MODE=prod but API keys are missing!")
            logger.error("   Please set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env")
            exit(1)

        from binance.client import Client

        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
        logger.info(f"[PROD] LIVE TRADING MODE - REAL MONEY ACTIVE ({TRADE_METHOD})")

        # Initialize Executor
        executor = BinanceExecutor(client, method=TRADE_METHOD)
        return BinanceWallet(client), executor
    else:  # dev mode
        logger.info("[DEV] SIMULATION MODE - FAKE MONEY FOR TESTING")
        return VirtualWallet(ALLOTED_USDT), None


def phase_ml_training():
    """
    PHASE 0: ML Training
    Train model if MODEL_MODE='train' or if no model exists (and not 'off')
    """
    global ml_engine

    if MODEL_MODE == "off":
        logger.info("[ML] Machine Learning module is DISABLED (Mode: OFF)")
        return

    logger.info("=" * 60)
    logger.info(f"PHASE 0: ML MODEL TRAINING (Mode: {MODEL_MODE.upper()})")
    logger.info("=" * 60)

    should_train = False
    if MODEL_MODE == "train":
        should_train = True
        logger.info("[ML] MODEL_MODE='train' -> Forcing new training session.")
    elif not ml_engine.is_trained:
        if IS_LIVE_MODE:
            logger.warning("[!] No trained ML model found.")
            # In production, we don't want to force a 30s delay unless the user wants it
            confirm = input("   No model found. Train now? (y/n) [Default: n]: ")
            if confirm.lower() == "y":
                should_train = True
            else:
                logger.info(
                    "[ML] Skipping training. Bot will run with Technical Analysis only."
                )
        else:
            should_train = True
            logger.info("[ML] No existing model found -> Starting training.")
    else:
        logger.info("[ML] Using existing trained model (Skipping training).")

    if should_train:
        logger.info(
            f"Training new model on {len(COINS)} coins (this may take 10-60s)..."
        )
        # Ensure we don't block signals during training
        # ml_engine.train is synchronous, so it will block, but we warned the user
        success = ml_engine.train(COINS)
        if not success:
            logger.error("[ML] Training failed. Proceeding without ML support.")

    logger.info("=" * 60 + "\n")


def phase1_historical_analysis():
    """
    PHASE 1: Analyze historical data
    Fetch and analyze past 24h, 12h, 6h, 1h data
    """
    global trend_data

    logger.info("=" * 60)
    logger.info("PHASE 1: HISTORICAL ANALYSIS")
    logger.info("=" * 60)

    for coin in COINS:
        for hours in PREV_ANALYSIS_HOURS:
            try:
                # Fetch historical klines
                klines = get_klines(coin, hours)
                if not klines:
                    logger.warning(f"  {hours}h: No data available")
                    continue

                # Convert to dataframe and calculate indicators
                df = klines_to_dataframe(klines)
                df = calculate_indicators(df)

                # Analyze trend
                trend = analyze_trend(df)

                # Get latest indicators
                indicators = get_latest_indicators(df)

                # Store 24h trend for later use
                if hours == 24:
                    trend_data[coin] = trend

                # Display analysis (Moved to debug)
                rsi = indicators.get("RSI", 0)
                logger.debug(
                    f"  {hours}h: Trend={trend}, RSI={rsi:.1f}, "
                    f"Price=${indicators.get('close', 0):,.2f}"
                )

            except Exception as e:
                logger.error(f"  {hours}h: Analysis failed - {e}")

    # Save state for GUI
    save_state(
        wallet,
        simulator.trades,
        phase="PHASE_1_COMPLETE",
        runtime_elapsed=0,
        runtime_total=0,  # Phase 1 is setup, no timer
    )

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 1 COMPLETE")
    logger.info("=" * 60 + "\n")


def phase2_live_monitoring():
    """
    PHASE 2: Live price monitoring
    Monitor live prices for ANALYSIS_LIVE_SECONDS
    """
    logger.info("=" * 60)
    logger.info("PHASE 2: LIVE MONITORING")
    logger.info(f"Monitoring for {ANALYSIS_LIVE_SECONDS}s...")
    logger.info("=" * 60)

    start_time = time.time()
    start_prices = {}

    # Get starting prices
    for coin in COINS:
        try:
            start_prices[coin] = get_current_price(coin)
        except:
            pass

    while time.time() - start_time < ANALYSIS_LIVE_SECONDS:
        elapsed = int(time.time() - start_time)

        if elapsed % 60 == 0:  # Log only every minute
            logger.info(f"\n[{elapsed}s/{ANALYSIS_LIVE_SECONDS}s] Live Prices:")

            for coin in COINS:
                try:
                    current_price = get_current_price(coin)
                    if coin in start_prices:
                        change_pct = (
                            (current_price - start_prices[coin]) / start_prices[coin]
                        ) * 100
                        logger.info(
                            f"  {coin}: ${current_price:,.2f} ({change_pct:+.2f}%)"
                        )
                    else:
                        logger.info(f"  {coin}: ${current_price:,.2f}")
                except Exception as e:
                    logger.debug(f"  {coin}: Failed to fetch - {e}")
        else:
            # Just update state silently
            for coin in COINS:
                try:
                    get_current_price(coin)  # keep fetching to ensure connection
                except:
                    pass

        # Update GUI with monitoring progress
        save_state(
            wallet,
            simulator.trades,
            phase="PHASE_2_MONITORING",
            runtime_elapsed=elapsed,
            runtime_total=ANALYSIS_LIVE_SECONDS,  # Phase 2 uses ANALYSIS_LIVE_SECONDS
        )

        time.sleep(10)  # Update every 10 seconds

    # Final monitoring state
    save_state(
        wallet,
        simulator.trades,
        phase="PHASE_2_COMPLETE",
        runtime_elapsed=ANALYSIS_LIVE_SECONDS,
        runtime_total=ANALYSIS_LIVE_SECONDS,
    )

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 2 COMPLETE")
    logger.info("=" * 60 + "\n")


def phase3_trading():
    """
    PHASE 3: Smart Trading
    Execute trades based on technical indicators + ML
    """
    global wallet, simulator

    logger.info("=" * 60)
    logger.info("PHASE 3: SMART TRADING")
    logger.info(f"Trading until MAX_RUNTIME_SECONDS ({MAX_RUNTIME_SECONDS}s)")
    logger.info("=" * 60)

    start_time = time.time()

    while True:
        elapsed = time.time() - start_time

        # Check if MAX_RUNTIME_SECONDS exceeded
        if elapsed >= MAX_RUNTIME_SECONDS:
            logger.info(f"\n[!] MAX_RUNTIME_SECONDS ({MAX_RUNTIME_SECONDS}s) reached!")
            break

        try:
            # Fetch current prices and indicators
            price_map = {}
            indicators_map = {}
            score_map = {}  # Store ML confidence

            for coin in COINS:
                try:
                    # Get latest 24h data for indicators
                    klines = get_klines(coin, 24)
                    if klines:
                        df = klines_to_dataframe(klines)
                        df = calculate_indicators(df)
                        indicators_map[coin] = get_latest_indicators(df)
                        price_map[coin] = indicators_map[coin]["close"]

                        # ML Prediction
                        ml_prob = ml_engine.predict_proba(df)
                        score_map[coin] = ml_prob

                        rsi = indicators_map[coin].get("RSI", 50)
                except Exception as e:
                    logger.error(f"Failed to get data for {coin}: {e}")
                    continue

            # Monitor and close existing trades
            closed_trades = []
            for trade in simulator.trades:
                if not trade.open:
                    continue

                coin = trade.coin
                if coin not in indicators_map:
                    continue

                current_price = price_map[coin]
                indicators = indicators_map[coin]

                # DEV MODE: Time-based closing for demo (close after 8 seconds)
                if APP_MODE.lower() == "dev":
                    hold_time = time.time() - trade.entry_time
                    if hold_time >= 8:  # 8 seconds holding
                        pnl_usdt, pnl_pct = simulator.close_trade(trade, current_price)
                        icon = "[+]" if pnl_usdt > 0 else "[-]"
                        logger.info(
                            f"{icon} CLOSED {coin} | Reason=DEV_TIMEOUT({hold_time:.0f}s) | PnL=${pnl_usdt:.4f} ({pnl_pct:.2f}%)"
                        )
                        closed_trades.append((coin, pnl_usdt, pnl_pct))
                        continue

                # Check sell signal
                should_close, reason = should_sell(
                    indicators,
                    trade.entry,
                    current_price,
                    TAKE_PROFIT_PERCENT,
                    STOP_LOSS_PERCENT,
                )

                if should_close:
                    pnl_usdt, pnl_pct = simulator.close_trade(trade, current_price)
                    icon = "[+]" if pnl_usdt > 0 else "[-]"
                    logger.info(
                        f"{icon} CLOSED {coin} | Reason={reason} | PnL=${pnl_usdt:.4f} ({pnl_pct:.2f}%)"
                    )
                    closed_trades.append((coin, pnl_usdt, pnl_pct))

            # Calculate trade amount ONCE for this cycle
            free_balance = wallet.snapshot()["free"]
            coins_with_signals = []

            # First pass: identify which coins have buy signals
            for coin in COINS:
                if coin not in indicators_map:
                    continue
                indicators = indicators_map[coin]
                trend = trend_data.get(coin, "UNKNOWN")

                # Check signals with ML Support
                ml_conf = score_map.get(coin, 0.5)
                if should_buy(indicators, trend, ml_confidence=ml_conf):
                    coins_with_signals.append(coin)

            # Random trade amount per coin within limits
            if coins_with_signals:
                # Second pass: open trades with random amounts
                for coin in coins_with_signals:
                    # Random amount between MIN and MAX
                    trade_amount = round(
                        random.uniform(MIN_SPOT_TRADE_USDT, MAX_SPOT_TRADE_USDT), 2
                    )
                    if (
                        trade_amount >= MIN_SPOT_TRADE_USDT
                        and free_balance >= trade_amount
                    ):
                        price = price_map[coin]
                        opened = simulator.open_trade(coin, trade_amount, price)
                        if opened:
                            indicators = indicators_map[coin]
                            trend = trend_data.get(coin, "UNKNOWN")
                            score = calculate_trade_score(indicators, trend)
                            logger.info(
                                f"[+] OPENED {coin} | ${trade_amount:.2f} @ ${price:,.2f} | Score={score}/100"
                            )

            # Save state for GUI
            save_state(
                wallet,
                simulator.trades,
                phase="PHASE_3_TRADING",
                runtime_elapsed=int(elapsed),
                runtime_total=MAX_RUNTIME_SECONDS,
            )

            time.sleep(1)  # Prevent excessive updates (1s delay)

        except KeyboardInterrupt:
            logger.info("\n[!] Manual shutdown requested")
            break
        except Exception as e:
            logger.error(f"[X] Error in trading loop: {e}", exc_info=True)
            time.sleep(5)


def phase4_shutdown():
    """
    PHASE 4: Graceful Shutdown
    Close all open trades and calculate final profit
    """
    global wallet, simulator, shutting_down

    if shutting_down:
        return
    shutting_down = True

    # Close all open trades with retries
    max_retries = 3
    for attempt in range(max_retries):
        open_trades = [t for t in simulator.trades if t.open]
        if not open_trades:
            logger.info("[✓] All trades successfully closed.")
            break

        logger.info(
            f"[!] {len(open_trades)} open trades remaining. Close attempt {attempt + 1}/{max_retries}..."
        )

        for trade in open_trades:
            try:
                # Get current price with retries
                current_price = get_current_price(trade.coin)
                pnl_usdt, pnl_pct = simulator.close_trade(trade, current_price)

                if not trade.open:
                    logger.info(
                        f"  [✓] Closed {trade.coin}: PnL=${pnl_usdt:.4f} ({pnl_pct:.2f}%)"
                    )
                else:
                    logger.warning(f"  [X] Failed to close {trade.coin} - Will retry.")
            except Exception as e:
                logger.error(f"  [!] Error during shutdown close for {trade.coin}: {e}")

        if open_trades:
            time.sleep(2)  # Wait before retry

    # Re-check one last time
    final_open_trades = [t for t in simulator.trades if t.open]
    if final_open_trades:
        logger.critical(f"UNABLE TO CLOSE {len(final_open_trades)} TRADES!")
        for t in final_open_trades:
            logger.critical(f"  STILL OPEN: {t.coin} - Qty: {t.quantity}")
        logger.critical("PLEASE CLOSE THESE TRADES MANUALLY ON BINANCE IMMEDIATELY!")

    # Final wallet snapshot
    wallet_snapshot = wallet.snapshot()
    logger.info("\nFINAL REPORT:")
    logger.info(f"  Total USDT Balance: ${wallet_snapshot['total']:.2f}")
    logger.info(f"  Total Realized Profit: ${wallet_snapshot['profit']:.4f}")

    profit_pct = (
        (wallet_snapshot["profit"] / ALLOTED_USDT) * 100 if ALLOTED_USDT > 0 else 0
    )
    logger.info(f"  Total Return: {profit_pct:+.2f}%")

    save_state(
        wallet,
        simulator.trades,
        phase="PHASE_4_SHUTDOWN",
        runtime_elapsed=MAX_RUNTIME_SECONDS,
        runtime_total=MAX_RUNTIME_SECONDS,
    )

    logger.info("\n" + "=" * 60)
    logger.info("ENGINE SHUTDOWN COMPLETE")
    logger.info("=" * 60)

    sys.exit(0)


def main():
    global wallet, simulator, executor, ml_engine  # GLOBALS

    # Print startup banner
    print("\n" + "=" * 60)
    print("[$] SikkaTrade AI-Powered Trading Engine")
    print("   Author: Hassan Ali (@softdevhassan)")
    print("=" * 60)
    print(
        f"Mode: [{APP_MODE.upper()}] {'LIVE TRADING - REAL MONEY' if IS_LIVE_MODE else 'SIMULATION - FAKE MONEY'}"
    )
    print(f"Method: {TRADE_METHOD if IS_LIVE_MODE else 'SIMULATION'}")
    print(f"Coins: {', '.join(COINS)}")
    print(f"Algorithm: Technical Analysis + Machine Learning (RandomForest)")
    print("=" * 60)
    print()

    # Initialize wallet and simulator
    wallet, executor = initialize_wallet()
    simulator = TradeSimulator(
        wallet,
        TAKE_PROFIT_PERCENT,
        STOP_LOSS_PERCENT,
        PARALLEL_TRADES,
        executor,
    )

    # Initialize ML Engine
    ml_engine = MLEngine()
    set_ml_engine(ml_engine)  # Inject into smart_decision

    logger.info("Engine initialized successfully\n")

    # Production Mode Double-Check
    if IS_LIVE_MODE:
        print("\n" + "!" * 60)
        print("  WARNING: YOU ARE STARTING IN PRODUCTION MODE!")
        print("  REAL MONEY WILL BE USED FOR TRADES ON BINANCE.")
        print("!" * 60)
        confirm = input("\nType 'PROD' to confirm you want to proceed: ")
        if confirm.strip().upper() != "PROD":
            print("[X] Startup aborted by user.")
            sys.exit(0)

    # Signal handling for graceful shutdown
    def signal_handler(sig, frame):
        logger.info(f"\n[!] Signal {sig} received. Starting graceful shutdown...")
        phase4_shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Execute System
        phase_ml_training()  # New Phase 0
        phase1_historical_analysis()
        phase2_live_monitoring()
        phase3_trading()
    except Exception as e:
        logger.error(f"[X] Fatal error: {e}", exc_info=True)
    finally:
        phase4_shutdown()


if __name__ == "__main__":
    main()
