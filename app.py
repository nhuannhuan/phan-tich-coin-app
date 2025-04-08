
import streamlit as st
import pandas as pd
import datetime
from ta.momentum import RSIIndicator
from ta.trend import MACD, EMAIndicator
from ta.volatility import BollingerBands
import plotly.graph_objs as go
from pycoingecko import CoinGeckoAPI

cg = CoinGeckoAPI()

st.set_page_config(page_title="Coin Trend Analyzer", layout="wide")

st.title("Phân tích xu hướng giá coin dựa trên các chỉ báo kỹ thuật")

# Chọn coin
coin_list = [coin["id"] for coin in cg.get_coins_list()]
coin_name = st.selectbox("Chọn tên coin (gõ để gợi ý):", coin_list, index=coin_list.index("bitcoin") if "bitcoin" in coin_list else 0)

# Chọn khung thời gian
interval = st.selectbox("Chọn khung thời gian:", ["1", "5", "15", "30", "60", "90", "120", "180", "360", "720", "1440"], index=2)
days_back = st.slider("Số ngày cần phân tích:", 1, 90, 7)

# Lấy dữ liệu
with st.spinner("Đang tải dữ liệu..."):
    try:
        vs_currency = "usd"
        to_ts = int(datetime.datetime.now().timestamp())
        from_ts = to_ts - days_back * 24 * 60 * 60

        hist = cg.get_coin_market_chart_range_by_id(
            id=coin_name,
            vs_currency=vs_currency,
            from_timestamp=from_ts,
            to_timestamp=to_ts
        )

        prices = hist["prices"]
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        df = df.resample(f"{interval}min").mean().dropna()

        # Tính các chỉ báo
        df["rsi"] = RSIIndicator(close=df["price"]).rsi()
        macd = MACD(close=df["price"])
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["ema21"] = EMAIndicator(close=df["price"], window=21).ema_indicator()
        boll = BollingerBands(close=df["price"])
        df["bb_upper"] = boll.bollinger_hband()
        df["bb_lower"] = boll.bollinger_lband()

        # Tính phần trăm thay đổi gần nhất
        pct_change = df["price"].pct_change().iloc[-1] * 100

        st.metric(f"Thay đổi gần nhất ({interval} phút):", f"{pct_change:.2f}%")

        # Vẽ biểu đồ
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df["price"], name="Giá", line=dict(color="white")))
        fig.add_trace(go.Scatter(x=df.index, y=df["ema21"], name="EMA21", line=dict(color="blue", dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper", line=dict(color="green", dash="dot")))
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower", line=dict(color="red", dash="dot")))

        fig.update_layout(title=f"Biểu đồ giá & chỉ báo kỹ thuật - {coin_name.upper()}",
                          xaxis_title="Thời gian", yaxis_title="Giá (USD)",
                          template="plotly_dark")

        st.plotly_chart(fig, use_container_width=True)

        # Phân tích tín hiệu
        latest = df.iloc[-1]
        signal = ""
        if latest["rsi"] > 70:
            signal += "RSI cho thấy quá mua. "
        elif latest["rsi"] < 30:
            signal += "RSI cho thấy quá bán. "

        if latest["macd"] > latest["macd_signal"]:
            signal += "MACD ủng hộ xu hướng tăng. "
        else:
            signal += "MACD cho tín hiệu giảm. "

        if latest["price"] > latest["ema21"]:
            signal += "Giá đang nằm trên EMA21 → xu hướng tăng. "
        else:
            signal += "Giá dưới EMA21 → xu hướng giảm. "

        st.subheader("Tín hiệu phân tích tổng hợp:")
        st.info(signal)

    except Exception as e:
        st.error(f"Không lấy được dữ liệu cho coin: {coin_name}")
        st.exception(e)
