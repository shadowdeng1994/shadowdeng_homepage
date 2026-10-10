#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""update.py —— 从 content/ 生成静态个人主页。

依赖：pyyaml、markdown。
若运行环境缺少 markdown 包，会自动回退到内置的极简 Markdown 渲染器
（仅用于本地预览；GitHub Actions 中会安装真正的 markdown 包）。

用法：
    python update.py            # 生成到仓库根目录
    python update.py --out _site  # 生成到指定目录（供 CI 上传 Pages 产物）
"""
import os
import re
import glob
import html
import shutil
import hashlib
import argparse
import datetime

import yaml

try:
    import markdown as _markdown
    _HAVE_MARKDOWN = True
except ImportError:
    _markdown = None
    _HAVE_MARKDOWN = False

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, 'content')
TEMPLATES = os.path.join(ROOT, 'templates')
STATIC = os.path.join(ROOT, 'static')

PLACEHOLDER_RE = re.compile(r'\{\{[A-Z_]+\}\}')
FRONT_RE = re.compile(r'^\s*---\s*\n(.*?)\n---\s*\n?(.*)$', re.S)


# ---------------- 基础工具 ----------------
def read_text(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def write_text(path, text):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def load_yaml(path):
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def esc(s):
    return html.escape(str(s), quote=True)


def norm_ws(s):
    return ' '.join(str(s).split())


def render_inline(s):
    s = esc(s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', s)
    return s


def lang_block(en_html, zh_html, tag='span', cls=''):
    """把同一段内容的中英两版包进 .lang-en / .lang-zh，由前端按语言切换显示。"""
    c = (' ' + cls) if cls else ''
    return ('<%s class="lang-en%s">%s</%s><%s class="lang-zh%s">%s</%s>'
            % (tag, c, en_html, tag, tag, c, zh_html, tag))


def prettify_slug(slug):
    return slug.replace('-', ' ').replace('_', ' ').strip()


def fill(template, mapping):
    out = template
    for k, v in mapping.items():
        out = out.replace('{{%s}}' % k, v)
    left = set(PLACEHOLDER_RE.findall(out))
    if left:
        raise RuntimeError('未替换的占位符: ' + ', '.join(sorted(left)))
    return out


# ---------------- Markdown 渲染 ----------------
def _inline(s):
    s = esc(s)
    s = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)',
               r'<img src="\2" alt="\1">', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)(?:\s+&quot;[^&]*&quot;)?\)',
               r'<a href="\2">\1</a>', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', s)
    return s


def _mini_md(text):
    blocks = re.split(r'\n\s*\n', text.strip())
    out = []
    for b in blocks:
        lines = b.split('\n')
        st = [ln.strip() for ln in lines]
        nonempty = [x for x in st if x]
        if nonempty and all(re.match(r'^[-*]\s+', x) for x in nonempty):
            items = ''.join('<li>%s</li>' % _inline(re.sub(r'^[-*]\s+', '', x))
                            for x in nonempty)
            out.append('<ul>%s</ul>' % items)
        elif nonempty and all(re.match(r'^\d+\.\s+', x) for x in nonempty):
            items = ''.join('<li>%s</li>' % _inline(re.sub(r'^\d+\.\s+', '', x))
                            for x in nonempty)
            out.append('<ol>%s</ol>' % items)
        elif nonempty and all(x.startswith('> ') for x in nonempty):
            out.append('<blockquote>%s</blockquote>'
                       % '<br>'.join(_inline(x[2:]) for x in nonempty))
        elif len(nonempty) == 1 and re.match(r'^#{1,6}\s+', nonempty[0]):
            m = re.match(r'^(#{1,6})\s+(.*)$', nonempty[0])
            lvl = len(m.group(1))
            out.append('<h%d>%s</h%d>' % (lvl, _inline(m.group(2)), lvl))
        else:
            out.append('<p>%s</p>' % '<br>'.join(_inline(ln) for ln in lines if ln.strip()))
    return '\n'.join(out)


def render_md(text):
    text = (text or '').strip()
    if not text:
        return ''
    if _HAVE_MARKDOWN:
        return _markdown.markdown(text, extensions=['extra', 'sane_lists'])
    return _mini_md(text)


# ---------------- 数据加载 ----------------
def load_about():
    return load_yaml(os.path.join(CONTENT, 'about', 'info.yml'))


def load_research():
    files = glob.glob(os.path.join(CONTENT, 'research', '*.yml'))
    items = []
    for f in files:
        d = load_yaml(f)
        try:
            order = int(d.get('order'))
        except (TypeError, ValueError):
            order = 999
        items.append((order, os.path.splitext(os.path.basename(f))[0], d))
    items.sort(key=lambda t: (t[0], t[1]))
    return [d for _, _, d in items]


def _paper_date_key(s):
    m = re.match(r'(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?', str(s or ''))
    if not m:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2) or 0), int(m.group(3) or 0))


def load_papers():
    d = os.path.join(CONTENT, 'papers')
    slugs = set()
    for f in glob.glob(os.path.join(d, '*.yml')) + glob.glob(os.path.join(d, '*.pdf')):
        slugs.add(os.path.splitext(os.path.basename(f))[0])
    papers = []
    for slug in slugs:
        ypath = os.path.join(d, slug + '.yml')
        ppath = os.path.join(d, slug + '.pdf')
        data = load_yaml(ypath) if os.path.exists(ypath) else {}
        date = str(data.get('date') or '')
        papers.append({
            'slug': slug,
            'title': data.get('title') or prettify_slug(slug),
            'authors': data.get('authors') or [],
            'venue': data.get('venue') or '',
            'year': _paper_date_key(date)[0],
            'date': date,
            'corresponding': data.get('corresponding') or [],
            'co_first': data.get('co_first') or [],
            'abstract': data.get('abstract') or '',
            'abstract_en': data.get('abstract_en') or '',
            'has_pdf': os.path.exists(ppath),
        })
    papers.sort(key=lambda p: (_paper_date_key(p['date']), p['slug']), reverse=True)
    return papers


def _fmt_date(v, stem):
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.strftime('%Y-%m-%d')
    if v:
        return str(v)
    m = re.match(r'(\d{4}-\d{2}-\d{2})', stem)
    return m.group(1) if m else ''


def _date_key(s):
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d')
    except (ValueError, TypeError):
        return datetime.datetime.min


def _strip_md(text):
    t = re.sub(r'!\[[^\]]*\]\([^)]*\)', '', text)
    t = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', t)
    t = re.sub(r'[#>*_`]', '', t)
    return re.sub(r'\s+', ' ', t).strip()


def _summarize(text, n=120):
    s = _strip_md(text)
    return s[:n].rstrip() + '…' if len(s) > n else s


def load_news():
    d = os.path.join(CONTENT, 'news')
    posts = []
    for f in glob.glob(os.path.join(d, '*.md')):
        stem = os.path.splitext(os.path.basename(f))[0]
        raw = read_text(f)
        m = FRONT_RE.match(raw)
        if m:
            fm = yaml.safe_load(m.group(1)) or {}
            body = m.group(2)
        else:
            fm, body = {}, raw
        title = fm.get('title') or prettify_slug(re.sub(r'^\d{4}-\d{2}-\d{2}-', '', stem))
        date_str = _fmt_date(fm.get('date'), stem)
        posts.append({
            'stem': stem, 'title': title, 'date': date_str,
            'body': body, 'summary': _summarize(body),
        })
    posts.sort(key=lambda p: (_date_key(p['date']), p['stem']), reverse=True)
    return posts


# ---------------- 片段构建 ----------------
def build_about(info, avatar_src):
    name_zh = info.get('name', '')
    name_en = info.get('name_en') or name_zh
    head_en = ' · '.join([x for x in [info.get('title_en'), info.get('affiliation_en')] if x])
    head_zh = ' · '.join([x for x in [info.get('title'), info.get('affiliation')] if x])
    if avatar_src:
        avatar_html = '<img class="avatar" src="%s" alt="%s">' % (esc(avatar_src), esc(name_en))
    else:
        avatar_html = '<div class="avatar">%s</div>' % esc(name_en[:1])
    email = info.get('email', '')
    email_html = ('<p class="muted"><a href="mailto:%s">%s</a></p>' % (esc(email), esc(email))) if email else ''
    links = info.get('links') or []
    links_html = ''
    if links:
        parts = []
        for l in links:
            url = str(l.get('url', ''))
            ext = ' target="_blank" rel="noopener"' if url.startswith('http') else ''
            label_en = l.get('label_en') or l.get('label', '')
            label_zh = l.get('label') or l.get('label_en', '')
            parts.append('<a href="%s"%s>%s</a>'
                         % (esc(url), ext, lang_block(esc(label_en), esc(label_zh))))
        links_html = '<div class="links">%s</div>' % ''.join(parts)
    bio_html = lang_block(render_md(info.get('bio_en', '')), render_md(info.get('bio', '')),
                          tag='div', cls='bio')
    return (
        '<div class="about-header">\n'
        '  %s\n'
        '  <div>\n'
        '    <h2>%s</h2>\n'
        '    <p class="muted">%s</p>\n'
        '    %s\n'
        '    %s\n'
        '  </div>\n'
        '</div>\n'
        '%s'
    ) % (avatar_html, lang_block(esc(name_en), esc(name_zh)),
         lang_block(esc(head_en), esc(head_zh)), email_html, links_html, bio_html)


def build_research(items):
    slides = []
    for i, d in enumerate(items, 1):
        def block(title, desc, tags):
            tag_items = ''.join('<li>%s</li>' % esc(t) for t in (tags or []))
            return ('<h3 class="slide-title">%s</h3>\n'
                    '<p class="slide-desc">%s</p>\n'
                    '<ul class="slide-tags">%s</ul>') % (esc(title), esc(norm_ws(desc)), tag_items)
        en = block(d.get('title_en') or d.get('title', ''),
                   d.get('description_en') or d.get('description', ''),
                   d.get('tags_en') or d.get('tags'))
        zh = block(d.get('title', ''), d.get('description', ''), d.get('tags'))
        slides.append(
            '<div class="slide">\n'
            '  <div class="slide-num">%02d</div>\n'
            '  <div class="lang-en">%s</div>\n'
            '  <div class="lang-zh">%s</div>\n'
            '</div>' % (i, en, zh)
        )
    return '\n'.join(slides)


def _name_key(s):
    return re.sub(r'[^a-z]', '', str(s).lower())


def _paper_meta(p):
    corr = set(_name_key(x) for x in p.get('corresponding') or [])
    cof = set(_name_key(x) for x in p.get('co_first') or [])

    def disp(a):
        marks = ''
        if _name_key(a) in cof:
            marks += '#'
        if _name_key(a) in corr:
            marks += '*'
        out = render_inline(a)
        if marks:
            out += '<sup class="author-mark">%s</sup>' % marks
        return out

    parts = []
    if p['authors']:
        parts.append(', '.join(disp(a) for a in p['authors']))
    if p['venue']:
        parts.append(render_inline(p['venue']))
    if p['year']:
        parts.append(str(p['year']))
    return ' · '.join(parts)


SELF_NAME = 'Shanjun Deng'


def is_lead_paper(p):
    """本人为通讯（含共通）、一作或共一的论文。"""
    key = _name_key(SELF_NAME)
    corr = set(_name_key(x) for x in p.get('corresponding') or [])
    cof = set(_name_key(x) for x in p.get('co_first') or [])
    if key in corr or key in cof:
        return True
    return bool(p['authors']) and _name_key(p['authors'][0]) == key


def build_papers(papers, limit=None, numbered=False):
    sel = papers[:limit] if limit else papers
    out = []
    for i, p in enumerate(sel, 1):
        bits = ['<li class="paper">']
        if numbered:
            bits.append('  <div class="item-num">%02d</div>' % i)
        bits.append('  <h3>%s</h3>' % render_inline(p['title']))
        meta = _paper_meta(p)
        if meta:
            bits.append('  <p class="meta">%s</p>' % meta)
        notes_en = []
        notes_zh = []
        if p.get('co_first'):
            notes_en.append('# Co-first author')
            notes_zh.append('# 共同第一作者')
        if p.get('corresponding'):
            notes_en.append('* Corresponding author')
            notes_zh.append('* 通讯作者')
        if notes_en:
            bits.append('  <p class="author-note">%s</p>'
                        % lang_block(esc(' · '.join(notes_en)), esc(' · '.join(notes_zh))))
        if p.get('abstract_en'):
            bits.append('  <p class="abstract lang-en">%s</p>' % render_inline(norm_ws(p['abstract_en'])))
        if p['abstract']:
            bits.append('  <p class="abstract lang-zh">%s</p>' % render_inline(norm_ws(p['abstract'])))
        if p['has_pdf']:
            bits.append('  <a class="pdf-link" href="assets/papers/%s.pdf">📄 %s</a>'
                        % (esc(p['slug']), lang_block('Download PDF', '下载 PDF')))
        bits.append('</li>')
        out.append('\n'.join(bits))
    return '\n'.join(out)


def build_news(posts, limit=None, numbered=False):
    sel = posts[:limit] if limit else posts
    out = []
    for i, p in enumerate(sel, 1):
        num = ('  <div class="item-num">%02d</div>\n' % i) if numbered else ''
        out.append(
            '<li class="news-item">\n'
            '%s'
            '  <span class="date">%s</span>\n'
            '  <a class="title" href="news/%s/">%s</a>\n'
            '  <p class="summary">%s</p>\n'
            '</li>' % (num, esc(p['date']), esc(p['stem']), esc(p['title']), esc(p['summary']))
        )
    return '\n'.join(out)


# ---------------- 资源与页面输出 ----------------
def copy_assets(info, out):
    assets = os.path.join(out, 'assets')
    if os.path.isdir(assets):
        shutil.rmtree(assets)
    os.makedirs(os.path.join(assets, 'papers'), exist_ok=True)
    avatar_src = None
    avatar = info.get('avatar')
    if avatar:
        src = os.path.join(CONTENT, 'about', avatar)
        if os.path.exists(src):
            dest = os.path.join(assets, avatar)
            shutil.copy2(src, dest)
            with open(dest, 'rb') as f:
                v = hashlib.sha1(f.read()).hexdigest()[:10]
            avatar_src = 'assets/%s?v=%s' % (avatar, v)
    for f in glob.glob(os.path.join(CONTENT, 'papers', '*.pdf')):
        shutil.copy2(f, os.path.join(assets, 'papers', os.path.basename(f)))
    return avatar_src


def logo_files():
    bright = None
    for n in ('logo_bright.png', 'logo.png', 'logo.jpg', 'logo.jpeg', 'logo.webp', 'logo.svg'):
        if os.path.exists(os.path.join(STATIC, n)):
            bright = n
            break
    dark = None
    for n in ('logo_dark.png', 'logo_dark.jpg', 'logo_dark.jpeg', 'logo_dark.webp'):
        if os.path.exists(os.path.join(STATIC, n)):
            dark = n
            break
    if bright is None:
        bright = 'logo.svg'
    if dark is None:
        dark = bright
    return bright, dark


def asset_version():
    h = hashlib.sha1()
    for name in set(['style.css', 'main.js'] + list(logo_files())):
        with open(os.path.join(STATIC, name), 'rb') as f:
            h.update(f.read())
    return h.hexdigest()[:10]


def build_news_pages(posts, out, asset_v, logo_light, logo_dark):
    newsdir = os.path.join(out, 'news')
    if os.path.isdir(newsdir):
        shutil.rmtree(newsdir)
    tpl = read_text(os.path.join(TEMPLATES, 'post.template.html'))
    for p in posts:
        dest = os.path.join(newsdir, p['stem'])
        os.makedirs(dest, exist_ok=True)
        imgsrc = os.path.join(CONTENT, 'news', p['stem'])
        if os.path.isdir(imgsrc):
            for f in os.listdir(imgsrc):
                fp = os.path.join(imgsrc, f)
                if os.path.isfile(fp):
                    shutil.copy2(fp, os.path.join(dest, f))
        page = fill(tpl, {
            'TITLE': esc(p['title']),
            'DATE': esc(p['date']),
            'CONTENT': render_md(p['body']),
            'ASSET_V': asset_v,
            'LOGO_LIGHT': logo_light,
            'LOGO_DARK': logo_dark,
        })
        write_text(os.path.join(dest, 'index.html'), page)


def copy_static(out):
    for name in ('style.css', 'main.js'):
        shutil.copy2(os.path.join(STATIC, name), os.path.join(out, name))
    for name in set(logo_files()):
        shutil.copy2(os.path.join(STATIC, name), os.path.join(out, name))
    write_text(os.path.join(out, '.nojekyll'), '')


def main():
    ap = argparse.ArgumentParser(description='生成静态个人主页')
    ap.add_argument('--out', default=ROOT, help='输出目录（默认仓库根目录）')
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    info = load_about()
    name_zh = info.get('name', '')
    name_en = info.get('name_en') or name_zh
    updated = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    asset_v = asset_version()
    logo_light, logo_dark = logo_files()

    avatar_src = copy_assets(info, out)
    about_html = build_about(info, avatar_src)
    research_html = build_research(load_research())
    papers = load_papers()
    news = load_news()
    lead_papers = [p for p in papers if is_lead_paper(p)]
    if news:
        news_all = build_news(news, numbered=True)
        news_latest = build_news(news, 5)
    else:
        news_all = news_latest = '<li class="news-empty">%s</li>' % lang_block(
            'No news yet — stay tuned.', '暂无新闻，敬请期待。')

    idx = fill(read_text(os.path.join(TEMPLATES, 'index.template.html')), {
        'NAME_EN': esc(name_en),
        'NAME_ZH': esc(name_zh),
        'ABOUT': about_html,
        'RESEARCH': research_html,
        'PAPERS': build_papers(lead_papers, 5),
        'NEWS': news_latest,
        'UPDATED_AT': esc(updated),
        'ASSET_V': asset_v,
        'LOGO_LIGHT': logo_light,
        'LOGO_DARK': logo_dark,
    })
    write_text(os.path.join(out, 'index.html'), idx)

    write_text(os.path.join(out, 'papers.html'),
               fill(read_text(os.path.join(TEMPLATES, 'papers.template.html')), {
                   'NAME_EN': esc(name_en),
                   'NAME_ZH': esc(name_zh),
                   'PAPERS': build_papers(papers, numbered=True),
                   'UPDATED_AT': esc(updated),
                   'ASSET_V': asset_v,
                   'LOGO_LIGHT': logo_light,
                   'LOGO_DARK': logo_dark,
               }))

    write_text(os.path.join(out, 'news.html'),
               fill(read_text(os.path.join(TEMPLATES, 'news.template.html')), {
                   'NAME_EN': esc(name_en),
                   'NAME_ZH': esc(name_zh),
                   'NEWS': news_all,
                   'UPDATED_AT': esc(updated),
                   'ASSET_V': asset_v,
                   'LOGO_LIGHT': logo_light,
                   'LOGO_DARK': logo_dark,
               }))

    build_news_pages(news, out, asset_v, logo_light, logo_dark)
    copy_static(out)

    print('生成完成 -> %s' % out)
    print('  markdown 渲染器: %s' % ('markdown 包' if _HAVE_MARKDOWN else '内置极简回退'))
    print('  论文 %d 篇 / 新闻 %d 篇 / 研究卡片 %d 张'
          % (len(papers), len(news), len(research_html.split('class="slide"')) - 1))


if __name__ == '__main__':
    main()
