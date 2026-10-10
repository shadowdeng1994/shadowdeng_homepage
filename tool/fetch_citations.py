#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_citations.py —— 按 DOI 抓取论文引用数，写回 content/papers/*.yml。

数据来源（免费、无需 API key）：
    - OpenAlex（默认，https://api.openalex.org）
    - Crossref（备选，is-referenced-by-count）

说明：Web of Science 需付费 API Key、Google Scholar 无官方 API 且禁止抓取，
因此这里用开放数据源；数字通常低于 Google Scholar。抓取结果写入 yml 的
`citations` 与 `citations_updated` 字段，由 update.py 在构建时读取展示。

用法：
    python tool/fetch_citations.py                # 用 OpenAlex（失败回退 Crossref）
    python tool/fetch_citations.py --source crossref
"""
import os
import re
import sys
import json
import socket
import datetime
import argparse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAPERS = os.path.join(ROOT, 'content', 'papers')
UA = 'shadowdeng-homepage/1.0 (mailto:dengshj8@mail.sysu.edu.cn)'


def _get_json(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode('utf-8'))


def openalex_count(doi):
    j = _get_json('https://api.openalex.org/works/doi:' + doi)
    return int(j.get('cited_by_count') or 0)


def crossref_count(doi):
    j = _get_json('https://api.crossref.org/works/' + doi)['message']
    return int(j.get('is-referenced-by-count') or 0)


def count_for(doi, source):
    order = ['openalex', 'crossref'] if source == 'openalex' else ['crossref', 'openalex']
    last = None
    for src in order:
        try:
            n = openalex_count(doi) if src == 'openalex' else crossref_count(doi)
            return n, src
        except Exception as e:  # noqa: BLE001
            last = e
    raise RuntimeError(str(last))


def set_fields(raw, n, today):
    cit = 'citations: %d' % n
    upd = 'citations_updated: %s' % today
    if re.search(r'^citations:', raw, re.M):
        raw = re.sub(r'^citations:.*$', cit, raw, count=1, flags=re.M)
        if re.search(r'^citations_updated:', raw, re.M):
            raw = re.sub(r'^citations_updated:.*$', upd, raw, count=1, flags=re.M)
        else:
            raw = re.sub(r'^(citations:.*)$', r'\1\n' + upd, raw, count=1, flags=re.M)
    elif re.search(r'^doi:', raw, re.M):
        raw = re.sub(r'^(doi:.*)$', r'\1\n' + cit + '\n' + upd, raw, count=1, flags=re.M)
    else:
        raw = raw.rstrip() + '\n' + cit + '\n' + upd + '\n'
    return raw


def main():
    ap = argparse.ArgumentParser(description='抓取论文引用数写回 yml')
    ap.add_argument('--source', choices=['openalex', 'crossref'], default='openalex')
    ap.add_argument('--timeout', type=int, default=30)
    args = ap.parse_args()
    socket.setdefaulttimeout(args.timeout)
    today = datetime.date.today().isoformat()

    files = sorted(f for f in os.listdir(PAPERS) if f.endswith('.yml'))
    ok = 0
    for name in files:
        path = os.path.join(PAPERS, name)
        raw = open(path, encoding='utf-8').read()
        m = re.search(r'^doi:\s*(\S+)', raw, re.M)
        if not m:
            print('skip  %-20s (no doi)' % name)
            continue
        doi = m.group(1)
        try:
            n, src = count_for(doi, args.source)
        except Exception as e:  # noqa: BLE001
            print('fail  %-20s %s -> %s' % (name, doi, e))
            continue
        open(path, 'w', encoding='utf-8').write(set_fields(raw, n, today))
        ok += 1
        print('ok    %-20s cited_by=%-5d (%s)' % (name, n, src))
    print('updated %d/%d files' % (ok, len(files)))


if __name__ == '__main__':
    main()
