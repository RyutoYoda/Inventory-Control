import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ページの設定
st.set_page_config(page_title="在庫管理アプリ", page_icon="📦")

# 補充タイミングを計算する関数
def calculate_replenishment(stock_level, daily_usage, safety_stock, lead_time):
    current_stock = stock_level
    consumption = daily_usage * lead_time
    replenishment_point = safety_stock + consumption
    return replenishment_point

# 在庫補充通知のメール送信機能
def send_email_notification(to_email, stock_level, replenishment_point):
    subject = "在庫補充のお知らせ"
    body = f"現在の在庫 ({stock_level} 単位) が補充ポイント ({replenishment_point} 単位) を下回りました。"
    
    # メールの設定
    from_email = "youremail@example.com"
    password = "yourpassword"
    
    # メール送信処理
    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    
    try:
        # GmailのSMTPサーバを利用
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        st.success("メールが送信されました！")
    except Exception as e:
        st.error(f"メール送信に失敗しました: {e}")

# ページタイトル
st.title("在庫管理と補充通知アプリ")

# トグルでアプリの使い方を表示
with st.expander("アプリの使い方を表示"):
    st.write("""
    このアプリでは、以下のパラメータを入力して在庫補充のタイミングを管理します:
    - **現在の在庫数**: 現時点での在庫量。
    - **1日の消費量**: 1日に消費される商品の単位数。
    - **安全在庫数**: 補充が必要になる前に維持したい最小限の在庫量。
    - **リードタイム**: 注文から納入までにかかる日数。
    在庫が補充ポイントを下回った場合、警告が表示されます。また、メール通知を設定しておくと、補充タイミングで通知が届きます。
    """)

# サイドバーでパラメータを入力
st.sidebar.header("在庫パラメータ")
stock_level = st.sidebar.number_input("現在の在庫数", min_value=0, value=500)
daily_usage = st.sidebar.number_input("1日の消費量（単位）", min_value=0, value=50)
safety_stock = st.sidebar.number_input("安全在庫数", min_value=0, value=30)
lead_time = st.sidebar.number_input("リードタイム（日数）", min_value=0, value=5)
email_address = st.sidebar.text_input("通知用メールアドレス", value="")

# 補充ポイントを計算
replenishment_point = calculate_replenishment(stock_level, daily_usage, safety_stock, lead_time)

# 在庫の補充が必要かを確認
if stock_level <= replenishment_point:
    st.warning(f"在庫が補充ポイント ({replenishment_point} 単位) を下回っています。補充を検討してください。")
    if email_address:
        if st.sidebar.button("メールで通知を送信"):
            send_email_notification(email_address, stock_level, replenishment_point)
else:
    st.success(f"在庫は十分です。現在の在庫数: {stock_level} 単位。")

# 次の入荷日の予測（後でデータベースと連携可能）
next_arrival_date = datetime.now() + timedelta(days=lead_time)
st.write(f"次の入荷予定日: {next_arrival_date.strftime('%Y-%m-%d')}")

# 在庫消費量の可視化（Plotlyを使用）
stock_data = {
    "日付": [f"Day {i+1}" for i in range(lead_time)],
    "在庫数": [stock_level - daily_usage * i for i in range(lead_time)],
}
df = pd.DataFrame(stock_data)

fig = px.line(df, x="日付", y="在庫数", title="在庫消費の推移", markers=True)
st.plotly_chart(fig)

# 在庫管理のデータテーブル
st.table(df)
