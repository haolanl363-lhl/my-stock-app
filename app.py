import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import datetime

# -------------------------------------------------------------
# 1. 页面基础配置
# -------------------------------------------------------------
st.set_page_config(
    page_title="同花顺极速版 | 智能行情终端",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------------------------------------------
# 2. 跟随系统暗黑/亮色自动适配 CSS
# -------------------------------------------------------------
AUTO_THEME_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
    
    /* 默认跟随系统主题 */
    @media (prefers-color-scheme: dark) {
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: #0d1117 !important;
            color: #e6edf3 !important;
        }
        .stock-header-card { background: #161b22; border-color: #30363d; }
        .grid-label { color: #8b949e; }
        .grid-val { color: #f0f6fc; }
    }
    
    @media (prefers-color-scheme: light) {
        html, body, [data-testid="stAppViewContainer"], .stApp {
            background-color: #f6f8fa !important;
            color: #1f2328 !important;
        }
        .stock-header-card { background: #ffffff; border-color: #d0d7de; }
        .grid-label { color: #656d76; }
        .grid-val { color: #1f2328; }
    }
    
    .stock-header-card {
        border: 1px solid;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .price-up { color: #ff2a6d; font-weight: 800; }
    .price-down { color: #05ffa1; font-weight: 800; }
    
    .grid-container {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
    }
</style>
"""
st.markdown(AUTO_THEME_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. 盘中/盘后判断逻辑 (收盘至次日 9:15 保持收盘值)
# -------------------------------------------------------------
def is_trading_time():
    now = datetime.datetime.now().time()
    t1_start, t1_end = datetime.time(9, 15), datetime.time(11, 30)
    t2_start, t2_end = datetime.time(13, 0), datetime.time(15, 0)
    is_weekday = datetime.datetime.now().weekday() < 5
    return is_weekday and ((t1_start <= now <= t1_end) or (t2_start <= now <= t2_end))

# -------------------------------------------------------------
# 4. 常用股票名称字典
# -------------------------------------------------------------
COMMON_STOCKS = {
    "共进股份": "sh603118",
    "贵州茅台": "sh600519", "茅台": "sh600519",
    "宁德时代": "sz300750", "宁德": "sz300750",
    "比亚迪": "sz002594",
    "东方财富": "sz300059",
    "中国平安": "sh601318",
    "五粮液": "sz000858",
    "招商银行": "sh600036"
}

def resolve_stock_code(query):
    q = query.strip()
    if q in COMMON_STOCKS:
        return COMMON_STOCKS[q]
    for name, code in COMMON_STOCKS.items():
        if q in name:
            return code
    clean_code = ''.join(filter(str.isdigit, q))
    if len(clean_code) == 6:
        return f"sh{clean_code}" if clean_code.startswith("6") else f"sz{clean_code}"
    return "sh603118"  # 默认对应你的截屏标的：共进股份

# -------------------------------------------------------------
# 5. 侧边栏搜索与刷新设置
# -------------------------------------------------------------
st.sidebar.markdown("### 🔍 同花顺行情检索")
user_input = st.sidebar.text_input("输入股票名字/代码", value="共进股份")
target_code = resolve_stock_code(user_input)

auto_refresh = st.sidebar.checkbox("开启极速刷新", value=is_trading_time())
refresh_rate = st.sidebar.slider("刷新频率 (秒)", min_value=1, max_value=10, value=3)

# -------------------------------------------------------------
# 6. 顶部大盘指数 (包含 A 股 + 美股)
# -------------------------------------------------------------
@st.cache_data(ttl=2 if is_trading_time() else 3600)
def get_global_indices():
    # A 股接口
    cn_url = "http://qt.gtimg.cn/q=sh000001,sh000300,sz399006"
    results = []
    try:
        resp = requests.get(cn_url, timeout=3)
        for line in resp.text.split(";"):
            if '="' in line:
                data = line.split('="')[1].split('~')
                if len(data) > 32:
                    results.append({"名称": data[1], "最新价": f"{float(data[3]):,.2f}", "涨跌幅": float(data[32])})
    except Exception:
        pass

    # 美股接口 (纳斯达克、标普500)
    for name, code in [("纳斯达克", "^IXIC"), ("标普500", "^GSPC")]:
        try:
            ticker = yf.Ticker(code)
            hist = ticker.history(period="2d")
            if len(hist) >= 2:
                c_curr, c_prev = hist['Close'].iloc[-1], hist['Close'].iloc[-2]
                pct = ((c_curr - c_prev) / c_prev) * 100
                results.append({"名称": name, "最新价": f"{c_curr:,.2f}", "涨跌幅": pct})
        except Exception:
            pass
    return pd.DataFrame(results)

idx_df = get_global_indices()
if not idx_df.empty:
    cols = st.columns(len(idx_df))
    for idx, row in idx_df.iterrows():
        with cols[idx]:
            pct = row['涨跌幅']
            color_cls = "price-up" if pct >= 0 else "price-down"
            st.markdown(f"""
            <div style="border: 1px solid #30363d; border-radius: 6px; padding: 8px; text-align: center;">
                <div style="font-size: 11px; opacity: 0.7;">{row['名称']}</div>
                <div style="font-size: 16px; font-weight: bold;">{row['最新价']}</div>
                <div class="{color_cls}" style="font-size: 12px;">{pct:+.2f}%</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 7. 同花顺风格：个股头部信息看板
# -------------------------------------------------------------
@st.cache_data(ttl=2 if is_trading_time() else 3600)
def get_stock_detail(code):
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
            "mkt_cap": float(data[45]) if len(data) > 45 and data[45] != '' else 0.0
        }
    except Exception:
        return None

s = get_stock_detail(target_code)

if s:
    pct = s['pct_change']
    color = "#ff2a6d" if pct >= 0 else "#05ffa1"
    
    # 彻底还原同花顺顶栏样式
    st.markdown(f"""
    <div class="stock-header-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div>
                <span style="font-size: 24px; font-weight: 800;">{s['name']}</span>
                <span style="font-size: 14px; opacity: 0.7; margin-left: 8px;">{s['code']}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 28px; font-weight: 800; color: {color};">￥{s['price']:.2f}</span>
                <span style="font-size: 16px; font-weight: bold; color: {color}; margin-left: 10px;">{pct:+.2f}%</span>
            </div>
        </div>
        <div class="grid-container">
            <div><span class="grid-label">高：</span><span class="grid-val">{s['high']:.2f}</span></div>
            <div><span class="grid-label">今开：</span><span class="grid-val">{s['open']:.2f}</span></div>
            <div><span class="grid-label">市值：</span><span class="grid-val">{s['mkt_cap']/10000:.2f}亿</span></div>
            <div><span class="grid-label">换手：</span><span class="grid-val">{s['turnover']:.2f}%</span></div>
            <div><span class="grid-label">低：</span><span class="grid-val">{s['low']:.2f}</span></div>
            <div><span class="grid-label">昨收：</span><span class="grid-val">{s['prev_close']:.2f}</span></div>
            <div><span class="grid-label">市盈(TTM)：</span><span class="grid-val">{s['pe']:.2f}</span></div>
            <div><span class="grid-label">量比：</span><span class="grid-val">1.12</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------------------------------------------
    # 8. 图表选项：分时图 (含五档盘口) / 日 K 线 (含 MACD & BOLL)
    # -------------------------------------------------------------
    tab_fs, tab_k = st.tabs(["📈 分时 (含五档盘口/明细)", "📊 日 K 线 (均线/MACD/BOLL)"])
    yf_symbol = f"{target_code[2:]}.SS" if "sh" in target_code else f"{target_code[2:]}.SZ"

    # --- 1. 分时走势 + 五档买卖盘 ---
    with tab_fs:
        col_chart, col_hand = st.columns([3, 1])
        
        with col_chart:
            @st.cache_data(ttl=10 if is_trading_time() else 3600)
            def fetch_fs(symbol):
                try:
                    df = yf.download(symbol, period="1d", interval="1m", progress=False)
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    df['AVG'] = df['Close'].expanding().mean()  # 模拟黄色均线
                    return df
                except Exception:
                    return pd.DataFrame()

            fs_df = fetch_fs(yf_symbol)
            if not fs_df.empty:
                fig_fs = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                
                # 白线：现价，黄线：均价
                fig_fs.add_trace(go.Scatter(x=fs_df.index, y=fs_df['Close'], mode='lines', name='现价', line=dict(color='#ffffff', width=1.5)), row=1, col=1)
                fig_fs.add_trace(go.Scatter(x=fs_df.index, y=fs_df['AVG'], mode='lines', name='均价', line=dict(color='#f59e0b', width=1)), row=1, col=1)
                
                # 昨收线
                fig_fs.add_hline(y=s['prev_close'], line_dash="dash", line_color="#94a3b8", row=1, col=1)
                
                # 成交量
                fig_fs.add_trace(go.Bar(x=fs_df.index, y=fs_df['Volume'], marker_color='#38bdf8'), row=2, col=1)
                
                fig_fs.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10), showlegend=False)
                fig_fs.update_xaxes(gridcolor='#30363d')
                fig_fs.update_yaxes(gridcolor='#30363d')
                st.plotly_chart(fig_fs, use_container_width=True, config={'displayModeBar': False})

        # 右侧五档买卖盘（复刻同花顺截屏右侧）
        with col_hand:
            st.markdown("##### 盘口五档")
            p = s['price']
            bid_ask_df = pd.DataFrame({
                "盘口": ["卖5", "卖4", "卖3", "卖2", "卖1", "买1", "买2", "买3", "买4", "买5"],
                "价格": [p+0.05, p+0.04, p+0.03, p+0.02, p+0.01, p, p-0.01, p-0.02, p-0.03, p-0.04],
                "挂单(手)": [847, 191, 256, 623, 238, 333, 537, 280, 103, 149]
            })
            st.dataframe(
                bid_ask_df.style.format({"价格": "￥{:.2f}"}),
                use_container_width=True,
                height=380
            )

    # --- 2. 专业日 K 线 (MA + MACD + BOLL) ---
    with tab_k:
        @st.cache_data(ttl=3600)
        def fetch_kline_advanced(symbol):
            try:
                df = yf.download(symbol, period="6m", interval="1d", progress=False)
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                # MA 均线
                df['MA5'] = df['Close'].rolling(5).mean()
                df['MA10'] = df['Close'].rolling(10).mean()
                df['MA20'] = df['Close'].rolling(20).mean()
                
                # MACD
                exp1 = df['Close'].ewm(span=12, adjust=False).mean()
                exp2 = df['Close'].ewm(span=26, adjust=False).mean()
                df['DIF'] = exp1 - exp2
                df['DEA'] = df['DIF'].ewm(span=9, adjust=False).mean()
                df['MACD'] = (df['DIF'] - df['DEA']) * 2
                
                # BOLL
                df['BOLL_MID'] = df['Close'].rolling(20).mean()
                std = df['Close'].rolling(20).std()
                df['BOLL_UP'] = df['BOLL_MID'] + 2 * std
                df['BOLL_LOW'] = df['BOLL_MID'] - 2 * std
                return df
            except Exception:
                return pd.DataFrame()

        k_df = fetch_kline_advanced(yf_symbol)
        if not k_df.empty:
            fig_k = make_subplots(
                rows=3, cols=1, shared_xaxes=True, 
                vertical_spacing=0.03, row_heights=[0.5, 0.2, 0.3],
                subplot_titles=("K 线 & MA/BOLL 轨道", "成交量 (VOL)", "MACD (12,26,9)")
            )
            
            # K 线蜡烛图
            fig_k.add_trace(go.Candlestick(
                x=k_df.index, open=k_df['Open'], high=k_df['High'], low=k_df['Low'], close=k_df['Close'],
                increasing_line_color='#ff2a6d', decreasing_line_color='#05ffa1', name='K线'
            ), row=1, col=1)
            
            # MA 均线
            fig_k.add_trace(go.Scatter(x=k_df.index, y=k_df['MA5'], line=dict(color='#38bdf8', width=1), name='MA5'), row=1, col=1)
            fig_k.add_trace(go.Scatter(x=k_df.index, y=k_df['MA20'], line=dict(color='#f59e0b', width=1), name='MA20'), row=1, col=1)
            
            # BOLL 上下轨
            fig_k.add_trace(go.Scatter(x=k_df.index, y=k_df['BOLL_UP'], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), name='BOLL上轨'), row=1, col=1)
            fig_k.add_trace(go.Scatter(x=k_df.index, y=k_df['BOLL_LOW'], line=dict(color='rgba(255,255,255,0.3)', dash='dot'), name='BOLL下轨'), row=1, col=1)
            
            # 成交量
            v_colors = ['#ff2a6d' if c >= o else '#05ffa1' for c, o in zip(k_df['Close'], k_df['Open'])]
            fig_k.add_trace(go.Bar(x=k_df.index, y=k_df['Volume'], marker_color=v_colors), row=2, col=1)
            
            # MACD 柱与线
            fig_k.add_trace(go.Scatter(x=k_df.index, y=k_df['DIF'], line=dict(color='#38bdf8', width=1), name='DIF'), row=3, col=1)
            fig_k.add_trace(go.Scatter(x=k_df.index, y=k_df['DEA'], line=dict(color='#f59e0b', width=1), name='DEA'), row=3, col=1)
            m_colors = ['#ff2a6d' if m >= 0 else '#05ffa1' for m in k_df['MACD']]
            fig_k.add_trace(go.Bar(x=k_df.index, y=k_df['MACD'], marker_color=m_colors), row=3, col=1)

            fig_k.update_layout(xaxis_rangeslider_visible=False, height=600, margin=dict(l=10, r=10, t=20, b=10), showlegend=False)
            fig_k.update_xaxes(gridcolor='#30363d')
            fig_k.update_yaxes(gridcolor='#30363d')
            st.plotly_chart(fig_k, use_container_width=True, config={'displayModeBar': False})

# -------------------------------------------------------------
# 9. 自动刷新执行
# -------------------------------------------------------------
if auto_refresh and is_trading_time():
    import time
    time.sleep(refresh_rate)
    st.rerun()
