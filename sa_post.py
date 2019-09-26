#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

from sa_g import *
#出力necoding をUTF-8に強制設定
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')

def print_2Dlist(data, f):
    if len(data) > 0:
        print(*('\t'.join(row) for row in data if len(row) > 0), sep='\n', file=f)

def print_filter_sub(rows, fl_donga, thresh_sc, thresh_ratio, ratio=1.0):
    '''
    タイトル行はthresh_sc以上に
    それ以外は、1/rate~rateの文字数比になるようにする
    ratioは、補正係数
    '''
    data = []
    i2 = 0
    for aid, i, ij, ik, sc, ja, ko in rows:
        r = len(ja) / len(ko) / ratio
        ii = ij + '-' + ik
        if r > 1 / thresh_ratio and r < thresh_ratio:
            if fl_donga and i == '0': # タイトル行
                if float(sc) >= thresh_sc:
                    data.append([aid, str(i2), ii, sc, ja, ko])
                    i2 += 1
                #else:
                    #r = int(r * 100 + 0.5) / 100
                    #print('error:\t', aid, i, ij, ik, sc, r, ja, ko, sep='\t', file=sys.stderr)
            elif float(sc) >= thresh_sc: # コンテンツ行も類似度を制限
                data.append([aid, str(i2), ii, sc, ja, ko])
                i2 += 1
        #else:
        #    print(len(ja), len(ko), sc, ja ,ko)
        #else:
            #r = int(r * 100 + 0.5) / 100
            #print(aid, i, ij, ik, sc, r, ja, ko, sep='\t', file=sys.stderr)
    return data
            
def print_filter(sa, my_env, f):
    '''
    複数文をつなぐ
    '''
    s_sep = ' ' # 後でオプション化する！！
    data = []
    i = 0
    for aid, j, k, sc, ja, ko in sa:
        if len(j) == 0 or len(k) == 0 or len(sc) == 0 or len(ja) == 0:
            continue
        if j != g_none and k != g_none:
            if j == g_same:
                data[len(data) - 1][6] += s_sep + ko
                data[len(data) - 1][3] = str(int(data[len(data) - 1][3]) + 1) # 文数のインクリメント
            elif k == g_same:
                data[len(data) - 1][5] += s_sep + ja
                data[len(data) - 1][2] = str(int(data[len(data) - 1][2]) + 1) # 文数のインクリメント
            else:
                data.append([aid, str(i), str(1), str(1), sc, ja, ko])
                i += 1
    fl_donga = True if 'donga' in my_env else False
    data2 = print_filter_sub(data, fl_donga, thresh_sc=20, thresh_ratio=3.0, ratio=1/3) #ratio=59/61 日韓
    print_2Dlist(data2, f=f)
