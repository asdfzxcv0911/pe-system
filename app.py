import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 頁面基本配置
st.set_page_config(page_title="體育課管理系統", layout="wide")

# CSS 優化：手機點擊更輕鬆
st.markdown("""<style>
    @media (max-width: 640px) { .main .block-container { padding: 10px; } }
    @media (min-width: 1024px) { .main .block-container { max-width: 800px; margin: auto; } }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #007bff; color: white; font-weight: bold; }
</style>""", unsafe_allow_html=True)

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🏃‍♂️ 體育課點名與成績系統")

# 側邊欄切換班級
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("請選擇班級", classes)

# 讀取資料
try:
    # 讀取目前選中班級的分頁
    df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all')
    
    # 自動處理「座號」：將座號轉為字串並去掉小數點 (.0)
    if '座號' in df.columns:
        df['座號'] = df['座號'].astype(str).str.split('.').str[0]
    elif '學號' in df.columns:
        df['座號'] = df['學號'].astype(str).str.split('.').str[0]
        
except Exception as e:
    st.error("⚠️ 系統讀取不到資料")
    st.write("請查看下方的原始錯誤訊息，這對修復非常有幫助：")
    st.code(str(e)) # 顯示真正的錯誤原因
    st.stop()

# 建立功能頁籤
tab1, tab2, tab3 = st.tabs(["📅 快速點名", "🏆 成績登記", "📊 查看總表"])
today = datetime.now().strftime("%Y-%m-%d")

with tab1:
    st.subheader(f"📅 {today} 點名紀錄")
    if today not in df.columns:
        df[today] = "出席"
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            c1.write(f"**{row.get('座號', i+1)}號 {row['姓名']}**")
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
    test_item = st.text_input("測驗項目名稱", "體適能測驗")
    if test_item not in df.columns:
        df[test_item] = 0.0

    with st.form("score_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            c1.write(f"**{row.get('座號', i+1)}號 {row['姓名']}**")
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
