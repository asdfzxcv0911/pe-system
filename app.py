import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定與 RWD 樣式優化
st.set_page_config(page_title="體育教學管理系統", layout="wide")

st.markdown("""<style>
    /* 移除頂部過多留白 */
    .main .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    
    /* 統計看板樣式 */
    .stat-container {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #ddd;
    }
    .stat-item { flex: 1; min-width: 100px; text-align: center; }
    .stat-label { font-size: 0.8em; color: #666; display: block; }
    .stat-value { font-size: 1.2em; font-weight: bold; }

    /* 男女姓名顏色 */
    .boy-name { color: #007bff; font-weight: bold; }
    .girl-name { color: #d63384; font-weight: bold; }

    /* 針對手機端優化按鈕寬度 */
    .stButton>button { width: 100%; height: 3.5em; border-radius: 8px; font-weight: 700; }
    
    /* 表單區塊分隔線 */
    .student-row { border-bottom: 1px solid #eee; padding: 10px 0; }
    
    @media (min-width: 1024px) {
        .main .block-container { max-width: 800px; margin: auto; }
    }
</style>""", unsafe_allow_html=True)

# 2. 建立 Google Sheets 連接
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 側邊欄設定
st.sidebar.header("🛠️ 系統選單")
classes = ["402", "601", "602", "603", "604"]
selected_class = st.sidebar.selectbox("切換班級", classes)

# 自由選擇日期
selected_date = st.sidebar.date_input("點名日期", datetime.now())
date_str = selected_date.strftime("%Y-%m-%d")

# 4. 讀取並處理資料
try:
    df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all', subset=['姓名'] if '姓名' in pd.DataFrame().columns else None)
    df['座號'] = df['座號'].astype(str).str.split('.').str[0]
except Exception:
    st.error("讀取失敗，請確認 Google 試算表分頁與標題正確。")
    st.stop()

if df.empty or '姓名' not in df.columns:
    st.warning(f"⚠️ 在 {selected_class} 找不到學生名單。")
    st.stop()

# --- 5. 顯示統計看板 ---
boys = len(df[df['性別'] == '男'])
girls = len(df[df['性別'] == '女'])
st.markdown(f"""
    <div class="stat-container">
        <div class="stat-item"><span class="stat-label">班級</span><span class="stat-value">{selected_class}</span></div>
        <div class="stat-item"><span class="stat-label">男生</span><span class="stat-value" style="color:#007bff">{boys}</span></div>
        <div class="stat-item"><span class="stat-label">女生</span><span class="stat-value" style="color:#d63384">{girls}</span></div>
        <div class="stat-item"><span class="stat-label">總人數</span><span class="stat-value">{len(df)}</span></div>
    </div>
""", unsafe_allow_html=True)

# 6. 功能分頁
tab1, tab2 = st.tabs(["📅 點名/成績", "📊 數據總表"])

with tab1:
    st.info(f"📍 目前正在處理：{date_str} 的紀錄")
    
    if date_str not in df.columns:
        df[date_str] = "出席"
    
    options = ["出席", "遲到", "缺席", "公假"]
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            # 建立學生行區塊
            with st.container():
                st.markdown(f"<div class='student-row'>", unsafe_allow_html=True)
                c1, c2 = st.columns([1.5, 3])
                
                # 姓名顯示
                gender = str(row.get('性別', ''))
                name_text = f"{row['座號']}. {row['姓名']}"
                if gender == "男":
                    c1.markdown(f"<span class='boy-name'>♂ {name_text}</span>", unsafe_allow_html=True)
                elif gender == "女":
                    c1.markdown(f"<span class='girl-name'>♀ {name_text}</span>", unsafe_allow_html=True)
                else:
                    c1.markdown(f"**{name_text}**", unsafe_allow_html=True)
                
                # 點名按鈕 (手機端會自動換行)
                curr = str(row[date_str]) if str(row[date_str]) in options else "出席"
                df.at[i, date_str] = c2.segmented_control(
                    "狀態", options, default=curr, key=f"b_{selected_class}_{date_str}_{i}", label_visibility="collapsed"
                )
                st.markdown("</div>", unsafe_allow_html=True)
        
        # 儲存按鈕
        if st.form_submit_button("🚀 儲存並同步至雲端"):
            try:
                conn.update(worksheet=selected_class, data=df)
                st.success(f"{date_str} 紀錄已更新！")
                st.balloons()
            except Exception as e:
                st.error(f"同步失敗：{e}")

with tab2:
    st.subheader("完整試算表預覽")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button("🔄 重新載入最新資料"):
        st.rerun()
