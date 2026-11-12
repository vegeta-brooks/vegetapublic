import hmac
import io
import urllib.request
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="全球债市 × 美股风险追踪", layout="wide")


# ---------- 密码门禁 ----------
# 密码保存在 Streamlit Cloud 的 Secrets（Manage app → Settings → Secrets），不进代码仓库：
#   password = "你的密码"
def check_password() -> bool:
    if st.session_state.get("auth_ok"):
        return True
    expected = st.secrets.get("password")
    if not expected:
        st.error("未配置访问密码：请在 Secrets 中设置 password。")
        return False

    def _submit():
        ok = hmac.compare_digest(st.session_state.get("pw_input", ""), str(expected))
        st.session_state["auth_ok"] = ok
        st.session_state["auth_failed"] = not ok
        st.session_state.pop("pw_input", None)  # 不在会话中保留明文

    st.text_input("访问密码", type="password", key="pw_input", on_change=_submit)
    if st.session_state.get("auth_failed"):
        st.error("密码错误")
    return False


if not check_password():
    st.stop()

st.title("全球债市抛售 × 美股风险追踪")
st.caption("数据：FRED / Yahoo Finance，每小时缓存刷新。仅供研究参考，不构成投资建议。")


@st.cache_data(ttl=3600)
def fred(series_id: str) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    raw = urllib.request.urlopen(url, timeout=20).read().decode()
    df = pd.read_csv(io.StringIO(raw), na_values=".")
    # pandas 3.x: 第一列默认是 string dtype，不能原地写入 datetime，改为新建 Series
    s = pd.Series(
        pd.to_numeric(df.iloc[:, 1], errors="coerce").to_numpy(),
        index=pd.to_datetime(df.iloc[:, 0]),
        name=series_id,
    )
    return s.tail(120)


@st.cache_data(ttl=3600)
def yahoo(ticker: str) -> pd.Series:
    s = yf.Ticker(ticker).history(period="6mo")["Close"]
    s.index = s.index.tz_localize(None).normalize()
    s.name = ticker
    return s


# ---------- 数据 ----------
dgs10 = fred("DGS10")
spx = fred("SP500")
tp = fred("THREEFYTP10")
move = yahoo("^MOVE")
vix = yahoo("^VIX")

df = pd.concat([dgs10, spx, move, vix], axis=1).dropna()
df["spx_ret"] = df["SP500"].pct_change()
df["bond_ret"] = -df["DGS10"].diff()  # 收益率上升 ≈ 债券价格下跌
df["corr20"] = df["spx_ret"].rolling(20).corr(df["bond_ret"])
last20 = df.tail(20)
tp20 = tp.dropna().tail(20)

# ---------- 侧边栏手动输入 ----------
st.sidebar.header("手动输入")
fwd_ey = st.sidebar.number_input("标普前瞻盈利收益率 (%)", value=4.5, step=0.1)
tail_bp = st.sidebar.number_input("最近10Y拍卖尾部 (bp，正数=有尾部)", value=1.0, step=0.1)
frde = st.sidebar.number_input("法德10Y利差 (bp)", value=147, step=1)

# ---------- 风险灯号 ----------
erp = fwd_ey - last20["DGS10"].iloc[-1]
signals = {
    "股债相关性为正": last20["corr20"].iloc[-1] > 0,
    "期限溢价20日上升": tp20.iloc[-1] > tp20.iloc[0],
    "MOVE 20日涨幅大于VIX": (last20["^MOVE"].iloc[-1] / last20["^MOVE"].iloc[0])
    > (last20["^VIX"].iloc[-1] / last20["^VIX"].iloc[0]),
    "拍卖出现尾部": tail_bp > 0,
    "法德利差逼近190bp": frde >= 170,
    "股票风险溢价低于0.5%": erp < 0.5,
}
n = sum(signals.values())
light = "🟢 绿灯" if n == 0 else ("🟡 黄灯" if n <= 2 else "🔴 红灯")

c1, c2, c3, c4 = st.columns(4)
c1.metric("风险灯号", light, f"{n} 项触发")
c2.metric(
    "美债10Y",
    f"{last20['DGS10'].iloc[-1]:.2f}%",
    f"{(last20['DGS10'].iloc[-1] - last20['DGS10'].iloc[0]) * 100:+.0f}bp / 20日",
)
c3.metric("MOVE", f"{last20['^MOVE'].iloc[-1]:.1f}")
c4.metric("股票风险溢价", f"{erp:.2f}%")

with st.expander("信号明细"):
    for k, v in signals.items():
        st.write(("⚠️ " if v else "✅ ") + k)

# ---------- 图表 ----------
l, r = st.columns(2)
l.subheader("美债10Y收益率 (%)")
l.line_chart(last20["DGS10"])
r.subheader("10Y期限溢价 (Kim-Wright)")
r.line_chart(tp20)
l.subheader("MOVE vs VIX")
l.line_chart(last20[["^MOVE", "^VIX"]])
r.subheader("20日股债相关性（>0 为利率冲击模式）")
r.line_chart(last20["corr20"])

st.markdown(
    "**欧洲国债实时数据**：[Investing.com 全球国债]"
    "(https://www.investing.com/rates-bonds/world-government-bonds)"
)
