# AGENTS.md — shadowdeng_homepage

邓善俊（Shanjun Deng）的个人主页生成器。**源文件在 `sources/` 与 `templates/`、`static/`；
根目录的 `index.html`、`papers.html`、`news.html`、`news/`、`assets/`、`style.css`、`main.js`、
`celltree.js`、`logo*.png`、`.nojekyll` 都是生成的产物，不要手改、不要提交。**

## 目录结构（手动区 vs 生成区）

**`sources/` —— 只有这里需要你手动维护：**
- `sources/about/info.yml`（+ 可选 `avatar.jpg`）：个人简介/信息。
- `sources/papers/*.pdf`：**文章只放 PDF**，其余由脚本生成。
- `sources/news/*.docx`：**新闻只放 Word**，其余由脚本生成。
- `sources/software.txt`：**软件只需维护这个清单**（每行一个 GitHub 仓库链接）。
- `sources/research/*.yml`：研究方向卡片（通常不动）。

**`content/` —— 全部由 `tool/` 脚本生成，勿手改：**
- `content/papers/<slug>.yml`（由 `tool/pdf2yml.py` 生成；含引用数等）。
- `content/news/<YYYY-MM-DD>.md` 与 `content/news/<日期>/`（图片，由 `tool/word2news.py` 生成）。
- `content/software/<slug>.yml` 与 `<slug>.readme.md`（由 `tool/fetch_software.py` 生成）。

`templates/`、`static/`、`tool/`、`update.py` 属于代码/模板。

## 常用命令

- **一键更新站点（推荐）**：`python tool/build.py`
  依次：把新 PDF 转 yml、把新 Word 转 md、抓取软件仓库、再生成站点（含刷新引用数）。
  `--no-net` 可跳过联网步骤。
- 只生成站点：`python update.py`（默认会先刷新论文引用数，`--no-citations` 跳过；`--out DIR` 指定输出）。
- 依赖：`pip install -r requirements.txt`（pyyaml、markdown）。Python ≥3.8，无需前端框架/构建工具。
- **生成产物会带上内容哈希**（`?v={{ASSET_V}}`）：`style.css`、`main.js`、`celltree.js`、logo 任一变化都会自动破缓存。

## 欢迎页（帷幕）

- 首页第一屏是 `.curtain`（帷幕）；背景是 `static/celltree.js` 里的「细胞谱系树」动画，画在
  `<canvas id="celltree" class="curtain-canvas">` 上（自相似分裂 + 镜头推进 + DNA 条形码）。
  该脚本会自动适配窗口、不可见时暂停省电；**离开视口/切后台不耗性能**。
- 打字欢迎语：`.curtain-content > .curtain-name`，词表见 `static/main.js` 的 `phrasesByLang`（见「中英文双语」）。
  桌面端位置由 `.curtain-content { margin-top }` 控制，移动端在 `@media (max-width:640px)` 单独覆盖。
- 帷幕内还有：左上角品牌 `.curtain-brand`（`{{LOGO_DARK}}` + `HeLab`，深色背景适用）、右上角语言开关 `.curtain-lang`。
- 想调动画（尺寸/位置/速度/配色/条形码）改 **`static/celltree.js`**；改完须重新构建才会生效。

## 中英文双语（重要）

站点支持 **中/英** 切换，**默认英文**，由 `<html>` 上的 `class="lang-en"`/`lang-zh`
配合 `static/main.js`、`static/style.css` 控制。**任何新增/修改的文字都要同时提供中英文。**

- 界面文案（`templates/*.html`）用成对 span：`<span class="lang-en">En</span><span class="lang-zh">中</span>`。
- 生成 HTML 时用 `update.py` 的 `lang_block(en_html, zh_html, tag, cls)` 包裹两版。
- 数据字段约定：about 用 `x`/`x_en`；research 用 `title/title_en`、`description/description_en`、`tags/tags_en`；
  papers 用 `abstract`(中) + `abstract_en`；news 用 `title_en` + `body_en`；software 用 `description_en`、`tags_en`。
- 欢迎页打字词表在 `static/main.js` 的 `phrasesByLang`，两种语言都要维护。英文名统一 **Shanjun Deng**。

## 主题（亮色 / 暗夜，默认亮色）

- `<html>` 上 `class="theme-light"`/`theme-dark`；切换按钮为导航的 `.theme-switch`（与语言开关 `.lang-switch` 共用样式）。
- 暗色样式集中在 `static/style.css` 末尾的「暗夜主题」段（`html.theme-dark ...`）。
  **新增任何区块/组件时，都要在该段补一条对应的暗色规则。**

## Logo

- `static/logo_bright.png`（亮色）、`static/logo_dark.png`（暗夜）；`update.py` 的 `logo_files()` 自动选用并注入
  `{{LOGO_LIGHT}}`/`{{LOGO_DARK}}`；模板里用 `.logo-light`/`.logo-dark` 配合主题显隐。favicon 用亮色版。
- 原始图片请先压缩（建议 ≤256×256 PNG）。

## 文章（Papers）

- 只把 PDF 放到 `sources/papers/`；`tool/pdf2yml.py`（`tool/build.py` 会调用）生成 `content/papers/<slug>.yml` 草稿。
- yml 字段：`title`、`authors`（本人加粗 `'**Shanjun Deng**'`）、`date`（YYYY-MM-DD，用于倒序）、`doi`、
  `venue`、`corresponding`、`co_first`、`abstract`(中)、`abstract_en`、`tags`、`citations`(生成)。
- 首页只显示**本人为通讯/共通/一作/共一**的论文前 5 篇（`is_lead_paper`）；`papers.html` 显示全部并带序号。
- 引用数：`tool/fetch_citations.py`（OpenAlex，失败回退 Crossref）写入 `citations`；`update.py` 默认会刷新，
  CI 部署前也会刷新（不提交回仓库）。Clarivate/Google Scholar 无免费接口，故不用。

## 新闻（News）

- 只把 Word（含图片）放到 `sources/news/`；`tool/word2news.py` 生成 `content/news/<日期>.md` + 图片目录。
  - 图片按 Word 真实顺序原位插入；图注自动斜体；`--me`（默认邓善俊）加粗本人姓名。
- **每条新闻都要补 `title_en` 与 `body_en`**（英文版，含相同的 `![](图片名)`），英文名 `**Shanjun Deng**` 加粗。
- **每次更新新闻都要检查排版 / 语法 / 错别字**：①图片是否落在对应段落；②段落有无错误合并；
  ③术语与标点统一（`SARS-CoV-2`、`溯祖`、`伪时间(pseudotime)`、`小鼠`）；④作者与本人标注。
- 列表按日期倒序；详情页可返回；`news.html` 带序号。

## 软件（Software）

- 只维护 `sources/software.txt`（每行一个仓库链接，顺序即展示顺序）；`tool/fetch_software.py` 抓取仓库
  简介/语言/主题与 **README**（存 `content/software/*.readme.md`），据此写卡片 yml。
- **写卡片介绍前先读对应 README**，总结该包的用途；yml 字段：`order`、`title/title_en`、`description/description_en`、
  `url`、`language`、`tags/tags_en`。整卡可点击，直接跳转对应 GitHub 仓库。

## 其它约定

- 静态资源引用带内容哈希 `?v={{ASSET_V}}`，避免缓存。
- 临时/中间文件用完即删。
- **构建前/后检查**：`python update.py` 应无「未替换的占位符」报错；改样式后确认亮/暗两种模式都正常。
