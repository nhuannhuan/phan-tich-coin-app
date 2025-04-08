
import streamlit as st
import pandas as pd
import requests
import ta

st.set_page_config(page_title="Phân Tích Coin Tự Động", layout="centered")
st.title("Phân tích xu hướng coin theo chỉ báo kỹ thuật")

symbol = st.text_input("Nhập tên coin (VD: bitcoin, ethereum)", value="bitcoin").lower().strip()

@st.cache_data
def get_data_from_coingecko(symbol='bitcoin', limit=100):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=1&interval=minute"
    response = requests.get(url)
    data = response.json()
    prices = data['prices'][-limit:]
    df = pd.DataFrame(prices, columns=['timestamp', 'price'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.set_index('timestamp')
    df['close'] = df['price']
    df['open'] = df['close']
    df['high'] = df['close']
    df['low'] = df['close']
    df['volume'] = 1
    df = df[['open', 'high', 'low', 'close', 'volume']]
    return df

def apply_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd_diff()
    df['ema20'] = ta.trend.EMAIndicator(df['close'], window=20).ema_indicator()
    df['ema50'] = ta.trend.EMAIndicator(df['close'], window=50).ema_indicator()
    bb = ta.volatility.BollingerBands(df['close'])
    df['bb_bbm'] = bb.bollinger_mavg()
    df['bb_bbh'] = bb.bollinger_hband()
    df['bb_bbl'] = bb.bollinger_lband()
    return df

def analyze(df):
    last = df.iloc[-1]
    signal = []
    if last['rsi'] < 30:
        signal.append('RSI: Quá bán (Oversold)')
    elif last['rsi'] > 70:
        signal.append('RSI: Quá mua (Overbought)')
    if last['macd'] > 0:
        signal.append('MACD: Tăng (Bullish)')
    else:
        signal.append('MACD: Giảm (Bearish)')
    if last['ema20'] > last['ema50']:
        signal.append('EMA: Giao cắt tăng (Bullish cross)')
    else:
        signal.append('EMA: Giao cắt giảm (Bearish cross)')
    if last['close'] < last['bb_bbl']:
        signal.append('BB: Dưới dải dưới (có thể bật lên)')
    elif last['close'] > last['bb_bbh']:
        signal.append('BB: Trên dải trên (có thể điều chỉnh)')
    return signal

if symbol:
    try:
        df = get_data_from_coingecko(symbol)
        df = apply_indicators(df)
        signals = analyze(df)
        st.subheader(f"Kết quả phân tích cho coin: {symbol}")
        for s in signals:
            st.markdown(f"- {s}")
    except:
        st.error("Không lấy được dữ liệu. Kiểm tra lại tên coin hoặc thử lại sau.")
