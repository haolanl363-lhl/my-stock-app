import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# -------------------------------------------------------------
# 1. 页面基础配置 (极简暗黑风)
# -------------------------------------------------------------
st.set_page_config(
    page_title="ALPHA QUANT | 智能量化终端",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 2. 纯黑 UI 样式
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
    .dark-card:hover { border-color: #38bdf8; }
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
# 3. 精准判断 A 股盘中 / 盘后收盘状态（收盘后至次日 9:15 保持收盘值）
# -------------------------------------------------------------
def is_trading_time():
    now = datetime.datetime.now().time()
    # 交易日 9:15 集合竞价开始到 11:30，13:00 到 15:00 收盘
    t1_start, t1_end = datetime.time(9, 15), datetime.time(11, 30)
    t2_start, t2_end = datetime.time(13, 0), datetime.time(15, 0)
    is_weekday = datetime.datetime.now().weekday() < 5
    
    if is_weekday and ((t1_start <= now <= t1_end) or (t2_start <= now <= t2_end)):
        return True
    return False

trading_status = "🟢 盘中实时更新" if is_trading_time() else "🔴 盘后休市 (固定收盘静态数据)"

# -------------------------------------------------------------
# 4. 股票中文名称与代码映射
# -------------------------------------------------------------
COMMON_STOCKS = {
    "贵州茅台": "sh600519", "茅台": "sh600519",
    "宁德时代": "sz300750", "宁德": "sz300750",
    "比亚迪": "sz002594",
    "东方财富": "sz300059", "东财": "sz300059",
    "中国平安": "sh601318", "平安": "sh601318",
    "五粮液": "sz000858",
    "招商银行": "sh600036", "招行": "sh600036",
    "中信证券": "sh600030",
    "隆基绿能": "sh601012", "隆基": "sh601012",
    "立讯精密": "sz002475",
    "科大讯飞": "sz002230",
    "长江电力": "sh600900",
    "格力电器": "sz000651",
    "恒瑞医药": "sh600276",
    "美的集团": "sz000333",
    "同花顺": "sz300033"
}

def resolve_stock_code(query):
    q = query.strip()
    if q in COMMON_STOCKS:
        return COMMON_STOCKS[q], q
    for name, code in COMMON_STOCKS.items():
        if q in name:
            return code, name
    clean_code = ''.join(filter(str.isdigit, q))
    if len(clean_code) == 6:
        if clean_code.startswith("6"):
            return f"sh{clean_code}", clean_code
        else:
            return f"sz{clean_code}", clean_code
    return "sh600519", "贵州茅台"

# -------------------------------------------------------------
# 5. 侧边栏搜索与刷新设置
# -------------------------------------------------------------
st.sidebar.markdown("### 🔍 个股名称/代码检索")
user_input = st.sidebar.text_input("输入股票名字/代码", value="贵州茅台")
target_code, matched_name = resolve_stock_code(user_input)

st.sidebar.markdown("---")
st.sidebar.caption(f"当前状态：{trading_status}")
auto_refresh = st.sidebar.checkbox("开启自动刷新", value=is_trading_time())
refresh_rate = st.sidebar.slider("刷新间隔 (秒)", min_value=1, max_value=10, value=3)

# -------------------------------------------------------------
# 6. 顶部 Header & A 股核心大盘指数
# -------------------------------------------------------------
st.markdown("<div class='terminal-title'>⚡ ALPHA QUANT 极速量化行情终端</div>", unsafe_allow_html=True)

@st.cache_data(ttl=2 if is_trading_time() else 86400)
def get_china_indices():
    indices = {
        "上证指数": "sh000001",
        "深证成指": "sz399001",
        "沪深300": "sh000300",
        "创业板指": "sz399006",
        "科创50": "sh688981"
    }
    codes = ",".join(indices.values())
    url = f"http://qt.gtimg.cn/q={codes}"
    results = []
    try:
        resp = requests.get(url, timeout=3)
        lines = resp.text.split(";")
        for idx_name, code in indices.items():
            for line in lines:
                if code in line and '="' in line:
                    data = line.split('="')[1].replace('";', '').split('~')
                    if len(data) > 32:
                        price = float(data[3])
                        prev_close = float(data[4])
                        pct_change = float(data[32]) if data[32] != '' else ((price - prev_close)/prev_close*100)
                        results.append({
                            "名称": idx_name, 
                            "最新价": f"{price:,.2f}", 
                            "涨跌幅": pct_change
                        })
    except Exception:
        pass
    return pd.DataFrame(results)

idx_df = get_china_indices()

if not idx_df.empty:
    cols = st.columns(len(idx_df))
    for idx, row in idx_df.iterrows():
        with cols[idx]:
            pct = row['涨跌幅']
            css_cls = "card-up" if pct >= 0 else "card-down"
            sym = "+" if pct >= 0 else ""
            st.markdown(f"""
            <div class="dark-card">
                <div class="card-label">{row['名称']}</div>
                <div class="card-val">{row['最新价']}</div>
                <div class="{css_cls}">{sym}{pct:.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 7. 个股行情看板 + 分时/K线图（盘后固定收盘值）
# -------------------------------------------------------------
@st.cache_data(ttl=2 if is_trading_time() else 86400)
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
            "pe": float(data[39]) if data[39] != '' else 0.0
        }
    except Exception:
        return None

stock_info = get_single_stock_realtime(target_code)

if stock_info:
    pct = stock_info['pct_change']
    color = "#ff2a6d" if pct >= 0 else "#05ffa1"
    
    c1, c2, c3, c4, c5 = st.columns(5)
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
        st.metric("市盈率", f"{stock_info['pe']}")

    tab_fenshi, tab_kline = st.tabs(["📈 分时图 (当日全貌)", "📊 日 K 线图"])

    yf_symbol = f"{target_code[2:]}.SS" if "sh" in target_code else f"{target_code[2:]}.SZ"

    # 分时走势
    with tab_fenshi:
        @st.cache_data(ttl=10 if is_trading_time() else 86400)
        def fetch_intraday_data(symbol):
            try:
                df = yf.download(symbol, period="1d", interval="1m", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
            except Exception:
                return pd.DataFrame()

        fdf = fetch_intraday_data(yf_symbol)

        if not fdf.empty:
            fig_fs = go.Figure()
            fig_fs.add_trace(go.Scatter(
                x=fdf.index, y=fdf['Close'],
                mode='lines', name='分时价格',
                line=dict(color='#38bdf8', width=2),
                fill='tozeroy', fillcolor='rgba(56, 189, 248, 0.08)'
            ))
            fig_fs.add_hline(
                y=stock_info['prev_close'], 
                line_dash="dash", line_color="#94a3b8", 
                annotation_text=f"昨收 ￥{stock_info['prev_close']:.2f}", annotation_position="bottom right"
            )
            fig_fs.update_layout(
                paper_bgcolor='#0b0f17', plot_bgcolor='#111827',
                font=dict(color='#94a3b8', family='JetBrains Mono'),
                height=400, margin=dict(l=10, r=10, t=20, b=10),
                xaxis=dict(gridcolor='#1e293b'), yaxis=dict(gridcolor='#1e293b'),
                showlegend=False
            )
            st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("💡 盘后收盘数据已冻结显示")

    # K 线图
    with tab_kline:
        @st.cache_data(ttl=86400)
        def fetch_kline_data(symbol):
            try:
                df = yf.download(symbol, period="6m", interval="1d", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                df['MA5'] = df['Close'].rolling(5).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                return df
            except Exception:
                return pd.DataFrame()

        kdf = fetch_kline_data(yf_symbol)

        if not kdf.empty:
            fig_k = make_subplots(
                rows=2, cols=1, shared_xaxes=True, 
                vertical_spacing=0.03, row_heights=[0.7, 0.3]
            )
            fig_k.add_trace(go.Candlestick(
                x=kdf.index, open=kdf['Open'], high=kdf['High'],
                low=kdf['Low'], close=kdf['Close'], name="K线",
                increasing_line_color='#ff2a6d', decreasing_line_color='#05ffa1'
            ), row=1, col=1)
            fig_k.add_trace(go.Scatter(x=kdf.index, y=kdf['MA5'], line=dict(color='#38bdf8', width=1.5), name="MA5"), row=1, col=1)
            fig_k.add_trace(go.Scatter(x=kdf.index, y=kdf['MA20'], line=dict(color='#f59e0b', width=1.5), name="MA20"), row=1, col=1)
            
            v_colors = ['#ff2a6d' if c >= o else '#05ffa1' for c, o in zip(kdf['Close'], kdf['Open'])]
            fig_k.add_trace(go.Bar(x=kdf.index, y=kdf['Volume'], marker_color=v_colors, name="成交量"), row=2, col=1)

            fig_k.update_layout(
                paper_bgcolor='#0b0f17', plot_bgcolor='#111827',
                font=dict(color='#94a3b8', family='JetBrains Mono'),
                xaxis_rangeslider_visible=False, height=450,
                margin=dict(l=10, r=10, t=20, b=10), showlegend=False
            )
            fig_k.update_xaxes(gridcolor='#1e293b')
            fig_k.update_yaxes(gridcolor='#1e293b')
            st.plotly_chart(fig_k, use_container_width=True, config={'displayModeBar': False})

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 8. 热门观察池排行榜 (盘后固定)
# -------------------------------------------------------------
st.markdown("##### 🔥 热门观察池涨跌排行榜")

WATCH_POOL = [
    "sh600519", "sz300750", "sz002594", "sh601318", "sz000858", 
    "sh600036", "sz002475", "sz300014", "sh600900", "sz000651", 
    "sh600276", "sz000333", "sh601888", "sz300274", "sh601668"
]

@st.cache_data(ttl=2 if is_trading_time() else 86400)
def get_rank_data():
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
                    turnover = float(data[37]) if data[37] != '' else 0.0
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
        return df.sort_values(by='涨跌幅', ascending=False).reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

rk_df = get_rank_data()

if not rk_df.empty:
    fig_bar = go.Figure(go.Bar(
        x=rk_df['名称'],
        y=rk_df['涨跌幅'],
        marker_color=['#ff2a6d' if p >= 0 else '#05ffa1' for p in rk_df['涨跌幅']],
        text=rk_df['涨跌幅'].apply(lambda x: f"{x:+.2f}%"),
        textposition='auto'
    ))
    
    fig_bar.update_layout(
        paper_bgcolor='#0b0f17', plot_bgcolor='#111827',
        font=dict(color='#94a3b8', family='JetBrains Mono'),
        height=280, margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(gridcolor='#1e293b'), yaxis=dict(gridcolor='#1e293b')
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

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
# 9. 盘中自动刷新控制
# -------------------------------------------------------------
if auto_refresh and is_trading_time():
    import time
    time.sleep(refresh_rate)
    st.rerun()

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)
st.caption("<div style='text-align: center; color: #475569; font-size: 11px;'>ALPHA QUANT TERMINAL © 2026 | A-SHARE REALTIME FEED</div>", unsafe_allow_html=True)
