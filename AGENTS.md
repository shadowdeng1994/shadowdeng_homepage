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

## 其它约定

- 静态资源引用带内容哈希版本号 `?v={{ASSET_V}}`（见 `asset_version()`），避免缓存。
- 头像须保存为 `content/about/avatar.jpg`（或在 `info.yml` 里改 `avatar:`）。
- CSV/摘要等临时文件属中间产物，用完即删。
