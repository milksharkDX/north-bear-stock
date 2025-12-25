import streamlit as st
import requests
import pandas as pd
import time

# 配置
API_KEY = "r5gT9lQiaBFY3otLnRYzndDfSUgs8chQ"
st.set_page_config(page_title="北熊 FMP 分析工具", layout="wide")

def fetch_fmp_data(url):
    """通用的 FMP 請求函式，加入錯誤處理"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"API 請求失敗，狀態碼：{response.status_code}")
            return None
    except Exception as e:
        st.error(f"連線發生錯誤: {e}")
        return None

def fetch_metrics(symbol):
    # 確保 period=annual 且 apikey 正確
    url = f"https://financialmodelingprep.com/api/v3/key-metrics/{symbol}?period=annual&apikey={API_KEY}"
    data = fetch_fmp_data(url)
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]
    return None

def fetch_profile(symbol):
    url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={API_KEY}"
    data = fetch_fmp_data(url)
    if data and isinstance(data, list) and len(data) > 0:
        return data[0]
    return None

st.title("🐻 北熊選股工具 (除錯優化版)")

raw_input = st.text_area("輸入股票代碼", placeholder="NVDA, AAPL", height=100)

if st.button("🚀 執行批次分析"):
    symbols = [s.strip().upper() for s in raw_input.replace('\n', ',').split(',') if s.strip()]
    
    if symbols:
        results = []
        bar = st.progress(0)
        
        for i, sym in enumerate(symbols):
            st.write(f"正在抓取 {sym}...") # 即時回饋，確保沒當機
            profile = fetch_profile(sym)
            metrics = fetch_metrics(sym)
            
            if profile and metrics:
                # 護城河邏輯
                nm = metrics.get('netProfitMargin', 0)
                roic = metrics.get('roic', 0)
                moat_count = 0
                if nm > 0.25: moat_count += 1
                if nm > 0.35: moat_count += 1
                if sym in ["AAPL", "NVDA", "MSFT", "GOOGL"]: moat_count += 1
                if roic > 0.2: moat_count += 1
                
                moat_display = "3個以上" if moat_count >= 3 else f"{moat_count}個"
                
                row = {
                    "股票代碼": sym,
                    "信心分數": 8 if moat_count >= 3 else 7,
                    "現在股價": f"${profile.get('price', 0):.2f}",
                    "合理價": f"${profile.get('price', 0) * 0.8:.2f}",
                    "Net Margin > 20%": f">20% ({nm:.1%})" if nm > 0.2 else f"No ({nm:.1%})",
                    "Piotroski F-Score": metrics.get('piotroskiScore', 0),
                    "Altman Z-Score": round(metrics.get('altmanZScore', 0), 2),
                    "Moat 總計": moat_display,
                    "風險：科技": "Yes"
                }
                results.append(row)
            else:
                st.error(f"⚠️ 無法取得 {sym} 的完整數據，請確認代號是否正確。")
            
            bar.progress((i + 1) / len(symbols))
        
        if results:
            df = pd.DataFrame(results)
            st.success("✅ 分析完成！")
            st.dataframe(df)
            csv = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button("📥 下載 CSV", csv, "analysis.csv", "text/csv")

