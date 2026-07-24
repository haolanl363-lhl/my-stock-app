import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import requests

# -------------------------------------------------------------
# 1. 页面基础配置 (纯黑主题)
# -------------------------------------------------------------
st.set_page_config(
    page_title="ALPHA QUANT | 纯黑极客量化终端",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# 2. 纯黑极客 UI 样式注入 (CSS)
# -------------------------------------------------------------
BLACK_TERMINAL_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600;800&display=swap');
    
    /* 强制全屏纯黑背景 */
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #0b0f17 !important;
        color: #e2e8f0 !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* 隐藏 Streamlit 默认顶部灰条 */
    header[data-testid="stHeader"] {
        background-color: rgba(11, 15, 23, 0.8) !important;
    }
    
    /* 极客终端主标题 */
    .terminal-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 24px;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #00f2fe, #4facfe, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
    }
    
    .terminal-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        text-align: center;
        color: #64748b;
        margin-bottom: 24px;
    }
    
    /* 纯黑发光卡片 */
    .dark-card {
        background: #111827;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        transition: all 0.25s ease-in-out;
    }
    .dark-card:hover {
        border-color: #38bdf8;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.25);
        transform: translateY(-2px);
    }
    
    .card-label {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .card-val {
        font-size: 19px;
        font-weight: 700;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
    }
    .card-up {
        font-size: 12px;
        color: #ff2a6d;
        font-weight: 700;
    }
    .card-down {
        font-size: 12px;
        color: #05ffa1;
        font-weight: 700;
    }
    
    /* 霓虹发光分割线 */
    .neon-hr {
        height: 1px;
        border: none;
        background: linear-gradient(90deg, transparent, #38bdf8, transparent);
        margin: 30px 0;
        opacity: 0.3;
    }
</style>
"""
st.markdown(BLACK_TERMINAL_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. 顶部 Header
# -------------------------------------------------------------
st.markdown("<div class='terminal-title'>⚡ ALPHA QUANT TERMINAL v2.0</div>", unsafe_allow_html=True)
st.markdown("<div class='terminal-sub'>REALTIME DATA ENGINE | 资金面 (40%) + 情绪面 (30%) + 技术面 (30%)</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. 模块一：全球大盘行情 (暗黑卡片)
# -------------------------------------------------------------
st.markdown("##### 🌐 全球核心指数监测")

@st.cache_data(ttl=60)
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
                results.append({"名称": name, "最新价": f"{close_curr:,.2f}", "涨跌幅": pct_change})
        except Exception:
            results.append({"名称": name, "最新价": "N/A", "涨跌幅": 0.0})
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
# 5. 模块二：三维量化实时推荐 Top 15
# -------------------------------------------------------------
st.markdown("##### 🏆 今日 A 股量化综合推荐 Top 15")

WATCH_POOL = [
    "sh600519", "sz300750", "sz002594", "sh601318", "sz000858", 
    "sh600036", "sz002475", "sz300014", "sh600900", "sz000651", 
    "sh600276", "sz000333", "sh601888", "sz300274", "sh601668", 
    "sh600030", "sz000001", "sh601166", "sz002714", "sh600887"
]

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
                    stock_list.append({
                        '代码': code, 
                        '名称': name, 
                        '最新价': price, 
                        '涨跌幅': round(pct_change, 2), 
                        '换手率': round(turnover, 2), 
                        '成交额': round(amount, 1)
                    })
        
        df = pd.DataFrame(stock_list)
        df = df[df['最新价'] > 0]
        
        # 资金面 (40分)
        df['资金面得分'] = np.clip((df['成交额'] / 50000) * 15 + np.where((df['换手率'] >= 2) & (df['换手率'] <= 8), 15, 8) + np.where(df['涨跌幅'] > 0, 10, 0), 0, 40).round(1)
        # 情绪面 (30分)
        df['情绪面得分'] = np.clip(np.where((df['涨跌幅'] >= 2) & (df['涨跌幅'] <= 8), 15, np.where(df['涨跌幅'] > 8, 12, 5)) + np.where(df['涨跌幅'] > 0, 15, 0), 0, 30).round(1)
        # 技术面 (30分)
        df['技术面得分'] = np.clip(np.where((df['涨跌幅'] >= 1.0) & (df['涨跌幅'] <= 6.0), 15, 8) + np.where(df['成交额'] > df['成交额'].median(), 15, 7), 0, 30).round(1)
        # 综合评分
        df['综合评价总分'] = (df['资金面得分'] + df['情绪面得分'] + df['技术面得分']).round(1)
        
        res = df.sort_values(by='综合评价总分', ascending=False).head(15).reset_index(drop=True)
        return res[['代码', '名称', '最新价', '涨跌幅', '换手率', '资金面得分', '情绪面得分', '技术面得分', '综合评价总分']]
    except Exception:
        return pd.DataFrame()

rk_df = get_realtime_quant()

if not rk_df.empty:
    top1 = rk_df.iloc[0]
    
    # 霓虹首选标的 Banner
    hero_card_html = f"""
    <div style="background: #0f172a; border: 1px solid #38bdf8; border-radius: 12px; padding: 18px 22px; margin-bottom: 24px; box-shadow: 0 0 20px rgba(56, 189, 248, 0.15);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <span style="background: #0284c7; color: #ffffff; padding: 3px 8px; border-radius: 4px; font-size: 11px; font-weight: 800; font-family: monospace;">TOP 1 QUANT CHOICE</span>
                <div style="font-size: 22px; font-weight: 800; color: #ffffff; margin-top: 6px;">
                    {top1['名称']} <span style="color: #64748b; font-size: 14px; font-weight: normal;">({top1['代码']})</span>
                </div>
            </div>
            <div style="display: flex; gap: 28px; font-family: 'JetBrains Mono', monospace;">
                <div>
                    <div style="font-size: 11px; color: #64748b;">最新价</div>
                    <div style="font-size: 18px; font-weight: 700; color: #f8fafc;">￥{top1['最新价']:.2f}</div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #64748b;">今日涨跌</div>
                    <div style="font-size: 18px; font-weight: 700; color: {'#ff2a6d' if top1['涨跌幅']>=0 else '#05ffa1'};">{top1['涨跌幅']:+.2f}%</div>
                </div>
                <div>
                    <div style="font-size: 11px; color: #38bdf8;">综合量化总分</div>
                    <div style="font-size: 22px; font-weight: 800; color: #38bdf8;">{top1['综合评价总分']} <span style="font-size: 12px;">PTS</span></div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(hero_card_html, unsafe_allow_html=True)

    # 纯黑极客风散点图
    fig_q = px.scatter(
        rk_df, 
        x="资金面得分", 
        y="技术面得分", 
        size="综合评价总分", 
        color="涨跌幅", 
        hover_name="名称", 
        text="名称", 
        color_continuous_scale=["#05ffa1", "#00f2fe", "#ff2a6d"],
        title="Top 15 标的“资金 vs 技术”两维度分布图"
    )
    
    fig_q.update_traces(textposition='top center', marker=dict(opacity=0.9, line=dict(width=1, color='#38bdf8')))
    fig_q.update_layout(
        paper_bgcolor='#0b0f17',
        plot_bgcolor='#111827',
        font=dict(color='#94a3b8', family='JetBrains Mono'),
        margin=dict(l=20, r=20, t=40, b=20),
        height=380,
        xaxis=dict(gridcolor='#1e293b', zerolinecolor='#334155'),
        yaxis=dict(gridcolor='#1e293b', zerolinecolor='#334155')
    )
    st.plotly_chart(fig_q, use_container_width=True)

    # 量化明细数据表
    st.markdown("##### 📋 量化评分明细矩阵")
    st.dataframe(
        rk_df.style.format({
            '最新价': '￥{:.2f}', 
            '涨跌幅': '{:+.2f}%', 
            '换手率': '{:.2f}%'
        }),
        use_container_width=True
    )

st.markdown("<div class='neon-hr'></div>", unsafe_allow_html=True)
st.caption("<div style='text-align: center; color: #475569; font-size: 11px; font-family: monospace;'>ALPHA QUANT TERMINAL © 2026 | DARK MODE V2.0 | REALTIME DATA FEED</div>", unsafe_allow_html=True)
