import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class Executor:
    """Base executor (Simulation)"""

    def buy(self, coin, usdt_amount, price):
        # Simulating buy
        quantity = usdt_amount / price
        logger.info(
            f"[SIM] BUY {coin} | ${usdt_amount} @ ${price} | Qty={quantity:.6f}"
        )
        return quantity, price

    def sell(self, coin, quantity, price):
        # Simulating sell
        usdt_amount = quantity * price
        logger.info(
            f"[SIM] SELL {coin} | {quantity:.6f} @ ${price} | Total=${usdt_amount:.2f}"
        )
        return usdt_amount, price


class BinanceExecutor(Executor):
    """Real trading executor using Binance API"""

    def __init__(self, client, method="SPOT"):
        self.client = client
        self.method = method.upper()
        self._symbol_info_cache = {}

    def _get_step_size(self, symbol):
        """Fetch stepSize for quantity precision"""
        if symbol not in self._symbol_info_cache:
            try:
                info = self.client.get_symbol_info(symbol)
                for f in info["filters"]:
                    if f["filterType"] == "LOT_SIZE":
                        self._symbol_info_cache[symbol] = float(f["stepSize"])
                        break
            except Exception as e:
                logger.error(f"Error fetching symbol info for {symbol}: {e}")
                return 0.000001  # Safe fallback
        return self._symbol_info_cache.get(symbol, 0.000001)

    def _truncate(self, value, step_size):
        """Truncate value according to stepSize using Decimal for precision"""
        from decimal import Decimal, ROUND_DOWN

        if step_size <= 0:
            return value

        # Determine precision from step_size
        step_str = f"{step_size:f}".rstrip("0")
        if "." in step_str:
            precision = len(step_str.split(".")[1])
        else:
            precision = 0

        # Use Decimal to floor the value to the correct precision
        d_value = Decimal(str(value))
        d_step = Decimal(str(step_size))

        # Formula: floor(value / step) * step
        truncated = (d_value // d_step) * d_step
        return float(truncated)

    def buy(self, coin, usdt_amount, price=None):
        symbol = f"{coin}USDT"

        if self.method == "CONVERT":
            return self._convert_trade("USDT", coin, usdt_amount)
        else:
            return self._spot_buy(symbol, usdt_amount)

    def sell(self, coin, quantity, price=None):
        symbol = f"{coin}USDT"

        if self.method == "CONVERT":
            return self._convert_trade(coin, "USDT", quantity)
        else:
            # Truncate quantity for SPOT sell
            step_size = self._get_step_size(symbol)
            truncated_qty = self._truncate(quantity, step_size)
            logger.debug(
                f"Truncated {quantity} to {truncated_qty} for {symbol} (stepSize: {step_size})"
            )
            return self._spot_sell(symbol, truncated_qty)

    def _spot_buy(self, symbol, usdt_amount):
        """Execute Spot Market Buy"""
        try:
            logger.info(f"[SPOT] Buying {symbol} with ${usdt_amount}...")
            # Spot Market Buy using quoteOrderQty (USDT amount)
            # Binance handles the quantity calculation based on market price
            order = self.client.order_market_buy(
                symbol=symbol, quoteOrderQty=usdt_amount
            )
            # Parse execution
            filled_qty = float(order["executedQty"])
            cummulative_quote_qty = float(
                order["cummulativeQuoteQty"]
            )  # Total USDT spent
            avg_price = cummulative_quote_qty / filled_qty

            logger.info(f"[SPOT] BOUGHT {symbol}: Qty={filled_qty} @ ${avg_price:.4f}")
            return filled_qty, avg_price
        except Exception as e:
            logger.error(f"[!] Spot Buy Failed: {e}")
            return None, None

    def _spot_sell(self, symbol, quantity):
        """Execute Spot Market Sell"""
        try:
            logger.info(f"[SPOT] Selling {quantity} {symbol}...")
            # We use the truncated quantity here
            order = self.client.order_market_sell(
                symbol=symbol, quantity=f"{quantity:f}"
            )

            filled_qty = float(order["executedQty"])
            cummulative_quote_qty = float(
                order["cummulativeQuoteQty"]
            )  # Total USDT received
            avg_price = cummulative_quote_qty / filled_qty

            logger.info(
                f"[SPOT] SOLD {symbol}: ${cummulative_quote_qty:.2f} @ ${avg_price:.4f}"
            )
            return cummulative_quote_qty, avg_price
        except Exception as e:
            logger.error(f"[!] Spot Sell Failed for {symbol} (Qty: {quantity}): {e}")
            return None, None

    def _convert_trade(self, from_asset, to_asset, amount):
        """Execute Binance Convert"""
        try:
            logger.info(f"[CONVERT] Swapping {amount} {from_asset} -> {to_asset}...")

            # 1. Get Quote
            quote = self.client.convert_get_quote(
                fromAsset=from_asset, toAsset=to_asset, fromAmount=amount
            )

            quote_id = quote["quoteId"]
            to_qty = float(quote["toAmount"])
            ratio = float(quote["ratio"])

            logger.info(
                f"   Quote: 1 {from_asset} = {ratio} {to_asset} | Get: {to_qty}"
            )

            # 2. Accept Quote
            # Note: Quoted price expires in seconds
            trade = self.client.convert_accept_quote(quoteId=quote_id)

            if trade["orderStatus"] == "SUCCESS":
                logger.info(
                    f"[CONVERT] SUCCESS! Swapped {amount} {from_asset} -> {to_qty} {to_asset}"
                )

                # If buying (USDT->COIN), return (qty, price)
                # If selling (COIN->USDT), return (usdt, price)

                if from_asset == "USDT":
                    # Buying: return coin_qty, avg_price
                    avg_price = amount / to_qty
                    return to_qty, avg_price
                else:
                    # Selling: return usdt_amt, avg_price
                    avg_price = to_qty / amount
                    return to_qty, avg_price

            else:
                logger.error(f"[!] Convert Failed: Status {trade['orderStatus']}")
                return None, None

        except Exception as e:
            logger.error(f"[!] Convert Error: {e}")
            return None, None
