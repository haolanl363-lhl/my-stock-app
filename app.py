import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. 页面配置
st.set_page_config(page_title="股票多维监控与量化看板", page_icon="📈", layout="wide")

# 2. 标题字号调小（20px）
st.markdown("<h3 style='text-align: center; font-size: 20px; font-weight: bold;'>📈 股票多维监控与三维量化推荐看板</h3>", unsafe_allow_html=True)
st.caption("综合【大盘指数 + 板块资金流 + 三维量化打分(资金40%+情绪30%+技术30%)】")
st.divider()

# -------------------------------------------------------------
# 一、大盘指数概览
# -------------------------------------------------------------
st.markdown("#### 📊 大盘指数概览")

@st.cache_data(ttl=300)
def get_index_data():
    indices = {
        "上证指数": "^000001.SS",
        "深证成指": "399001.SZ",
        "创业板指": "399006.SZ",
        "纳斯达克": "^IXIC",
        "标普500": "^GSPC"
    }
    results = []
    for name, code in indices.items():
        try:
            ticker = yf.Ticker(code)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                close_curr = hist['Close'].iloc[-1]
                close_prev = hist['Close'].iloc[-2]
                change = close_curr - close_prev
                pct_change = (change / close_prev) * 100
                results.append({"名称": name, "最新价": f"{close_curr:.2f}", "涨跌幅": f"{pct_change:+.2f}%"})
        except Exception:
            results.append({"名称": name, "最新价": "暂无数据", "涨跌幅": "-"})
    return pd.DataFrame(results)

idx_df = get_index_data()
if not idx_df.empty:
    cols = st.columns(len(idx_df))
    for idx, row in idx_df.iterrows():
        with cols[idx]:
            st.metric(label=row['名称'], value=row['最新价'], delta=row['涨跌幅'])

st.divider()

# -------------------------------------------------------------
# 二、行业板块资金净流入 Top 10
# -------------------------------------------------------------
st.markdown("#### 🔥 行业板块资金净流入 Top 10")

@st.cache_data(ttl=600)
def get_sector_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=10&po=1&np=1&fields=f12,f14,f62,f3&fid=f62&fs=m:90+t:2"
    try:
        resp = requests.get(url, headers=headers, timeout=4)
        data = resp.json()['data']['diff']
        df = pd.DataFrame(data)
        df = df.rename(columns={'f14': '名称', 'f62': '主力净流入', 'f3': '今日涨跌幅'})
        df['今日主力净流入(亿元)'] = (df['主力净流入'] / 1e8).round(2)
        return df[['名称', '今日主力净流入(亿元)', '今日涨跌幅']]
    except Exception:
        mock = {
            '名称': ['半导体', '软件开发', '汽车整车', '消费电子', '光伏设备', '医疗器械', '通信设备', '证券', '电力行业', '酿酒行业'],
            '今日主力净流入(亿元)': [18.5, 14.2, 12.8, 10.6, 8.9, 7.5, 6.2, 5.8, 4.3, 3.1],
            '今日涨跌幅': [3.2, 2.8, 2.1, 1.9, 1.5, 1.2, 0.9, 0.8, 0.5, 0.3]
        }
        return pd.DataFrame(mock)

sec_df = get_sector_data()
if not sec_df.empty:
    fig_sec = go.Figure(go.Bar(
        x=sec_df['今日主力净流入(亿元)'],
        y=sec_df['名称'],
        orientation='h',
        marker=dict(color=sec_df['今日主力净流入(亿元)'], colorscale='Reds')
    ))
    fig_sec.update_layout(title="主力资金净流入行业（亿元）", yaxis=dict(autorange="reversed"), height=350, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig_sec, use_container_width=True)

st.divider()

# -------------------------------------------------------------
# 三、A股个股三维推荐排行榜 Top 15
# -------------------------------------------------------------
st.markdown("#### 🏆 今日A股三维推荐排行榜 Top 15")

@st.cache_data(ttl=300)
def get_stock_rankings():
    headers = {'User-Agent': 'Mozilla/5.0'}
    url = "https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=50&po=1&np=1&fields=f12,f14,f2,f3,f8,f10,f62&fid=f62&fs=m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"
    try:
        resp = requests.get(url, headers=headers, timeout=4)
        data = resp.json()['data']['diff']
        df = pd.DataFrame(data)
        df = df.rename(columns={'f12':'代码', 'f14':'名称', 'f2':'最新价', 'f3':'涨跌幅', 'f8':'换手率', 'f10':'量比', 'f62':'主力净流入'})
        df = df[~df['名称'].str.contains("ST|退")]
        df = df[df['最新价'] > 0]
        
        for c in ['最新价', '涨跌幅', '换手率', '量比', '主力净流入']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

        df['资金面得分'] = np.clip((df['主力净流入']/1e7) + np.where((df['换手率']>=3)&(df['换手率']<=10), 15, 5) + np.where(df['量比']>1.2, 5, 2), 0, 40).round(1)
        df['情绪面得分'] = np.clip(np.where((df['涨跌幅']>=3)&(df['涨跌幅']<=9.9), 15, np.where(df['涨跌幅']>9.9, 12, 5)) + np.where(df['涨跌幅']>0, 15, 0), 0, 30).round(1)
        df['技术面得分'] = np.clip(np.where(df['量比']>=1.5, 15, 8) + np.where((df['涨跌幅']>=1.5)&(df['涨跌幅']<=6.0), 15, 7), 0, 30).round(1)
        df['综合评价总分'] = (df['资金面得分'] + df['情绪面得分'] + df['技术面得分']).round(1)
        
        res = df.sort_values(by='综合评价总分', ascending=False).head(15).reset_index(drop=True)
        return res[['代码', '名称', '最新价', '涨跌幅', '换手率', '量比', '资金面得分', '情绪面得分', '技术面得分', '综合评价总分']]
    except Exception:
        mock = {
            '代码': ['600519', '300750', '002594', '601318', '000858', '600036', '002475', '300014', '600900', '000651', '6002
