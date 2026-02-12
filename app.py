import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育教學管理系統", layout="wide")

# 2. 老師專屬精確 CSS (9:16 比例、顏色鎖定、無橫線)
st.markdown("""<style>
    .main .block-container { padding: 0.5rem 0.2rem; }
    [data-testid="stVerticalBlock"] > div { gap: 0rem !important; }
    
    /* 統計看板：背景底色、純黑與男女專屬色 */
    .stat-row {
        display: flex; justify-content: space-around; background-color: #e9ecef;
        padding: 8px 0; margin-bottom: 5px; border-radius: 5px;
    }
    .stat-box { text-align: center; flex: 1; }
    .stat-label { font-size: 0.7em; color: #333; display: block; }
    .stat-val-black { font-weight: 900; font-size: 1.1em; color: #000000; }
    .stat-val-boy { font-weight: 900; font-size: 1.1em; color: #007bff; }
    .stat-val-girl { font-weight: 900; font-size: 1.1em; color: #d63384; }

    /* 學生列：同列顯示、完全移除橫線 */
    .student-row { padding: 1px 0; display: flex; align-items: center; border: none !important; }
    .boy-name { color: #007bff; font-weight: bold; font-size: 0.85em; white-space: nowrap; }
    .girl-name { color: #d63384; font-weight: bold; font-size: 0.85em; white-space: nowrap; }
    .normal-name { color: #000000; font-weight: bold; font-size: 0.85em; white-space: nowrap; }

    /* 儲存按鈕：高對比黑底白字 */
    .stButton>button { width: 100%; height: 3em; background-color: #000; color: white; border-radius: 5px; margin-top: 10px; }
    
    @media (min-width: 1024px) { .main .block-container { max-width: 400px; margin: auto; } }
</style>""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 頂部選擇區
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

tab1, tab2, tab3 = st.tabs(["📅 點名", "🏆 成績", "📊 總表"])

with tab1:
    df_att = load_data("點名")
    if not df_att.empty:
        # 統計看板 (班級與總數黑、男藍、女粉)
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
                st.success("點名成功！")

with tab2:
    df_score = load_data("成績")
    if not df_score.empty:
        # --- 雙模式輸入區 ---
        mode = st.radio("輸入方式", ["選擇現有項目", "自行輸入項目"], horizontal=True)
        
        if mode == "選擇現有項目":
            test_options = ["體適能-800m", "體適能-仰臥捲腹", "體適能-立定跳遠", "體適能-坐姿體前彎", "平時成績"]
            test_item = st.selectbox("請選擇測驗內容", test_options)
        else:
            test_item = st.text_input("請輸入新項目名稱", "自訂測驗")
        
        if test_item not in df_score.columns: df_score[test_item] = 0.0
        
        with st.form("score_form"):
            for i, row in df_score.iterrows():
                st.markdown("<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1.2, 2.5])
                name_t = f"{row['座號']}.{row['姓名']}"
                if row['性別']=="男": c1.markdown(f"<span class='boy-name'>{name_t}</span>", unsafe_allow_html=True)
                elif row['性別']=="女": c1.markdown(f"<span class='girl-name'>{name_t}</span>", unsafe_allow_html=True)
                df_score.at[i, test_item] = c2.number_input("分", value=float(df_score.at[i, test_item]), key=f"s_{selected_class}_{i}", label_visibility="collapsed")
                st.markdown("</div>", unsafe_allow_html=True)
            if st.form_submit_button(f"💾 儲存 {test_item} 成績"):
                conn.update(worksheet=f"{selected_class}_成績", data=df_score)
                st.success("成績儲存成功！")

with tab3:
    st.write("點名表預覽")
    st.dataframe(load_data("點名"), hide_index=True)
    st.write("成績表預覽")
    st.dataframe(load_data("成績"), hide_index=True)
