#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""word2news.py —— 把带图片的 Word 新闻稿转换成 content/news/<slug>.md。

只依赖标准库（zipfile + xml.etree），无需 python-docx。

用法：
    python tool/word2news.py <news.docx> [--out content/news] [--date YYYY-MM-DD]
                             [--slug NAME] [--title "标题"] [--title-en "Title"]
                             [--source "来源"] [--me "邓善俊"] [--force]

行为：
- 按 Word 里的真实顺序输出文字与图片：段内图片会留在它出现的位置（不会挤到一起），
  图片抽取到 content/news/<slug>/ 并以 ![](图片名) 原位插入；表格文字按段落摊平。
- 标题默认取首个非空段落整行（含期刊名，如 "Advanced Biotechnology | …"）。
- 忽略无意义的空行；图注（紧跟图片、且较短的段）自动设为斜体。
- --me（默认「邓善俊」）：把正文里出现的本人姓名加粗突出（作者/通讯信息处）。
- 日期默认从文件名（YYYYMMDD / YYYY-MM-DD）推断，否则用今天。
- 输出文件名以 YYYY-MM-DD 开头，便于 update.py 按日期排序；同名已存在需 --force。
- 可选 --title-en 写入英文标题（供中英切换）。
"""
import os
import re
import sys
import zipfile
import argparse
import datetime
import xml.etree.ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def scalar(s):
    s = str(s)
    if s == '' or s != s.strip() or re.search(r'[:#\[\]{}&*!|>\'"%@`,]', s) or s[0] in '-?':
        return "'" + s.replace("'", "''") + "'"
    return s


def bold_name(text, me):
    if not me or me not in text:
        return text
    return re.sub(re.escape(me), '**' + me + '**', text).replace('****', '**')


def read_docx(path):
    z = zipfile.ZipFile(path)
    doc = ET.fromstring(z.read('word/document.xml'))
    try:
        rels = ET.fromstring(z.read('word/_rels/document.xml.rels'))
    except KeyError:
        rels = ET.fromstring(b'<Relationships/>')
    rid2target = {}
    for rel in rels:
        rid2target[rel.get('Id')] = rel.get('Target')
    return z, doc, rid2target


def para_text(p):
    return ' '.join(''.join(t.text or '' for t in p.iter(W + 't')).split())


def para_style(p):
    el = p.find('.//' + W + 'pStyle')
    return el.get(W + 'val') if el is not None else ''


def para_segments(p):
    """按文档顺序返回 [('t', 文本) / ('img', rId) ...]。"""
    segs = []
    buf = ''
    for node in p.iter():
        if node.tag == W + 't':
            buf += node.text or ''
        elif node.tag in (W + 'br', W + 'cr'):
            buf += '\n'
        elif node.tag == A + 'blip':
            if buf.strip():
                segs.append(('t', buf))
                buf = ''
            rid = node.get(R + 'embed')
            if rid:
                segs.append(('img', rid))
    if buf.strip():
        segs.append(('t', buf))
    return segs


def heading_level(style):
    if not style:
        return 0
    m = re.search(r'(?:heading|标题)\s*(\d)', style, re.I)
    if m:
        return int(m.group(1))
    if style in ('1', '2', '3', '4', '5', '6'):
        return int(style)
    return 0


def collect_paragraphs(doc):
    body = doc.find(W + 'body')
    paras = []
    for child in body:
        if child.tag == W + 'p':
            paras.append(child)
        elif child.tag == W + 'tbl':
            paras.extend(child.iter(W + 'p'))
    return paras


def guess_date(path, override):
    if override:
        return override
    stem = os.path.splitext(os.path.basename(path))[0]
    m = re.match(r'(\d{4})-?(\d{2})-?(\d{2})', stem)
    if m:
        return '%s-%s-%s' % (m.group(1), m.group(2), m.group(3))
    return datetime.date.today().isoformat()


def convert(path, out_dir, date, slug, title, title_en, source, me, force):
    z, doc, rid2target = read_docx(path)
    paras = collect_paragraphs(doc)

    if not title:
        for p in paras:
            t = para_text(p)
            if t:
                title = t
                break
    if not title:
        sys.exit('无法从文档中识别标题，请用 --title 指定')

    stem = slug if slug else date
    if slug and not re.match(r'^\d{4}-\d{2}-\d{2}', stem):
        stem = date + '-' + stem

    md_path = os.path.join(out_dir, stem + '.md')
    if os.path.exists(md_path) and not force:
        sys.exit('已存在 %s（用 --force 覆盖）' % md_path)

    blocks = []
    images = []
    used_title = False
    after_img = False

    def flush(text, style):
        nonlocal after_img
        lines = [ln.strip() for ln in text.split('\n') if ln.strip()]
        if not lines:
            return
        lvl = heading_level(style)
        for j, ln in enumerate(lines):
            if lvl:
                blocks.append('#' * lvl + ' ' + bold_name(ln, me))
            else:
                cap = bool(re.match(r'^图\s*\d', ln)) or (j == 0 and after_img and len(ln) <= 60)
                blocks.append(('*' + bold_name(ln, me) + '*') if cap else bold_name(ln, me))
        after_img = False

    for p in paras:
        flat = para_text(p)
        style = para_style(p)
        skip_text = bool(not used_title and flat and flat == title)
        if skip_text:
            used_title = True
        for kind, val in para_segments(p):
            if kind == 'img':
                target = rid2target.get(val)
                if not target:
                    continue
                name = os.path.basename(target)
                images.append(('word/' + target.lstrip('/'), name))
                blocks.append('![](' + name + ')')
                after_img = True
            elif not skip_text:
                flush(val, style)

    if images:
        img_dir = os.path.join(out_dir, stem)
        os.makedirs(img_dir, exist_ok=True)
        for zip_path, name in images:
            try:
                data = z.read(zip_path)
            except KeyError:
                continue
            with open(os.path.join(img_dir, name), 'wb') as f:
                f.write(data)

    fm = ['---', 'title: ' + scalar(title)]
    if title_en:
        fm.append('title_en: ' + scalar(title_en))
    fm.append('date: ' + date)
    if source:
        fm.append('source: ' + scalar(source))
    fm.append('---')
    content = '\n'.join(fm) + '\n\n' + '\n\n'.join(blocks).strip() + '\n'

    os.makedirs(out_dir, exist_ok=True)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return md_path, stem, len(images), title


def main():
    ap = argparse.ArgumentParser(description='把带图片的 Word 新闻稿转成 content/news/<slug>.md')
    ap.add_argument('docx')
    ap.add_argument('--out', default=os.path.join(ROOT, 'content', 'news'))
    ap.add_argument('--date', default=None, help='YYYY-MM-DD（默认从文件名推断）')
    ap.add_argument('--slug', default=None, help='输出文件名（默认用日期）')
    ap.add_argument('--title', default=None)
    ap.add_argument('--title-en', default=None)
    ap.add_argument('--source', default=None)
    ap.add_argument('--me', default='邓善俊', help='需要加粗突出的本人姓名（默认 邓善俊）')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    if not os.path.exists(args.docx):
        sys.exit('找不到文件: ' + args.docx)
    date = guess_date(args.docx, args.date)
    md_path, stem, nimg, title = convert(
        args.docx, args.out, date, args.slug, args.title, args.title_en,
        args.source, args.me, args.force)
    print('已生成: %s' % md_path)
    print('  标题: %s' % title)
    print('  日期: %s  图片: %d 张' % (date, nimg))
    print('  突出: %s' % (args.me or '(无)'))
    print('  图片目录: %s' % os.path.join(args.out, stem))


if __name__ == '__main__':
    main()
