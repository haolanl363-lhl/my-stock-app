import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
import requests

# -------------------------------------------------------------
# 1. 页面基础配置
# -------------------------------------------------------------
st.set_page_config(
    page_title="ALPHA QUANT | 智能量化监控终端",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# 2. 自定义高级 UI 样式 (CSS)
# -------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* 引入高端无衬线字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* 页面全局背景渐变 */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%);
        color: #f8fafc;
    }
    
    /* 主标题样式 */
    .main-header {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 22px !important;
        font-weight: 800 !important;
        text-align: center;
        letter-spacing: 1px;
        margin-bottom: 2px;
    }
    
    .sub-title {
        text-align: center;
        color: #94a3b8;
        font-size: 12px;
        margin-bottom: 20px;
    }
    
    /* 高级卡片封装 (Card Container) */
    .glass-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.36);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    
    /* 自定义 Metric 样式 */
    .metric-label {
        font-size: 12px;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .metric-value {
        font-size: 20px;
        font-weight: 700;
        color: #f8fafc;
    }
    .metric-delta-up {
        font-size: 13px;
        color: #f43f5e;
        font-weight: 600;
    }
    .metric-delta-down {
        font-size: 13px;
        color: #10b981;
        font-weight: 600;
    }
    
    /* 分隔线装饰 */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
        margin: 25px 0;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -------------------------------------------------------------
# 3. 顶部 Header
# -------------------------------------------------------------
st.markdown("<div class='main-header'>⚡ ALPHA QUANT 智能多维量化终端</div>", unsafe_allow_html=True)
st.caption("<div class='sub-title'>实时行情引擎驱动 | 资金面 (40%) + 情绪面 (30%) + 技术面 (30%) 三维评分体系</div>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 4. 模块一：全球核心指数
# -------------------------------------------------------------
st.markdown("##### 📊 全球核心指数行情")

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
            pct = row['漲跌幅' if '漲跌幅' in row else '涨跌幅']
            delta_class = "metric-delta-up" if pct >= 0 else "metric-delta-down"
            delta_symbol = "+" if pct >= 0 else ""
            
            card_html = f"""
            <div class="glass-card">
                <div class="metric-label">{row['名称']}</div>
                <div class="metric-value">{row['最新价']}</div>
                <div class="{delta_class}">{delta_symbol}{pct:.2f}%</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# -------------------------------------------------------------
# 5. 模块二：三维量化实时推荐 Top 15
# -------------------------------------------------------------
st.markdown("##### 🏆 今日 A 股量化综合推荐榜 Top 15")

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
    
    # 冠军标的卡片
    hero_card_html = f"""
    <div class="glass-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(168, 85, 247, 0.15) 100%); border: 1px solid rgba(168, 85, 247, 0.3); margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="background: #a855f7; color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: bold; margin-right: 8px;">TOP 1 量化首选</span>
                <span style="font-size: 18px; font-weight: bold; color: white;">{top1['名称']}</span>
                <span style="color: #94a3b8; font-size: 12px; margin-left: 5px;">({top1['代码']})</span>
            </div>
            <div style="display: flex; gap: 20px;">
                <div>
                    <div style="font-size: 10px; color: #94a3b8;">最新价</div>
                    <div style="font-size: 16px; font-weight: bold; color: white;">￥{top1['最新价']:.2f}</div>
                </div>
                <div>
                    <div style="font-size: 10px; color: #94a3b8;">今日涨跌</div>
                    <div style="font-size: 16px; font-weight: bold; color: {'#f43f5e' if top1['涨跌幅']>=0 else '#10b981'};">{top1['涨跌幅']:+.2f}%</div>
                </div>
                <div>
                    <div style="font-size: 10px; color: #a855f7; font-weight: bold;">综合量化得分</div>
                    <div style="font-size: 20px; font-weight: 800; color: #38bdf8;">{top1['综合评价总分']} <span style="font-size: 11px;">分</span></div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(hero_card_html, unsafe_allow_html=True)

    # 散点图可视化 (极客暗黑风)
    fig_q = px.scatter(
        rk_df, 
        x="资金面得分", 
        y="技术面得分", 
        size="综合评价总分", 
        color="涨跌幅", 
        hover_name="名称", 
        text="名称", 
        color_continuous_scale=["#10b981", "#38bdf8", "#f43f5e"],
        title="Top 15 标的“资金 vs 技术”两维度强弱分布图"
    )
    
    fig_q.update_traces(textposition='top center', marker=dict(opacity=0.85, line=dict(width=1, color='white')))
    fig_q.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15, 23, 42, 0.6)',
        font=dict(color='#94a3b8'),
        margin=dict(l=20, r=20, t=40, b=20),
        height=380,
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.1)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.1)')
    )
    st.plotly_chart(fig_q, use_container_width=True)

    # 精美数据表格
    st.markdown("##### 📋 量化评分明细矩阵")
    st.dataframe(
        rk_df.style.format({
            '最新价': '￥{:.2f}', 
            '涨跌幅': '{:+.2f}%', 
            '换手率': '{:.2f}%'
        }).background_gradient(cmap="Blues", subset=['综合评价总分']),
        use_container_width=True
    )

st.markdown("<hr>", unsafe_allow_html=True)
st.caption("<div style='text-align: center; color: #64748b; font-size: 11px;'>ALPHA QUANT © 2026 | 开盘期间每60s自动更新 | 数据源：腾讯财经开放数据接口</div>", unsafe_allow_html=True)
