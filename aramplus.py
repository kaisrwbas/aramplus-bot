
import yfinance as yf
import vectorbt as vbt
import pandas as pd
import numpy as np
import os

# --- CONFIG ---
SYMBOL = "BTC-USD"
INIT_CASH = 10000
MA_WINDOW = 50
RSI_THRESHOLD = 60
SL_PERCENT = 0.05
TP_PERCENT = 0.10

# --- DATA ---
print("📥 Fetching data...")
btc = yf.download(SYMBOL, period="1y", interval="1d", progress=False)

# Flatten multi-index (if any)
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = [c[0] for c in btc.columns]
btc = btc[['Close']].dropna()

# --- INDICATORS ---
def rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

btc['MA'] = btc['Close'].rolling(MA_WINDOW).mean()
btc['RSI'] = rsi(btc['Close'])
btc = btc.dropna()

# --- SIGNAL ---
btc['Signal'] = (
    (btc['Close'] > btc['MA']) & 
    (btc['RSI'] < RSI_THRESHOLD)
).astype(int)

# --- BACKTEST ---
entries = btc['Signal'].astype(bool)
exits = (~entries).shift(1).fillna(False)
port = vbt.Portfolio.from_signals(
    btc['Close'], entries, exits,
    init_cash=INIT_CASH, fees=0.001
)

# --- LATEST SIGNAL ---
latest_signal = btc['Signal'].iloc[-1]
current_price = btc['Close'].iloc[-1]
last_ma = btc['MA'].iloc[-1]
last_rsi = btc['RSI'].iloc[-1]

print(f"📈 {SYMBOL} | Price: ${current_price:.2f}")
print(f"📊 MA({MA_WINDOW}): ${last_ma:.2f} | RSI: {last_rsi:.1f}")
print(f"🎯 Signal: {'🟢 BUY' if latest_signal else '🔴 NO TRADE'}")

# --- OUTPUT FOR AUTOMATION ---
# ✅ NEW (works everywhere):
import os

# Save outputs in current directory (where script runs)
with open("signal.txt", "w") as f:
    f.write("BUY" if latest_signal else "HOLD")
with open("price.txt", "w") as f:
    f.write(f"{current_price:.2f}")

print("✅ Signal & price saved to current directory.")
