from datetime import datetime
import time


class Trade:
    def __init__(self, coin, amount, entry_price):
        self.coin = coin
        self.amount = amount
        self.entry = entry_price
        self.open = True
        self.exit_price = None
        self.timestamp = datetime.now().strftime("%I:%M:%S %p")
        self.entry_time = time.time()  # For time-based closing in DEV

    def close(self, exit_price):
        pnl_pct = (exit_price - self.entry) / self.entry
        pnl_usdt = self.amount * pnl_pct
        self.open = False
        self.exit_price = exit_price
        return pnl_usdt, pnl_pct * 100
