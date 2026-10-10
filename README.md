# 个人主页（静态站点）

这是一个长期维护的静态个人主页项目，托管在 GitHub Pages 上。

页面由一个 Python 脚本（`update.py`，下一轮编写）从 `content/` 目录读取数据，
结合 `templates/` 中的模板与 `static/` 中的样式，生成纯静态的 HTML + CSS + 原生 JS。
**不使用任何前端框架，也不使用构建工具。**

> 占位提示：模板与样式已就绪，**运行 `update.py` 生成网页**（脚本将在下一轮编写）。

## 目录结构

```
个人主页/
├── content/                # 源数据（手写，纳入版本控制）
│   ├── about/              # 个人信息
│   │   ├── info.yml
│   │   └── avatar.jpg
│   ├── research/           # 研究方向卡片（主页轮播），每张一个 .yml
│   │   └── <slug>.yml
│   ├── papers/             # 论文：每个 slug 对应一个 .pdf 与可选的 .yml
│   │   ├── 2025-attention.pdf
│   │   ├── 2025-attention.yml
│   │   └── ...
│   └── news/               # 新闻：每篇一个 .md，可配同名图片文件夹
│       ├── 2026-03-15-attend-icml.md
│       ├── 2026-03-15-attend-icml/photo-1.jpg
│       └── ...
├── templates/              # HTML 模板（源）
│   ├── index.template.html     # 帷幕 + 主页 → index.html
│   ├── papers.template.html    # 全部论文页 → papers.html
│   ├── news.template.html      # 全部新闻页 → news.html
│   └── post.template.html      # 新闻详情 → news/<slug>/index.html
├── static/                 # 静态资源（源）
│   ├── style.css
│   └── main.js
├── update.py               # 生成脚本（下一轮编写）
├── README.md
└── .gitignore
```

**源文件与产物分离**：`content/`、`templates/`、`static/` 是源；
`index.html`、`papers.html`、`news.html`、`news/`、`assets/`、`style.css`、`main.js`
是脚本生成的产物，已在 `.gitignore` 中忽略，无需手动编辑。

## 页面结构

- **index.html**：全屏"帷幕"开场（姓名 + 头衔），点击 / 滚动 / 回车进入主页；
  向下依次为 个人简介、研究方向（轮播卡片）、Publication（最新 5 条）、News（最新 5 条），
  顶部吸顶导航随滚动高亮。
- **papers.html / news.html**：全部论文 / 全部新闻列表，由主页"查看全部"进入。
- **news/<slug>/index.html**：新闻详情页，含返回 News 链接。

暗色主题、视差背景、轮播与导航高亮等交互由 `static/main.js` 提供，
脚本注入的数据位置使用占位符（见各模板内注释）。

## 数据格式

### 1. 个人信息 `content/about/info.yml`

```yaml
name: 姓名
title: 头衔（如"博士研究生"）
affiliation: 单位
email: 邮箱
avatar: 头像文件名（如 avatar.jpg）
bio: |
  多行文本，Markdown 格式。
research_interests:        # 字符串列表
  - 研究方向 A
  - 研究方向 B
links:                     # 列表，每项含 label 与 url
  - label: Google Scholar
    url: https://scholar.google.com/
```

### 2. 论文 `content/papers/<slug>.yml`

约定：**`.yml` 与 `.pdf` 同名（同 slug），脚本自动配对。**
没有 `.yml` 的 `.pdf` 也能正常显示（fallback：用文件名当标题）。

```yaml
title: 论文标题
authors:                   # 作者列表（字符串）
  - 作者一
  - 作者二
venue: 发表会议或期刊
year: 2025
citation: |                # 完整引用文本，citation 风格，多行
  作者. 标题. 会议/期刊, 年份.
abstract: |                # 可选，论文简介
  这篇 paper 做了什么。
tags:                      # 可选，字符串列表
  - tag-a
  - tag-b
```

### 3. 新闻 `content/news/YYYY-MM-DD-<slug>.md`

Markdown 文件，带 frontmatter：

```markdown
---
title: 文章标题
date: 2026-03-15
---

正文内容，Markdown 格式。
```

- **新闻没有"封面图"概念，也不需要 `cover` 字段，图片只出现在正文内部。**
- 图片约定：每篇新闻可配一个**与 md 同名的文件夹**，存放正文用到的图片；
  md 内用相对路径引用，例如 `![](photo-1.jpg)`。
- 也可以完全不放图片文件夹，即纯文字新闻。

### 4. 研究卡片 `content/research/<slug>.yml`

主页"研究方向"轮播的每一张卡片，脚本按 `order` 升序排列。

```yaml
order: 1                   # 轮播顺序（升序）
title: 研究方向标题
description: |             # 卡片正文，多行
  这个方向在做什么。
tags:                      # 标签，渲染为卡片底部小块
  - 标签 A
  - 标签 B
```

## 本地生成

依赖仅 `pyyaml` 与 `markdown`：

```bash
pip install pyyaml markdown
python update.py
```

运行后在仓库根目录生成 `index.html`、`papers.html`、`news.html`、`news/`、`assets/`、`style.css`、`main.js`。

## 部署到 GitHub Pages

1. 将本仓库推送到 GitHub。
2. 在本地运行 `python update.py` 生成产物（或配置 CI 自动生成）。
3. 在仓库 **Settings → Pages** 中选择部署来源：
   - **Deploy from a branch**：选择包含产物的分支与根目录 `/ (root)`；
     由于产物被 `.gitignore` 忽略，推荐用 GitHub Actions 在推送时生成并部署，
     或将产物提交到 `gh-pages` 分支。
   - **GitHub Actions**：使用 `actions/configure-pages` + `actions/upload-pages-artifact`
     上传生成后的站点目录。
4. 访问 `https://<用户名>.github.io/<仓库名>/` 即可。

> 提示：若站点部署在子路径下，生成脚本中的资源链接需使用相对路径，
> 或在配置中设置站点 base path。
