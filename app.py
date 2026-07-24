import streamlit as st
import akshare as ak
import yfinance as yf
import pandas as pd
import plotly.express as px

# 网页配置
st.set_page_config(page_title="全球市场与资金面监控看板", layout="wide")
st.title("📈 股票市场多维监控看板（A股 / 美股夜盘 / 资金面）")

# 创建三大标签页
tab1, tab2, tab3 = st.tabs(["🇨🇳 A股与资金面", "🇺🇸 美股盘前/夜盘", "📰 实时信息面"])

# --- Tab 1: A股与资金面监控 ---
with tab1:
    st.header("A股实时大盘与主力资金流向")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("大盘指数概览")
        try:
            df_index = ak.stock_zh_a_spot_em()
            target_indices = df_index[df_index['名称'].isin(['上证指数', '深证成指', '创业板指'])]
            st.dataframe(target_indices[['代码', '名称', '最新价', '涨跌幅', '成交量']], hide_index=True)
        except Exception as e:
            st.error(f"获取A股行情失败: {e}")

    with col2:
        st.subheader("行业板块资金净流入 Top 10")
        try:
            df_fund = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
            top_fund = df_fund.head(10)
            fig = px.bar(top_fund, x='名称', y='今日净额-净额', title="资金净流入排行 (万元)", color='今日净额-净额')
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"获取资金面数据失败: {e}")

# --- Tab 2: 美股盘前/夜盘监控 ---
with tab2:
    st.header("美股核心指数与科技巨头盘前/夜盘跟踪")
    us_tickers = ["^GSPC", "^IXIC", "AAPL", "NVDA", "TSLA", "MSFT"]
    
    try:
        data = yf.download(us_tickers, period="2d", interval="15m", prepost=True)
        st.write("最新美股/夜盘行情点位：")
        latest_prices = data['Close'].iloc[-1]
        st.json(latest_prices.to_dict())
    except Exception as e:
        st.error(f"获取美股夜盘数据失败: {e}")

# --- Tab 3: 信息面（快讯） ---
with tab3:
    st.header("财联社/电报秒级新闻快讯")
    try:
        news_df = ak.stock_telegraph_cls()
        for idx, row in news_df.head(15).iterrows():
            st.markdown(f"**[{row['发布时间']}]** {row['内容']}")
            st.divider()
    except Exception as e:
        st.error(f"获取新闻快讯失败: {e}")
