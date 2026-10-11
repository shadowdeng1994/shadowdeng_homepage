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
- 刷新：`python update.py` **默认会先抓取一次**（`--no-citations` 可跳过）；也可单独运行
  `python tool/fetch_citations.py`。抓取结果会写回 yml，再由 `update.py` 读取显示
  「Cited by N / 被引 N」。
- CI 部署（`.github/workflows/deploy.yml`）：构建前先跑 `python tool/fetch_citations.py`
  （`continue-on-error: true`，失败不影响部署），再 `python update.py --out _site --no-citations`，
  确保线上显示的是部署当时的最新引用数（不提交回仓库）。
- 引用数大于 0 才显示徽标。

## 新闻（News）

- 用带图片的 Word 稿生成新闻：`python tool/word2news.py content/news/<name>.docx`
  （std/tool 仅用标准库）。会生成 `content/news/<YYYY-MM-DD>.md` 与图片目录
  `content/news/<YYYY-MM-DD>/`，图片在正文原位插入；标题取首段整行（含期刊名，如
  `Advanced Biotechnology | …`）。
- 常用参数：`--date` 覆盖日期、`--slug` 指定文件名后缀、`--title`/`--title-en` 覆盖标题、
  `--source` 来源、`--force` 覆盖。
- 列表条目显示日期并按日期倒序（`load_news` 用 front matter 的 `date:` 或文件名前缀）。
- 双语：**每条新闻都要提供 `title_en` 与 `body_en`（英文版）**，否则英文模式会显示中文。
  `word2news.py --title-en` 写入英文标题；正文英文写在 front matter 的 `body_en: |` 块里
  （保留同样的 `![](图片名)` 图片位置），并把英文名 `**Shanjun Deng**` 加粗。
- 列出所有新闻用 `numbered=True`（`update.py` 在 `news.html` 上启用序号）。
- **期刊发表类新闻**：正文末尾常含通讯作者/第一作者信息。用 `--me`（默认「邓善俊」）
  把正文里出现的本人姓名加粗突出（工具默认开启）。若原稿没有作者信息，需在文末补一句
  说明（如「…为本文共同第一作者/通讯作者」）并把**邓善俊**加粗。
- **每次更新新闻都要检查排版 / 语法 / 错别字**：重点确认
  ① 图片落在对应段落的位置（`word2news.py` 现在按 Word 真实顺序插图片，不再把多张图挤在一起）；
  ② 段落没有错误的合并/断行；③ 术语与标点统一（如 `SARS-CoV-2`、`溯祖`、`伪时间(pseudotime)`、`小鼠`）；
  ④ 作者信息与本人姓名标注正确。发现明显错误当次改正。

## 软件（Software）

- 数据在 `content/software/*.yml`；同目录的 `softwarelist.txt` 只是待抓取的仓库清单，不会被读取。
- 字段：`order`、`title`/`title_en`（仓库名）、`description`/`description_en`、`url`（GitHub 链接）、
  `language`、`tags`/`tags_en`。**中英双语**（描述英文可取自 GitHub，中文翻译补上）。
- 抓取仓库信息：`GET https://api.github.com/repos/<owner>/<repo>` 的 `description`/`language`
  （`topics` 常为空，标签需人工补）。
- `update.py` 的 `load_software()`/`build_software()` 渲染为卡片网格（空时占位）；
  首页与子页导航都有「软件 / Software」入口。
