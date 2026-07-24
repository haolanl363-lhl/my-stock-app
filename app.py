import streamlit as st
import pandas as pd
import akshare as ak
import yfinance as yf
import plotly.graph_objects as go

# 页面基本配置
st.set_page_config(
    page_title="股票多维监控看板",
    page_icon="📈",
    layout="wide"
)

st.title("📈 股票多维监控看板")

# -------------------------------------------------------------
# 1. 大盘指数概览（双接口保障）
# -------------------------------------------------------------
st.subheader("📊 大盘指数概览")

@st.cache_data(ttl=300) # 缓存5分钟，避免频繁请求被封
def get_index_data():
    indices = {
        "上证指数": {"ak_code": "sh000001", "yf_code": "000001.SS"},
        "深证成指": {"ak_code": "sz399001", "yf_code": "399001.SZ"},
        "创业板指": {"ak_code": "sz399006", "yf_code": "399006.SZ"},
        "纳斯达克": {"ak_code": "gb_yx_ixic", "yf_code": "^IXIC"},
    }
    
    results = []
    
    # 尝试方案 A: 尝试使用 AkShare 抓取
    try:
        df_ak = ak.stock_zh_a_spot_em()
        for name, codes in indices.items():
            sub_df = df_ak[df_ak['代码'].str.contains(codes['ak_code'][-6:])]
            if not sub_df.empty:
                latest = sub_df.iloc[0]
                results.append({
                    "名称": name,
                    "最新价": latest['最新价'],
                    "涨跌幅": f"{latest['涨跌幅']}%",
                    "涨跌额": latest['涨跌额']
                })
    except Exception:
        pass # 如果 AkShare 被拦截，自动无感切到 Yahoo Finance
        
    # 方案 B: 备用方案 Yahoo Finance (对海外服务器100%友好)
    if len(results) < len(indices):
        results = [] # 重置结果，统一用 yfinance 抓取
        for name, codes in indices.items():
            try:
                ticker = yf.Ticker(codes['yf_code'])
                hist = ticker.history(period="2d")
                if len(hist) >= 2:
                    close_curr = hist['Close'].iloc[-1]
                    close_prev = hist['Close'].iloc[-2]
                    change = close_curr - close_prev
                    pct_change = (change / close_prev) * 100
                    results.append({
                        "名称": name,
                        "最新价": f"{close_curr:.2f}",
                        "涨跌幅": f"{pct_change:+.2f}%",
                        "涨跌额": f"{change:+.2f}"
                    })
            except Exception:
                results.append({"名称": name, "最新价": "暂无数据", "涨跌幅": "-", "涨跌额": "-"})
                
    return pd.DataFrame(results)

# 渲染大盘指数卡片
index_df = get_index_data()
if not index_df.empty:
    cols = st.columns(len(index_df))
    for idx, row in index_df.iterrows():
        with cols[idx]:
            st.metric(
                label=row['名称'],
                value=row['最新价'],
                delta=row['涨跌幅']
            )

st.divider()

# -------------------------------------------------------------
# 2. 板块资金流向 (加容错处理)
# -------------------------------------------------------------
st.subheader("🔥 行业板块资金净流入 Top 10")

@st.cache_data(ttl=600)
def get_sector_fund_flow():
    try:
        # 使用东财板块资金流接口
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业板块")
        df_top10 = df.head(10)[['名称', '今日主力净流入-净额', '今日超大单净流入-净额', '今日涨跌幅']]
        # 单位转换 (元 -> 亿元)
        df_top10['今日主力净流入(亿元)'] = (df_top10['今日主力净流入-净额'] / 1e8).round(2)
        return df_top10[['名称', '今日主力净流入(亿元)', '今日涨跌幅']]
    except Exception as e:
        return None

sector_df = get_sector_fund_flow()

if sector_df is not None and not sector_df.empty:
    fig = go.Figure(go.Bar(
        x=sector_df['今日主力净流入(亿元)'],
        y=sector_df['名称'],
        orientation='h',
        marker=dict(color=sector_df['今日主力净流入(亿元)'], colorscale='Reds')
    ))
    fig.update_layout(
        title="主力资金净流入行业（亿元）",
        yaxis=dict(autorange="reversed"),
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 当前非交易时间或受数据源限制，资金流数据暂停更新。请开盘后刷新查看。")

st.caption("提示：如数据未实时刷新，可点击右上角三点菜单选择 'Clear cache' 强制更新。")
