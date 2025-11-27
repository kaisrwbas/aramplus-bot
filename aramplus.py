import yfinance as yf
import vectorbt as vbt
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
pd.set_option('future.no_silent_downcasting', True)

print("🚀 AramPlus v1.0 | Daily Signal Generator")

# --- CONFIG ---
SYMBOL = "BTC-USD"
INIT_CASH = 10000
MA_WINDOW = 50
RSI_THRESHOLD = 60

# --- DATA ---
btc = yf.download(SYMBOL, period="1y", interval="1d", progress=False)
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

# --- SIGNAL + RISK MANAGEMENT ---
btc['Signal'] = ((btc['Close'] > btc['MA']) & (btc['RSI'] < RSI_THRESHOLD)).astype(int)

# Add ATR-based stop-loss (14-day ATR × 1.5)
def atr(high, low, close, window=14):
    tr = np.maximum(high - low,
                    np.maximum(abs(high - close.shift(1)),
                               abs(low - close.shift(1))))
    return tr.rolling(window).mean()

# Fetch full OHLC for ATR
full = yf.download(SYMBOL, period="1y", interval="1d", progress=False)
if isinstance(full.columns, pd.MultiIndex):
    full.columns = [c[0] for c in full.columns]
full = full[['Open', 'High', 'Low', 'Close']].dropna()

btc = btc.join(full[['High', 'Low']], how='left')
btc['ATR'] = atr(btc['High'], btc['Low'], btc['Close'], 14)
btc['SL'] = btc['Close'] - 1.5 * btc['ATR']  # long stop-loss
btc['TP'] = btc['Close'] + 3.0 * btc['ATR']  # 2:1 reward:risk

# Final signal only when SL/TP are valid
btc = btc.dropna(subset=['ATR'])
latest_signal = btc['Signal'].iloc[-1] == 1
current_price = btc['Close'].iloc[-1]
sl_price = btc['SL'].iloc[-1]
tp_price = btc['TP'].iloc[-1]

print(f"📈 {SYMBOL} | Price: ${current_price:.2f}")
print(f"🎯 Signal: {'🟢 BUY' if latest_signal else '🔴 HOLD'}")
if latest_signal:
    print(f"🛡️ SL: ${sl_price:.2f} | 🎯 TP: ${tp_price:.2f} | R:R = 2:1")

# Save enhanced signal
with open("signal.txt", "w") as f:
    f.write("BUY" if latest_signal else "HOLD")
with open("price.txt", "w") as f:
    f.write(f"{current_price:.2f}")
with open("sl.txt", "w") as f:
    f.write(f"{sl_price:.2f}" if latest_signal else "N/A")
with open("tp.txt", "w") as f:
    f.write(f"{tp_price:.2f}" if latest_signal else "N/A")

# --- OPTIONAL: Testnet Balance Check (only if keys provided) ---
try:
    api_key = os.getenv("BINANCE_TESTNET_KEY", "").strip()
    api_secret = os.getenv("BINANCE_TESTNET_SECRET", "").strip()
    
    if api_key and api_secret:
        import ccxt
        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'urls': {
                'api': {
                    'public': 'https://testnet.binance.vision/api',
                    'private': 'https://testnet.binance.vision/api',
                }
            },
            'options': {'defaultType': 'spot'}
        })
        account = exchange.privateGetAccount()
        balances = {b['asset']: float(b['free']) for b in account['balances']}
        usdt = balances.get('USDT', 0)
        btc_balance = balances.get('BTC', 0)
        print(f"📡 Testnet Balance: {btc_balance:.6f} BTC, ${usdt:.2f} USDT")
        
        # Auto-trade if signal=BUY and enough USDT
        if latest_signal and usdt > 100:
            print("🤖 Placing testnet BUY order (0.001 BTC)...")
            order = exchange.create_market_buy_order('BTC/USDT', 0.001)
            print(f"✅ Order ID: {order['id']}")
except Exception as e:
    print(f"⚠️ Testnet check skipped or failed: {str(e)}")

print("✅ AramPlus run completed.")
