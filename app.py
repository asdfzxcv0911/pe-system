import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="體育課點名系統", layout="wide")

# 介面優化
st.markdown("""<style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #28a745; color: white; font-weight: bold; }
    @media (max-width: 640px) { .main .block-container { padding: 10px; } }
</style>""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 選擇班級
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("請選擇班級", classes)

# 2. 讀取資料並檢查
try:
    # 這裡強製使用讀取工作表的方式
    df = conn.read(worksheet=selected_class, ttl=0)
    # 移除全空的列
    df = df.dropna(how='all', subset=['姓名'] if '姓名' in df.columns else None)
except Exception as e:
    st.error(f"連線失敗：{e}")
    st.stop()

# --- 安全鎖：檢查是否有資料 ---
if df.empty or '姓名' not in df.columns:
    st.warning(f"⚠️ 在『{selected_class}』分頁中找不到學生名單！")
    st.info("💡 請確認 Google 表格第一列是否有『座號』和『姓名』，且下方已填入名單。")
    if st.button("🔄 點我重新讀取表格"):
        st.rerun()
    st.stop()

# --- 如果有資料，才顯示點名介面 ---
# 處理座號格式
if '座號' in df.columns:
    df['座號'] = df['座號'].astype(str).str.split('.').str[0]

tab1, tab2 = st.tabs(["📅 快速點名", "📊 查看總表"])
today = datetime.now().strftime("%Y-%m-%d")

with tab1:
    st.subheader(f"📅 {today} 點名作業")
    if today not in df.columns:
        df[today] = "出席"
    
    with st.form("attendance_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            c1.write(f"**{row.get('座號', '')}號 {row['姓名']}**")
            
            # 點名按鈕
            res = c2.segmented_control(
                "狀態", ["出席", "遲到", "缺席", "公假"], 
                default=row[today], 
                key=f"btn_{selected_class}_{i}",
                label_visibility="collapsed"
            )
            df.at[i, today] = res
        
        # 只有在有資料的情況下才會出現這個按鈕
        if st.form_submit_button("✅ 確認點名並同步至雲端"):
            conn.update(worksheet=selected_class, data=df)
            st.success("存檔成功！資料已寫入 Google 表格。")
            st.balloons()

with tab2:
    st.subheader(f"📊 {selected_class} 紀錄總覽")
    st.dataframe(df, use_container_width=True, hide_index=True)
