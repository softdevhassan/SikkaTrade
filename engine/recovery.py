import json
import os
import time
from datetime import datetime
from config.settings import ANALYSIS_LIVE_SECONDS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "..", "state.json")


def save_state(wallet, trades, phase="TRADING", runtime_elapsed=0, runtime_total=3600):
    """Save current state for GUI with full trade history"""
    wallet_snapshot = wallet.snapshot()

    # Build complete trade history with timestamps and PnL
    trades_history = []
    for idx, t in enumerate(trades, 1):
        current_price = t.exit_price if not t.open else t.entry
        pnl_usdt = 0
        if not t.open and t.exit_price:
            pnl_usdt = (t.exit_price - t.entry) * (t.amount / t.entry)

        trades_history.append(
            {
                "no": idx,
                "time": (
                    t.timestamp
                    if hasattr(t, "timestamp")
                    else datetime.now().strftime("%I:%M:%S %p")
                ),
                "coin": t.coin,
                "entry_price": round(t.entry, 2),
                "amount": round(t.amount, 2),
                "status": "OPEN" if t.open else "CLOSED",
                "pnl": round(pnl_usdt, 4),
            }
        )

    state = {
        "wallet": wallet_snapshot,
        "trades_history": trades_history,  # Full history with all details
        "phase": phase,
        "runtime_elapsed": runtime_elapsed,
        "runtime_total": runtime_total,
        "last_update": datetime.now().strftime("%I:%M:%S %p"),
    }

    with open("state.json", "w") as f:
        json.dump(state, f, indent=2)
