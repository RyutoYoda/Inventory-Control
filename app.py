import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# 補充タイミングを計算する関数
def calculate_replenishment(stock_level, daily_usage, safety_stock, lead_time):
    current_stock = stock_level
    consumption = daily_usage * lead_time
    replenishment_point = safety_stock + consumption
    return replenishment_point

# ページタイトルを設定
st.title("在庫管理と補充通知")

# サイドバーでパラメータを入力
st.sidebar.header("在庫パラメータ")
stock_level = st.sidebar.number_input("現在の在庫数", min_value=0, value=500)
daily_usage = st.sidebar.number_input("1日の消費量（単位）", min_value=0, value=50)
safety_stock = st.sidebar.number_input("安全在庫数", min_value=0, value=30)
lead_time = st.sidebar.number_input("リードタイム（日数）", min_value=0, value=5)

# 補充ポイントを計算
replenishment_point = calculate_replenishment(stock_level, daily_usage, safety_stock, lead_time)

# 在庫の補充が必要かを確認
if stock_level <= replenishment_point:
    st.warning(f"在庫が補充ポイント ({replenishment_point} 単位) を下回っています。補充を検討してください。")
else:
    st.success(f"在庫は十分です。現在の在庫数: {stock_level} 単位。")

# 次の入荷日の予測（後でデータベースと連携可能）
next_arrival_date = datetime.now() + timedelta(days=lead_time)
st.write(f"次の入荷予定日: {next_arrival_date.strftime('%Y-%m-%d')}")

# 在庫管理の可視化のためのデータテーブル
stock_data = {
    "日付": [f"Day {i+1}" for i in range(lead_time)],
    "在庫数": [stock_level - daily_usage * i for i in range(lead_time)],
    "消費量": [daily_usage for _ in range(lead_time)],
}
df = pd.DataFrame(stock_data)
st.table(df)
