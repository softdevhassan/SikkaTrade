# SikkaTrade - AI-Powered Crypto Trading Bot

> **Automated cryptocurrency trading system with technical analysis and AI-powered decision making**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ⚠️ Important: DEV vs PROD Mode

### 🧪 DEV Mode (Current Default - Testing Only)

**Purpose:** Testing and demonstration  
**Behavior:**

- Uses **FAKE MONEY** (simulation)
- Trades auto-close after **8 seconds** for demo purposes
- Relaxed buy conditions (RSI < 85, Trend UP)
- Random trade amounts ($0.10 - $2.00)
- **NOT designed for profit** - just validates system works

### 💰 PROD Mode (Live Trading - Real Money)

**Purpose:** Actual profit generation  
**Behavior:**

- Uses **REAL MONEY** via Binance API
- Trades close on proper TP/SL or technical signals
- Strict buy conditions (5 criteria including MACD, Bollinger Bands, Volume)
- Configurable trade amounts
- **Designed for profit** with risk management

**To switch:** Set `APP_MODE=prod` in `.env` (⚠️ Test thoroughly first!)

---

## ✨ Features

- **🤖 AI-Powered Analysis**: Smart buy/sell decisions based on RSI, MACD, Bollinger Bands, and volume analysis
- **📊 Real-Time Dashboard**: Beautiful Tailwind CSS UI with live trade tracking
- **⚡ Fast Execution**: Continuous trading with no delays between cycles
- **🛡️ Risk Management**: Built-in take-profit and stop-loss protection
- **🔄 Dual Mode**: Dev mode (simulation) and Prod mode (live trading)
- **📈 Multi-Coin**: Trade multiple cryptocurrencies simultaneously

## 🚀 Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/SikkaTrade.git
cd SikkaTrade

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your Binance API keys

# 4. Start trading
python start.py
```

**Dashboard will auto-open at:** `http://localhost:8501`

## 📖 Documentation

- **[Setup Guide](SETUP.md)** - Detailed installation and configuration
- **[Developer Guide](DEVELOPER.md)** - Architecture and development docs

## ⚙️ Configuration

### Dev Mode (Simulation - Fake Money)

```ini
APP_MODE=dev
ALLOTED_USDT=10
MAX_RUNTIME_SECONDS=30
```

**Expected Behavior:**

- Trades open/close rapidly (8-second timeout)
- Many small trades for testing
- No real profit expected

### Prod Mode (Live Trading - Real Money) ⚠️

```ini
APP_MODE=prod
ALLOTED_USDT=100
MAX_RUNTIME_SECONDS=3600
```

**Expected Behavior:**

- Trades held until TP/SL or technical exit
- Fewer, larger trades
- Designed for profit with risk management

**Always test in `dev` mode first!**

## 🎯 How It Works

### 4-Phase Trading System

1. **📊 Historical Analysis** - Analyzes 48h, 24h, 12h, 6h, 1h candles
2. **👀 Live Monitoring** - Tracks real-time price movements
3. **⚡ Smart Trading** - Opens/closes trades based on indicators
4. **🛑 Auto-Shutdown** - Closes all positions at max runtime

### Buy Conditions

**Dev Mode (Relaxed for Testing):**

- RSI < 85 (very lenient)
- 24h trend is UP
- **Result:** Many trades open quickly

**Prod Mode (Strict for Profit):**

- RSI < 40 (oversold)
- MACD > MACD Signal (bullish crossover)
- Price near Bollinger lower band
- 24h trend is UP
- Volume > 1.5x average
- **Result:** Fewer, high-quality setups

### Sell Conditions

**Dev Mode:**

- 8-second timeout (for demo)
- OR RSI > 95
- OR TP/SL hit

**Prod Mode:**

- RSI > 70 (overbought)
- Take Profit (+2%)
- Stop Loss (-1.5%)
- MACD bearish crossover

## 🛡️ Safety Features

- **✅ Virtual Wallet** - Dev mode uses fake money
- **✅ Parallel Limits** - Max 10 concurrent trades
- **✅ Random Amounts** - Dev: $0.10-$2.00, Prod: configurable
- **✅ Auto Shutdown** - Closes all trades at max runtime

## 🔧 Tech Stack

- **Backend**: Python 3.11+
- **UI**: Streamlit + Remix Icons + Custom CSS
- **Data**: Binance API
- **Analysis**: pandas-ta (RSI, MACD, Bollinger Bands)

## 📝 FAQ

**Q: Why are only 2 coins trading?**  
A: In DEV mode, coins need RSI < 85 AND 24h trend UP. If DOGE's trend is SIDEWAYS/DOWN, it won't trade.

**Q: Why do trades close so fast?**  
A: DEV mode has 8-second auto-close for testing. Real profit mode (PROD) holds trades properly.

**Q: How do I make actual profit?**  
A: Switch to `APP_MODE=prod`, increase `ALLOTED_USDT`, set `MAX_RUNTIME_SECONDS=86400` (24h), and use proper Binance API keys with trading permissions.

## 📝 License

MIT License - see [LICENSE](LICENSE) file

## 👨‍💻 Author

**Hassan Ali** ([@softdevhassan](https://github.com/softdevhassan))

## ⚠️ Disclaimer

**Trading cryptocurrencies involves substantial risk of loss.** This bot is provided for educational purposes. Always:

- Test thoroughly in `dev` mode first
- Start with small amounts in `prod` mode
- Never invest more than you can afford to lose
- Use API key restrictions (IP whitelist, trading-only permissions)

---

**Made with ❤️ by Hassan Ali**
