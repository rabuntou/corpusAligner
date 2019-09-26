#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

import gzip

def read_sysdic(fn):
    '''高電社日韓システム辞書の読み込み：複数の韓国語訳はリストにする'''
    dic = defaultdict(list)
    with open(fn, 'r', encoding='utf-8') as f:
        for ln in f:
            j, k = ln.rstrip().split('\t')
            dic[j].append(k)
            #dic[k].append(j)
    return dic

def read_sysdic_bin(fn):
    '''バイナリ化した高電社日韓システム辞書の読み込み：複数の韓国語訳はリストにする'''
    dic = defaultdict(list)
    with open(fn, 'rb') as f:
        m = f.read()
        m = b'\x1f\x8b\x08\x08' + m[4:]
        lns = gzip.decompress(m).decode('utf-8').split('\n')
        for ln in lns:
            tpl = ln.split('\t')
            if len(tpl) == 2:
                j, k = tpl
                dic[j].append(k)

    return dic

def read_sysdic_bin_int(mmm):
    '''バイナリ化した高電社日韓システム辞書の読み込み：複数の韓国語訳はリストにする'''
    dic = defaultdict(list)
    m = b'\x1f\x8b\x08\x00' + mmm[4:]
    lns = gzip.decompress(m).decode('utf-8').split('\n')
    for ln in lns:
        tpl = ln.split('\t')
        if len(tpl) == 2:
            j, k = tpl
            dic[j].append(k)
    return dic

