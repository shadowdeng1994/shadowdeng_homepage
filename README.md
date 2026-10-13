# 个人主页

邓善俊（Shanjun Deng）的个人主页。纯静态：`update.py` 从 `content/` 生成 HTML，不用前端框架。

## 我只需要维护 `sources/`

| 改什么 | 放哪 |
|---|---|
| 简介 / 信息 | `sources/about/info.yml`（+ 可选 `avatar.jpg`） |
| 文章 | `sources/papers/*.pdf`（只放 PDF） |
| 新闻 | `sources/news/*.docx`（只放 Word） |
| 软件 | `sources/software.txt`（每行一个仓库链接） |
| 研究方向 | `sources/research/*.yml`（一般不动） |

其余 `content/`、根目录产物都由脚本生成，别手改。

## 生成 + 部署

```bash
pip install -r requirements.txt
python tool/build.py      # 转 PDF/Word + 抓软件 + 生成站点（--no-net 跳过联网）
```

只生成站点：`python update.py`。推送到 `main` 后 GitHub Actions 自动构建并部署到 Pages。

> 细节（双语、亮/暗主题、新闻排版检查、欢迎页动画等）见 `AGENTS.md`。
