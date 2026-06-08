import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px

# 1. 页面基础配置：深色专业金融风
st.set_page_config(page_title="A股行业热度雷达", layout="wide", initial_sidebar_state="expanded")

# 强制深色模式的一些自定义视觉样式
st.markdown("""
<style>
    .reportview-container { background: #0e1117; color: #fafafa; }
    h1, h2, h3 { color: #3b82f6; font-family: 'Noto Sans SC', sans-serif; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
</style>
""", unsafe_allow_html=True)

st.title("📊 A股行业热度预警雷达")
st.markdown("监控行业资金流向，捕捉市场情绪拐点 | *数据来源: 东方财富 (基于 Akshare 开源库)*")

# 2. 获取数据的函数 (加入缓存让网页加载变快)
@st.cache_data(ttl=600)
def get_industry_ranking():
    try:
        # 获取东方财富行业板块实时数据
        df = ak.stock_board_industry_name_em()
        df = df[['板块名称', '最新价', '涨跌幅', '总市值', '换手率', '上涨家数', '下跌家数']]
        df = df.sort_values(by='涨跌幅', ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def get_industry_history(symbol):
    try:
        # 获取某个板块的历史数据走势
        df = ak.stock_board_industry_hist_em(symbol=symbol, adjust="qfq")
        return df.tail(15) # 取最近15个交易日
    except:
        return pd.DataFrame()

# 3. 页面布局：左侧排名，右侧详情
left_col, right_col = st.columns([1, 2])

# 获取实时排行榜数据
df_ranking = get_industry_ranking()

with left_col:
    st.subheader("🔥 实时板块涨跌幅榜")
    if not df_ranking.empty:
        # 在左侧显示一个漂亮的交互式表格
        st.dataframe(
            df_ranking[['板块名称', '涨跌幅', '换手率']].head(31), 
            use_container_width=True,
            hide_index=True
        )
        
        # 让用户交互式选择一个行业看详情
        industry_list = df_ranking['板块名称'].tolist()
        selected_industry = st.selectbox("👉 选择一个行业板块查看资金走势:", industry_list)
    else:
        st.error("数据抓取失败，请检查网络或稍后再试。")
        selected_industry = None

with right_col:
    if selected_industry:
        st.subheader(f"📈 {selected_industry} - 资金趋势与 AI 情绪评估")
        
        # 抓取选定行业的历史数据
        df_hist = get_industry_history(selected_industry)
        
        if not df_hist.empty:
            # { "user_intent": "LEARN_CONCEPT" }
            # 提取当天的具体数据
            current_data = df_ranking[df_ranking['板块名称'] == selected_industry].iloc[0]
            
            # 显示顶部核心指标卡片（Metric 组件）
            col1, col2, col3 = st.columns(3)
            col1.metric("今日涨跌幅", f"{current_data['涨跌幅']}%", 
                        delta="强势上攻" if current_data['涨跌幅'] > 0 else "回调走弱")
            col2.metric("行业换手率", f"{current_data['换手率']}%", 
                        delta="交投活跃" if current_data['换手率'] > 3 else "交投平淡", delta_color="off")
            col3.metric("板块红绿家数比", f"涨 {current_data['上涨家数']} : 跌 {current_data['下跌家数']}")
            
            # 用 Plotly 画一张专业的深色折线图
            st.markdown("##### 行业指数收盘价走势趋势线")
            fig = px.line(df_hist, x='日期', y='收盘', markers=True, template="plotly_dark")
            fig.update_traces(line_color='#10b981', line_width=3)
            st.plotly_chart(fig, use_container_width=True)
            
            # AI 情绪解读模块 (完美闭环你的产品设计逻辑)
            st.markdown("---")
            st.subheader("🤖 政策脉搏 & 散户情绪评估")
            
            # 根据真实数据进行条件化 AI 综述模拟
            if current_data['涨跌幅'] > 2.5:
                vibe_status = "🔴 情绪亢奋区（短线主力抢筹，防范冲高回落）"
                policy_vibe = "该板块今日遭遇资金强烈共振，政策预期极强。散户跟风盘活跃，建议关注具备业绩支撑的滞涨龙头，切忌盲目追高。"
            elif current_data['涨跌幅'] < -2.5:
                vibe_status = "🟢 情绪冰点区（恐慌盘杀跌，进入左侧观察期）"
                policy_vibe = "行业遭遇短期获利了结或政策利空压制，资金净流出明显。短线建议规避，但如果核心基本面未变，可留意冰点带来的错杀建仓机会。"
            else:
                vibe_status = "⚪ 情绪收敛区（多空博弈平衡，处于震荡整理）"
                policy_vibe = "今日板块无明显异动，换手率处于正常水位。建议保持观望，等待新一轮政策催化剂或主力资金的放量信号。"
                
            st.info(f"**市场水位监测：** {vibe_status}")
            st.success(f"**AI 投资策略综述：** {policy_vibe}")
            
            # 底部合规红线声明
            st.markdown("""
            <p style='font-size: 12px; color: #64748b; text-align: center; margin-top: 30px;'>
            免责声明：本工具仅供量化逻辑演示与学术交流，不构成任何实质性投资建议。市场有风险，入市需谨慎。
            </p>
            """, unsafe_allow_html=True)
