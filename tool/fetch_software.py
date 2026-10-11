#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fetch_software.py —— 按 softwarelist.txt 抓取 GitHub 仓库信息与 README。

用途：为「软件」卡片准备素材——把仓库的简介、语言、主题，以及 **README 全文**抓下来，
便于人工/AI 理解这个包是干什么的，从而写更好的中英双语卡片介绍。

用法：
    python tool/fetch_software.py [--list content/software/softwarelist.txt]
                                  [--out content/software] [--write-draft] [--force]

- 默认把每个仓库的 README 保存为 content/software/<slug>.readme.md（供参考，不会被读取渲染）。
- --write-draft 会额外生成 content/software/<slug>.yml 草稿（标题/链接/语言取自仓库，
  description_en 取自仓库简介；中文描述留空，需人工/AI 补齐）。已存在的 yml 需 --force 覆盖。
- GitHub 未认证 API 限速 60 次/小时；公开仓库无需 token。
"""
import os
import re
import sys
import json
import base64
import socket
import argparse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = 'shadowdeng-homepage/1.0'


def api(path):
    req = urllib.request.Request('https://api.github.com' + path,
                                 headers={'User-Agent': UA, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode('utf-8'))


def parse_repos(list_path):
    repos = []
    for line in open(list_path, encoding='utf-8'):
        line = line.strip()
        m = re.search(r'github\.com/([^/\s]+)/([^/\s#?]+)', line)
        if m:
            repos.append((m.group(1) + '/' + m.group(2)).rstrip('/'))
    return repos


def slug_of(full):
    return full.split('/')[1].lower().replace('.', '_')


def scalar(s):
    s = str(s)
    if s == '' or s != s.strip() or re.search(r'[:#\[\]{}&*!|>\'"%@`,]', s) or s[0] in '-?':
        return "'" + s.replace("'", "''") + "'"
    return s


def main():
    ap = argparse.ArgumentParser(description='抓取 GitHub 仓库信息与 README')
    ap.add_argument('--list', default=os.path.join(ROOT, 'content', 'software', 'softwarelist.txt'))
    ap.add_argument('--out', default=os.path.join(ROOT, 'content', 'software'))
    ap.add_argument('--write-draft', action='store_true')
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    socket.setdefaulttimeout(30)

    repos = parse_repos(args.list)
    for i, full in enumerate(repos, 1):
        slug = slug_of(full)
        try:
            repo = api('/repos/' + full)
        except Exception as e:  # noqa: BLE001
            print('fail %s -> %s' % (full, e))
            continue
        name = repo.get('name')
        desc = repo.get('description') or ''
        lang = repo.get('language') or ''
        topics = repo.get('topics') or []
        print('== %s' % full)
        print('   name=%s  lang=%s  stars=%s' % (name, lang or '?', repo.get('stargazers_count')))
        print('   desc=%s' % desc)
        print('   topics=%s' % topics)

        # README
        try:
            rm = api('/repos/%s/readme' % full)
            text = base64.b64decode(rm['content']).decode('utf-8', 'replace')
            open(os.path.join(args.out, slug + '.readme.md'), 'w', encoding='utf-8').write(text)
            print('   README saved: %s (%d chars)' % (slug + '.readme.md', len(text)))
        except Exception as e:  # noqa: BLE001
            print('   README fail: %s' % e)

        if args.write_draft:
            path = os.path.join(args.out, slug + '.yml')
            if os.path.exists(path) and not args.force:
                print('   yml exists, skip (use --force): %s' % path)
                continue
            lines = ['order: %d' % i,
                     'title: ' + scalar(name),
                     'title_en: ' + scalar(name),
                     'description: ' + scalar(''),  # 待人工/AI 翻译
                     'description_en: ' + scalar(desc),
                     'url: https://github.com/' + full,
                     'language: ' + scalar(lang)]
            lines.append('tags: []')
            lines.append('tags_en:')
            for t in topics:
                lines.append('  - ' + scalar(t))
            open(path, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
            print('   draft written: %s' % path)


if __name__ == '__main__':
    main()
