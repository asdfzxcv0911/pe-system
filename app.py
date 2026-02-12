import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 網頁基礎設定
st.set_page_config(page_title="體育教學管理系統", layout="wide")

# CSS 優化：針對手機端調整按鈕與看板
st.markdown("""<style>
    /* 移除多餘邊距 */
    .main .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    
    /* 統計單排看板：移除底色增加對比 */
    .stat-row {
        display: flex;
        justify-content: space-around;
        align-items: center;
        background-color: #ffffff;
        padding: 10px 0;
        border-bottom: 2px solid #333;
        margin-bottom: 15px;
        font-size: 0.95em;
    }
    .stat-box { text-align: center; flex: 1; border-right: 1px solid #eee; }
    .stat-box:last-child { border-right: none; }
    .stat-label { font-size: 0.75em; color: #555; display: block; margin-bottom: 2px; }
    .stat-val { font-weight: 800; color: #000; }

    /* 男女姓名顏色 */
    .boy-name { color: #0056b3; font-weight: bold; }
    .girl-name { color: #c71585; font-weight: bold; }

    /* 讓選擇器按鈕更高、更好點 */
    div[data-baseweb="tab-list"] { gap: 5px; }
    button[data-baseweb="tab"] { border-radius: 8px !important; }
    
    /* 儲存按鈕樣式 */
    .stButton>button { width: 100%; height: 3.5em; background-color: #1a73e8; color: white; border-radius: 10px; font-weight: bold; }
    
    @media (min-width: 1024px) {
        .main .block-container { max-width: 800px; margin: auto; }
    }
</style>""", unsafe_allow_html=True)

# 2. 建立連接
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 頂部選擇區 (將原本在側邊欄的改到主畫面)
classes = ["402", "601", "602", "603", "604"]

# 使用分段選擇器 (像按鈕一樣) 切換班級
selected_class = st.segmented_control(
    "選擇班級", classes, default="402", key="class_selector"
)

# 日期選擇 (放在班級下方)
selected_date = st.date_input("點名日期", datetime.now(), key="date_selector")
date_str = selected_date.strftime("%Y-%m-%d")

# 4. 讀取資料
try:
    df = conn.read(worksheet=selected_class, ttl=0).dropna(how='all', subset=['姓名'] if '姓名' in pd.DataFrame().columns else None)
    df['座號'] = df['座號'].astype(str).str.split('.').str[0]
except Exception:
    st.error("讀取失敗，請確認 Google Sheets 設定。")
    st.stop()

if df.empty or '姓名' not in df.columns:
    st.warning(f"⚠️ {selected_class} 尚未填入名單。")
    st.stop()

# --- 5. 顯示單排統計看板 ---
boys = len(df[df['性別'] == '男'])
girls = len(df[df['性別'] == '女'])
total = len(df)

st.markdown(f"""
    <div class="stat-row">
        <div class="stat-box"><span class="stat-label">班級</span><span class="stat-val">{selected_class}</span></div>
        <div class="stat-box"><span class="stat-label">男生</span><span class="stat-val" style="color:#0056b3">{boys}人</span></div>
        <div class="stat-box"><span class="stat-label">女生</span><span class="stat-val" style="color:#c71585">{girls}人</span></div>
        <div class="stat-box"><span class="stat-label">總人數</span><span class="stat-val">{total}人</span></div>
    </div>
""", unsafe_allow_html=True)

# 6. 功能分頁
tab1, tab2 = st.tabs(["📅 快速點名", "📊 查看總表"])

with tab1:
    if date_str not in df.columns:
        df[date_str] = "出席"
    
    options = ["出席", "遲到", "缺席", "公假"]
    
    with st.form("att_form"):
        for i, row in df.iterrows():
            c1, c2 = st.columns([1, 2])
            
            # 姓名顯示
            gender = str(row.get('性別', ''))
            name_text = f"{row['座號']}. {row['姓名']}"
            if gender == "男":
                c1.markdown(f"<span class='boy-name'>♂ {name_text}</span>", unsafe_allow_html=True)
            elif gender == "女":
                c1.markdown(f"<span class='girl-name'>♀ {name_text}</span>", unsafe_allow_html=True)
            else:
                c1.markdown(f"**{name_text}**", unsafe_allow_html=True)
            
            # 點名按鈕
            curr = str(row[date_str]) if str(row[date_str]) in options else "出席"
            df.at[i, date_str] = c2.segmented_control(
                "狀態", options, default=curr, key=f"b_{selected_class}_{date_str}_{i}", label_visibility="collapsed"
            )
            st.write("---")
            
        if st.form_submit_button(f"🚀 儲存 {date_str} 紀錄"):
            try:
                conn.update(worksheet=selected_class, data=df)
                st.success(f"{date_str} 已同步成功！")
                st.balloons()
            except Exception as e:
                st.error(f"同步失敗：{e}")

with tab2:
    st.dataframe(df, use_container_width=True, hide_index=True)
    if st.button("🔄 重新整理"): st.rerun()
