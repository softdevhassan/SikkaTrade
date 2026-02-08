# Why Only 2 Trades Open?

## Issue

Free balance = $8.08, but only BTC and ETH trading. DOGE never opens despite having balance.

## Root Cause

**DEV Mode Buy Conditions** (see `analysis/smart_decision.py`):

```python
# Both must be TRUE:
1. RSI < 85  ✓ (DOGE RSI is usually 50-52)
2. Trend = UP  ✗ (DOGE trend is SIDEWAYS or DOWN)
```

## Example from Logs

```
[DEV BUY CHECK] RSI=74.0<85.0? [Y] | Trend=UP? [Y]  → BTC opens ✓
[DEV BUY CHECK] RSI=64.5<85.0? [Y] | Trend=UP? [Y]  → ETH opens ✓
[DEV BUY CHECK] RSI=51.9<85.0? [Y] | Trend=UP? [N]  → DOGE rejected ✗
```

DOGE ka 24h trend UP nahi hai, so buy signal fail!

## Solution Options

### Option 1: Remove Trend Check (DEV Only)

```ini
# .env
# Set very high threshold
RSI_OVERSOLD=90
```

### Option 2: Trade More Coins

```ini
# .env
COINS=BTC,ETH,DOGE,SOL,ADA,XRP
```

More coins = higher chance some have UP trends

### Option 3: Use PROD Mode

PROD mode has 5 strict conditions but will wait for proper setups on all coins.

## Current Behavior is CORRECT

System is working as designed - only trading coins with favorable conditions (RSI + Trend).
