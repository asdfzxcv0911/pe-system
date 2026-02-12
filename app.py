import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育點名系統", layout="wide")

# 2. 極簡化 CSS：大幅縮減間距與優化對比
st.markdown("""<style>
    /* 移除頂部與元件間的留白 */
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    [data-testid="stVerticalBlock"] > div { gap: 0rem; } 
    
    /* 統計單排看板：緊湊設計 */
    .stat-row {
        display: flex;
        justify-content: space-around;
        background-color: #ffffff;
        padding: 5px 0;
        border-bottom: 2px solid #333;
        margin-bottom: 10px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.7em; color: #666; display: block; }
    .stat-val { font-weight: 800; font-size: 0.9em; }

    /* 學生列：極小化間距 */
    .student-row { 
        border-bottom: 1px solid #f0f0f0; 
        padding: 2px 0; 
        margin: 0;
        display: flex;
        align-items: center;
    }
    
    /* 男女姓名顏色與大小 */
    .boy-name { color: #0056b3; font-weight: bold; font-size: 0.95em; }
    .girl-name { color: #c71585; font-weight: bold; font-size: 0.95em; }

    /* 儲存按鈕：顯眼且適中 */
    .stButton>button { 
        width: 100%; 
        height: 3em; 
        background-color: #1a73e8; 
        color: white; 
        border-radius: 8px; 
        font-weight: bold;
        margin-top: 15px;
    }
    
    @media (min-width: 1024px) {
        .main .block-container { max-width: 600px; margin: auto; }
    }
</style>""", unsafe_allow_html=True)

# 3. 建立連接
conn = st.connection("gsheets", type=GSheetsConnection)

# 4. 頂部選擇區
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

if df.empty or '姓名' not in df.columns:
    st.warning(f"名單空白")
    st.stop()

# --- 6. 統計看板 ---
boys = len(df[df['性別'] == '男'])
girls = len(df[df['性別'] == '女'])
st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box"><span class="stat-label">班級</span><span class="stat-val">{selected_class}</span></div>
        <div class="stat-box"><span class="stat-label">男生</span><span class="stat-val" style="color:#0056b3">{boys}人</span></div>
        <div class="stat-box"><span class="stat-label">女生</span><span class="stat-val" style="color:#c71585">{girls}人</span></div>
        <div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val">{len(df)}人</span></div>
    </div>
""", unsafe_allow_html=True)

# 7. 功能分頁
tab1, tab2 = st.tabs(["📅 點名", "📊 總表"])

with tab1:
    # --- 重要：固定預設為出席 ---
    # 無論 Google 表格原本寫什麼，載入時 App 介面一律先呈現「出席」
    df[date_str] = "出席"
    
    options = ["出席", "遲到", "缺席", "公假"]
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            st.markdown(f"<div class='student-row'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1.2, 3])
            
            # 姓名與顏色
            gender = str(row.get('性別', ''))
            name_text = f"{row['座號']}.{row['姓名']}"
            if gender == "男":
                c1.markdown(f"<span class='boy-name'>♂ {name_text}</span>", unsafe_allow_html=True)
            elif gender == "女":
                c1.markdown(f"<span class='girl-name'>♀ {name_text}</span>", unsafe_allow_html=True)
            else:
                c1.markdown(f"**{name_text}**", unsafe_allow_html=True)
            
            # 點名按鈕 (強制預設為 出席)
            df.at[i, date_str] = c2.segmented_control(
                "狀態", options, default="出席", 
                key=f"b_{selected_class}_{date_str}_{i}", 
                label_visibility="collapsed"
            )
            st.markdown("</div>", unsafe_allow_html=True)
            
        if st.form_submit_button(f"🚀 儲存並同步至雲端"):
            try:
                conn.update(worksheet=selected_class, data=df)
                st.success(f"已儲存！")
                st.balloons()
            except Exception as e:
                st.error(f"失敗：{e}")

with tab2:
    st.dataframe(df, use_container_width=True, hide_index=True)
