#!/usr/bin/env python
# s_align_jk.0.py に辞書データを内包させ、
# s_align_jk.py として出力

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

import gzip

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    argv = sys.argv
    if len(argv) != 2 or not argv[1].endswith('dic.txt') or not os.path.isfile(argv[1]):
        print('dic.txt is needed', file=sys.stderr)
        return

    fn = argv[1]
    with open(fn, 'r', encoding='utf-8') as f:
        s = f.read().encode('utf-8')
        m = gzip.compress(s)
        mmm = b'KDS1' + m[4:]
        with open('s_align_jk.0.py', 'r', encoding='utf-8') as f4:
            with open('s_align_jk.py', 'w', encoding='utf-8') as f5:
                for i, ln in enumerate(f4):
                    ln = ln.rstrip()
                    if i == 1: # 2行目に辞書データを挿入
                        print('mmm=', end='', file=f5)
                        print(mmm, file=f5)
                    else:
                        print(ln, file=f5)

if __name__ == '__main__':
    main()
