# dailytracking — 全球债市抛售 × 美股风险追踪

Streamlit 应用，展示最近 20 个交易日的：

| 图表 | 数据源 |
|---|---|
| 美债 10Y 收益率 | FRED `DGS10` |
| 10Y 期限溢价（Kim-Wright） | FRED `THREEFYTP10` |
| MOVE vs VIX | Yahoo Finance `^MOVE` / `^VIX` |
| 20 日股债相关性 | FRED `SP500` + `DGS10` 计算 |

股票风险溢价、拍卖尾部、法德利差在侧边栏手动输入，合计 6 个信号生成风险灯号（0 项绿灯 / 1–2 项黄灯 / ≥3 项红灯）。阈值为经验参考，可自行调整。

## 部署（Streamlit Community Cloud）

1. 打开 https://share.streamlit.io ，用 GitHub 登录
2. Create app → 仓库 `vegeta-brooks/vegetapublic`，分支 `main`
3. Main file path 填 `dailytracking/app.py`
4. Deploy，拿到网址后在手机浏览器“添加到主屏幕”

> 仅供研究参考，不构成投资建议。
