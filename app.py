import streamlit as st
import pandas as pd

st.title("🔍 系統連線診斷中...")

# 1. 檢查 Secrets 是否有讀到
if "connections" not in st.secrets:
    st.error("❌ 系統完全讀不到 Secrets 設定，請檢查 Streamlit Cloud 的 Secrets 區塊。")
else:
    target_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
    st.write(f"✅ 成功讀取 Secrets 網址：`{target_url}`")

    # 2. 嘗試用最原始的方式讀取 (不透過 GSheets 套件)
    # 將網址轉換成 CSV 下載格式
    csv_url = target_url.replace("/edit", "/export?format=csv")
    
    st.write("正在測試各班級分頁...")
    classes = ["402", "601", "602", "603", "604"]
    
    for cls in classes:
        try:
            # 嘗試讀取特定分頁
            test_df = pd.read_csv(f"{csv_url}&sheet={cls}")
            st.success(f"✅ 班級 {cls} 連線成功！偵測到欄位：{list(test_df.columns)}")
        except Exception as e:
            st.error(f"❌ 班級 {cls} 讀取失敗。原因：{e}")

st.info("請把上面的測試結果（特別是紅色的錯誤訊息）截圖或複製傳給我。")
