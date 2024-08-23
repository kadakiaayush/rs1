import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Custom CSS for improved styling
st.markdown(
    """
    <style>
        .title {
            font-family: 'Arial', sans-serif;
            font-size: 2.5em;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 0.5em;
        }
        .sidebar .sidebar-content {
            background-color: #f7f9fc;
            padding: 20px;
            border-radius: 15px;
        }
        .info-box {
            border-radius: 15px;
            padding: 15px;
            color: white;
            text-align: center;
            margin-bottom: 1em;
        }
        .footer {
            text-align: center;
            font-size: 0.8em;
            margin-top: 2em;
            color: #95a5a6;
        }
        .footer i {
            font-style: italic;
        }
        .stButton>button {
            border-radius: 8px;
            background-color: #3498db;
            color: white;
        }
        .stButton>button:hover {
            background-color: #2980b9;
        }
        .stSidebar input[type=text] {
            border-radius: 8px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<h1 class='title'>📊 RSI & Momentum Analysis for Stocks, Treasuries, and ETFs</h1>", unsafe_allow_html=True)
st.sidebar.header("🔧 Customization Options")

# Sidebar options with improved UI
rsi_period = st.sidebar.slider("Select RSI Period", min_value=7, max_value=30, value=14)

instruments = {
    "S&P 500 ETF (SPY)": "SPY",
    "Dow Jones Industrial Average (DJIA)": "^DJI",
    "Nasdaq Composite Index (Nasdaq)": "^IXIC",
    "New York Stock Exchange Composite Index (NYSE)": "^NYA",
    "10-Year Treasury (^TNX)": "^TNX",
    "2-Year Treasury (^IRX)": "^IRX",
    "30-Year Treasury (^TYX)": "^TYX",
    "Gold ETF (GLD)": "GLD",
    "Crude Oil ETF (USO)": "USO"
}

selected_instrument = st.sidebar.selectbox("Select a Predefined Instrument", list(instruments.keys()))
custom_symbol = st.sidebar.text_input("Or Enter Custom Symbol (e.g., MSFT, AAPL, QQQ):", "")
stock_symbol = custom_symbol if custom_symbol else instruments[selected_instrument]

def calculate_rsi(data, period):
    delta = data['Adj Close'].diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()

    avg_gain.iloc[period] = gain.iloc[:period+1].mean()
    avg_loss.iloc[period] = loss.iloc[:period+1].mean()

    for i in range(period + 1, len(avg_gain)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, short_period=12, long_period=26, signal_period=9):
    short_ema = data['Adj Close'].ewm(span=short_period, adjust=False).mean()
    long_ema = data['Adj Close'].ewm(span=long_period, adjust=False).mean()
    macd = short_ema - long_ema
    signal = macd.ewm(span=signal_period, adjust=False).mean()
    return macd, signal

def calculate_sma(data, period=20):
    return data['Adj Close'].rolling(window=period).mean()

if stock_symbol:
    stock_data = yf.download(stock_symbol, period='6mo', interval='1d')

    if not stock_data.empty:
        stock_data['RSI'] = calculate_rsi(stock_data, rsi_period)
        stock_data['SMA_20'] = calculate_sma(stock_data)
        stock_data['MACD'], stock_data['Signal'] = calculate_macd(stock_data)

        current_rsi = stock_data['RSI'].iloc[-1]
        rsi_status = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"

        rsi_status_color = "#e74c3c" if rsi_status == "Overbought" else "#2ecc71" if rsi_status == "Oversold" else "#f39c12"
        st.markdown(
            f"""
            <div class='info-box' style='background-color: {rsi_status_color};'>
                <h2>RSI for {stock_symbol}: {current_rsi:.2f}</h2>
                <p>Status: {rsi_status}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader(f"🔍 Insights for {stock_symbol}")

        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=stock_data.index, y=stock_data['RSI'], mode='lines', name='RSI'))
        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought", annotation_position="bottom right")
        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold", annotation_position="top right")
        fig_rsi.update_layout(title=f"{stock_symbol} RSI (Default Period: {rsi_period})", yaxis_title="RSI Value")
        st.plotly_chart(fig_rsi)

        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=stock_data.index, y=stock_data['MACD'], mode='lines', name='MACD', line=dict(color='purple')))
        fig_macd.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Signal'], mode='lines', name='Signal Line', line=dict(color='orange')))
        fig_macd.update_layout(title=f"{stock_symbol} MACD", yaxis_title="MACD Value")
        st.plotly_chart(fig_macd)

        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(x=stock_data.index, y=stock_data['Adj Close'], mode='lines', name='Price', line=dict(color='black')))
        fig_price.add_trace(go.Scatter(x=stock_data.index, y=stock_data['SMA_20'], mode='lines', name='20-day SMA', line=dict(color='red')))
        fig_price.update_layout(title=f"{stock_symbol} Price and 20-day SMA", yaxis_title="Price")
        st.plotly_chart(fig_price)

        if rsi_status == "Overbought":
            st.warning(f"⚠️ {stock_symbol} is currently overbought. Potential for price correction.")
        elif rsi_status == "Oversold":
            st.success(f"💡 {stock_symbol} is currently oversold. Consider potential buying opportunities.")
    else:
        st.error("Failed to fetch data. Please check the symbol.")

st.markdown(
    "<small><i>Default RSI period is 14...</i></small>",
    unsafe_allow_html=True,
)
st.markdown("<div class='footer'>💸 Developed by Ayush Kadakia 💸</div>", unsafe_allow_html=True)
