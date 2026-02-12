import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="體育課點名系統", layout="wide")

# 介面風格設定
st.markdown("""<style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #28a745; color: white; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    @media (max-width: 640px) { .main .block-container { padding: 10px; } }
</style>""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 選擇班級
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("請選擇班級", classes)

# 2. 讀取資料
try:
    df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all', subset=['姓名'] if '姓名' in pd.DataFrame().columns else None)
except Exception as e:
    st.error(f"連線失敗，請檢查 Google Sheets 設定。")
    st.stop()

# --- 安全檢查：如果沒名字，停止操作 ---
if df.empty or '姓名' not in df.columns:
    st.warning(f"⚠️ 在『{selected_class}』分頁中找不到名單！")
    st.info("💡 請確認 Google 表格中是否有『座號』與『姓名』兩欄，且下方有名單。")
    if st.button("🔄 重新整理"): st.rerun()
    st.stop()

# 整理座號與基本狀態
df['座號'] = df['座號'].astype(str).str.split('.').str[0]
today = datetime.now().strftime("%Y-%m-%d")
options = ["出席", "遲到", "缺席", "公假"]

if today not in df.columns:
    df[today] = "出席"

tab1, tab2 = st.tabs(["📅 快速點名", "📊 查看總表"])

with tab1:
    st.subheader(f"📅 {today} 點名作業")
    
    # 建立表單
    with st.form("attendance_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            c1.write(f"**{row['座號']}號 {row['姓名']}**")
            
            # 防錯機制：如果格子是空的或亂碼，預設為「出席」
            current_val = str(row[today]) if str(row[today]) in options else "出席"
            
            # 點名選擇器
            df.at[i, today] = c2.segmented_control(
                "狀態", options, 
                default=current_val, 
                key=f"btn_{selected_class}_{i}",
                label_visibility="collapsed"
            )
        
        # 儲存按鈕 (放在迴圈外面，確保一定會出現)
        submit = st.form_submit_button("✅ 確認點名並同步至雲端")
        
        if submit:
            try:
                conn.update(worksheet=selected_class, data=df)
                st.success("存檔成功！資料已寫入 Google 表格。")
                st.balloons()
            except Exception as e:
                st.error(f"儲存失敗，請確認試算表是否有共用給服務帳號：{e}")

with tab2:
    st.subheader(f"📊 {selected_class} 紀錄總覽")
    st.dataframe(df, use_container_width=True, hide_index=True)
