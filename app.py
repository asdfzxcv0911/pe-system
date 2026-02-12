import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 基本網頁設定
st.set_page_config(page_title="體育課管理系統", layout="wide")

# 優化手機/電腦顯示
st.markdown("""<style>
    @media (max-width: 640px) { .main .block-container { padding: 10px; } }
    @media (min-width: 1024px) { .main .block-container { max-width: 900px; margin: auto; } }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #007bff; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; padding: 0 20px; }
</style>""", unsafe_allow_html=True)

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🏃‍♂️ 體育課點名與成績系統")

# 側邊欄選擇班級
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("請選擇班級", classes)

# 讀取資料 (ttl=0 確保讀取最新)
try:
    df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all')
    # 強制將座號轉為整數或字串，避免出現 .0
    if '座號' in df.columns:
        df['座號'] = df['座號'].astype(str).str.replace('.0', '', regex=False)
except Exception as e:
    st.error("讀取資料失敗，請檢查 Google Sheets 分頁名稱。")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📅 快速點名", "🏆 成績登記", "📊 班級總表"])
today = datetime.now().strftime("%Y-%m-%d")

# --- 點名功能 ---
with tab1:
    st.subheader(f"📅 {today} 點名作業")
    if today not in df.columns:
        df[today] = "出席"
    
    with st.form("attendance_form"):
        for i, row in df.iterrows():
            col_name, col_status = st.columns([1, 2])
            col_name.write(f"**{row['座號']}號 {row['姓名']}**")
            # 使用分段選擇器，手機點選超快
            status = col_status.segmented_control(
                "狀態", ["出席", "遲到", "缺席", "公假"], 
                default=row[today], 
                key=f"att_{selected_class}_{i}",
                label_visibility="collapsed"
            )
            df.at[i, today] = status
        
        if st.form_submit_button("✅ 儲存今日點名紀錄"):
            conn.update(worksheet=selected_class, data=df)
            st.success("點名紀錄已成功同步至 Google Sheets！")
            st.balloons()

# --- 成績功能 ---
with tab2:
    st.subheader("🏆 測驗成績登記")
    test_item = st.text_input("輸入測驗項目名稱", "體適能成績")
    
    if test_item not in df.columns:
        df[test_item] = 0.0

    with st.form("score_form"):
        for i, row in df.iterrows():
            col_name, col_score = st.columns([1, 2])
            col_name.write(f"**{row['座號']}號 {row['姓名']}**")
            score = col_score.number_input(
                "分數", value=float(df.at[i, test_item]), 
                key=f"score_{selected_class}_{i}",
                label_visibility="collapsed"
            )
            df.at[i, test_item] = score
            
        if st.form_submit_button("💾 儲存成績"):
            conn.update(worksheet=selected_class, data=df)
            st.success(f"{test_item} 成績已同步至雲端！")

# --- 總表功能 ---
with tab3:
    st.subheader(f"📊 {selected_class} 完整紀錄")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button("🔄 重新讀取雲端資料"):
        st.rerun()
