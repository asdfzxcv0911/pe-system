import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育課管理系統", layout="wide")

# 2. 終極 CSS：標題單行化、徹底移除所有間距
st.markdown("""<style>
    /* 標題強制單行且縮小字體以適應手機 */
    .main-title {
        font-size: 1.2rem;
        font-weight: 900;
        white-space: nowrap;
        text-align: center;
        margin-bottom: 5px;
    }

    /* 移除全網頁所有預設間隔 (Gap) */
    .main .block-container { padding: 0.2rem 0.1rem !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; margin: 0px !important; padding: 0px !important; }
    div[data-testid="stForm"] { padding: 0px !important; border: none !important; }
    div[data-testid="column"] { padding: 0px !important; }
    
    /* 統計看板：黑、藍、粉紅鎖定 */
    .stat-row {
        display: flex; justify-content: space-around; background-color: #e9ecef;
        padding: 4px 0; margin-bottom: 2px; border-radius: 4px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.6em; color: #333; display: block; }
    .stat-val-black { font-weight: 900; font-size: 0.9em; color: #000000; }
    .stat-val-boy { font-weight: 900; font-size: 0.9em; color: #007bff; }
    .stat-val-girl { font-weight: 900; font-size: 0.9em; color: #d63384; }

    /* 學生列：名字與按鈕「絕對同列」且「零間距」 */
    .student-row { 
        padding: 0px !important; 
        margin: 0px !important;
        display: flex;
        align-items: center;
        height: 34px; /* 極限高度，完全消除間隔感 */
        border: none !important;
    }
    
    /* 姓名樣式：藍、粉紅、黑 */
    .boy-name { color: #007bff; font-weight: bold; font-size: 0.8em; white-space: nowrap; }
    .girl-name { color: #d63384; font-weight: bold; font-size: 0.8em; white-space: nowrap; }
    .normal-name { color: #000000; font-weight: bold; font-size: 0.8em; }

    /* 儲存按鈕 */
    .stButton>button { 
        width: 100%; height: 2.5em; background-color: #000; color: white; border-radius: 4px; margin-top: 5px; 
    }
    
    @media (min-width: 1024px) { .main .block-container { max-width: 380px; margin: auto; } }
</style>""", unsafe_allow_html=True)

# --- 標題區 (調整為單行) ---
st.markdown('<div class="main-title">【體育課成績/出缺席登錄】</div>', unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 選擇區
classes = ["402", "601", "602", "603", "604"]
selected_class = st.segmented_control("班級", classes, default="402")
selected_date = st.date_input("日期", datetime.now())
date_str = selected_date.strftime("%Y-%m-%d")

# 4. 讀取功能
def load_data(sheet_suffix):
    try:
        sheet_name = f"{selected_class}_{sheet_suffix}"
        data = conn.read(worksheet=sheet_name, ttl=0).dropna(how='all', subset=['姓名'])
        data['座號'] = data['座號'].astype(str).str.split('.').str[0]
        return data
    except:
        return pd.DataFrame()

tab1, tab2 = st.tabs(["📅 點名", "🏆 成績"])

# --- Tab 1: 點名 ---
with tab1:
    df_att = load_data("點名")
    if not df_att.empty:
        # 統計看板 (黑/藍/粉紅)
        b, g = len(df_att[df_att['性別']=='男']), len(df_att[df_att['性別']=='女'])
        st.markdown(f'<div class="stat-row"><div class="stat-box"><span class="stat-label">班級</span><span class="stat-val-black">{selected_class}</span></div><div class="stat-box"><span class="stat-label">男生</span><span class="stat-val-boy">{b}</span></div><div class="stat-box"><span class="stat-label">女生</span><span class="stat-val-girl">{g}</span></div><div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val-black">{len(df_att)}</span></div></div>', unsafe_allow_html=True)
        
        df_att[date_str] = "出席"
        options = ["出席", "遲到", "缺席", "公假"]
        
        with st.form("att_form"):
            for i, row in df_att.iterrows():
                st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 3.2])
                name_t = f"{row['座號']}.{row['姓名']}"
                if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                else: c1.markdown(f"<span class='normal-name'>{name_t}</span>", unsafe_allow_html=True)
                
                df_att.at[i, date_str] = c2.segmented_control("S", options, default="出席", key=f"a_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 儲存今日點名"):
                conn.update(worksheet=f"{selected_class}_點名", data=df_att)
                st.success("已儲存")

# --- Tab 2: 成績 ---
with tab2:
    df_score = load_data("成績")
    if not df_score.empty:
        mode = st.radio("模式", ["選擇項目", "自行輸入"], horizontal=True)
        if mode == "選擇項目":
            test_options = ["體適能-800m", "體適能-仰臥捲腹", "體適能-立定跳遠", "體適能-坐姿體前彎", "平時成績"]
            test_item = st.selectbox("項目", test_options)
        else:
            test_item = st.text_input("輸入名稱", "自訂測驗")
        
        if test_item not in df_score.columns: df_score[test_item] = 0.0
        
        with st.form("score_form"):
            for i, row in df_score.iterrows():
                st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2.5])
                name_t = f"{row['座號']}.{row['姓名']}"
                if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                
                df_score.at[i, test_item] = c2.number_input("分", value=float(df_score.at[i, test_item]), key=f"s_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button(f"💾 儲存 {test_item} 成績"):
                conn.update(worksheet=f"{selected_class}_成績", data=df_score)
                st.success("已儲存")
