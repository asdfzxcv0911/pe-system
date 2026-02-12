import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="體育課點名系統", layout="wide")

# CSS 優化：定義男女生顏色與按鈕樣式
st.markdown("""<style>
    .boy-name { color: #1e90ff; font-weight: bold; font-size: 1.1em; }
    .girl-name { color: #ff1493; font-weight: bold; font-size: 1.1em; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #28a745; color: white; font-weight: bold; }
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

# 安全檢查：確保有名單
if df.empty or '姓名' not in df.columns:
    st.warning(f"⚠️ 在『{selected_class}』分頁中找不到名單！")
    st.stop()

# 整理座號與日期格式
df['座號'] = df['座號'].astype(str).str.split('.').str[0]
today = datetime.now().strftime("%Y-%m-%d")
options = ["出席", "遲到", "缺席", "公假"]

if today not in df.columns:
    df[today] = "出席"

tab1, tab2 = st.tabs(["📅 快速點名", "📊 查看總表"])

with tab1:
    st.subheader(f"📅 {today} 點名作業")
    
    with st.form("attendance_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            
            # --- 顏色區分邏輯 ---
            gender = str(row.get('性別', '')) # 讀取性別欄位
            seat_info = f"{row['座號']}號 {row['姓名']}"
            
            if gender == "男":
                c1.markdown(f"<span class='boy-name'>♂ {seat_info}</span>", unsafe_allow_html=True)
            elif gender == "女":
                c1.markdown(f"<span class='girl-name'>♀ {seat_info}</span>", unsafe_allow_html=True)
            else:
                c1.write(f"**{seat_info}**")
            
            # 點名選擇器
            current_val = str(row[today]) if str(row[today]) in options else "出席"
            df.at[i, today] = c2.segmented_control(
                "狀態", options, 
                default=current_val, 
                key=f"btn_{selected_class}_{i}",
                label_visibility="collapsed"
            )
        
        if st.form_submit_button("✅ 確認點名並同步至雲端"):
            try:
                conn.update(worksheet=selected_class, data=df)
                st.success("存檔成功！資料已同步到 Google 表格。")
                st.balloons()
            except Exception as e:
                st.error(f"儲存失敗：{e}")

with tab2:
    st.subheader(f"📊 {selected_class} 紀錄總覽")
    st.dataframe(df, use_container_width=True, hide_index=True)
