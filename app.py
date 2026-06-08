#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app.py — Streamlit 可视化：A 股均线策略 + 波动率 / VaR 风控

逻辑与 stock_alert.py 完全一致（数据、均线、风控阈值、买卖判断）。
本文件只负责网页展示。

启动方式（Mac 终端）：
  cd /Users/luomashifeixiang/Desktop/python
  streamlit run app.py

浏览器会自动打开；若未打开，访问终端里显示的 Local URL（一般为 http://localhost:8501）。
"""

from __future__ import annotations

import streamlit as st

# 复用 stock_alert.py 中的数据获取、均线、风控与信号判断
from stock_alert import (
    DEFAULT_SYMBOL,
    HISTORY_DAYS,
    MA_LONG,
    MA_SHORT,
    MAX_ANNUAL_VOLATILITY,
    MAX_VAR_95_RATIO,
    RISK_WINDOW,
    compute_moving_averages,
    compute_risk_metrics,
    evaluate_signal,
    fetch_history_closes,
    fetch_stock_name,
    normalize_a_share_code,
)

# ---------------------------------------------------------------------------
# 页面基础配置
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="量化风控大脑",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 少量自定义样式：大标题、决策信号横幅
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #1a237e, #0d47a1, #1565c0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.25rem;
    }
    .sub-title {
        text-align: center;
        color: #546e7a;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .signal-buy {
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #1b5e20, #2e7d32);
        color: #ffffff;
        font-size: 1.35rem;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 4px 14px rgba(46, 125, 50, 0.35);
    }
    .signal-hold {
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #455a64, #607d8b);
        color: #eceff1;
        font-size: 1.35rem;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 4px 14px rgba(69, 90, 100, 0.25);
    }
  </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300, show_spinner=False)
def load_analysis(code: str) -> dict:
    """
    拉取并计算单只股票的全部分析结果（缓存 5 分钟，减轻接口压力）。

    返回字典供页面各模块使用。
    """
    name = fetch_stock_name(code)
    hist = fetch_history_closes(code, HISTORY_DAYS)
    hist_ma = compute_moving_averages(hist)
    risk = compute_risk_metrics(hist_ma, RISK_WINDOW)
    buy, reason, summary = evaluate_signal(hist_ma, risk)
    latest_date = hist_ma["日期"].iloc[-1].strftime("%Y-%m-%d")

    return {
        "code": code,
        "name": name,
        "hist_ma": hist_ma,
        "risk": risk,
        "buy": buy,
        "reason": reason,
        "summary": summary,
        "latest_date": latest_date,
    }


def render_signal_banner(buy: bool, name: str, reason: str) -> None:
    """页面最显眼处：绿色买入 / 灰色观望。"""
    if buy:
        st.markdown(
            f'<div class="signal-buy">✅ 买入信号触发：{name} 符合策略且风险可控！</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"策略说明：{reason}")
    else:
        st.markdown(
            '<div class="signal-hold">⏸ 保持观望</div>',
            unsafe_allow_html=True,
        )
        st.caption(f"未触发原因：{reason}")


def render_chart(hist_ma) -> None:
    """近 60 日收盘价折线图，并叠加 MA5 / MA20。"""
    chart_df = hist_ma.set_index("日期")[["收盘", f"ma{MA_SHORT}", f"ma{MA_LONG}"]].copy()
    chart_df.columns = ["收盘价", f"MA{MA_SHORT}", f"MA{MA_LONG}"]
    st.line_chart(chart_df, height=400)


def main() -> None:
    # ----- 顶部大标题 -----
    st.markdown('<p class="main-title">我的私人量化风控大脑</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-title">均线多头 + 波动率 / 历史 VaR 风控 · 数据来自 AKShare（东财 / 腾讯）</p>',
        unsafe_allow_html=True,
    )

    # ----- 侧边栏：股票代码输入 -----
    with st.sidebar:
        st.header("查询设置")
        raw_code = st.text_input(
            "A 股代码（6 位数字）",
            value=DEFAULT_SYMBOL,
            max_chars=12,
            help="例如 600519（贵州茅台）、600036（招商银行）",
        )
        st.caption("支持 sh600519、600519.SS 等写法，会自动规范化。")
        analyze = st.button("开始分析", type="primary", use_container_width=True)
        st.divider()
        st.markdown("**策略条件**")
        st.markdown(f"- MA{MA_SHORT} > MA{MA_LONG}")
        st.markdown(f"- 年化波动率 ≤ {MAX_ANNUAL_VOLATILITY:.0%}")
        st.markdown(f"- 95% VaR 占比 ≤ {MAX_VAR_95_RATIO:.0%}")
        st.divider()
        st.caption("免责声明：仅供学习，不构成投资建议。")

    # 首次打开自动分析默认股；改代码后需点「开始分析」
    first_visit = "bootstrapped" not in st.session_state
    if not analyze and not first_visit:
        st.info("👈 修改代码后，请点击左侧 **开始分析**。")
        return

    try:
        code = normalize_a_share_code(raw_code)
    except ValueError as exc:
        st.error(str(exc))
        return

    st.session_state["bootstrapped"] = True

    with st.spinner(f"正在获取 {code} 近 {HISTORY_DAYS} 日行情，请稍候…"):
        try:
            result = load_analysis(code)
        except Exception as exc:
            st.error(f"数据获取失败：{exc}")
            st.warning(
                "若频繁断连，可关闭 VPN/代理后重试：\n"
                "`unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy`"
            )
            return

    name = result["name"]
    risk = result["risk"]
    summary = result["summary"]
    buy = result["buy"]
    reason = result["reason"]
    hist_ma = result["hist_ma"]

    # ----- 决策信号（最显眼） -----
    st.subheader("决策信号")
    render_signal_banner(buy, name, reason)

    st.divider()

    # ----- 股票信息与核心指标卡片 -----
    col_title, col_date = st.columns([3, 1])
    with col_title:
        st.markdown(f"### {name}（{code}）")
    with col_date:
        st.metric("最新交易日", result["latest_date"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("最新收盘价", f"{risk['last_price']:.2f} 元")
    m2.metric(
        f"近 {int(risk['window'])} 日年化波动率",
        f"{risk['annual_volatility']:.2%}",
        help=f"阈值 ≤ {MAX_ANNUAL_VOLATILITY:.0%}",
    )
    m3.metric(
        "95% VaR 占比（1 日）",
        f"{risk['var_95_ratio']:.2%}",
        help=f"历史模拟法，阈值 ≤ {MAX_VAR_95_RATIO:.0%}",
    )
    m4.metric(
        "95% VaR 金额",
        f"{risk['var_95_amount']:.2f} 元",
        help="占现价比例见上一列",
    )

    if summary:
        st.caption(
            f"MA{MA_SHORT} = {summary['ma_short']:.2f} 元 · "
            f"MA{MA_LONG} = {summary['ma_long']:.2f} 元 · "
            f"均线多头：{'是' if summary.get('trend_ok') else '否'} · "
            f"波动率达标：{'是' if summary.get('vol_ok') else '否'} · "
            f"VaR 达标：{'是' if summary.get('var_ok') else '否'}"
        )

    st.divider()

    # ----- 价格走势图 -----
    st.subheader(f"近 {HISTORY_DAYS} 日收盘价走势")
    render_chart(hist_ma)

    with st.expander("查看原始数据（最近 10 行）"):
        show_cols = ["日期", "收盘", f"ma{MA_SHORT}", f"ma{MA_LONG}"]
        display = hist_ma[show_cols].tail(10).copy()
        display["日期"] = display["日期"].dt.strftime("%Y-%m-%d")
        st.dataframe(display, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
