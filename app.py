import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 手機版/電腦版自動優化界面
st.set_page_config(page_title="體育課管理系統", layout="wide")
st.markdown("""<style>
    @media (max-width: 640px) { .main .block-container { padding: 10px; } }
    @media (min-width: 1024px) { .main .block-container { max-width: 900px; margin: auto; } }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #007bff; color: white; }
</style>""", unsafe_allow_html=True)

# 連接 Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

st.title("🏃‍♂️ 體育課點名成績系統")

# 選擇班級
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("選擇目前班級", classes)

# 讀取資料
df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all')

tab1, tab2, tab3 = st.tabs(["📅 點名", "🏆 成績", "📊 總表"])
today = datetime.now().strftime("%Y-%m-%d")

with tab1:
    st.header(f"{today} 點名")
    if today not in df.columns: df[today] = "出席"
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            col1, col2 = st.columns([1, 2])
            col1.write(f"**{row['姓名']}**")
            df.at[i, today] = col2.segmented_control("狀態", ["出席", "遲到", "缺席", "公假"], default=row[today], key=f"a_{selected_class}_{i}", label_visibility="collapsed")
        if st.form_submit_button("上傳點名紀錄"):
            conn.update(worksheet=selected_class, data=df)
            st.success("點名已同步至 Google Sheets！")

with tab2:
    item = st.text_input("測驗項目", "平時成績")
    if item not in df.columns: df[item] = 0
    with st.form("score_form"):
        for i, row in df.iterrows():
            col1, col2 = st.columns([1, 2])
            col1.write(f"**{row['姓名']}**")
            df.at[i, item] = col2.number_input("分數", value=float(df.at[i, item]), key=f"s_{selected_class}_{i}", label_visibility="collapsed")
        if st.form_submit_button("儲存成績"):
            conn.update(worksheet=selected_class, data=df)
            st.success(f"{item} 成績已同步！")

with tab3:
    st.dataframe(df, use_container_width=True)
    if st.button("手動更新數據"): st.rerun()
