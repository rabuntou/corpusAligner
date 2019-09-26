#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

from sa_sim import show_sims_all, get_all_sims, get_sim
from sa_core import compute_sim_matrix
from sa_post import print_filter, print_2Dlist

def print_output(o_form, senj, senk, aid, my_env, sa):
    '''
    表示形式を出力
    東亜日報の場合は文IDをインクリメント
    '''

    for j, k, sc, ja, ko in o_form:
        if ja == 'ja':
            ja = senj[j]
        if ko == 'ko':
            ko = senk[k]
        ja = ja.strip()
        ko = ko.strip()
        # コンテンツは1-スタートなので数字の場合はインクリメントする
        if 'donga' in my_env:
            if re.match(r'^\d+$', str(j)):
                j += 1
            if re.match(r'^\d+$', str(k)):
                k += 1
        s_sc = str(sc) ### perlに合わせる　100.0 => 100 など
        if s_sc.endswith('.0'): ###
            s_sc = s_sc[:-2] ###
        sa.append([aid, str(j), str(k), s_sc, ja, ko])
    
def s_align(aid, senj, senk, jass, koss, my_env):
    '''
    文アラインメントのメイン関数
    calc_sim_noun.py の main_all() をアレンジしている
    入力：記事ID（表示用）、日本語文（表示用）、韓国語文（表示用）、日本語解析結果の韓国語訳、韓国語解析結果
    東亜日報の場合は、タイトル行を別扱い
    '''    
    # 最初のタイトル行は別扱い（アラインメントに参加させず、類似度のみ求める）
    jas_ttl = []
    kos_ttl = []
    sim_ttl = 0
    if 'donga' in my_env:
        jas_ttl = jass.pop(0)
        kos_ttl = koss.pop(0)
        sim_ttl = get_sim(jas_ttl, kos_ttl, aid)
    
    # 類似度計算
    sims = get_all_sims(jass, koss, aid)
#    show_sims_all(sims) # 類似度全表示

    # 類似度マトリックスから格子構造を作り最適パスを算出、それを出力形式に変換
    # （言語対に依存しないコアの処理をまとめたもの）
    len_jass = len(jass)
    len_koss = len(koss)
    o_form = compute_sim_matrix(aid, sims, len_jass, len_koss)
#    print(o_form) #只显示对齐了的 1行对1行
    
    # 先にタイトル部分を出力
    sa = []
    if 'donga' in my_env:
        senj_ttl = senj.pop(0)
        senk_ttl = senk.pop(0)
        s_sim_ttl = str(sim_ttl) ### perlに合わせる　100.0 => 100 など
        if s_sim_ttl.endswith('.0'): ###
            s_sim_ttl = s_sim_ttl[:-2] ###    
        sa.append([aid, '0', '0', s_sim_ttl, senj_ttl, senk_ttl])
    # コンテンツ部分のアラインメントを出力
    if len(o_form) > 0:
        print_output(o_form, senj, senk, aid, my_env, sa)
    else:
        print('warning: no alignment:', aid, file=sys.stderr)        
    return sa

