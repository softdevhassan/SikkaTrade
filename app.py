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
)

from engine.wallet import VirtualWallet, BinanceWallet
from engine.simulator import TradeSimulator
from data.binance_data import get_current_price, get_klines
from engine.recovery import save_state
from analysis.indicators import (
    klines_to_dataframe,
    calculate_indicators,
    analyze_trend,
    get_latest_indicators,
)
from analysis.smart_decision import should_buy, should_sell, calculate_trade_score

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
trend_data = {}  # Store 24h trend for each coin


def initialize_wallet():
    """Initialize wallet based on APP_MODE"""
    if IS_LIVE_MODE:  # prod mode
        if not BINANCE_API_KEY or not BINANCE_SECRET_KEY:
            logger.error(f"[!] APP_MODE=prod but API keys are missing!")
            logger.error("   Please set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env")
            exit(1)

        from binance.client import Client

        client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)
        logger.info("[PROD] LIVE TRADING MODE - REAL MONEY ACTIVE")
        return BinanceWallet(client)
    else:  # dev mode
        logger.info("[DEV] SIMULATION MODE - FAKE MONEY FOR TESTING")
        return VirtualWallet(ALLOTED_USDT)


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
        logger.info(f"\n[{coin}] Historical Analysis:")

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

                # Display analysis
                rsi = indicators.get("RSI", 0)
                logger.info(
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
        remaining = ANALYSIS_LIVE_SECONDS - elapsed

        logger.info(f"\n[{elapsed}s/{ANALYSIS_LIVE_SECONDS}s] Live Prices:")

        for coin in COINS:
            try:
                current_price = get_current_price(coin)
                if coin in start_prices:
                    change_pct = (
                        (current_price - start_prices[coin]) / start_prices[coin]
                    ) * 100
                    logger.info(f"  {coin}: ${current_price:,.2f} ({change_pct:+.2f}%)")
                else:
                    logger.info(f"  {coin}: ${current_price:,.2f}")
            except Exception as e:
                logger.warning(f"  {coin}: Failed to fetch - {e}")

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
    Execute trades based on technical indicators
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
            logger.info(
                f"\n--- Trading Cycle: {datetime.now().strftime('%H:%M:%S')} ---"
            )
            logger.info(f"Runtime: {int(elapsed)}s / {MAX_RUNTIME_SECONDS}s")

            # Fetch current prices and indicators
            price_map = {}
            indicators_map = {}

            for coin in COINS:
                try:
                    # Get latest 24h data for indicators
                    klines = get_klines(coin, 24)
                    if klines:
                        df = klines_to_dataframe(klines)
                        df = calculate_indicators(df)
                        indicators_map[coin] = get_latest_indicators(df)
                        price_map[coin] = indicators_map[coin]["close"]

                        rsi = indicators_map[coin].get("RSI", 50)
                        logger.info(f"{coin}: ${price_map[coin]:,.2f} | RSI={rsi:.1f}")
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
                    trade.entry,  # Fixed: was entry_price
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
                if should_buy(indicators, trend):
                    coins_with_signals.append(coin)

            # Random trade amount per coin within limits
            if coins_with_signals:
                # Each coin gets random amount between MIN and MAX
                pass  # Placeholder, actual logic below

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
            wallet_snapshot = wallet.snapshot()
            logger.info(
                f"Wallet: Total=${wallet_snapshot['total']:.2f} "
                f"Free=${wallet_snapshot['free']:.2f} "
                f"Used=${wallet_snapshot['used']:.2f} "
                f"Profit=${wallet_snapshot['profit']:.4f}"
            )

            save_state(
                wallet,
                simulator.trades,
                phase="PHASE_3_TRADING",
                runtime_elapsed=int(elapsed),
                runtime_total=MAX_RUNTIME_SECONDS,
            )

            # No sleep - continuous trading!

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
    global wallet, simulator

    logger.info("\n" + "=" * 60)
    logger.info("PHASE 4: AUTO-SHUTDOWN")
    logger.info("=" * 60)

    # Close all open trades
    open_trades = [t for t in simulator.trades if t.open]

    if open_trades:
        logger.info(f"Closing {len(open_trades)} open trades...")

        for trade in open_trades:
            try:
                current_price = get_current_price(trade.coin)
                pnl_usdt, pnl_pct = simulator.close_trade(trade, current_price)
                logger.info(
                    f"  Closed {trade.coin}: PnL=${pnl_usdt:.4f} ({pnl_pct:.2f}%)"
                )
            except Exception as e:
                logger.error(f"  Failed to close {trade.coin}: {e}")

    # Final wallet snapshot
    wallet_snapshot = wallet.snapshot()
    logger.info("\nFINAL REPORT:")
    logger.info(f"  Total USDT: ${wallet_snapshot['total']:.2f}")
    logger.info(f"  Total Profit: ${wallet_snapshot['profit']:.4f}")

    profit_pct = (wallet_snapshot["profit"] / ALLOTED_USDT) * 100
    logger.info(f"  Profit %: {profit_pct:+.2f}%")

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
    global wallet, simulator

    # Print startup banner
    print("\n" + "=" * 60)
    print("[$] SikkaTrade AI-Powered Trading Engine")
    print("   Author: Hassan Ali (@softdevhassan)")
    print("=" * 60)
    print(
        f"Mode: [{APP_MODE.upper()}] {'LIVE TRADING - REAL MONEY' if IS_LIVE_MODE else 'SIMULATION - FAKE MONEY'}"
    )
    print(f"Coins: {', '.join(COINS)}")
    print(f"Max Runtime: {MAX_RUNTIME_SECONDS}s")
    print(f"Analysis Interval: {ANALYSIS_LIVE_SECONDS}s")
    print(f"Parallel Trades: {PARALLEL_TRADES}")
    print("=" * 60)
    print()

    # Initialize wallet and simulator
    wallet = initialize_wallet()
    simulator = TradeSimulator(
        wallet, TAKE_PROFIT_PERCENT, STOP_LOSS_PERCENT, PARALLEL_TRADES
    )

    logger.info("Engine initialized successfully\n")

    try:
        # Execute 4-phase trading system
        phase1_historical_analysis()
        phase2_live_monitoring()
        phase3_trading()
    except KeyboardInterrupt:
        logger.info("\n[!] Keyboard interrupt received")
    except Exception as e:
        logger.error(f"[X] Fatal error: {e}", exc_info=True)
    finally:
        phase4_shutdown()


if __name__ == "__main__":
    main()
