# Developer Guide

Technical documentation for contributors and developers.

## Architecture Overview

```
SikkaTrade/
├── app.py              # Main trading engine (4 phases)
├── start.py            # Auto-launcher (engine + dashboard)
├── gui.py              # Streamlit dashboard (Tailwind UI)
├── config/
│   └── settings.py     # Configuration loader
├── engine/
│   ├── wallet.py       # VirtualWallet & BinanceWallet
│   ├── simulator.py    # Trade simulation & management
│   ├── trade.py        # Trade object model
│   ├── risk.py         # Risk management (TP/SL)
│   └── recovery.py     # State persistence
├── data/
│   └── binance_data.py # API data fetching
└── analysis/
    ├──indicators.py   # Technical indicators (RSI, MACD, BB)
    └── smart_decision.py # Buy/sell logic
```

## System Flow

### 1. Startup (`start.py`)

```python
1. Launch app.py (trading engine) in background
2. Wait for state.json creation
3. Launch gui.py (Streamlit dashboard)
4. Stream engine logs to console
5. Auto-terminate dashboard when engine stops
```

### 2. Trading Engine (`app.py`)

#### Phase 1: Historical Analysis

- Fetches 48h, 24h, 12h, 6h, 1h candles
- Calculates RSI, MACD, Bollinger Bands
- Determines overall trend (UP/DOWN/SIDEWAYS)

#### Phase 2: Live Monitoring

- Continuous price tracking
- Real-time indicator updates
- Saves state every cycle

#### Phase 3: Smart Trading

- **Buy Logic**: Checks conditions per coin
- **Sell Logic**: Monitors open trades for TP/SL
- **Random Amounts**: Each trade gets $0.1-$2 USDT
- **No Delays**: Continuous execution

#### Phase 4: Shutdown

- Closes all open trades
- Saves final state with `phase="SHUTDOWN"`
- Dashboard detects and shows end screen

## Key Components

### Engine Module

#### `VirtualWallet` (engine/wallet.py)

```python
class VirtualWallet:
    def __init__(self, initial_usdt):
        self.total =  initial_usdt
        self.used = 0

    def allocate(self, amount) -> bool:
        # Reserve funds for trade

    def release(self, amount, pnl):
        # Return funds + profit/loss
```

#### `TradeSimulator` (engine/simulator.py)

```python
class TradeSimulator:
    def open_trade(self, coin, amount, price):
        # Opens trade if:
        # - Not duplicate coin
        # - Under parallel limit
        # - Wallet has funds

    def monitor_trades(self, price_map):
        # Auto-close on TP/SL

    def close_trade(self, trade, price):
        # Manual close (shutdown)
```

#### `Trade` (engine/trade.py)

```python
class Trade:
    coin: str
    amount: float
    entry: float
    open: bool
    exit_price: float | None
    timestamp: str
```

### Analysis Module

#### Technical Indicators (analysis/indicators.py)

```python
def calculate_rsi(df, period=14):
    # Relative Strength Index

def calculate_macd(df):
    # MACD + Signal + Histogram

def calculate_bollinger_bands(df):
    # Upper, Middle, Lower bands

def analyze_trend(df):
    # Returns: "UP", "DOWN", "SIDEWAYS"
```

#### Decision Logic (analysis/smart_decision.py)

```python
def should_buy(indicators, trend):
    # Dev: RSI < 85 + Trend UP
    # Prod: 5 conditions (RSI, MACD, BB, Trend, Volume)

def should_sell(indicators, entry_price, current_price, tp%, sl%):
    # Returns: (should_close, reason)
    # Checks: TP/SL, RSI overbought, MACD bearish
```

## State Management

### state.json Structure

```json
{
  "wallet": {
    "total": 10.0,
    "free": 7.2,
    "used": 2.8,
    "profit": -0.0015
  },
  "trades_history": [
    {
      "no": 1,
      "time": "07:45:32 PM",
      "coin": "BTC",
      "entry_price": 71200.5,
      "amount": 1.23,
      "status": "OPEN",
      "pnl": 0.0045
    }
  ],
  "phase": "PHASE_3_TRADING",
  "runtime_elapsed": 15,
  "runtime_total": 30
}
```

## UI Components (gui.py)

### Tailwind + Remix Icons Integration

```html
<!-- CDN Injection -->
<link
  href="https://cdn.jsdelivr.net/npm/remixicon@4.0.0/fonts/remixicon.css"
  rel="stylesheet"
/>
<script src="https://cdn.tailwindcss.com"></script>

<!-- Icon Usage -->
<i class="ri-wallet-3-line text-blue-400"></i>
<i class="ri-line-chart-line text-purple-400"></i>
```

### Auto-Refresh

```python
st_autorefresh(interval=500, key="refresh")  # 500ms
```

## Adding New Features

### Add New Indicator

1. **Create function** in `analysis/indicators.py`:

```python
def calculate_stochastic(df, period=14):
    return df.ta.stoch(period=period)
```

2. **Update** `get_latest_indicators()`:

```python
indicators["stoch_k"] = latest["STOCHk_14"]
indicators["stoch_d"] = latest["STOCHd_14"]
```

3. **Use in decision** logic:

```python
if indicators["stoch_k"] < 20:  # Oversold
    buy_signal = True
```

### Add New Coin

Simply update `.env`:

```ini
COINS=BTC,ETH,DOGE,SOL,ADA
```

### Customize UI Theme

Edit Tailwind config in `gui.py`:

```javascript
tailwind.config = {
  theme: {
    extend: {
      colors: {
        primary: "#your_color",
      },
    },
  },
};
```

## Testing

### Unit Testing (Recommended)

```python
# tests/test_wallet.py
def test_virtual_wallet_allocate():
    wallet = VirtualWallet(100)
    assert wallet.allocate(50) == True
    assert wallet.free == 50
```

### Integration Testing

1. Set `MAX_RUNTIME_SECONDS=10`
2. Run `python start.py`
3. Verify all phases execute
4. Check `state.json` structure

## Performance Optimization

### Reduce API Calls

- Cache klines data (5 second intervals)
- Reuse price data across coins
- Batch indicator calculations

### Memory Management

- Limit trade history size
- Clear old candle data
- Use pandas efficiently

## Security Considerations

### API Key Protection

- Never log API keys
- Use environment variables only
- Restrict IP addresses
- Disable withdrawal permissions

### Input Validation

- Validate all user inputs from `.env`
- Handle API errors gracefully
- Sanitize coin symbols

## Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-feature`
3. Make changes with clear commits
4. Test thoroughly in dev mode
5. Submit pull request

## Code Style

- **PEP 8** for Python code
- **Type hints** for function signatures
- **Docstrings** for complex functions
- **Comments** for non-obvious logic

## License

MIT License - see LICENSE file

---

**Questions?** Open an issue on GitHub!
