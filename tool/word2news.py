#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""word2news.py —— 把带图片的 Word 新闻稿转换成 content/news/<slug>.md。

只依赖标准库（zipfile + xml.etree），无需 python-docx。

用法：
    python tool/word2news.py <news.docx> [--out content/news] [--date YYYY-MM-DD]
                             [--slug NAME] [--title "标题"] [--title-en "Title"]
                             [--source "来源"] [--force]

行为：
- 正文按 Word 段落顺序转成 Markdown；段内图片抽取到 content/news/<slug>/，
  并在原位插入 ![](图片名)；表格文字按段落摊平。
- 标题默认取首个非空段落；若该段形如 "来源 | 标题"，则取竖线后为标题、前部为来源。
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


def para_info(p):
    text = ''.join(t.text or '' for t in p.iter(W + 't')).strip()
    style_el = p.find('.//' + W + 'pStyle')
    style = style_el.get(W + 'val') if style_el is not None else ''
    rids = [b.get(R + 'embed') for b in p.iter(A + 'blip') if b.get(R + 'embed')]
    return text, style, rids


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


def convert(path, out_dir, date, slug, title, title_en, source, force):
    z, doc, rid2target = read_docx(path)
    infos = [para_info(p) for p in collect_paragraphs(doc)]

    if not title:
        for text, style, rids in infos:
            if text:
                if '|' in text:
                    head, tail = text.split('|', 1)
                    source = source or head.strip()
                    title = tail.strip()
                else:
                    title = text
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
    for text, style, rids in infos:
        tail = text.split('|', 1)[1].strip() if '|' in text else text
        if not used_title and text and tail == title:
            used_title = True
        else:
            lvl = heading_level(style)
            if text and lvl:
                blocks.append('#' * lvl + ' ' + text)
            elif text:
                blocks.append('*' + text + '*' if re.match(r'^图\s*\d', text) else text)
        for rid in rids:
            target = rid2target.get(rid)
            if not target:
                continue
            name = os.path.basename(target)
            images.append(('word/' + target.lstrip('/'), name))
            blocks.append('![](' + name + ')')

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
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()

    if not os.path.exists(args.docx):
        sys.exit('找不到文件: ' + args.docx)
    date = guess_date(args.docx, args.date)
    md_path, stem, nimg, title = convert(
        args.docx, args.out, date, args.slug, args.title, args.title_en, args.source, args.force)
    print('已生成: %s' % md_path)
    print('  标题: %s' % title)
    print('  日期: %s  图片: %d 张' % (date, nimg))
    print('  图片目录: %s' % os.path.join(args.out, stem))


if __name__ == '__main__':
    main()
