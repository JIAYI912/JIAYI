import streamlit as st
import akshare as ak
import pandas as pd
import plotly.express as px

# ================= 页面基础配置 =================
st.set_page_config(page_title="A股全量行业雷达", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; color: #fafafa; }
    h1, h2, h3 { color: #3b82f6; font-family: 'Noto Sans SC', sans-serif; }
    .stMetric { background-color: #1e293b; padding: 15px; border-radius: 10px; border: 1px solid #334155; }
    /* 美化 DataFrame 表格 */
    .stDataFrame { border-radius: 8px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

st.title("📊 A股全量行业与核心标的雷达")
st.markdown("监控全市场资金流向，深度挖掘板块领涨龙头 | *本地高频运行版*")

# ================= 核心数据抓取引擎 =================
@st.cache_data(ttl=300) # 每5分钟更新一次缓存
def get_all_industries():
    """获取大A所有行业板块最新数据"""
    try:
        df = ak.stock_board_industry_name_em()
        df = df[['板块名称', '最新价', '涨跌幅', '总市值', '换手率', '上涨家数', '下跌家数']]
        df = df.sort_values(by='涨跌幅', ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"行业数据抓取失败: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_industry_history(symbol):
    """获取板块近15日K线走势"""
    try:
        df = ak.stock_board_industry_hist_em(symbol=symbol, adjust="qfq")
        return df.tail(15)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_top_5_stocks(symbol):
    """获取板块内涨幅前5的个股"""
    try:
        # 获取该板块下的所有成分股
        df_cons = ak.stock_board_industry_cons_em(symbol=symbol)
        df_cons = df_cons[['代码', '名称', '最新价', '涨跌幅', '换手率', '市盈率-动态']]
        # 按涨跌幅降序排列，取前5名
        df_top5 = df_cons.sort_values(by='涨跌幅', ascending=False).head(5).reset_index(drop=True)
        return df_top5
    except Exception as e:
        return pd.DataFrame()

# ================= UI 布局与渲染 =================
left_col, right_col = st.columns([1, 2])

# 1. 加载全量行业数据
with st.spinner('正在从东方财富同步大A全量行业数据...'):
    df_ranking = get_all_industries()

with left_col:
    st.subheader("🔥 实时板块涨跌幅总榜")
    if not df_ranking.empty:
        # 左侧展示所有行业（去掉行索引，视觉更干净）
        st.dataframe(
            df_ranking[['板块名称', '涨跌幅', '换手率']], 
            use_container_width=True, 
            height=600,
            hide_index=True
        )
        
        industry_list = df_ranking['板块名称'].tolist()
        selected_industry = st.selectbox("👉 选择板块深度挖掘:", industry_list)
    else:
        selected_industry = None

with right_col:
    if selected_industry:
        st.subheader(f"📈 {selected_industry} - 资金趋势与核心标的")
        
        current_data = df_ranking[df_ranking['板块名称'] == selected_industry].iloc[0]
        
        # 顶部指标卡片
        col1, col2, col3 = st.columns(3)
        col1.metric("今日板块涨跌", f"{current_data['涨跌幅']}%", delta="做多资金涌入" if current_data['涨跌幅'] > 0 else "资金净流出")
        col2.metric("板块换手率", f"{current_data['换手率']}%", delta="活跃度" , delta_color="off")
        col3.metric("多空家数比", f"涨 {current_data['上涨家数']} : 跌 {current_data['下跌家数']}")
        
        # 走势图
        df_hist = get_industry_history(selected_industry)
        if not df_hist.empty:
            fig = px.line(df_hist, x='日期', y='收盘', markers=True, template="plotly_dark", height=300)
            fig.update_traces(line_color='#10b981', line_width=3)
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
        # ================= 新增：Top 5 核心标的挖掘模块 =================
        st.markdown("---")
        st.subheader("🏆 板块领涨先锋 (Top 5 核心个股)")
        
        with st.spinner(f'正在分析 {selected_industry} 板块成分股...'):
            df_top_stocks = get_top_5_stocks(selected_industry)
            
        if not df_top_stocks.empty:
            # 格式化数据，让展示更专业
            df_top_stocks['最新价'] = df_top_stocks['最新价'].apply(lambda x: f"¥ {x:.2f}")
            df_top_stocks['涨跌幅'] = df_top_stocks['涨跌幅'].apply(lambda x: f"{x:.2f} %")
            df_top_stocks['换手率'] = df_top_stocks['换手率'].apply(lambda x: f"{x:.2f} %")
            
            st.dataframe(
                df_top_stocks,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("该板块暂无成分股交易数据。")
            
        # AI 逻辑评估
        st.markdown("---")
        st.subheader("🤖 交易逻辑简评")
        if current_data['涨跌幅'] > 2.5:
            st.success("**进攻信号**：板块整体爆发，上方领涨先锋若封死涨停，可关注板块内具有补涨潜力的低位股。")
        elif current_data['涨跌幅'] < -2.5:
            st.warning("**防守信号**：泥沙俱下，即便板块内有抗跌个股也不建议在此刻逆势建仓，谨防补跌风险。")
        else:
            st.info("**震荡信号**：板块分化严重，重点关注上方 Top 5 个股是否具备独立于板块的特殊基本面利好。")
