import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import requests

# 1. 页面设置与小字号标题
st.set_page_config(page_title="A股实时量化看板", page_icon="📈", layout="wide")
st.markdown("<h3 style='text-align: center; font-size: 20px; font-weight: bold;'>📈 股票多维监控与三维量化推荐看板</h3>", unsafe_allow_html=True)
st.caption("实时/盘后自动计算：【资金面(40%) + 情绪面(30%) + 技术面(30%)】")
st.divider()

# 2. 大盘指数
st.markdown("#### 📊 大盘指数概览")

@st.cache_data(ttl=60)
def get_index_data():
    indices = {"上证指数": "^000001.SS", "深证成指": "399001.SZ", "创业板指": "399006.SZ", "纳斯达克": "^IXIC", "标普500": "^GSPC"}
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

# 3. 核心：实时/盘后A股量化打分榜 Top 15
st.markdown("#### 🏆 当日A股三维量化推荐排行榜 Top 15")

WATCH_POOL = ["sh600519", "sz300750", "sz002594", "sh601318", "sz000858", "sh600036", "sz002475", "sz300014", "sh600900", "sz000651", "sh600276", "sz000333", "sh601888", "sz300274", "sh601668", "sh600030", "sz000001", "sh601166", "sz002714", "sh600887"]

@st.cache_data(ttl=60)
def get_realtime_quant():
    codes = ",".join(WATCH_POOL)
    url = f"http://qt.gtimg.cn/q={codes}"
    try:
        resp = requests.get(url, timeout=5)
        lines = resp.text.split(";")
        stock_list = []
        for line in lines:
            if '="' in line:
                data = line.split('="')[1].replace('";', '').split('~')
                if len(data) > 37:
                    name = data[1]
                    code = data[2]
                    price = float(data[3])
                    prev_close = float(data[4])
                    pct_change = float(data[32]) if data[32] != '' else ((price - prev_close)/prev_close*100)
                    volume = float(data[6])
                    turnover = float(data[37]) if data[37] != '' else 1.5
                    amount = price * volume / 100
                    stock_list.append({'代码': code, '名称': name, '最新价': price, '涨跌幅': round(pct_change, 2), '换手率': round(turnover, 2), '成交额': round(amount, 1)})
        
        df = pd.DataFrame(stock_list)
        df = df[df['最新价'] > 0]
        
        # 资金面 (40分)
        df['资金面得分'] = np.clip((df['成交额'] / 50000) * 15 + np.where((df['换手率'] >= 2) & (df['换手率'] <= 8), 15, 8) + np.where(df['涨跌幅'] > 0, 10, 0), 0, 40).round(1)
        # 情绪面 (30分)
        df['情绪面得分'] = np.clip(np.where((df['涨跌幅'] >= 2) & (df['涨跌幅'] <= 8), 15, np.where(df['涨跌幅'] > 8, 12, 5)) + np.where(df['涨跌幅'] > 0, 15, 0), 0, 30).round(1)
        # 技术面 (30分)
        df['技术面得分'] = np.clip(np.where((df['涨跌幅'] >= 1.0) & (df['涨跌幅'] <= 6.0), 15, 8) + np.where(df['成交额'] > df['成交额'].median(), 15, 7), 0, 30).round(1)
        
        df['综合评价总分'] = (df['资金面得分'] + df['情绪面得分'] + df['技術面得分' if '技術面得分' in df else '技术面得分']).round(1)
        res = df.sort_values(by='综合评价总分', ascending=False).head(15).reset_index(drop=True)
        return res[['代码', '名称', '最新价', '涨跌幅', '换手率', '资金面得分', '情绪面得分', '技术面得分', '综合评价总分']]
    except Exception as e:
        return pd.DataFrame()

rk_df = get_realtime_quant()

if not rk_df.empty:
    top1 = rk_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🥇 今日量化冠军", f"{top1['名称']} ({top1['代码']})")
    with c2:
        st.metric("综合得分", f"{top1['综合评价总分']} 分")
    with c3:
        st.metric("最新价 / 涨跌幅", f"￥{top1['最新价']}", f"{top1['涨跌幅']}%")
    with c4:
        st.metric("资金/情绪/技术", f"{top1['资金面得分']}/{top1['情绪面得分']}/{top1['技术面得分']}")

    st.markdown("##### 📈 Top 15 标的“资金 vs 技术”分布图")
    fig_q = px.scatter(rk_df, x="资金面得分", y="技术面得分", size="综合评价总分", color="涨跌幅", hover_name="名称", text="名称", color_continuous_scale="Reds")
    fig_q.update_traces(textposition='top center')
    st.plotly_chart(fig_q, use_container_width=True)

    st.markdown("##### 📋 当日真实行情打分详细列表")
    st.dataframe(rk_df.style.format({'最新价': '￥{:.2f}', '涨跌幅': '{:+.2f}%', '换手率': '{:.2f}%'}), use_container_width=True)

st.caption("提示：开盘时间自动每60秒更新实时打分，收盘后自动锁定当天的最新收盘数据得出评分。")
