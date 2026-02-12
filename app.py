import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育點名與成績系統", layout="wide")

# 2. 針對 9:16 比例與老師要求的精確 CSS
st.markdown("""<style>
    .main .block-container { padding: 0.5rem 0.2rem; }
    [data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
    
    /* 統計看板：純黑、藍、粉紅 */
    .stat-row {
        display: flex;
        justify-content: space-around;
        background-color: #e9ecef;
        padding: 8px 0;
        margin-bottom: 5px;
        border-radius: 5px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.7em; color: #333; display: block; }
    .stat-val-black { font-weight: 900; font-size: 1.1em; color: #000000; }
    .stat-val-boy { font-weight: 900; font-size: 1.1em; color: #007bff; }
    .stat-val-girl { font-weight: 900; font-size: 1.1em; color: #d63384; }

    /* 學生列：同一行顯示 */
    .student-row { padding: 1px 0; display: flex; align-items: center; }
    .boy-name { color: #007bff; font-weight: bold; font-size: 0.9em; white-space: nowrap; }
    .girl-name { color: #d63384; font-weight: bold; font-size: 0.9em; white-space: nowrap; }
    .normal-name { color: #000000; font-weight: bold; font-size: 0.9em; white-space: nowrap; }

    /* 儲存按鈕 */
    .stButton>button { width: 100%; height: 3em; background-color: #000; color: white; border-radius: 5px; margin-top: 10px; }
    
    @media (min-width: 1024px) { .main .block-container { max-width: 400px; margin: auto; } }
</style>""", unsafe_allow_html=True)

# 3. 建立連線
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

# 6. 統計看板 (純黑/藍/粉紅)
boys = len(df[df['性別'] == '男'])
girls = len(df[df['性別'] == '女'])
st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box"><span class="stat-label">班級</span><span class="stat-val-black">{selected_class}</span></div>
        <div class="stat-box"><span class="stat-label">男生</span><span class="stat-val-boy">{boys}</span></div>
        <div class="stat-box"><span class="stat-label">女生</span><span class="stat-val-girl">{girls}</span></div>
        <div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val-black">{len(df)}</span></div>
    </div>
""", unsafe_allow_html=True)

# 7. 功能頁籤
tab1, tab2, tab3 = st.tabs(["📅 點名", "🏆 登記成績", "📊 總表"])

# --- Tab 1: 點名 ---
with tab1:
    df[date_str] = "出席"
    options = ["出席", "遲到", "缺席", "公假"]
    with st.form("att_form"):
        for i, row in df.iterrows():
            st.markdown("<div class='student-row'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1.1, 3.2])
            gender = str(row.get('性別', ''))
            name_text = f"{row['座號']}.{row['姓名']}"
            if gender == "男": c1.markdown(f"<span class='boy-name'>{name_text}</span>", unsafe_allow_html=True)
            elif gender == "女": c1.markdown(f"<span class='girl-name'>{name_text}</span>", unsafe_allow_html=True)
            else: c1.markdown(f"<span class='normal-name'>{name_text}</span>", unsafe_allow_html=True)
            df.at[i, date_str] = c2.segmented_control("狀態", options, default="出席", key=f"b_{selected_class}_{date_str}_{i}", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        if st.form_submit_button("🚀 儲存點名"):
            conn.update(worksheet=selected_class, data=df)
            st.success("已儲存！")

# --- Tab 2: 登記成績 ---
with tab2:
    test_item = st.text_input("輸入測驗項目 (如: 800M, 跳繩)", "體適能成績")
    if test_item not in df.columns: df[test_item] = 0.0
    with st.form("score_form"):
        for i, row in df.iterrows():
            st.markdown("<div class='student-row'>", unsafe_allow_html=True)
            c1, c2 = st.columns([1.2, 2.5])
            gender = str(row.get('性別', ''))
            name_text = f"{row['座號']}.{row['姓名']}"
            if gender == "男": c1.markdown(f"<span class='boy-name'>{name_text}</span>", unsafe_allow_html=True)
            elif gender == "女": c1.markdown(f"<span class='girl-name'>{name_text}</span>", unsafe_allow_html=True)
            else: c1.markdown(f"<span class='normal-name'>{name_text}</span>", unsafe_allow_html=True)
            df.at[i, test_item] = c2.number_input("分數", value=float(df.at[i, test_item]), key=f"s_{selected_class}_{i}", label_visibility="collapsed")
            st.markdown("</div>", unsafe_allow_html=True)
        if st.form_submit_button(f"💾 儲存 {test_item} 成績"):
            conn.update(worksheet=selected_class, data=df)
            st.success("成績已同步！")

with tab3:
    st.dataframe(df, use_container_width=True, hide_index=True)
