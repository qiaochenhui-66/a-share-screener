# A 股 14:30 自动选股（尽量免费、可在线访问）

**架构：GitHub Pages 静态网页 + GitHub Actions 定时 Python 抓取 + Git 仓库存储 JSON 历史数据。** 适合个人轻量使用，不需要持续在线的付费服务器。代码公开仓库时，筛选数据也公开。

## 五项筛选条件

1. 当日涨跌幅 **3%～5%**，含 3 和 5。
2. 当日换手率 **5%～10%**，含 5 和 10。
3. 当日量比 **严格大于 1.0**。
4. 不含创业板、科创板：仅考虑沪深 A 股主板代码前缀 `600`、`601`、`603`、`605`、`000`、`001`、`002`、`003`。
5. 排除名称中包含 `ST`（大小写不敏感）的股票，如 `ST`、`*ST`。

**没有**“排除新股、次新股”的条件，也没有按上市天数限制。

## 部署：跟着做一次即可

1. 注册/登录 https://github.com 。点击右上角 **+ → New repository**，仓库名称例如 `a-share-screener`，选择 **Public**，创建空仓库；可不勾选初始化 README。
2. 解压本 ZIP 包。打开仓库网页，点击 **uploading an existing file / Add file → Upload files**，将解压后的 **所有内容**（包括 `.github/workflows/screen-and-deploy.yml`、`docs`、`screener.py`、`requirements.txt` 和 `tests`）上传，并提交到 `main` 分支。
   - **注意：** Windows 资源管理器可能隐藏 `.github` 文件夹。如果网页上传无法完整上传隐藏文件，可通过 GitHub 网页单独创建 `.github/workflows/screen-and-deploy.yml`，或者使用 GitHub Desktop / Git 命令。
3. 打开仓库 **Settings → Pages → Build and deployment**，将 **Source** 改成 **GitHub Actions**。
4. 打开仓库 **Actions** 标签，如果有启用提示请允许工作流。首次推送会尝试部署网页。若未启动，选择左侧 **每日14点30分选股并发布网页 → Run workflow**；可选择“是否现在抓取行情”进行手动运行（非交易日自动跳过）。
5. 等 `Actions` 运行成功，在 **Settings → Pages** 找到你的网址，通常是：`https://你的用户名.github.io/a-share-screener/`。
6. **验证**：访问网站，看看日期、真实抓取时间以及结果。如果显示“尚未运行”，在 A 股交易日从 Actions 手动运行，再查看执行日志。不要把“0 只”与“还没抓到数据”混为一谈。

## 自动执行规则

- 文件 `.github/workflows/screen-and-deploy.yml` 的 `30 6 * * 1-5` 为 **UTC 周一～周五 06:30 = 北京时间 14:30**。
- Python 还使用交易所日历判定是否为交易日。休市不覆盖历史结果。
- GitHub Actions **不提供严格准点保障**：运行可能延迟、排队或偶发不执行，不能用于分秒级/实时交易。
- 数据源：AKShare `stock_zh_a_spot_em`，间接依赖东方财富公开行情。接口可能被限流、封锁或变更；不能保证可用。
- 抓取失败时返回非零状态，但工作流会继续发布 **上次成功的数据**，网页会根据日期突出提示旧数据。可以在 Actions 的“采集与筛选”步骤查看报错。
- 每次成功采集更新 `docs/data/latest.json` 和 `docs/data/history/YYYY-MM-DD.json`，提交到 Git 历史。长期大量快照会使仓库体积增长，适时清理历史数据。
- `workflow_dispatch` 为手动运行入口；网页上的“刷新最新结果”**只重新加载已保存数据，不会触发服务器采集**。
- GitHub Actions 可能对仓库未活动一段时间的定时任务进行自动禁用，需到 Actions 重新启用。

## 本地测试（可选）

需要 Python 3.11+：

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python screener.py
python -m http.server 8000 --directory docs
```

打开 http://localhost:8000/ ，本地运行程序会真正发起行情抓取。**只运行 `python screener.py` 不等于已部署到 GitHub。**

## 免费成本、数据与限制

- GitHub Pages 对符合条件的 **Public 仓库**在 GitHub Free 计划可用；标准 GitHub-hosted Actions runner 的公开仓库用量通常免费，受 GitHub 现行规则和反滥用限制约束。
- 页面网址公开，仓库的数据 JSON 也公开；不要提交私密交易信息。
- 仅对抓到的全市场数据做快照筛选，不是券商 Level-2 终端、专业交易系统，也没有保证及时性。
- 浏览器本地 CSV 导入为兜底办法；仅接受 UTF-8 CSV 表头：`代码,名称,最新价,涨跌幅,换手率,量比`。CSV 导入不会同步到其他设备。
- 部署需要你自己的 GitHub 账号授权；该 ZIP 包**不能仅靠双击自动生成互联网网址**。

参考：[GitHub Pages 文档](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)、[GitHub Actions 定时工作流](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)、[GitHub Actions 使用与计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)、[AKShare 文档](https://akshare.akfamily.xyz/)。
