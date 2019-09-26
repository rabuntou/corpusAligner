#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

from sa_g import *
from sa_5c import *

def div_cell(src):
    src = re.sub(r'(。)+', '\\1\n', src)
    src = re.sub(r'(\.\s?)+ ', '\\1 \n', src)
    elms = [el for el in re.split(r'\s*\n\s*', src) if len(el) > 0]
    return elms

def is_english(s):
    s = re.sub(r'[\p{S}\p{P}\s]+', '', s)
    if len(s) == len(s.encode('utf8')):
        return True
    return False

def pre_copy_each(fn, fn_out, fl_donga, fl_nodiv, fl_ja=False):
    '''
    前処理はここでする
    '''
    with open(fn, 'r', encoding='utf-8', errors='replace') as f:
        with open(fn_out, 'w', encoding='utf-8') as f_out:
            tbl_5c = make_5c_tbl() if fl_ja else None #英日文字化け処理は不要???
            for i, ln in enumerate(f):
                ln = re.sub(r'\s+', ' ', ln).strip()
                #if is_english(ln): # 英語行は排除する（日韓）
                #    continue
                if (i == 0 and  fl_donga) or fl_nodiv:
                    ss = [ln] #　タイトル別扱いの時は、タイトルの文分割をしない
                else:
                    ss = div_cell(ln) # さらに文分割
                for s in ss:
                    if fl_ja:
                        s = search_5c_tbl(s, tbl_5c)
                    if len(s) > 0 and not re.match(r' $', s):
                        print(s, file=f_out)

def pre_proc(d, aid, my_env):
    '''
    RAMディスクにコピーもしくは前処理したファイルを起き、ファイル名を返す
    後で削除すること
    '''
    d_tmp = my_env['ramdisk']
    fl_donga = True if 'donga' in my_env else False
    fl_nodiv = True if 'no_div' in my_env else False
    t = time.time()
    tt = str(t - int(t))[-6:] # ファイル名を一意的にするための追加文字列
    fn_ja = d + '/' + aid + '.ja'
    fn_ja2 = d_tmp + '/' + aid + '.' + tt + '.ja'
    pre_copy_each(fn_ja, fn_ja2, fl_donga, fl_nodiv, fl_ja=True)
    fn_ko = d + '/' + aid + '.en'
    fn_ko2 = d_tmp + '/' + aid + '.' + tt + '.en'
    pre_copy_each(fn_ko, fn_ko2, fl_donga, fl_nodiv)
    return fn_ja2, fn_ko2

