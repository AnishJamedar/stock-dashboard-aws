import streamlit as st
import pandas as pd
import boto3
import json
import time
from pyathena import connect
from datetime import datetime, timedelta
import plotly.graph_objects as go

# Athena config
DATABASE = 'stock-clean-table'
TABLE = 'clean'
S3_OUTPUT = 's3://stock-data-bucket-1a/athena-results/'

# Connect to Athena
conn = connect(s3_staging_dir=S3_OUTPUT, region_name='us-east-1')

# Lambda client
lambda_client = boto3.client('lambda', region_name='us-east-1')

# UI
st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("Stock Insights • AWS-Powered")
st.caption("Powered by AWS Athena, S3, Lambda and Step Functions")

# State management
if "custom_df" not in st.session_state:
    st.session_state.custom_df = None
if "custom_symbol" not in st.session_state:
    st.session_state.custom_symbol = None

base_symbols = ["AAPL", "TSLA", "GOOGL", "NVDA"]

# Athena repair function
def repair_partitions():
    with conn.cursor() as cursor:
        cursor.execute(f"MSCK REPAIR TABLE `{DATABASE}`.`{TABLE}`")

# Athena query
@st.cache_data(show_spinner=True)
def get_full_data(symbol):
    query = f"""
    SELECT date, open, high, low, close, volume
    FROM "{DATABASE}"."{TABLE}"
    WHERE symbol = '{symbol}'
    ORDER BY date ASC
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    columns = [col[0] for col in cursor.description]
    df = pd.DataFrame(rows, columns=columns)
    return df

# Symbol selection with custom
symbol_options = base_symbols + ["Custom"]
selected_symbol = st.selectbox("Choose a stock symbol", symbol_options)

if selected_symbol == "Custom":
    custom_symbol = st.text_input("Enter a custom stock symbol (e.g., AMZN)")
    if st.button("📡 Fetch Custom Stock Data"):
        if not custom_symbol:
            st.warning("Please enter a stock symbol.")
        else:
            lambda_client.invoke(
                FunctionName='one-time-load-function',
                InvocationType='Event',
                Payload=json.dumps({"symbols": [custom_symbol.upper()]})
            )
            with st.spinner(f"⏳ Fetching historical data for {custom_symbol.upper()}..."):
                time.sleep(10)
                repair_partitions()
                max_retries = 6
                for attempt in range(max_retries):
                    df_check = get_full_data(custom_symbol.upper())
                    if not df_check.empty:
                        st.session_state.custom_df = df_check
                        st.session_state.custom_symbol = custom_symbol.upper()
                        st.success(f"✅ Data for {custom_symbol.upper()} is ready!")
                        st.rerun()

                    time.sleep(3)
                st.warning(f"⚠️ Data for {custom_symbol.upper()} is still loading or unavailable.")
    df = st.session_state.custom_df if st.session_state.custom_df is not None else pd.DataFrame()
    selected_symbol = st.session_state.custom_symbol if st.session_state.custom_symbol else ""
else:
    df = get_full_data(selected_symbol)

# 🔁 Manual Refresh Button
st.info(
    "📅 Don't see today's data? Market data is updated at 8 AM ET on trading days.\n"
    "Press below to force refresh cache."
)
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.success("✅ Cache cleared! Please reselect a stock to reload data.")

# Plotting and analysis
if df.empty:
    st.warning("No data found.")
else:
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values("date")
    df['ma_7'] = df['close'].rolling(window=7).mean()
    df['pct_change'] = df['close'].pct_change() * 100
    df.set_index('date', inplace=True, drop=False)

    df_display = df.reset_index(drop=True)
    df_display['date'] = pd.to_datetime(df_display['date'], errors='coerce')

    # 🔍 Specific Day Stats
    st.markdown("### 📅 Stats for a Specific Day")
    available_dates = df_display['date'].dt.date.tolist()
    min_d, max_d = min(available_dates), max(available_dates)

    st.write(f"🗓️ Available date range: {min_d} → {max_d}")

    selected_date = st.date_input(
        "Select a date to view stats",
        value=max_d,
        min_value=min_d,
        max_value=max_d
    )

    day_row = df_display[df_display['date'].dt.date == selected_date]
    if not day_row.empty:
        row = day_row.iloc[0]
        st.success(
            f"📊 **{selected_symbol} on {selected_date}**\n\n"
            f"- 📈 Close: {row['close']}\n"
            f"- 🧱 Volume: {row['volume']}\n"
            f"- 🔺 % Change: {round(row['pct_change'], 2)}%"
        )
    else:
        st.warning("No data for selected date.")

    # 📉 Historical Charts
    st.markdown("---")
    st.markdown("### 📉 Historical Chart Visualizations")

    days = st.selectbox("Select time window", [7, 30, 90], index=1)
    chart_start_date = datetime.today().date() - timedelta(days=days)
    df_window = df[df.index.date >= chart_start_date]

    show_ma = st.checkbox("📈 Close + 7-day MA", value=True)
    show_pct = st.checkbox("📉 Daily % Change", value=True)
    show_volume = st.checkbox("📊 Volume", value=True)
    show_candle = st.checkbox("🕯️ Candlestick Chart", value=True)

    if show_ma:
        st.subheader(f"📈 Close Price with 7-day MA: {selected_symbol}")
        st.line_chart(df_window[['close', 'ma_7']])

    if show_pct:
        st.subheader("📉 Daily % Price Change")
        st.line_chart(df_window['pct_change'])

    if show_volume:
        st.subheader("📊 Volume")
        st.bar_chart(df_window['volume'])

    if show_candle:
        st.subheader("🕯️ Candlestick Chart")
        candle_df = df_window[['open', 'high', 'low', 'close']].dropna()
        if candle_df.empty:
            st.warning("❌ Not enough recent data to display candlestick chart.")
        else:
            fig = go.Figure(data=[go.Candlestick(
                x=candle_df.index,
                open=candle_df['open'],
                high=candle_df['high'],
                low=candle_df['low'],
                close=candle_df['close']
            )])
            fig.update_layout(xaxis_rangeslider_visible=False, height=500)
            st.plotly_chart(fig, use_container_width=True)

    # 📄 Data Preview + Download
    st.markdown("---")
    st.subheader("📄 Recent Data Preview")
    st.dataframe(df_display.tail(10), use_container_width=True)

    st.download_button(
        label="📥 Download CSV",
        data=df_display.to_csv(index=False),
        file_name=f"{selected_symbol}_data.csv",
        mime='text/csv'
    )
