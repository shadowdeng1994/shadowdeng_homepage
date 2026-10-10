#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pdf2yml —— 从论文 PDF 提取文本，生成 content/papers/<slug>.yml 草稿。

用法：
    python tool/pdf2yml.py <paper.pdf> [--out content/papers] [--slug NAME]
                           [--me "Your Name"] [--force] [--dump-text PATH]

说明：
- 优先使用已安装的 PDF 库（pymupdf/fitz、pdfplumber、pdfminer.six、pypdf、PyPDF2）；
  若都没有，则回退到内置的纯标准库解析（zlib 解压内容流 + 文本算子重排）。
- 标题 / 作者 / 摘要为“尽力而为”的启发式提取，PDF 常有连字、上标、分栏，
  结果可能有出入，**务必对照原文核对**。DOI、年份相对可靠。
- 生成的 yml 与 pdf 同名（放在 --out 目录），供 update.py 自动配对。
- --me 指定本人姓名：在 authors 与 citation 中自动 **加粗**；venue 自动 *斜体*。
"""
import os
import re
import sys
import zlib
import argparse


# ---------------- PDF 文本提取 ----------------
def _read(path):
    with open(path, 'rb') as f:
        return f.read()


def _stdlib_text(path):
    """无第三方库时：解压内容流，按 TJ 字距重排文本。"""
    data = _read(path)

    def read_paren(b, i):
        depth = 0
        out = bytearray()
        i += 1
        n = len(b)
        while i < n:
            c = b[i]
            if c == 0x5c:  # backslash
                nxt = b[i + 1] if i + 1 < n else 0
                mp = {0x6e: 0x0a, 0x72: 0x0d, 0x74: 0x09, 0x62: 0x08, 0x66: 0x0c,
                      0x28: 0x28, 0x29: 0x29, 0x5c: 0x5c}
                if nxt in mp:
                    out.append(mp[nxt]); i += 2; continue
                if 0x30 <= nxt <= 0x37:
                    od = bytearray(); j = i + 1
                    while j < n and len(od) < 3 and 0x30 <= b[j] <= 0x37:
                        od.append(b[j]); j += 1
                    out.append(int(od, 8) & 0xff); i = j; continue
                out.append(nxt); i += 2; continue
            if c == 0x28:
                depth += 1; out.append(c); i += 1; continue
            if c == 0x29:
                if depth == 0:
                    return bytes(out), i + 1
                depth -= 1; out.append(c); i += 1; continue
            out.append(c); i += 1
        return bytes(out), i

    def process(stream):
        out = []
        i = 0
        n = len(stream)
        in_arr = False
        while i < n:
            c = stream[i]
            if c == 0x28:
                s, i = read_paren(stream, i)
                t = s.decode('latin-1', 'replace')
                t = ''.join(ch for ch in t if ch in '\n\t' or 32 <= ord(ch) < 127 or ord(ch) >= 160)
                out.append(t)
                continue
            if c == 0x5b:
                in_arr = True; i += 1; continue
            if c == 0x5d:
                in_arr = False; i += 1; continue
            m = re.match(rb'[-+]?\d*\.?\d+', stream[i:i + 12])
            if m and (i == 0 or stream[i - 1] in b' \t\r\n[]'):
                try:
                    val = float(m.group())
                except ValueError:
                    val = None
                if val is not None:
                    if in_arr and val <= -100:
                        out.append(' ')
                    i += len(m.group()); continue
            if (65 <= c <= 90) or (97 <= c <= 122):
                m = re.match(rb"[A-Za-z*'\"]+", stream[i:i + 8])
                op = m.group()
                if op in (b'Td', b'TD', b'Tm', b'T*', b'ET'):
                    out.append('\n')
                i += len(op); continue
            i += 1
        return ''.join(out)

    parts = []
    for m in re.finditer(rb'stream\r?\n(.*?)\r?\nendstream', data, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompress(raw)
        except Exception:
            continue
        if b'BT' not in raw or (b'Tj' not in raw and b'TJ' not in raw):
            continue
        parts.append(process(raw))
    blob = '\n'.join(parts)
    blob = re.sub(r'[ \t]{2,}', ' ', blob)
    blob = re.sub(r'\n{2,}', '\n', blob)
    return blob


def extract_text(path):
    """返回 (text, engine)。优先第三方库，失败回退标准库。"""
    try:
        import fitz  # pymupdf
        doc = fitz.open(path)
        return '\n'.join(p.get_text() for p in doc), 'pymupdf'
    except Exception:
        pass
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return '\n'.join((p.extract_text() or '') for p in pdf.pages), 'pdfplumber'
    except Exception:
        pass
    try:
        from pdfminer.high_level import extract_text as _et
        return _et(path), 'pdfminer'
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        r = PdfReader(path)
        return '\n'.join((pg.extract_text() or '') for pg in r.pages), 'pypdf'
    except Exception:
        pass
    try:
        from PyPDF2 import PdfReader
        r = PdfReader(path)
        return '\n'.join((pg.extract_text() or '') for pg in r.pages), 'PyPDF2'
    except Exception:
        pass
    return _stdlib_text(path), 'stdlib'


# ---------------- 元数据启发式提取 ----------------
JOURNALS = [
    'Nature Communications', 'Nature Methods', 'Nature Biotechnology',
    'Nature Genetics', 'Nature Medicine', 'Nature Immunology', 'Nature Cell Biology',
    'Nature', 'Science Advances', 'Science', 'Cell Reports', 'Cell Stem Cell',
    'Cancer Cell', 'Developmental Cell', 'Molecular Cell', 'Genome Biology',
    'Genome Research', 'Nucleic Acids Research', 'Bioinformatics', 'PNAS', 'eLife',
    'ACM Computing Surveys', 'NeurIPS', 'ICML', 'ICLR', 'ACL', 'EMNLP', 'CVPR',
]
_BOILER = re.compile(
    r'^(article|research|letter|review|brief communication|perspective|'
    r'nature(\s+communications)?(\s*\|)|www\.|volume\b|check for updates|'
    r'https?://|\d+\s*$|[|·—–-]+$)', re.I)


def _lines(text):
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def find_doi(text):
    m = re.search(r'(10\.\d{4,9}/[^\s"\'<>]+)', text)
    if m:
        return m.group(1).rstrip('.,;)')
    return ''


def find_year(text):
    for pat in (r'Published[^0-9]*(20\d{2})', r'Accepted[^0-9]*(20\d{2})',
                r'Received[^0-9]*(20\d{2})'):
        m = re.search(pat, text, re.I)
        if m:
            return int(m.group(1))
    m = re.search(r'\b(20\d{2})\b', text[:2000])
    return int(m.group(1)) if m else ''


def find_venue(text):
    head = text[:2500]
    for j in sorted(JOURNALS, key=len, reverse=True):
        if re.search(r'\b' + re.escape(j) + r'\b', head):
            return j
    return ''


def _strip_sup(s):
    s = re.sub(r'\d+(?:[,\-]\d+)*', '', s)   # 去掉上标单位号 1,2,13
    s = s.replace('✉', '').replace('*', '').replace('\u2709', '')
    return s


AUTHOR_START = re.compile(r"^[A-Z][a-z]+ [A-Z][a-z]+")
AFF = re.compile(r'^\d+\s+[A-Z]')
SUP = re.compile(r'^[\d,.\-–—\s]+$')
SECTION = re.compile(
    r'^(introduction|here we|deciphering|in this study|colorectal cancer \(|'
    r'background|results|discussion)\b', re.I)


def _front_bounds(st):
    """返回 (a0, a_end)：作者区起止索引（基于 stripped 列表）。"""
    n = len(st)
    a0 = None
    for i in range(n):
        ln = st[i]
        if ln and not _BOILER.match(ln) and AUTHOR_START.match(ln):
            a0 = i
            break
    if a0 is None:
        return None, None
    a_end = n
    for i in range(a0, n):
        ln = st[i]
        if AFF.match(ln) or 'doi.org' in ln.lower() or 'received' in ln.lower():
            a_end = i
            break
        if len(ln) > 45 and not SUP.match(ln):   # 进入摘要/正文
            a_end = i
            break
    return a0, a_end


def parse_front(text):
    """返回 (title, authors[list])。尽力而为，务必核对。"""
    raw = text.splitlines()
    st = [ln.strip() for ln in raw]
    a0, a_end = _front_bounds(st)
    if a0 is None:
        a0 = a_end = 0
    title_src = [st[i] for i in range(a0) if st[i] and not _BOILER.match(st[i])]
    title = re.sub(r'\s+', ' ', ' '.join(title_src)).strip()
    joined = _strip_sup(''.join(raw[a0:a_end])).replace('&', ',')
    authors = []
    for piece in joined.split(','):
        name = re.sub(r'\s+', ' ', piece).strip(' .;')
        if 3 <= len(name) <= 40 and re.match(r"^[A-Za-z][A-Za-z.'\- ]+$", name):
            authors.append(name)
    seen = set()
    uniq = []
    for a in authors:
        if a.lower() not in seen:
            seen.add(a.lower())
            uniq.append(a)
    return title, uniq


def parse_abstract(text):
    """取作者区之后、正文之前的一段作为摘要（启发式）。"""
    raw = text.splitlines()
    st = [ln.strip() for ln in raw]
    a0, a_end = _front_bounds(st)
    if a0 is None:
        return ''
    buf = []
    total = 0
    for i in range(a_end, len(st)):
        s = st[i]
        if not s or SUP.match(s) or AFF.match(s):
            continue
        if SECTION.match(s) and total > 200:
            break
        buf.append(s)
        total += len(s)
        if total > 1400:
            break
    return re.sub(r'\s+', ' ', ' '.join(buf)).strip()


# ---------------- yml 生成 ----------------
def _initials(name):
    toks = [t for t in re.split(r'\s+', name.strip()) if t]
    if not toks:
        return name
    last = toks[-1]
    inits = ' '.join(t[0].upper() + '.' for t in toks[:-1])
    return (last + ', ' + inits) if inits else last


def _needs_quote(s):
    s = str(s)
    return (s[:1] in '*&!%@`#,[{>\'"|' or s != s.strip() or ': ' in s
            or s.endswith(':') or s == '' or s[:1] in '-?')


def _scalar(s):
    s = str(s)
    if _needs_quote(s):
        return "'" + s.replace("'", "''") + "'"
    return s


def _norm(name):
    return re.sub(r'[^a-z]', '', name.lower())


def build_yml(meta, me=''):
    title = meta['title']
    venue = meta['venue']
    year = meta['year']
    doi = meta['doi']
    me_n = _norm(me) if me else ''

    venue_disp = ('*' + venue + '*') if venue else venue

    author_lines = []
    initials_list = []
    for a in meta['authors']:
        disp = ('**' + a + '**') if (me_n and _norm(a) == me_n) else a
        author_lines.append('  - ' + _scalar(disp))
        initials_list.append(_initials(a))

    # citation
    if initials_list:
        auth_str = ', '.join(initials_list[:-1]) + (', & ' if len(initials_list) > 1 else '') + initials_list[-1] if len(initials_list) > 1 else initials_list[0]
    else:
        auth_str = '<作者，请补充>'
    if me:
        me_init = _initials(me)
        auth_str = auth_str.replace(me_init, '**' + me_init + '**')
    cite_venue = ('*' + venue + '*') if venue else '<venue>'
    doi_part = (' https://doi.org/' + doi) if doi else ''
    citation = '%s %s. %s (%s).%s' % (auth_str, title or '<title>', cite_venue, year or '<year>', doi_part)

    abstract = meta['abstract'] or '（请补充摘要）'

    out = []
    out.append('# 由 tool/pdf2yml.py 自动生成 —— 请对照 PDF 人工核对（作者/摘要可能有出入）')
    out.append('title: ' + _scalar(title or '<title，请核对>'))
    out.append('authors:')
    out.extend(author_lines or ['  - "<作者，请补充>'])
    out.append('venue: ' + _scalar(venue_disp or '<venue>'))
    out.append('year: ' + str(year or 0))
    out.append('citation: |')
    out.append('  ' + citation)
    out.append('abstract: |')
    for ln in _wrap(abstract, 90):
        out.append('  ' + ln)
    out.append('tags: []')
    out.append('')
    return '\n'.join(out)


def _wrap(text, width):
    words = text.split(' ')
    lines, cur = [], ''
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur); cur = w
        else:
            cur = (cur + ' ' + w).strip()
    if cur:
        lines.append(cur)
    return lines or ['']


# ---------------- CLI ----------------
def main():
    ap = argparse.ArgumentParser(description='从论文 PDF 生成 content/papers/<slug>.yml 草稿')
    ap.add_argument('pdf', help='PDF 路径')
    ap.add_argument('--out', default=None, help='输出目录（默认 <repo>/content/papers）')
    ap.add_argument('--slug', default=None, help='输出文件名（默认取 pdf 文件名）')
    ap.add_argument('--me', default='', help='本人姓名，自动在作者/引用中加粗')
    ap.add_argument('--force', action='store_true', help='覆盖已存在的 yml')
    ap.add_argument('--dump-text', default=None, help='把提取的纯文本另存到该路径')
    args = ap.parse_args()

    if not os.path.exists(args.pdf):
        sys.exit('找不到 PDF: ' + args.pdf)

    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_dir = args.out or os.path.join(repo, 'content', 'papers')
    os.makedirs(out_dir, exist_ok=True)
    stem = args.slug or os.path.splitext(os.path.basename(args.pdf))[0]
    out_path = os.path.join(out_dir, stem + '.yml')
    if os.path.exists(out_path) and not args.force:
        sys.exit('已存在 %s（用 --force 覆盖）' % out_path)

    text, engine = extract_text(args.pdf)
    if args.dump_text:
        with open(args.dump_text, 'w', encoding='utf-8') as f:
            f.write(text)

    title, authors = parse_front(text)
    meta = {
        'title': title,
        'authors': authors,
        'venue': find_venue(text),
        'year': find_year(text),
        'doi': find_doi(text),
        'abstract': parse_abstract(text),
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(build_yml(meta, args.me))

    print('引擎: %s' % engine)
    print('已生成: %s' % out_path)
    print('  标题: %s' % (meta['title'] or '(未识别)'))
    print('  作者: %d 位' % len(meta['authors']))
    print('  出处: %s  年份: %s  DOI: %s' % (meta['venue'] or '?', meta['year'] or '?', meta['doi'] or '?'))
    print('请打开 yml 对照 PDF 核对作者与摘要。')


if __name__ == '__main__':
    main()
