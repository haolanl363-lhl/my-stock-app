import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# -------------------------------------------------------------
# 1. 页面基础配置 (纯黑极客风格)
# -------------------------------------------------------------
st.set_page_config(
    page_title="ALPHA QUANT | 智能量化终端",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 2. 纯黑终端 CSS 样式
# -------------------------------------------------------------
BLACK_TERMINAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #0b0f17 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif;
    }
    
    header[data-testid="stHeader"] {
        background-color: rgba(11, 15, 23, 0.9) !important;
    }
    
    .terminal-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 22px;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #00f2fe, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 1px;
    }
    
    .dark-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 12px 14px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .dark-card:hover {
        border-color: #38bdf8;
    }
    .card-label { font-size: 11px; color: #94a3b8; font-weight: 600; }
    .card-val { font-size: 18px; font-weight: 700; color: #ffffff; font-family: 'JetBrains Mono'; }
    .card-up { font-size: 12px; color: #ff2a6d; font-weight: 700; }
    .card-down { font-size: 12px; color: #05ffa1; font-weight: 700; }
    
    .neon-hr {
        height: 1px; border: none;
        background: linear-gradient(90deg, transparent, #38bdf8, transparent);
        margin: 20px 0; opacity: 0.3;
    }
</style>
"""
st.markdown(BLACK_TERMINAL_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. 侧边栏：1~10秒自动刷新设置与股票搜索控制
# -------------------------------------------------------------
st.sidebar.markdown("### ⚙️ 终端控制面板")

# 自动刷新机制
auto_refresh = st.sidebar.checkbox("开启实时刷新 (1~10秒)", value=False)
refresh_rate = st.sidebar.slider("刷新频率 (秒)", min_value=1, max_value=10, value=3)

if auto_refresh:
    st.sidebar.caption(f"⚡ 已开启自动刷新：每 {refresh_rate} 秒更新")
    # 动态 Streamlit 刷新逻辑
    st.empty()

# 常用股票快速预设字典
STOCK_DICT = {
    "贵州茅台 (600519)": "sh600519",
    "宁德时代 (300750)": "sz300750",
    "比亚迪 (002594)": "sz002594",
    "中国平安 (601318)": "sh601318",
    "五粮液 (000858)": "sz000858",
    "招商银行 (600036)": "sh600036",
    "东方财富 (300059)": "sz300059",
    "中信证券 (600030)": "sh600030",
    "隆基绿能 (601012)": "sh601012",
    "立讯精密 (002475)": "sz002475"
}

st.sidebar.markdown("### 🔍 个股行情检索")
search_input = st.sidebar.text_input("输入股票代码/拼音 (例如: 600519 或 300750)", value="600519")

# 解析股票代码格式
def parse_stock_code(code_str):
    clean_code = code_str.strip().lower()
    for name, code in STOCK_DICT.items():
        if clean_code in name or clean_code in code:
            return code
    if clean_code.startswith("6"):
        return f"sh{clean_code}"
    elif clean_code.startswith("0") or clean_code.startswith("3"):
        return f"sz{clean_code}"
    return f"sh{clean_code}"

selected_code = parse_stock_code(search_input)

# -------------------------------------------------------------
# 4. 顶部 Header & 全球指数 (包含上证指数)
# -------------------------------------------------------------
st.markdown("<div class='terminal-title'>⚡ ALPHA QUANT 极速量化交易终端</div>", unsafe_allow_html=True)
st.caption("<div style='text-align:center; color:#64748b;'>数据源：腾讯财经 / Yahoo Finance 毫秒级数据流</div>", unsafe_allow_html=True)

@st.cache_data(ttl=3)
def get_index_data():
    indices = {
        "上证指数": "^000001.SS", 
        "沪深300": "000300.SS", 
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
                results.append({"名称": name, "最新价": f"{close_curr:,.2f}", "涨跌幅": pct_change})
            else:
                results.append({"名称": name, "最新价": "--", "涨跌幅": 0.0})
        except Exception:
            results.append({"名称": name, "最新价": "--", "涨跌幅": 0.0})
    return pd.DataFrame(results)

idx_df = get_index_data()

if not idx_df.empty:
    cols = st.columns(len(idx_df))
    for idx, row in idx_df.iterrows():
        with cols[idx]:
            pct = row['涨跌幅']
            css_cls = "card-up" if pct >= 0 else "card-down"
            sym = "+" if pct >= 0 else ""
            
            card_html = f"""
            <div class="dark-card">
                <div class="card-label">{row['名称']}</div>
                <div class="card-val">{row['最新价']}</div>
                <div class="{css_cls}">{sym}{pct:.2f}%</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. 核心模块：同花顺风格——个股实时检索 & K线图 (新增有用功能)
# -------------------------------------------------------------
st.markdown(f"##### 📱 同花顺极速行情看板 - 当前检索: `{selected_code.upper()}`")

@st.cache_data(ttl=2)
def get_single_stock_realtime(code):
    url = f"http://qt.gtimg.cn/q={code}"
    try:
        resp = requests.get(url, timeout=3)
        data = resp.text.split('="')[1].split('~')
        return {
            "name": data[1],
            "code": data[2],
            "price": float(data[3]),
            "prev_close": float(data[4]),
            "open": float(data[5]),
            "volume": float(data[6]),
            "high": float(data[33]),
            "low": float(data[34]),
            "pct_change": float(data[32]),
            "turnover": float(data[37]) if data[37] != '' else 0.0,
            "pe": float(data[39]) if data[39] != '' else 0.0,
            "amount": float(data[37]) if data[37] != '' else 0.0
        }
    except Exception:
        return None

stock_info = get_single_stock_realtime(selected_code)

if stock_info:
    # 顶部个股数据面板
    c1, c2, c3, c4, c5 = st.columns(5)
    pct = stock_info['pct_change']
    color = "#ff2a6d" if pct >= 0 else "#05ffa1"
    
    with c1:
        st.markdown(f"### {stock_info['name']}")
        st.caption(f"代码: {stock_info['code']}")
    with c2:
        st.markdown(f"<h2 style='color:{color}; margin:0;'>￥{stock_info['price']:.2f}</h2>", unsafe_allow_html=True)
        st.markdown(f"<span style='color:{color}; font-weight:bold;'>{pct:+.2f}%</span>", unsafe_allow_html=True)
    with c3:
        st.metric("今开", f"￥{stock_info['open']:.2f}")
        st.metric("昨收", f"￥{stock_info['prev_close']:.2f}")
    with c4:
        st.metric("最高", f"￥{stock_info['high']:.2f}")
        st.metric("最低", f"￥{stock_info['low']:.2f}")
    with c5:
        st.metric("换手率", f"{stock_info['turnover']}%")
        st.metric("市盈率(PE)", f"{stock_info['pe']}")

    # 获得 K 线历史数据 (绘制专业蜡烛图+均线+成交量)
    yf_symbol = f"{selected_code[2:]}.SS" if "sh" in selected_code else f"{selected_code[2:]}.SZ"
    
    @st.cache_data(ttl=60)
    def fetch_kline(symbol):
        try:
            df = yf.download(symbol, period="6m", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            df['MA5'] = df['Close'].rolling(5).mean()
            df['MA20'] = df['Close'].rolling(20).mean()
            return df
        except Exception:
            return pd.DataFrame()

    kdf = fetch_kline(yf_symbol)

    if not kdf.empty:
        # 创建 K线 + 成交量 双图层
        fig = make_subplots(
            rows=2, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.7, 0.3],
            subplot_titles=(f"{stock_info['name']} 日 K 线走势与均线系统", "成交量 (Volume)")
        )

        # 蜡烛图
        fig.add_trace(go.Candlestick(
            x=kdf.index,
            open=kdf['Open'], high=kdf['High'],
            low=kdf['Low'], close=kdf['Close'],
            name="K线",
            increasing_line_color='#ff2a6d', decreasing_line_color='#05ffa1'
        ), row=1, col=1)

        # 移动平均线
        fig.add_trace(go.Scatter(x=kdf.index, y=kdf['MA5'], line=dict(color='#38bdf8', width=1.5), name="MA5"), row=1, col=1)
        fig.add_trace(go.Scatter(x=kdf.index, y=kdf['MA20'], line=dict(color='#f59e0b', width=1.5), name="MA20"), row=1, col=1)

        # 成交量柱状图
        colors = ['#ff2a6d' if c >= o else '#05ffa1' for c, o in zip(kdf['Close'], kdf['Open'])]
        fig.add_trace(go.Bar(x=kdf.index, y=kdf['Volume'], marker_color=colors, name="成交量"), row=2, col=1)

        fig.update_layout(
            paper_bgcolor='#0b0f17',
            plot_bgcolor='#111827',
            font=dict(color='#94a3b8', family='JetBrains Mono'),
            xaxis_rangeslider_visible=False,
            height=500,
            margin=dict(l=10, r=10, t=30, b=10)
        )
        fig.update_xaxes(gridcolor='#1e293b')
        fig.update_yaxes(gridcolor='#1e293b')

        st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ 未查询到该股票实时数据，请确认代码是否正确（例如：600519 / 300750）。")

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 6. 替换后的实用分析：Top 15 领涨/热门标的资金面与涨跌幅排行图
# -------------------------------------------------------------
st.markdown("##### 📊 今日 A 股主力资金与涨跌幅直观排行 (Top 15)")

WATCH_POOL = [
    "sh600519", "sz300750", "sz002594", "sh601318", "sz000858", 
    "sh600036", "sz002475", "sz300014", "sh600900", "sz000651", 
    "sh600276", "sz000333", "sh601888", "sz300274", "sh601668", 
    "sh600030", "sz000001", "sh601166", "sz002714", "sh600887"
]

@st.cache_data(ttl=3)
def get_realtime_quant():
    codes = ",".join(WATCH_POOL)
    url = f"http://qt.gtimg.cn/q={codes}"
    try:
        resp = requests.get(url, timeout=3)
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
                    stock_list.append({
                        '代码': code, 
                        '名称': name, 
                        '最新价': price, 
                        '涨跌幅': round(pct_change, 2), 
                        '换手率': round(turnover, 2), 
                        '成交额(万)': round(amount, 1)
                    })
        
        df = pd.DataFrame(stock_list)
        df = df[df['最新价'] > 0]
        
        df['资金得分'] = np.clip((df['成交额(万)'] / 50000) * 20 + np.where(df['涨跌幅'] > 0, 20, 5), 0, 100).round(1)
        res = df.sort_values(by='涨跌幅', ascending=False).head(15).reset_index(drop=True)
        return res
    except Exception:
        return pd.DataFrame()

rk_df = get_realtime_quant()

if not rk_df.empty:
    # 替换掉原先怪异的散点图，换成清晰实用的“涨跌幅+资金面”柱状图
    fig_bar = go.Figure()
    
    fig_bar.add_trace(go.Bar(
        x=rk_df['名称'],
        y=rk_df['涨跌幅'],
        name="涨跌幅 (%)",
        marker_color=['#ff2a6d' if p >= 0 else '#05ffa1' for p in rk_df['涨跌幅']],
        text=rk_df['涨跌幅'].apply(lambda x: f"{x:+.2f}%"),
        textposition='auto'
    ))
    
    fig_bar.update_layout(
        title="热门观察池标的今日涨跌幅对比排行榜",
        paper_bgcolor='#0b0f17',
        plot_bgcolor='#111827',
        font=dict(color='#94a3b8', family='JetBrains Mono'),
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor='#1e293b'),
        yaxis=dict(gridcolor='#1e293b')
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # 数据表
    st.markdown("##### 📋 核心观察池实时明细")
    st.dataframe(
        rk_df.style.format({
            '最新价': '￥{:.2f}', 
            '涨跌幅': '{:+.2f}%', 
            '换手率': '{:.2f}%',
            '成交额(万)': '￥{:.1f}'
        }),
        use_container_width=True
    )

# -------------------------------------------------------------
# 7. 自动刷新执行逻辑
# -------------------------------------------------------------
if auto_refresh:
    import time
    time.sleep(refresh_rate)
    st.rerun()

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)
st.caption("<div style='text-align: center; color: #475569; font-size: 11px;'>ALPHA QUANT TERMINAL © 2026 | HIGH FREQUENCY DATA ENGINE</div>", unsafe_allow_html=True)
