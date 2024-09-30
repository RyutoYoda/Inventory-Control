import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# 在庫補充通知のメール送信機能
def send_email_notification(to_emails, stores_info):
    subject = "在庫補充のお知らせ"
    body = "以下の店舗で補充が必要です:\n\n"
    for info in stores_info:
        body += f"{info['店舗名']}: 現在の在庫 {info['在庫数']} 単位、補充ポイント {info['補充ポイント']} 単位、補充必要量 {info['不足量']} 単位\n"
    
    from_email = "youremail@example.com"
    password = "yourpassword"
    
    for email in to_emails:
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = email.strip()
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(from_email, password)
            text = msg.as_string()
            server.sendmail(from_email, email, text)
            server.quit()
            st.success(f"メールが {email} に送信されました！")
        except Exception as e:
            st.error(f"メール送信に失敗しました ({email}): {e}")

# ページタイトル
st.title("📦 在庫管理と補充通知アプリ")

# トグルでアプリの使い方を表示
with st.expander("アプリの使い方を表示"):
    st.write("""
    - **CSVファイルをアップロード**: 各店舗や倉庫の住所、在庫数、1日の消費量、リードタイムなどを含むCSVファイルをアップロードします。
    - **在庫消費量と補充タイミングの可視化**: データをもとに、在庫消費の推移と補充タイミングを表示します。
    - **住所から地図上にプロット**: 住所データをもとに、自動的に緯度と経度を取得し、地図上にマッピングします。
    """)

# CSVファイルのアップロード
uploaded_file = st.file_uploader("CSVファイルをアップロード", type=["csv"])

if uploaded_file is not None:
    # CSVファイルを読み込み
    warehouse_data = pd.read_csv(uploaded_file)

    # 各店舗での補充ポイントを計算し、補充が必要な量を計算
    warehouse_data['補充ポイント'] = warehouse_data['在庫数'].apply(lambda x: calculate_replenishment(x, daily_usage, safety_stock, lead_time))
    warehouse_data['不足量'] = warehouse_data.apply(lambda row: calculate_replenishment_quantity(row['在庫数'], row['補充ポイント']), axis=1)

    # 在庫が補充ポイントを下回っている店舗をリストアップ
    shortage_stores = warehouse_data[warehouse_data['不足量'] > 0]

    # CSVデータを表示
    st.subheader("アップロードされたデータ")
    st.dataframe(warehouse_data)

    # 不足がある場合は警告を表示し、メール送信オプションを提供
    if not shortage_stores.empty:
        for _, row in shortage_stores.iterrows():
            st.warning(f"{row['店舗名']} の在庫が補充ポイント ({row['補充ポイント']} 単位) を下回っています。補充が必要な量は {row['不足量']} 単位です。")
        
        if email_addresses:
            email_list = email_addresses.split(',')
            if st.sidebar.button("メールで通知を送信"):
                stores_info = shortage_stores.to_dict('records')
                send_email_notification(email_list, stores_info)
    else:
        st.success("すべての店舗で在庫は十分です。")

    # 在庫消費量の可視化（Plotlyを使用）
    stock_data = {
        "日付": [f"Day {i+1}" for i in range(lead_time)],
        "在庫数": [warehouse_data['在庫数'].mean() - daily_usage * i for i in range(lead_time)],
        "安全在庫": [safety_stock for _ in range(lead_time)]
    }
    df = pd.DataFrame(stock_data)

    # 複数指標の可視化
    fig = px.line(df, x="日付", y=["在庫数", "安全在庫"], title="平均在庫と安全在庫の推移", markers=True)
    st.plotly_chart(fig)

    # ======= 地理的可視化機能（サブ機能）=======
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

    # 住所から緯度経度を取得
    warehouse_data['緯度'], warehouse_data['経度'] = zip(*warehouse_data['住所'].apply(geocode_address))

    # Foliumマップ作成
    m = folium.Map(location=[35.6895, 139.6917], zoom_start=5)

    for i, row in warehouse_data.iterrows():
        if pd.notnull(row['緯度']) and pd.notnull(row['経度']):
            folium.Marker(
                location=[row['緯度'], row['経度']],
                popup=f"{row['店舗名']}: {row['在庫数']}個",
                icon=folium.Icon(color="blue" if row['在庫数'] > 200 else "red")
            ).add_to(m)

    # FoliumマップをStreamlitで表示
    st_folium(m, width=700)
else:
    st.warning("CSVファイルをアップロードしてください。")
