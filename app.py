import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 頁面基本配置
st.set_page_config(page_title="體育課管理系統", layout="wide")

# CSS 優化：讓手機點擊按鈕更輕鬆
st.markdown("""<style>
    @media (max-width: 640px) { .main .block-container { padding: 10px; } }
    @media (min-width: 1024px) { .main .block-container { max-width: 800px; margin: auto; } }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #007bff; color: white; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# 1. 取得 Secrets 網址並進行「防錯清洗」
try:
    raw_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    # 確保網址格式純淨，只取到 /edit 以前的部分
    base_url = raw_url.split('/edit')[0]
    # 建立連線物件（用於寫入資料）
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as e:
    st.error("❌ Secrets 設定有誤，請檢查 Streamlit Cloud 的設定。")
    st.stop()

st.title("🏃‍♂️ 體育課點名與成績系統")

# 2. 側邊欄切換班級
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("請選擇班級", classes)

# 3. 讀取資料 (使用診斷成功的 CSV 讀取法)
try:
    csv_url = f"{base_url}/export?format=csv&sheet={selected_class}"
    df = pd.read_csv(csv_url).dropna(how='all')
    
    # 自動處理「座號」：去掉 1.0 這種小數點
    for col in ['座號', '學號']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.split('.').str[0]
except Exception as e:
    st.error(f"⚠️ 無法讀取 {selected_class} 的資料")
    st.write("錯誤代碼：", e)
    st.stop()

# 4. 建立功能頁籤
tab1, tab2, tab3 = st.tabs(["📅 快速點名", "🏆 成績登記", "📊 查看總表"])
today = datetime.now().strftime("%Y-%m-%d")

with tab1:
    st.subheader(f"📅 {today} 點名紀錄")
    if today not in df.columns:
        df[today] = "出席"
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            # 優先顯示座號，沒有的話顯示姓名
            label = f"{row.get('座號', '')}號 {row['姓名']}"
            c1.write(f"**{label}**")
            res = c2.segmented_control(
                "狀態", ["出席", "遲到", "缺席", "公假"], 
                default=row[today], 
                key=f"a_{selected_class}_{i}",
                label_visibility="collapsed"
            )
            df.at[i, today] = res
            
        if st.form_submit_button("✅ 儲存並同步至雲端"):
            conn.update(worksheet=selected_class, data=df)
            st.success("點名成功！資料已同步到 Google Sheets。")
            st.balloons()

with tab2:
    st.subheader("🏆 測驗成績登記")
    test_item = st.text_input("測驗項目名稱 (例如: 800M跑, 跳繩)", "體適能表現")
    if test_item not in df.columns:
        df[test_item] = 0.0

    with st.form("score_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            label = f"{row.get('座號', '')}號 {row['姓名']}"
            c1.write(f"**{label}**")
            score = c2.number_input("分數", value=float(df.at[i, test_item]), key=f"s_{selected_class}_{i}", label_visibility="collapsed")
            df.at[i, test_item] = score
        if st.form_submit_button("💾 儲存成績"):
            conn.update(worksheet=selected_class, data=df)
            st.success(f"{test_item} 成績已同步至雲端！")

with tab3:
    st.subheader(f"📊 {selected_class} 班級紀錄表")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button("🔄 重新整理資料"):
        st.rerun()
