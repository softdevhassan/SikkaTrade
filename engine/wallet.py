class VirtualWallet:
    """Virtual wallet for simulation mode - no real money"""

    def __init__(self, balance):
        self.total = balance
        self.free = balance
        self.used = 0
        self.profit = 0

    def allocate(self, amount):
        if self.free >= amount:
            self.free -= amount
            self.used += amount
            return True
        return False

    def release(self, amount, pnl):
        self.used -= amount
        self.free += amount + pnl
        self.profit += pnl

    def snapshot(self):
        return {
            "total": round(self.total + self.profit, 4),
            "free": round(self.free, 4),
            "used": round(self.used, 4),
            "profit": round(self.profit, 4),
        }


class BinanceWallet:
    """Live wallet for real trading - uses actual Binance account"""

    def __init__(self, client):
        self.client = client
        self.initial_balance = 0
        self.used = 0
        self.profit = 0

        # Fetch initial USDT balance from Binance
        self._fetch_balance()

    def _fetch_balance(self):
        """Fetch current USDT balance from Binance"""
        try:
            account = self.client.get_account()
            for asset in account["balances"]:
                if asset["asset"] == "USDT":
                    total_usdt = float(asset["free"]) + float(asset["locked"])
                    if self.initial_balance == 0:
                        self.initial_balance = total_usdt
                    return total_usdt
            return 0
        except Exception as e:
            print(f"[!] Error fetching Binance balance: {e}")
            return 0

    def allocate(self, amount):
        """Allocate USDT for a trade"""
        current_balance = self._fetch_balance()
        free = current_balance - self.used

        if free >= amount:
            self.used += amount
            return True
        return False

    def release(self, amount, pnl):
        """Release allocated USDT and record profit/loss"""
        self.used -= amount
        self.profit += pnl

    def snapshot(self):
        """Get current wallet state"""
        current_balance = self._fetch_balance()
        free = current_balance - self.used

        return {
            "total": round(current_balance, 4),
            "free": round(free, 4),
            "used": round(self.used, 4),
            "profit": round(self.profit, 4),
        }
