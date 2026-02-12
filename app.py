import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育管理系統", layout="wide")

# 2. 終極 CSS：標題單行、零間隔、顏色鎖定
st.markdown("""<style>
    /* 標題單行化與置頂 */
    .main-title {
        font-size: 1.25rem; font-weight: 900; white-space: nowrap;
        text-align: center; margin-bottom: 5px; color: #000;
    }

    /* 徹底移除所有預設間距 */
    .main .block-container { padding: 0.1rem 0.1rem !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; margin: 0px !important; padding: 0px !important; }
    div[data-testid="stForm"] { padding: 0px !important; border: none !important; }
    div[data-testid="column"] { padding: 0px !important; }
    
    /* 統計看板：黑、藍、粉紅鎖定 */
    .stat-row {
        display: flex; justify-content: space-around; background-color: #f1f3f5;
        padding: 5px 0; margin-bottom: 3px; border-radius: 4px; border: 1px solid #dee2e6;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.65em; color: #495057; display: block; }
    .stat-val-black { font-weight: 900; font-size: 1.05em; color: #000000 !important; }
    .stat-val-boy { font-weight: 900; font-size: 1.05em; color: #007bff !important; }
    .stat-val-girl { font-weight: 900; font-size: 1.05em; color: #d63384 !important; }

    /* 學生操作列：零間距極速排版 */
    .student-row { 
        padding: 0px !important; margin: 0px !important;
        display: flex; align-items: center;
        height: 38px; border-bottom: 1px solid #f8f9fa; /* 極細底線輔助對齊但無間隔 */
    }
    
    /* 姓名樣式：藍、粉紅、黑 */
    .boy-name { color: #007bff; font-weight: 800; font-size: 0.85em; white-space: nowrap; padding-left: 5px; }
    .girl-name { color: #d63384; font-weight: 800; font-size: 0.85em; white-space: nowrap; padding-left: 5px; }
    .normal-name { color: #000000; font-weight: 800; font-size: 0.85em; padding-left: 5px; }

    /* 按鈕樣式微調 */
    .stSegmentedControl { margin: 0px !important; }
    
    /* 儲存按鈕：黑底白字高對比 */
    .stButton>button { 
        width: 100%; height: 3em; background-color: #000; color: white; border-radius: 6px; margin-top: 8px; font-weight: 900;
    }
    
    @media (min-width: 1024px) { .main .block-container { max-width: 420px; margin: auto; } }
</style>""", unsafe_allow_html=True)

# --- 單行標題 ---
st.markdown('<div class="main-title">【體育課成績/出缺席登錄】</div>', unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 快速選擇區
classes = ["402", "601", "602", "603", "604"]
selected_class = st.segmented_control("班級", classes, default="402")
selected_date = st.date_input("日期", datetime.now())
date_str = selected_date.strftime("%Y-%m-%d")

# 4. 數據讀取
def load_data(sheet_suffix):
    try:
        sheet_name = f"{selected_class}_{sheet_suffix}"
        data = conn.read(worksheet=sheet_name, ttl=0).dropna(how='all', subset=['姓名'])
        data['座號'] = data['座號'].astype(str).str.split('.').str[0]
        return data
    except:
        return pd.DataFrame()

# --- 復原三個分頁 ---
tab1, tab2, tab3 = st.tabs(["📅 點名", "🏆 成績", "📊 總表"])

# --- Tab 1: 點名介面 (新排版) ---
with tab1:
    df_att = load_data("點名")
    if not df_att.empty:
        # 統計看板
        b, g = len(df_att[df_att['性別']=='男']), len(df_att[df_att['性別']=='女'])
        st.markdown(f'<div class="stat-row"><div class="stat-box"><span class="stat-label">班級</span><span class="stat-val-black">{selected_class}</span></div><div class="stat-box"><span class="stat-label">男生</span><span class="stat-val-boy">{b}</span></div><div class="stat-box"><span class="stat-label">女生</span><span class="stat-val-girl">{g}</span></div><div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val-black">{len(df_att)}</span></div></div>', unsafe_allow_html=True)
        
        df_att[date_str] = "出席" # 預設出席
        opts = ["出席", "遲到", "缺席", "公假"]
        
        with st.form("att_form"):
            for i, row in df_att.iterrows():
                st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1.1, 3.1]) # 調整比例確保同列
                name_t = f"{row['座號']}.{row['姓名']}"
                if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                else: c1.markdown(f"<span class='normal-name'>{name_t}</span>", unsafe_allow_html=True)
                df_att.at[i, date_str] = c2.segmented_control("S", opts, default="出席", key=f"a_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 儲存今日點名紀錄"):
                conn.update(worksheet=f"{selected_class}_點名", data=df_att)
                st.success("存檔成功")
    else:
        st.warning("請確認 Google 試算表中有 [班級_點名] 分頁")

# --- Tab 2: 成績介面 (新排版) ---
with tab2:
    df_score = load_data("成績")
    if not df_score.empty:
        mode = st.radio("模式", ["現有項目", "自訂"], horizontal=True)
        if mode == "現有項目":
            test_opts = ["體適能-800m", "體適能-仰臥捲腹", "體適能-立定跳遠", "體適能-坐姿體前彎", "平時成績"]
            test_item = st.selectbox("項目", test_opts)
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
                df_score.at[i, test_item] = c2.number_input("N", value=float(df_score.at[i, test_item]), key=f"s_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button(f"💾 儲存 {test_item} 成績"):
                conn.update(worksheet=f"{selected_class}_成績", data=df_score)
                st.success("成績存檔成功")

# --- Tab 3: 總表復原 ---
with tab3:
    st.markdown("### 📋 點名歷史紀錄")
    st.dataframe(load_data("點名"), hide_index=True, use_container_width=True)
    st.markdown("---")
    st.markdown("### 🏆 成績歷史紀錄")
    st.dataframe(load_data("成績"), hide_index=True, use_container_width=True)
