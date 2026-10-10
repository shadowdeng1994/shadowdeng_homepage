# AGENTS.md — shadowdeng_homepage

静态个人主页生成器。源文件在 `content/`、`templates/`、`static/`；根目录下的
`index.html`、`papers.html`、`news.html`、`news/`、`assets/`、`style.css`、`main.js`、
`logo.svg`、`.nojekyll` 都是 `python update.py`（或 CI 的 `--out _site`）生成的**产物**，
不要手改，也不要提交。

## 构建 / 预览

- 生成到仓库根目录：`python update.py`
- 生成到指定目录（CI 用）：`python update.py --out _site`
- 依赖：`pyyaml`、`markdown`（`pip install -r requirements.txt`）
- 若无 PDF 库，`tool/pdf2yml.py` 会回退到纯标准库解析。

## 中英文双语（重要）

站点支持 **中/英** 切换，**默认英文**，由 `<html>` 上的 `class="lang-en"` / `class="lang-zh"`
配合 `static/main.js` 与 `static/style.css` 控制。

**任何新增/修改的文字内容都必须同时提供中英文，否则切换后会漏字或串语言。** 具体：

- 模板（`templates/*.html`）里的界面文案用成对的 span：
  `<span class="lang-en">English</span><span class="lang-zh">中文</span>`。
- 生成 HTML 时，用 `update.py` 里的 `lang_block(en_html, zh_html, tag, cls)` 包裹同一段内容的两版。
- 数据文件的字段约定：
  - `content/about/info.yml`：`name/name_en`、`title/title_en`、`affiliation/affiliation_en`、
    `bio/bio_en`、`research_interests/research_interests_en`。
  - `content/research/*.yml`：`title/title_en`、`description/description_en`、`tags/tags_en`。
  - `content/papers/*.yml`：`abstract`（中文）+ `abstract_en`（英文）；论文题目/作者/期刊保持原文（英文）。
  - `content/news/*.md`：新增新闻时需同时提供中英标题与正文（`title`/`title_en` 等），
    并在 `update.py` 的 `build_news`/`build_news_pages` 中做双语渲染。
- 欢迎页打字动画的短语列表在 `static/main.js` 的 `phrasesByLang`，两种语言都要维护。

新增英语姓名：**Shanjun Deng**。

## 主题（亮色 / 暗夜，默认亮色）

- 由 `<html>` 上的 `class="theme-light"` / `theme-dark` 控制，切换按钮为导航里的
  `.theme-switch`（与语言开关 `.lang-switch` 共用样式与 `.ls-knob`）。
- `static/main.js` 的 `applyTheme`/`setTheme` 负责切换并写入 `localStorage.theme`；
  `<head>` 内联脚本会先按存储设置，避免闪烁。
- 暗色样式集中在 `static/style.css` 末尾的「暗夜主题」段（`html.theme-dark ...`）。
  **新增任何区块/组件时，都要在该段补一条对应的暗色规则**，否则暗夜下会沿用亮色配色。

## Logo（两套）

- `static/logo_bright.png`（亮色主题用）、`static/logo_dark.png`（暗夜主题用）。
  `update.py` 的 `logo_files()` 会自动选用（找不到则回退 `logo.png`…`logo.svg`），
  并分别注入 `{{LOGO_LIGHT}}` / `{{LOGO_DARK}}`；模板里两套 logo 用 `.logo-light` /
  `.logo-dark` 配合主题显隐。favicon 用亮色版。
- 放入的原始图片请先压缩（建议 ≤256×256 PNG，几十 KB 级别），避免仓库体积过大。


## 其它约定

- 静态资源引用带内容哈希版本号 `?v={{ASSET_V}}`（见 `asset_version()`），避免缓存。
- 头像须保存为 `content/about/avatar.jpg`（或在 `info.yml` 里改 `avatar:`）。
- CSV/摘要等临时文件属中间产物，用完即删。

## 论文引用数（citations）

- 每篇 `content/papers/*.yml` 带 `doi:`；引用数由 `tool/fetch_citations.py` 按 DOI 抓取，
  写入 `citations:` 与 `citations_updated:` 字段（开放数据源：OpenAlex，失败回退 Crossref）。
- Web of Science 需付费 API Key、Google Scholar 无 API 且禁止抓取，故不采用；数字通常低于 Google Scholar。
- 刷新：`python tool/fetch_citations.py`（可定期手动运行）。`update.py` 构建时只读取
  `citations` 字段显示「Cited by N / 被引 N」，不做网络请求，保证构建可离线复现。
- 引用数大于 0 才显示徽标。
