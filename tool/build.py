#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build.py —— 一键：把 sources/ 里的手改内容转成 content/ 数据，再生成站点。

你只需要维护 sources/（下面四个部分）：
    sources/about/info.yml       个人简介 / 信息（可选 avatar.jpg 头像）
    sources/papers/*.pdf           文章：只放 PDF
    sources/news/*.docx            新闻：只放 Word
    sources/software.txt           软件：只维护仓库链接清单（每行一个）
    （sources/research/*.yml）     研究方向卡片（通常不动）

本脚本会自动：
    1. 对 sources/papers 里还没有 yml 的 PDF 运行 tool/pdf2yml.py（生成 content/papers/<slug>.yml）；
    2. 对 sources/news 里还没有 md 的 Word 运行 tool/word2news.py（生成 content/news/<日期>.md + 图片）；
    3. 运行 tool/fetch_software.py（按清单生成 content/software/*.yml 与 README）；
    4. 运行 update.py 生成站点（update.py 默认还会刷新论文引用数）。

用法：
    python tool/build.py            # 全流程
    python tool/build.py --no-net   # 跳过联网步骤（引用数、软件抓取），仅本地已有数据出站
"""
import os
import re
import sys
import glob
import argparse
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOL = os.path.join(ROOT, 'tool')
SOURCES = os.path.join(ROOT, 'sources')
CONTENT = os.path.join(ROOT, 'content')
PY = sys.executable


def run(args):
    print('> ' + ' '.join(args))
    subprocess.check_call(args)


def derive_date(stem):
    m = re.match(r'(\d{4})-?(\d{2})-?(\d{2})', stem)
    return '%s-%s-%s' % m.groups() if m else None


def main():
    ap = argparse.ArgumentParser(description='一键转换 sources/ 并生成站点')
    ap.add_argument('--me', default='Shanjun Deng', help='pdf2yml 加粗的本人姓名')
    ap.add_argument('--no-net', action='store_true', help='跳过联网步骤（软件抓取 / 引用数）')
    args = ap.parse_args()

    # 1) papers: sources/papers/*.pdf -> content/papers/*.yml
    for pdf in sorted(glob.glob(os.path.join(SOURCES, 'papers', '*.pdf'))):
        slug = os.path.splitext(os.path.basename(pdf))[0]
        yml = os.path.join(CONTENT, 'papers', slug + '.yml')
        if not os.path.exists(yml):
            run([PY, os.path.join(TOOL, 'pdf2yml.py'), pdf, '--me', args.me])

    # 2) news: sources/news/*.docx -> content/news/<date>.md (+ 图片)
    for docx in sorted(glob.glob(os.path.join(SOURCES, 'news', '*.docx'))):
        stem = os.path.splitext(os.path.basename(docx))[0]
        date = derive_date(stem)
        md = os.path.join(CONTENT, 'news', (date or stem) + '.md')
        if not os.path.exists(md):
            run([PY, os.path.join(TOOL, 'word2news.py'), docx])

    # 3) software
    if not args.no_net and os.path.exists(os.path.join(SOURCES, 'software.txt')):
        run([PY, os.path.join(TOOL, 'fetch_software.py')])

    # 4) build
    cmd = [PY, os.path.join(ROOT, 'update.py')]
    if args.no_net:
        cmd.append('--no-citations')
    run(cmd)

    print('\n完成。生成站点在仓库根目录。')


if __name__ == '__main__':
    main()
