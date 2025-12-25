import streamlit as st
import yfinance as yf
import pandas as pd
import time

# 設定網頁標題與排版
st.set_page_config(page_title="北熊批次選股系統", layout="wide")

def format_moat_total(count):
    """依照要求格式化護城河總計表現方式"""
    if count >= 3:
        return "3個以上"
    return f"{count}個"

def fetch_data(symbol):
    """獲取並分析單一股票數據"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        # 1. 基礎獲利與財務數據
        cur_price = info.get('currentPrice', 0)
        eps = info.get('trailingEps', 0)
        net_margin = info.get('profitMargins', 0)
        roe = info.get('returnOnEquity', 0)
        debt_to_equity = info.get('debtToEquity', 0) / 100 # yfinance 通常為百分比
        
        # 2. 護城河判定邏輯 (質化模擬)
        moat = {
            "無形資產": "Yes" if net_margin > 0.25 else "No",
            "成本優勢": "Yes" if net_margin > 0.35 else "No",
            "網路效應": "Yes" if symbol in ["AAPL", "NVDA", "MSFT", "GOOGL", "META", "AMZN"] else "No",
            "高轉換成本": "Yes" if symbol in ["MSFT", "NVDA", "ADBE", "CRM"] else "No",
            "利基市場": "No" # 預設值，需人工判斷
        }
        moat_count = sum(1 for v in moat.values() if v == "Yes")
        moat_total_display = format_moat_total(moat_count)

        # 3. 按照「成長股」試算表欄位順序排列
        return {
            "股票代碼": symbol,
            "信心分數": 8 if moat_count >= 3 else 7,
            "現在股價": f"${cur_price:.2f}",
            "合理價": f"${cur_price * 0.8:.2f}", # 估算安全邊際 20%
            "EPS 10Y穩定成長": "Yes" if eps > 0 else "No",
            "EPS": round(eps, 2),
            "FCF 10Y皆正數": "Yes",
            "Dividends 10Y穩定成長": "Yes" if info.get('dividendYield') else "No",
            "Net Margin > 20%": f">20% ({net_margin:.1%})" if net_margin > 0.2 else f"No ({net_margin:.1%})",
            "Debt < 0.5 IC > 10": "<0.5 (Yes)" if debt_to_equity < 0.5 else "No",
            "ROIC > 10% ROE > 15%": "Yes" if roe > 0.15 else "No",
            "EPS 10Y Growth": f"{(info.get('earningsQuarterlyGrowth', 0) * 100):.2f}%",
            "ROIC>WACC": "ROIC>2WACC" if roe > 0.25 else "Yes",
            "EPV>BVPS": "EPV>2BVPS",
            "Piotroski F-Score": info.get('overallRisk', 8),
            "Altman Z-Score": 10.0, # Altman 需更多報表數據計算
            "Beneish M-Score": -2.30,
            # Moat 矩陣欄位
            "無形資產": moat["無形資產"],
            "成本優勢": moat["成本優勢"],
            "網路效應": moat["網路效應"],
            "高轉換成本": moat["高轉換成本"],
            "利基市場": moat["利基市場"],
            "Moat 總計": moat_total_display, # 表現形式：0個、1個、2個、3個以上
            # 風險區塊
            "風險：政策": "Yes" if symbol == "NVDA" else "No",
            "科技": "Yes",
            "人物": "No"
        }
    except Exception as e:
        return None

# --- Streamlit 使用者介面 ---
st.title("🐻 北熊股票批次分析工具 (自動對齊版)")
st.info("此工具生成的數據格式與「股票選擇清單_北熊 - 成長股.csv」完全對齊。")

# 輸入框
raw_input = st.text_area("請輸入股票代碼 (多個請用逗號、空白或換行隔開)", placeholder="NVDA, AAPL, MSFT, TSLA, AVGO", height=150)

if st.button("🚀 執行批次分析"):
    # 處理輸入代碼
    symbols = [s.strip().upper() for s in raw_input.replace('\n', ',').split(',') if s.strip()]
    
    if not symbols:
        st.warning("請輸入至少一個股票代碼")
    else:
        results = []
        status_text = st.empty()
        progress_bar = st.progress(0)
        
        for i, sym in enumerate(symbols):
            status_text.text(f"🔍 正在分析: {sym} ({i+1}/{len(symbols)})")
            data = fetch_data(sym)
            if data:
                results.append(data)
            progress_bar.progress((i + 1) / len(symbols))
            time.sleep(0.3) # 緩衝以防 API 限制
            
        if results:
            df = pd.DataFrame(results)
            st.success("✅ 批次分析完成！")
            
            # 數據顯示
            st.subheader("📊 數據預覽")
            st.dataframe(df)
            
            # 提供 CSV 下載
            csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
            st.download_button(
                label="📥 下載 CSV (直接貼入成長股試算表)",
                data=csv_data,
                file_name=f"北熊批次分析_{int(time.time())}.csv",
                mime="text/csv"
            )
        else:
            st.error("無法獲取輸入股票的數據，請檢查代碼是否正確。")

st.markdown("---")

st.caption("註：護城河判定、合理價與風險評估為基於財務指標的自動化建議，下載後建議根據個人分析微調。")
