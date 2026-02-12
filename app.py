import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育管理系統", layout="wide")

# 2. 老師專屬 CSS：標題、零間距、顏色絕對鎖定、9:16 適配
st.markdown("""<style>
    .main-title {
        font-size: 1.5rem !important; font-weight: 900; white-space: nowrap;
        text-align: center; color: #FFD700 !important; background-color: #000; 
        padding: 8px 0; margin-bottom: 5px; border-radius: 5px;
    }
    .main .block-container { padding: 0.1rem 0.1rem !important; }
    div[data-testid="stVerticalBlock"] > div { gap: 0rem !important; margin: 0px !important; padding: 0px !important; }
    div[data-testid="stForm"] { padding: 0px !important; border: none !important; }
    div[data-testid="column"] { padding: 0px !important; }
    .stat-row {
        display: flex; justify-content: space-around; background-color: #f1f3f5;
        padding: 4px 0; margin-bottom: 2px; border-radius: 4px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.65em; color: #333; display: block; }
    .stat-val-black { font-weight: 900; font-size: 1.1em; color: #000000 !important; }
    .stat-val-boy { font-weight: 900; font-size: 1.1em; color: #007bff !important; }
    .stat-val-girl { font-weight: 900; font-size: 1.1em; color: #d63384 !important; }
    .student-row { padding: 0px !important; margin: 0px !important; display: flex; align-items: center; height: 36px; border: none !important; }
    .boy-name { color: #007bff; font-weight: 800; font-size: 0.85em; white-space: nowrap; padding-left: 5px; }
    .girl-name { color: #d63384; font-weight: 800; font-size: 0.85em; white-space: nowrap; padding-left: 5px; }
    .stButton>button { width: 100%; height: 2.8em; background-color: #000; color: white; border-radius: 4px; margin-top: 5px; font-weight: bold; }
    @media (min-width: 1024px) { .main .block-container { max-width: 400px; margin: auto; } }
</style>""", unsafe_allow_html=True)

st.markdown('<div class="main-title">體育課成績/出缺席登錄</div>', unsafe_allow_html=True)
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 快速選擇區
classes = ["402", "601", "602", "603", "604"]
selected_class = st.segmented_control("班級", classes, default="402")
selected_date = st.date_input("日期", datetime.now())
date_str = selected_date.strftime("%Y-%m-%d")

def load_data(sheet_suffix):
    try:
        sheet_name = f"{selected_class}_{sheet_suffix}"
        data = conn.read(worksheet=sheet_name, ttl=0).dropna(how='all', subset=['姓名'])
        data['座號'] = data['座號'].astype(str).str.split('.').str[0]
        return data
    except: return pd.DataFrame()

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
            if st.form_submit_button("🚀 儲存今日點名"):
                conn.update(worksheet=f"{selected_class}_點名", data=df_att)
                st.success("已同步至雲端")

# --- Tab 2: 成績 (自動記憶自訂項目) ---
with tab2:
    df_score = load_data("成績")
    if not df_score.empty:
        # 💡 自動讀取試算表中的所有現有測驗項目
        standard_items = ["體適能-800m", "體適能-仰臥捲腹", "體適能-立定跳遠", "體適能-坐姿體前彎", "平時成績"]
        # 找出表格中除了 metadata 以外的所有欄位
        existing_cols = [c for c in df_score.columns if c not in ['座號', '姓名', '性別', '座號 ', '姓名 ', '性別 ']]
        # 合併並去重，讓原本自訂的項目也能出現在選單中
        test_options = sorted(list(set(standard_items + existing_cols)))
        
        mode = st.radio("模式", ["選擇現有/自訂項目", "新增項目"], horizontal=True)
        
        if mode == "選擇現有/自訂項目":
            test_item = st.selectbox("請選擇測驗項目", test_options)
        else:
            test_item = st.text_input("輸入新項目名稱", placeholder="例如：跳繩、仰臥起坐")
        
        if test_item and test_item.strip():
            if test_item not in df_score.columns:
                df_score[test_item] = None
            
            # 確保舊數據能正確讀取顯示
            df_score[test_item] = pd.to_numeric(df_score[test_item], errors='coerce')
            
            with st.form("score_form"):
                for i, row in df_score.iterrows():
                    st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                    c1, c2 = st.columns([1, 2.5])
                    name_t = f"{row['座號']}.{row['姓名']}"
                    if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                    elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                    
                    # 讀取舊分數，若無則顯示空白 (移除 0.00)
                    val = float(row[test_item]) if pd.notnull(row[test_item]) else None
                    df_score.at[i, test_item] = c2.number_input("N", value=val, placeholder="未測", key=f"s_{selected_class}_{i}", label_visibility="collapsed")
                    st.markdown("</div>", unsafe_allow_html=True)
                if st.form_submit_button(f"💾 儲存 {test_item} 成績"):
                    conn.update(worksheet=f"{selected_class}_成績", data=df_score)
                    st.success(f"{test_item} 已存檔")
        else: st.info("💡 請選擇或新增測驗項目")

with tab3:
    st.write("點名歷史")
    st.dataframe(load_data("點名"), hide_index=True)
    st.write("成績歷史")
    st.dataframe(load_data("成績"), hide_index=True)
