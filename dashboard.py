import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="AramPlus Dashboard", layout="wide")
st.title("📡 AramPlus Live Dashboard")

# Simulate latest data (in real use, read from CSV/logs)
data = {
    'Time': ['2025-11-27 00:00 UTC'],
    'Price': [90323.42],
    'Signal': ['HOLD'],
    'MA50': [104146.70],
    'RSI': [29.9],
    'Equity': [10000],
}
df = pd.DataFrame(data)

col1, col2, col3, col4 = st.columns(4)
col1.metric("BTC/USD", f"${df.Price.iloc[0]:,.2f}")
col2.metric("Signal", df.Signal.iloc[0], delta="Stable")
col3.metric("RSI", f"{df.RSI.iloc[0]:.1f}", delta="-0.2")
col4.metric("Equity", f"${df.Equity.iloc[0]:,.0f}")

# Equity curve (mock)
fig = go.Figure()
fig.add_trace(go.Scatter(x=pd.date_range('2025-01-01', periods=300), 
                         y=10000 * (1 + 0.001 * (pd.np.random.randn(300).cumsum())), 
                         name="AramPlus"))
fig.update_layout(title="📈 Equity Curve", height=400)
st.plotly_chart(fig, use_container_width=True)