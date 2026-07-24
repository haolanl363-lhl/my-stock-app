import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests

# 1. 页面配置
st.set_page_config(page_title="A股实时量化与监控看板", page_icon="📈", layout="wide")

# 2. 标题字号调小（20px）
st.markdown("<h3 style='text-align: center; font-size: 20px; font-weight: bold;'>📈 股票多维监控与三维量化推荐看板</h3>", unsafe_allow_html=True)
st.caption("数据来源：实时/盘后行情接口 | 维度：【资金面(40%) + 情绪面(30%) + 技术面(30%)】")
st.divider()

# -------------------------------------------------------------
# 一、大盘指数概览
# -------------------------------------------------------------
st.markdown("#### 📊 大盘指数概览")

@st.cache_data(ttl=60) # 每60秒更新一次
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
# 二、核心：当日实时/盘后 A股个股三维量化打分榜 Top 15
# -------------------------------------------------------------
st.markdown("#### 🏆 当日A股三维量化推荐排行榜 Top 15")

# 选取覆盖沪深两市代表性龙头标的池进行实时计算打分
WATCH_POOL = [
    "sh600519", "sz300750", "sz002594", "sh601318", "sz000858", 
    "sh600036", "sz002475", "sz300014", "sh600900", "sz000651", 
    "sh600276", "sz000333", "sh601888", "sz300274", "sh601668",
    "sh600030", "sz000001", "sh601166", "sz002714", "sh600887",
    "sz300059", "sh600011", "sh601899", "sz002415", "sh600309"
]

@st.cache_data(ttl=60) # 盘中60秒自动刷新最新盘面
def get_realtime_quant_rankings():
    # 使用新浪/腾讯开放行情接口（海外服务器100%连通）
    codes = ",".join(WATCH_POOL)
    url = f"http://qt.gtimg.cn/q={codes}"
    
    try:
        resp = requests.get(url, timeout=5)
        lines = resp.text.split(";")
        stock_list = []
        
        for line in lines:
            if '="' in line:
                code_raw = line.split('=')[0].split('q_')[-1]
                data = line.split('="')[1].replace('";', '').split('~')
                if len(data) > 30:
                    name = data[1]
                    code = data[2]
                    price = float(data[3])
                    prev_close = float(data[4])
                    pct_change = float(data[32]) if len(data) > 32 and data[32] != '' else ((price - prev_close)/prev_close*100)
                    volume = float(data[6]) # 成交量(手)
                    turnover = float(data[37]) if len(data) > 37 and data[37] != '' else 1.5 # 换手率
                    
                    # 估算成交额 (万元)
                    amount = float(data[37]) if len(data) > 37 and data[37] != '' else (price * volume / 100)
                    
                    stock_list.append({
                        '代码': code,
                        '名称': name,
                        '最新价': price,
                        '涨跌幅': round(pct_change, 2),
                        '换手率': round(turnover, 2),
                        '成交额(万)': round(amount, 1),
                        'prev_close': prev_close
                    })
        
        df = pd.DataFrame(stock_list)
        df = df[df['最新价'] > 0]
        
        # --- 量化算法逻辑 (根据当天实时/收盘数据计算) ---
        
        # 1. 资金面得分 (40分)：结合成交额大小与涨跌幅方向
        df['资金面得分'] = np.clip(
            (df['成交额(万)'] / 50000) * 15 + 
            np.where((df['换手率'] >= 2) & (df['换手率'] <= 8), 15, 8) + 
            np.where(df['涨跌幅'] > 0, 10, 0), 0, 40
        ).round(1)

        # 2. 情绪面得分 (30分)：偏好强阳线/防守反弹标的
        df['情绪面得分'] = np.clip(
            np.where((df['涨跌幅'] >= 2) & (df['涨跌幅'] <= 8), 15, np.where(df['涨跌幅'] > 8, 12, 5)) + 
            np.where(df['涨跌幅'] > 0, 15, 0), 0, 30
        ).round(1)

        # 3. 技术面得分 (30分)：量价配合度
        df['技术面得分'] = np.clip(
            np.where((df['涨跌幅'] >= 1.0) & (df['涨跌幅'] <= 6.0), 15, 8) + 
            np.where(df['成交额(万)'] > df['成交额(万)'].median(), 15, 7), 0, 30
        ).round(1)

        # 综合总分
        df['综合评价总分'] = (df['资金面得分'] + df['情绪面得分'] + df['技术面得分']).round(1)
        
        # 按总分降序排列，取 Top 15
        res = df.sort_values(by='综合评价总分', ascending=False).head(15).reset_index(drop=True)
        return res[['代码', '名称', '最新价', '涨跌幅', '换手率', '资金面得分', '情绪面得分', '技术面得分', '综合评价总分']]
   except Exception as e:
        st.error(f"行情接口连接异常，请刷新重试: {e}")
        return pd.DataFrame()

rk_df = get_realtime_quant_rankings()

if not rk_df.empty:
    # 冠军卡片
    top1 = rk_df.iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("🥇 今日量化冠军标的", f"{top1['名称']} ({top1['代码']})")
    with c2:
        st.metric("综合得分", f"{top1['综合评价总分']} 分")
    with c3:
        st.metric("最新价 / 涨跌幅", f"￥{top1['最新价']}", f"{top1['涨跌幅']}%")
    with c4:
        st.metric("资金/情绪/技术", f"{top1['资金面得分']}/{top1['情绪面得分']}/{top1['技术面得分']}")

    st.markdown("##### 📈 Top 15 标的“资金 vs 技术”三维强弱分布")
    fig_q = px.scatter(
        rk_df, x="资金面得分", y="技术面得分", size="综合评价总分", color="涨跌幅",
        hover_name="名称", text="名称", color_continuous_scale="Reds"
    )
    fig_q.update_traces(textposition='top center')
    st.plotly_chart(fig_q, use_container_width=True)

    st.markdown("##### 📋 当日真实数据量化打分表")
    st.dataframe(
        rk_df.style.format({'最新价': '￥{:.2f}', '涨跌幅': '{:+.2f}%', '换手率': '{:.2f}%'}),
        use_container_width=True
    )

st.caption("提示：开盘时间（09:30-15:00）网页每 60 秒自动更新实时打分；收盘后自动锁定今日最终收盘数据得出评分。")
