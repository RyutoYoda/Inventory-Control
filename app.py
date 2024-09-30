import streamlit as st
import pandas as pd
import pydeck as pdk
from geopy.geocoders import Nominatim

# Geocoderの設定
geolocator = Nominatim(user_agent="inventory_app")

# ページの設定
st.set_page_config(page_title="在庫管理アプリ", page_icon="📦", layout="wide")

# 補充タイミングを計算する関数
def calculate_replenishment(stock_level, daily_usage, safety_stock, lead_time):
    consumption = daily_usage * lead_time
    replenishment_point = safety_stock + consumption
    return replenishment_point

# 必要な補充量を計算
def calculate_replenishment_quantity(stock_level, replenishment_point):
    return max(0, replenishment_point - stock_level)

# ページタイトル
st.title("📦 在庫管理と補充通知アプリ")

# トグルでアプリの使い方を表示
with st.expander("アプリの使い方を表示"):
    st.write("""
    - **CSVファイルをアップロード**: 各店舗や倉庫の住所、在庫数、1日の消費量、リードタイムなどを含むCSVファイルをアップロードします。
    - **在庫消費量と補充タイミングの可視化**: データをもとに、在庫消費の推移と補充タイミングを表示します。
    - **住所から地図上にプロット**: 住所データをもとに、自動的に緯度と経度を取得し、地図上にマッピングします。
    """)

# サイドバーでパラメータを入力
st.sidebar.header("🔧 在庫パラメータの設定")
daily_usage = st.sidebar.number_input("1日の消費量（単位）", min_value=0, value=50)
safety_stock = st.sidebar.number_input("安全在庫数", min_value=0, value=30)
lead_time = st.sidebar.number_input("リードタイム（日数）", min_value=0, value=5)

# CSVファイルのアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    # CSVファイルを読み込み
    warehouse_data = pd.read_csv(uploaded_file)

    # 各店舗での補充ポイントを計算し、補充が必要な量を計算
    warehouse_data['補充ポイント'] = warehouse_data['在庫数'].apply(lambda x: calculate_replenishment(x, daily_usage, safety_stock, lead_time))
    warehouse_data['不足量'] = warehouse_data.apply(lambda row: calculate_replenishment_quantity(row['在庫数'], row['補充ポイント']), axis=1)

    # CSVデータを表示
    st.subheader("アップロードされたデータ")
    st.dataframe(warehouse_data)

    # 不足がある場合は警告を表示
    shortage_stores = warehouse_data[warehouse_data['不足量'] > 0]
    if not shortage_stores.empty:
        for _, row in shortage_stores.iterrows():
            st.warning(f"{row['店舗名']} の在庫が補充ポイント ({row['補充ポイント']} 単位) を下回っています。補充が必要な量は {row['不足量']} 単位です。")
    else:
        st.success("すべての店舗で在庫は十分です。")

    # ======= Pydeckで地理的可視化機能 =======
    st.write("### 倉庫・店舗の在庫マップ")

    # 住所データを使用して緯度・経度を取得
    def geocode_address(address):
        try:
            location = geolocator.geocode(address)
            if location:
                return location.latitude, location.longitude
            else:
                return None, None
        except:
            return None, None

    # 緯度・経度を取得
    warehouse_data['latitude'], warehouse_data['longitude'] = zip(*warehouse_data['住所'].apply(geocode_address))

    # 緯度・経度が存在する行のみをフィルタリング
    warehouse_data_clean = warehouse_data.dropna(subset=['latitude', 'longitude'])

    # Pydeckでマップ作成
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=warehouse_data_clean,
        get_position=['longitude', 'latitude'],
        get_radius=50000,
        get_color=[0, 100, 255],
        pickable=True
    )

    # Pydeckのビュー設定
    view_state = pdk.ViewState(
        latitude=warehouse_data_clean['latitude'].mean(),
        longitude=warehouse_data_clean['longitude'].mean(),
        zoom=5,
        pitch=50,
    )

    # Pydeckチャート表示
    r = pdk.Deck(layers=[layer], initial_view_state=view_state)
    st.pydeck_chart(r)

else:
    st.warning("CSVファイルをアップロードしてください。")
