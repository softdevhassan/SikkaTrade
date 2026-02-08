# Setup Guide

Complete installation and configuration guide for SikkaTrade.

## Prerequisites

### System Requirements

- **OS**: Windows 10/11, macOS, or Linux
- **Python**: 3.11 or higher
- **RAM**: Minimum 2GB
- **Internet**: Stable connection required

### Binance Account Setup

1. **Create Binance Account**
   - Visit [binance.com](https://www.binance.com)
   - Complete KYC verification

2. **Generate API Keys**
   - Go to Account → API Management
   - Create New Key
   - **Enable**: "Enable Reading" and "Enable Spot & Margin Trading"
   - **Disable**: "Enable Withdrawals"
   - Save API Key and Secret Key (you won't see secret again!)

3. **Restrict API Key** (Highly Recommended)
   - Add IP whitelist in API settings
   - Restrict to trading-only permissions

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/SikkaTrade.git
cd SikkaTrade
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\\Scripts\\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**

- `python-binance` - Binance API client
- `streamlit` - Web dashboard
- `streamlit-autorefresh` - Auto-refresh UI
- `pandas-ta` - Technical indicators
- `python-dotenv` - Environment variables

### Step 4: Configure Environment

1. **Copy example file:**

```bash
cp .env.example .env
```

2. **Edit `.env` file:**

```ini
# Mode: dev (simulation) or prod (live trading)
APP_MODE=dev

# Your Binance API Keys
BINANCE_API_KEY=YOUR_API_KEY_HERE
BINANCE_SECRET_KEY=YOUR_SECRET_KEY_HERE

# Trading pairs (comma-separated)
COINS=BTC,ETH,DOGE

# Wallet allocation (USDT)
ALLOTED_USDT=10

# Max concurrent trades
PARALLEL_TRADES=10

# Trade amount limits (USDT)
MIN_SPOT_TRADE_USDT=0.1
MAX_SPOT_TRADE_USDT=2

# Risk management
TAKE_PROFIT_PERCENT=0.3    # 0.3%
STOP_LOSS_PERCENT=0.15     # 0.15%

# Runtime limit (seconds)
MAX_RUNTIME_SECONDS=30

# Analysis interval (seconds)
ANALYSIS_LIVE_SECONDS=5

# RSI thresholds
RSI_OVERSOLD=85   # Dev: 85, Prod: 40
RSI_OVERBOUGHT=95 # Dev: 95, Prod: 70
```

## Running the Bot

### Development Mode (Simulation)

```bash
python start.py
```

**What happens:**

1. Trading engine starts (app.py)
2. Dashboard launches at `http://localhost:8501`
3. Bot uses **virtual wallet** with fake money
4. All trades are simulated

**Expected output:**

```
============================================================
[$] SikkaTrade AI-Powered Trading Engine
============================================================
Mode: [DEV] SIMULATION - FAKE MONEY
Coins: BTC, ETH, DOGE
Max Runtime: 30s
```

### Production Mode (Live Trading) ⚠️

**Before going live:**

1. Test thoroughly in dev mode
2. Verify API keys have IP restrictions
3. Start with small `ALLOTED_USDT` amount
4. Monitor first few runs closely

**Enable prod mode:**

```ini
APP_MODE=prod
RSI_OVERSOLD=40
RSI_OVERBOUGHT=70
```

**Run:**

```bash
python start.py
```

## Dashboard Navigation

### Home Screen

- **Wallet Metrics**: Total, Free, Used, Profit
- **Live Trades Table**: Real-time trade tracking
- **Progress Bar**: Phase and runtime indicator

### Trade Table Columns

- `#` - Trade number
- `Time` - Entry time (12hr format)
- `Coin` - Cryptocurrency symbol
- `Entry` - Entry price (USDT)
- `Amount` - Trade amount (USDT)
- `Status` - OPEN or CLOSED
- `PnL` - Profit/Loss (USDT)

## Troubleshooting

### Issue: API Connection Error

```
BinanceAPIException: Invalid API-key
```

**Solution:**

- Verify API key and secret in `.env`
- Check API key is enabled
- Ensure IP is whitelisted

### Issue: No Trades Opening

```
[BUY SIGNAL] but Wallet: Free=$0.00
```

**Solution:**

- Check `MIN_SPOT_TRADE_USDT` < `ALLOTED_USDT / COINS`
- Increase `ALLOTED_USDT` or decrease `MIN_SPOT_TRADE_USDT`

### Issue: Dashboard Not Loading

**Solution:**

1. Check if port 8501 is available
2. Try `streamlit run gui.py --server.port 8502`
3. Clear browser cache

### Issue: Module Not Found

```
ModuleNotFoundError: No module named 'streamlit'
```

**Solution:**

```bash
pip install -r requirements.txt
```

## Next Steps

1. ✅ Run in dev mode and observe behavior
2. ✅ Adjust RSI/MACD thresholds for testing
3. ✅ Review trade history in dashboard
4. ✅ When confident, switch to prod with small amount
5. ✅ Monitor logs and dashboard closely

## Security Best Practices

- ✅ Never commit `.env` file to git
- ✅ Use IP whitelist on Binance API
- ✅ Disable withdrawal permissions
- ✅ Start with minimal `ALLOTED_USDT` in prod
- ✅ Monitor trades in real-time

## Support

Need help? Check:

- [Developer Guide](DEVELOPER.md) - Architecture details
- [GitHub Issues](https://github.com/yourusername/SikkaTrade/issues)

---

**Ready to trade!** Run `python start.py` and watch the magic happen! ✨
