from engine.trade import Trade
from engine.risk import should_close


class TradeSimulator:
    def __init__(self, wallet, tp, sl, max_parallel):
        self.wallet = wallet
        self.tp = tp
        self.sl = sl
        self.max_parallel = max_parallel
        self.trades = []

    def open_trade(self, coin, amount, price):
        """Open a new trade if capacity available"""
        # Count current open trades
        open_count = sum(1 for t in self.trades if t.open)

        # Check if we've hit the parallel limit
        if open_count >= self.max_parallel:
            return None

        # Check if we already have an open trade for this coin
        for t in self.trades:
            if t.coin == coin and t.open:
                return None  # Don't open duplicate

        # Try to allocate funds
        if self.wallet.allocate(amount):
            trade = Trade(coin, amount, price)
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
                pnl_usdt, _ = trade.close(current_price)
                self.wallet.release(trade.amount, pnl_usdt)
                closed.append((trade.coin, pnl_usdt, pnl_pct))

        return closed

    def close_trade(self, trade, current_price):
        """Manually close a specific trade"""
        if not trade.open:
            return 0, 0

        pnl_usdt, pnl_pct = trade.close(current_price)
        self.wallet.release(trade.amount, pnl_usdt)
        return pnl_usdt, pnl_pct
