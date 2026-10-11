# 个人主页（静态站点）

邓善俊（Shanjun Deng）的个人主页，托管在 GitHub Pages。纯静态：一个 Python 脚本从数据
生成 HTML + CSS + 原生 JS，不使用前端框架。

## 我只需要维护 `sources/`（四个部分）

| 要改的东西 | 放在哪 | 怎么改 |
|---|---|---|
| 个人简介 / 信息 | `sources/about/info.yml`（+ 可选 `avatar.jpg`） | 直接编辑 yml |
| 文章 | `sources/papers/*.pdf` | **只放 PDF**，其余由脚本生成 |
| 新闻 | `sources/news/*.docx` | **只放带图片的 Word**，其余由脚本生成 |
| 软件 | `sources/software.txt` | **只维护仓库链接清单**（每行一个） |
| 研究方向卡片（一般不动） | `sources/research/*.yml` | 直接编辑 yml |

## 一键生成

```bash
pip install -r requirements.txt      # pyyaml, markdown
python tool/build.py                 # 转 PDF/Word + 抓软件仓库 + 生成站点
```

`tool/build.py` 会：
1. 把 `sources/papers/` 里还没有 yml 的 PDF 转成 `content/papers/<slug>.yml`；
2. 把 `sources/news/` 里还没有 md 的 Word 转成 `content/news/<日期>.md` + 图片；
3. 按 `sources/software.txt` 抓取仓库信息与 README；
4. 运行 `update.py` 生成站点（并刷新论文引用数）。`--no-net` 可跳过联网步骤。

只生成站点：`python update.py`（`--no-citations` 跳过引用数抓取，`--out DIR` 指定输出目录）。

## 目录结构

```
shadowdeng_homepage/
├── sources/                 # ★ 手动维护区（只有这里需要你改）
│   ├── about/               #   个人简介(info.yml) + 头像(avatar.jpg)
│   ├── papers/              #   文章 PDF
│   ├── news/                #   新闻 Word(.docx，带图片)
│   ├── research/            #   研究方向卡片 yml
│   └── software.txt         #   软件仓库链接清单
├── content/                 # 脚本生成的数据区（勿手改）
│   ├── papers/*.yml         #   pdf2yml.py 生成
│   ├── news/*.md + <日期>/  #   word2news.py 生成（含图片）
│   └── software/*.yml       #   fetch_software.py 生成（+ *.readme.md 参考）
├── templates/               # HTML 模板（源）
├── static/                  # style.css / main.js / logo（源）
├── tool/                    # 转换脚本：build.py、pdf2yml.py、word2news.py、
│                            #   fetch_software.py、fetch_citations.py
├── update.py                # 站点生成脚本
└── AGENTS.md                # 给协作者/AI 的详细约定（双语、主题、新闻检查等）
```

产物 `index.html`、`papers.html`、`news.html`、`news/`、`assets/`、`style.css`、`main.js`、
`logo*.png`、`.nojekyll` 由脚本生成，已在 `.gitignore` 忽略，无需手动编辑或提交。

## 部署

`.github/workflows/deploy.yml`：推送到 `main` 即自动构建并部署 Pages
（构建前会先刷新论文引用数）。仓库 **Settings → Pages → Source** 选 **GitHub Actions**。

> 更多细节（中英文双语要求、亮/暗主题、新闻排版检查、软件卡片等）见 **`AGENTS.md`**。
