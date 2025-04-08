
import streamlit as st
import pandas as pd
import requests
import ta

st.set_page_config(page_title="Phân tích Coin", layout="wide")
st.title("Dự đoán xu hướng coin bằng chỉ báo kỹ thuật")

# Lấy danh sách coin từ CoinGecko
@st.cache_data
def get_coin_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return sorted(data, key=lambda x: x['name'])
    else:
        return []

coin_list = get_coin_list()

# Tạo autocomplete cho người dùng chọn coin
coin_names = [f"{coin['name']} ({coin['symbol'].upper()})" for coin in coin_list]
selected_coin_name = st.selectbox("Chọn coin:", coin_names)

# Lấy ID từ tên coin
selected_coin_id = next((coin['id'] for coin in coin_list if f"{coin['name']} ({coin['symbol'].upper()})" == selected_coin_name), None)

# Lấy dữ liệu giá từ CoinGecko
@st.cache_data
def get_price_data(coin_id, days=1):
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=hourly"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        prices = data['prices']
        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    else:
        return None

if selected_coin_id:
    df = get_price_data(selected_coin_id)

    if df is not None and not df.empty:
        st.line_chart(df['price'], height=300)

        # Tính các chỉ báo kỹ thuật
        df['rsi'] = ta.momentum.RSIIndicator(df['price']).rsi()
        df['ema_9'] = ta.trend.EMAIndicator(df['price'], window=9).ema_indicator()
        df['ema_21'] = ta.trend.EMAIndicator(df['price'], window=21).ema_indicator()
        df['macd'] = ta.trend.MACD(df['price']).macd_diff()

        latest = df.iloc[-1]

        st.subheader("Tín hiệu chỉ báo mới nhất:")
        st.write(f"**Giá hiện tại:** {latest['price']:.2f} USD")
        st.write(f"**RSI:** {latest['rsi']:.2f} → {'Quá bán' if latest['rsi'] < 30 else ('Quá mua' if latest['rsi'] > 70 else 'Trung tính')}")
        st.write(f"**EMA(9) vs EMA(21):** {'Tăng' if latest['ema_9'] > latest['ema_21'] else 'Giảm'}")
        st.write(f"**MACD Histogram:** {latest['macd']:.4f} → {'Tăng' if latest['macd'] > 0 else 'Giảm'}")
    else:
        st.error("Không lấy được dữ liệu giá. Hãy thử lại sau hoặc chọn coin khác.")
else:
    st.warning("Không xác định được ID của coin đã chọn.")
