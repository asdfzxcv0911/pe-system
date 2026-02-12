import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育點名系統", layout="wide")

# 2. 超極簡 CSS：強制壓縮所有間距並修正顏色
st.markdown("""<style>
    /* 移除所有預設留白 */
    .main .block-container { padding-top: 0.5rem; padding-bottom: 0.5rem; }
    [data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
    [data-testid="column"] { padding: 0px !important; }
    
    /* 統計看板：純黑字體與極簡間距 */
    .stat-row {
        display: flex;
        justify-content: space-around;
        padding: 2px 0;
        border-bottom: 2px solid #000;
        margin-bottom: 5px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.7em; color: #444; display: block; }
    .stat-val { font-weight: 900; font-size: 1em; color: #000000 !important; }

    /* 學生列：完全壓縮高度 */
    .student-row { 
        border-bottom: 1px solid #eee; 
        padding: 0px; 
        margin: 0px;
        line-height: 1;
    }
    
    /* 姓名樣式：縮小字體以符合緊湊佈局 */
    .boy-name { color: #0056b3; font-weight: bold; font-size: 0.9em; }
    .girl-name { color: #c71585; font-weight: bold; font-size: 0.9em; }

    /* 調整選擇器按鈕的高度，使其不那麼佔空間 */
    div[data-baseweb="tab-list"] { margin-bottom: 5px; }
    
    /* 儲存按鈕 */
    .stButton>button { 
        width: 100%; 
        height: 3em; 
        background-color: #000; 
        color: white; 
        border-radius: 5px; 
        margin-top: 10px;
    }
    
    @media (min-width: 1024px) {
        .main .block-container { max-width: 500px; margin: auto; }
    }
</style>""", unsafe_allow_html=True)

# 3. 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 頂部選擇區 (班級與日期)
classes = ["402", "601", "602", "603", "604"]
selected_class = st.segmented_control("班級", classes, default="402")
selected_date = st.date_input("日期", datetime.now())
date_str = selected_date.strftime("%Y-%m-%d")

# 5. 讀取資料
try:
    df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all', subset=['姓名'] if '姓名' in pd.DataFrame().columns else None)
    df['座號'] = df['座號'].astype(str).str.split('.').str[0]
except Exception:
    st.error("讀取失敗")
    st.stop()

# --- 6. 統計看板：數字全部改為純黑 ---
boys = len(df[df['性別'] == '男'])
girls = len(df[df['性別'] == '女'])
st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box"><span class="stat-label">班級</span><span class="stat-val">{selected_class}</span></div>
        <div class="stat-box"><span class="stat-label">男生</span><span class="stat-val">{boys}</span></div>
        <div class="stat-box"><span class="stat-label">女生</span><span class="stat-val">{girls}</span></div>
        <div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val">{len(df)}</span></div>
    </div>
""", unsafe_allow_html=True)

# 7. 功能分頁
tab1, tab2 = st.tabs(["📅 點名", "📊 總表"])

with tab1:
    # 強制預設為出席
    df[date_str] = "出席"
    options = ["出席", "遲到", "缺席", "公假"]
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            st.markdown(f"<div class='student-row'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1, 2.5])
            
            # 姓名顯示
            gender = str(row.get('性別', ''))
            name_text = f"{row['座號']}.{row['姓名']}"
            if gender == "男":
                c1.markdown(f"<span class='boy-name'>{name_text}</span>", unsafe_allow_html=True)
            elif gender == "女":
                c1.markdown(f"<span class='girl-name'>{name_text}</span>", unsafe_allow_html=True)
            else:
                c1.markdown(f"**{name_text}**", unsafe_allow_html=True)
            
            # 點名按鈕
            df.at[i, date_str] = c2.segmented_control(
                "狀態", options, default="出席", 
                key=f"b_{selected_class}_{date_str}_{i}", 
                label_visibility="collapsed"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        if st.form_submit_button(f"🚀 儲存紀錄"):
            try:
                conn.update(worksheet=selected_class, data=df)
                st.success(f"已儲存！")
                st.balloons()
            except Exception:
                st.error(f"儲存失敗")

with tab2:
    st.dataframe(df, use_container_width=True, hide_index=True)
