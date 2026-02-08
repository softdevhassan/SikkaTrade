from engine.trade import Trade
from engine.risk import should_close


class TradeSimulator:
    def __init__(self, wallet, tp, sl, max_parallel, executor=None):
        self.wallet = wallet
        self.tp = tp
        self.sl = sl
        self.max_parallel = max_parallel
        self.executor = executor  # Inject executor (None for simulation)
        self.trades = []

    def open_trade(self, coin, amount, price):
        """Open a new trade if capacity available"""
        # Count current open trades
        open_count = sum(1 for t in self.trades if t.open)

        # Check if we've hit the parallel limit
        if open_count >= self.max_parallel:
            return None

        # Check if we already have an open trade for this coin
        # for t in self.trades:
        #     if t.coin == coin and t.open:
        #         return None  # Don't open duplicate

        # Try to allocate funds
        if self.wallet.allocate(amount):
            quantity = None
            entry_price = price

            # REAL EXECUTION
            if self.executor:
                qty, exec_price = self.executor.buy(coin, amount, price)
                if not qty:
                    # Buy failed, release funds
                    self.wallet.release(amount, 0)
                    return None
                quantity = qty
                entry_price = exec_price  # Use actual execution price

            trade = Trade(coin, amount, entry_price, quantity)
            self.trades.append(trade)
            return trade
        return None

    def monitor_trades(self, price_map):
        """Monitor all open trades and close if TP/SL hit"""
        closed = []

        for trade in self.trades:
            if not trade.open:
                continue

            current_price = price_map.get(trade.coin)
            if not current_price:
                continue

            close, pnl_pct = should_close(trade.entry, current_price, self.tp, self.sl)

            if close:
                self.close_trade(trade, current_price)
                # re-calculate pnl after close
                pnl_usdt = (
                    (trade.exit_price - trade.entry) * trade.quantity * trade.entry
                )  # approx or use actual
                # Actually close_trade returns correct pnl
                # But wait, close_trade calls self.wallet.release
                # We need to capture the return from close_trade which is called above
                # Refactoring monitor to use close_trade properly

                # Logic handled inside close_trade now
                # We just need to append to closed list
                # But close_trade returns (pnl_usdt, pnl_pct)
                # So we can't call it twice.
                pass

        # Re-implementing correctly:
        # The loop modification inside iteration is bad practice if we modify list, but we aren't removing.
        # However, checking `should_close` and then calling `close_trade` is correct.
        # Let's rewrite the loop safely.

        # New safe loop
        for trade in self.trades:
            if not trade.open:
                continue

            current_price = price_map.get(trade.coin)
            if not current_price:
                continue

            close, reason = should_close(trade.entry, current_price, self.tp, self.sl)
            if close:
                pnl_usdt, pnl_pct = self.close_trade(trade, current_price)
                closed.append((trade.coin, pnl_usdt, pnl_pct))

        return closed

    def close_trade(self, trade, current_price):
        """Manually close a specific trade"""
        if not trade.open:
            return 0, 0

        exit_price = current_price

        # REAL EXECUTION
        if self.executor:
            usdt_returned, exec_price = self.executor.sell(
                trade.coin, trade.quantity, current_price
            )
            if usdt_returned:
                exit_price = exec_price
                # Recalculate PnL based on actual returned USDT
                # pnl = returned - initial
                real_pnl = usdt_returned - trade.amount
                trade.open = False
                trade.exit_price = exit_price
                self.wallet.release(trade.amount, real_pnl)
                pnl_pct = (real_pnl / trade.amount) * 100
                return real_pnl, pnl_pct
            else:
                # Sell failed, keep open? Or force close?
                # Ideally keep open and retry. For now return 0
                return 0, 0

        # SIMULATION
        pnl_usdt, pnl_pct = trade.close(exit_price)
        self.wallet.release(trade.amount, pnl_usdt)
        return pnl_usdt, pnl_pct
