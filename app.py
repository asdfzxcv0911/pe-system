import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育管理系統", layout="wide")

# 2. 老師專屬 CSS：標題放大變色、零間隔、顏色鎖定
st.markdown("""<style>
    /* 標題：放大、換色（鮮黃色在深色背景極明顯）、強制單行 */
    .main-title {
        font-size: 1.6rem !important; 
        font-weight: 900; 
        white-space: nowrap;
        text-align: center; 
        color: #FFD700 !important; /* 金黃色，對比度最高 */
        background-color: #000; /* 給標題一個黑色底塊增加辨識度 */
        padding: 5px 0;
        margin-bottom: 5px;
        border-radius: 5px;
    }

    /* 徹底移除所有預設間距與橫線 */
    .main .block-container { padding: 0.1rem 0.1rem !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; margin: 0px !important; padding: 0px !important; }
    div[data-testid="stForm"] { padding: 0px !important; border: none !important; }
    div[data-testid="column"] { padding: 0px !important; }
    
    /* 統計看板：黑、藍、粉紅鎖定 */
    .stat-row {
        display: flex; justify-content: space-around; background-color: #f1f3f5;
        padding: 4px 0; margin-bottom: 2px; border-radius: 4px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.65em; color: #333; display: block; }
    .stat-val-black { font-weight: 900; font-size: 1.1em; color: #000000 !important; }
    .stat-val-boy { font-weight: 900; font-size: 1.1em; color: #007bff !important; }
    .stat-val-girl { font-weight: 900; font-size: 1.1em; color: #d63384 !important; }

    /* 學生操作列：完全無橫線且高度壓縮 */
    .student-row { 
        padding: 0px !important; margin: 0px !important;
        display: flex; align-items: center;
        height: 36px; border: none !important; /* 移除橫線 */
    }
    
    /* 姓名樣式：藍、粉紅、黑 */
    .boy-name { color: #007bff; font-weight: 800; font-size: 0.85em; white-space: nowrap; padding-left: 5px; }
    .girl-name { color: #d63384; font-weight: 800; font-size: 0.85em; white-space: nowrap; padding-left: 5px; }
    
    /* 儲存按鈕：高對比黑底白字 */
    .stButton>button { 
        width: 100%; height: 2.8em; background-color: #000; color: white; border-radius: 4px; margin-top: 5px; font-weight: bold;
    }
    
    @media (min-width: 1024px) { .main .block-container { max-width: 400px; margin: auto; } }
</style>""", unsafe_allow_html=True)

# --- 醒目大標題 ---
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

tab1, tab2, tab3 = st.tabs(["📅 點名", "🏆 成績", "📊 總表"])

# --- Tab 1: 點名 ---
with tab1:
    df_att = load_data("點名")
    if not df_att.empty:
        b, g = len(df_att[df_att['性別']=='男']), len(df_att[df_att['性別']=='女'])
        st.markdown(f'<div class="stat-row"><div class="stat-box"><span class="stat-label">班級</span><span class="stat-val-black">{selected_class}</span></div><div class="stat-box"><span class="stat-label">男生</span><span class="stat-val-boy">{b}</span></div><div class="stat-box"><span class="stat-label">女生</span><span class="stat-val-girl">{g}</span></div><div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val-black">{len(df_att)}</span></div></div>', unsafe_allow_html=True)
        
        df_att[date_str] = "出席"
        opts = ["出席", "遲到", "缺席", "公假"]
        
        with st.form("att_form"):
            for i, row in df_att.iterrows():
                st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 3.2])
                name_t = f"{row['座號']}.{row['姓名']}"
                if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                df_att.at[i, date_str] = c2.segmented_control("S", opts, default="出席", key=f"a_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 儲存點名"):
                conn.update(worksheet=f"{selected_class}_點名", data=df_att)
                st.success("已存檔")

# --- Tab 2: 成績 (移除 0.00 預設值) ---
with tab2:
    df_score = load_data("成績")
    if not df_score.empty:
        mode = st.radio("模式", ["現有項目", "自訂"], horizontal=True)
        test_item = st.selectbox("項目", ["體適能-800m", "體適能-仰臥捲腹", "體適能-立定跳遠", "體適能-坐姿體前彎", "平時成績"]) if mode == "現有項目" else st.text_input("輸入名稱", "自訂測驗")
        
        if test_item not in df_score.columns: df_score[test_item] = None
        
        with st.form("score_form"):
            for i, row in df_score.iterrows():
                st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1, 2.5])
                name_t = f"{row['座號']}.{row['姓名']}"
                if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                
                # 使用 value=None 讓輸入框預設為空，不顯示 0.00
                df_score.at[i, test_item] = c2.number_input("N", value=None, placeholder="輸入分數", key=f"s_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button(f"💾 儲存 {test_item}"):
                conn.update(worksheet=f"{selected_class}_成績", data=df_score)
                st.success("成績已儲存")

with tab3:
    st.dataframe(load_data("點名"), hide_index=True)
    st.dataframe(load_data("成績"), hide_index=True)
