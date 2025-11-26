import yfinance as yf
import vectorbt as vbt
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

# Config
SYMBOL = "BTC-USD"
INIT_CASH = 10000
MA_WINDOW = 50
RSI_THRESHOLD = 60

# Fetch & clean data
btc = yf.download(SYMBOL, period="1y", interval="1d", progress=False)
if isinstance(btc.columns, pd.MultiIndex):
    btc.columns = [c[0] for c in btc.columns]
btc = btc[['Close']].dropna()

# Indicators
def rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

btc['MA'] = btc['Close'].rolling(MA_WINDOW).mean()
btc['RSI'] = rsi(btc['Close'])
btc = btc.dropna()

# Signal
btc['Signal'] = ((btc['Close'] > btc['MA']) & (btc['RSI'] < RSI_THRESHOLD)).astype(int)

# --- CRITICAL: Clean for Numba ---
btc.index = pd.to_datetime(btc.index).tz_localize(None)
btc = btc[~btc.index.duplicated()]
close = btc['Close'].astype(np.float64)
entries = (btc['Signal'] == 1).astype(np.bool_)
exits = (btc['Signal'] == 0).shift(1).fillna(False).astype(np.bool_)

# Backtest
try:
    port = vbt.Portfolio.from_signals(
        close, entries, exits,
        init_cash=INIT_CASH,
        fees=0.001,
        freq='1D'
    )
    latest_signal = entries.iloc[-1]
    current_price = close.iloc[-1]
except Exception as e:
    print("⚠️ Fallback mode due to Numba error:", e)
    latest_signal = btc['Signal'].iloc[-1] == 1
    current_price = btc['Close'].iloc[-1]

# Output
print(f"📈 {SYMBOL} | Price: ${current_price:.2f}")
print(f"🎯 Signal: {'🟢 BUY' if latest_signal else '🔴 NO TRADE'}")

# Save (relative path!)
with open("signal.txt", "w") as f:
    f.write("BUY" if latest_signal else "HOLD")
with open("price.txt", "w") as f:
    f.write(f"{current_price:.2f}")
print("✅ Signal & price saved.")
