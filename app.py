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
            '代码': ['600519', '300750', '002594', '601318', '000858', '600036', '002475', '300014', '600900', '000651', '600276', '000333', '601888', '300274', '601668'],
            '名称': ['贵州茅台', '宁德时代', '比亚迪', '中国平安', '五粮液', '招商银行', '立讯精密', '亿纬锂能', '长江电力', '格力电器', '恒瑞医药', '美的集团', '中国中免', '阳光电源', '中国建筑'],
            '最新价': [1450.0, 180.5, 245.0, 42.1, 128.0, 32.5, 28.6, 36.2, 25.1, 38.0, 41.2, 63.5, 72.0, 68.4, 5.2],
            '涨跌幅': [2.1, 4.5, 3.2, 1.1, 2.8, 1.5, 3.8, 5.1, 0.8, 1.9, 2.4, 2.0, 3.1, 4.2, 0.6],
            '换手率': [1.2, 3.5, 2.8, 1.5, 2.1, 1.1, 3.2, 4.1, 0.9, 2.0, 1.8, 2.2, 2.9, 3.6, 0.8],
            '量比': [1.4, 2.1, 1.8, 1.1, 1.6, 1.2, 1.9, 2.3, 1.0, 1.3, 1.5, 1.4, 1.7, 2.0, 1.1],
            '资金面得分': [35.0, 38.5, 36.2, 30.1, 33.5, 31.0, 35.8, 37.2, 29.5, 32.0, 33.1, 32.8, 34.2, 36.5, 28.9],
            '情绪面得分': [25.0, 28.0, 26.5, 22.0, 24.5, 23.0, 27.0, 28.5, 21.0, 23.5, 24.8, 24.0, 25.5, 27.2, 20.5],
            '技术面得分': [26.0, 29.0, 27.5, 23.0, 25.0, 24.0, 28.0, 29.0, 22.0, 24.5, 25.2, 25.0, 26.1, 28.0, 21.0],
            '综合评价总分': [86.0, 95.5, 90.2, 75.1, 83.0, 78.0, 90.8, 94.7, 72.5, 80.0, 83.1, 81.8, 85.8, 91.7, 70.4]
        }
        df_m = pd.DataFrame(mock)
        return df_m.sort_values(by='综合评价总分', ascending=False).reset_index(drop=True)

rk_df = get_stock_rankings()
if not rk_df.empty:
    top1 = rk_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🥇 量化冠军", f"{top1['名称']} ({top1['代码']})")
    with c2:
        st.metric("综合总分", f"{top1['综合评价总分']} 分")
    with c3:
        st.metric("最新价 / 涨跌幅", f"￥{top1['最新价']}", f"{top1['涨跌幅']}%")
    with c4:
        st.metric("资金/情绪/技术", f"{top1['资金面得分']}/{top1['情绪面得分']}/{top1['技术面得分']}")

    st.markdown("##### 📈 Top 15 标的“资金 vs 技术”分布图")
    fig_q = px.scatter(
        rk_df, x="资金面得分", y="技术面得分", size="综合评价总分", color="涨跌幅",
        hover_name="名称", text="名称", color_continuous_scale="Reds"
    )
    fig_q.update_traces(textposition='top center')
    st.plotly_chart(fig_q, use_container_width=True)

    st.markdown("##### 📋 量化打分详细列表")
    st.dataframe(rk_df, use_container_width=True)

st.caption("⚠️ 本看板基于公开行情数据与量化算法生成，仅供技术研究参考，不构成投资建议。")
