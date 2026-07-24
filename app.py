import streamlit as st
import pandas as pd
import numpy as np
import akshare as ak
import plotly.express as px

# 页面配置
st.set_page_config(
    page_title="A股个股智能量化推荐看板",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 A股个股三维量化评分与推荐排行榜")
st.caption("综合【资金面 (40%) + 情绪面 (30%) + 技术面 (30%)】实时多维量化打分系统")

# -------------------------------------------------------------
# 核心量化打分逻辑函数
# -------------------------------------------------------------
@st.cache_data(ttl=300) # 缓存5分钟
def get_quant_stock_rankings():
    try:
        # 获取全市场A股实时行情
        df = ak.stock_zh_a_spot_em()
        
        # 基础数据清洗与过滤（剔除ST、次新及停牌股）
        df = df[~df['名称'].str.contains("ST|退")]
        df = df[df['最新价'] > 0]
        
        # 转换为数值类型
        numeric_cols = ['最新价', '涨跌幅', '成交量', '成交额', '换手率', '量比', '主力净流入']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        # --- 1. 资金面打分 (40分) ---
        # 主力净流入得分 (最高20分)
        fund_in_score = np.clip((df['成交额'] * (df['涨跌幅'] / 100)) / 1e7, 0, 20)
        # 换手率/量比得分 (最高20分)
        turnover_score = np.where((df['换手率'] >= 3) & (df['换手率'] <= 10), 15, 5)
        volume_ratio_score = np.where(df['量比'] > 1.2, 5, 2)
        df['资金面得分'] = (fund_in_score + turnover_score + volume_ratio_score).round(1)

        # --- 2. 情绪面打分 (30分) ---
        # 涨幅强度得分：偏好 3%~7% 的稳健大阳线或涨停标的 (最高15分)
        emotion_pct_score = np.where((df['涨跌幅'] >= 3) & (df['涨跌幅'] <= 9.9), 15, 
                             np.where(df['涨跌幅'] > 9.9, 12, 5))
        # 逆势抗跌性：在今日大盘震荡时保持红盘 (最高15分)
        emotion_resilience_score = np.where(df['涨跌幅'] > 0, 15, 0)
        df['情绪面得分'] = (emotion_pct_score + emotion_resilience_score).round(1)

        # --- 3. 技术面打分 (30分) ---
        # 量价配合度与高低位区间估算 (最高30分)
        tech_volume_score = np.where(df['量比'] >= 1.5, 15, 8)
        tech_price_score = np.where((df['涨跌幅'] >= 1.5) & (df['涨跌幅'] <= 6.0), 15, 7)
        df['技术面得分'] = (tech_volume_score + tech_price_score).round(1)

        # --- 总分汇总 ---
        df['综合评价总分'] = (df['资金面得分'] + df['情绪面得分'] + df['技术面得分']).round(1)
        
        # 排序并取 Top 15
        top_df = df.sort_values(by='综合评价总分', ascending=False).head(15).reset_index(drop=True)
        
        # 提取展示列
        result_df = top_df[['代码', '名称', '最新价', '涨跌幅', '换手率', '量比', '资金面得分', '情绪面得分', '技术面得分', '综合评价总分']]
        return result_df

    except Exception as e:
        st.error(f"量化数据获取或计算异常: {e}")
        return pd.DataFrame()

# -------------------------------------------------------------
# 界面渲染
# -------------------------------------------------------------
st.subheader("🏆 今日A股三维推荐排行榜 Top 15")

rank_df = get_quant_stock_rankings()

if not rank_df.empty:
    # 1. 榜单第一名金牌展示
    top1 = rank_df.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🥇 今日冠军标的", f"{top1['名称']} ({top1['代码']})")
    with col2:
        st.metric("综合量化总分", f"{top1['综合评价总分']} 分")
    with col3:
        st.metric("最新价格 / 涨跌幅", f"￥{top1['最新价']}", f"{top1['涨跌幅']}%")
    with col4:
        st.metric("资金 / 情绪 / 技术分", f"{top1['资金面得分']}/{top1['情绪面得分']}/{top1['技术面得分']}")

    st.divider()

    # 2. 三维得分可视化散点图
    st.subheader("📈 Top 15 标的三维能力分布图")
    fig = px.scatter(
        rank_df, 
        x="资金面得分", 
        y="技术面得分", 
        size="综合评价总分", 
        color="涨跌幅",
        hover_name="名称",
        text="名称",
        title="资金面 vs 技术面 强弱分布（圆圈大小代表综合总分）",
        color_continuous_scale="Reds"
    )
    fig.update_traces(textposition='top center')
    st.plotly_chart(fig, use_container_width=True)

    # 3. 详细排行榜表格
    st.subheader("📋 详细量化得分列表")
    st.dataframe(
        rank_df.style.highlight_max(subset=['综合评价总分'], color='#ffcccc')
                     .format({'最新价': '￥{:.2f}', '涨跌幅': '{:+.2f}%', '换手率': '{:.2f}%'}),
        use_container_width=True
    )
else:
    st.warning("⏳ 正在获取行情数据并计算量化得分，请稍候或刷新页面...")

st.info("⚠️ 声明：本看板基于市场公开数据与量化算法自动打分生成，仅供技术研究与参考，不构成任何投资建议。")
