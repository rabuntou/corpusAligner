#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

def show_sims_all(sims, f=sys.stderr):
    '類似度全表示'
    for j in sims:
        for k in sims[j]:
            for jj in sims[j][k]:
                for kk in sims[j][k][jj]:
                    print(j, k, jj, kk, sims[j][k][jj][kk], file=f)

def make_db(ws, mode):
    '類似度計算用の語彙作成'
    data = defaultdict(int)
    for w in ws:
        ww = w.split(' ')
        if (mode == "ja"):
            ww = list(set(ww))
        for www in ww:
            data[www] += 1
    return data

def get_sim(jas, kos, aid):
    '１文の類似度計算'
    dja = make_db(jas, "ja")
    dko = make_db(kos, "ko")
    num = 0 # 類似度計算分子（の1/2倍）
    for ko in kos:
        if ko in dja and dja[ko] > 0 and dko[ko] > 0:
            num += 1 / (dja[ko] * dko[ko]) # dko[ko] は一致する語のカウント
            dja[ko] -= 1 # 一度使ったらデクリメント
            dko[ko] -= 1 # 一度使ったらデクリメント

    if len(jas) + len(kos) == 0:
        # print('warning: get_sim: no items:', aid, file=sys.stderr) # デバッグ用
        return 0
    sim = 0
    if num > min(len(jas), len(kos)):
        num = min(len(jas), len(kos))
    if len(jas) > len(kos):
        sim = 2 * num / (len(jas) + len(kos)) # 類似度計算
    else:
        sim = num / len(kos) # 類似度計算 
    sim = int(sim * 1000) / 10 # 100倍して丸める
    return sim

def get_sim_range(jass, koss, js, ks, len0, aid):
    '１文対複数文の類似度計算'
    jas = []
    kos = []
    for j in js:
        jas += jass[j]
    for k in ks:
        kos += koss[k]

    sim  = get_sim(jas, kos, aid) 
    #if len(js) == 1 and len(ks) == 1:
    #    if (js[0] == ks[0] ):
    #print("x:", sim,  js, ks, len(jas), jas, len(kos), kos)
    ### ここでperl版にはスコア補正があったが、使用していないので省略
    return sim    

def get_sim_set(jass, koss, j, k, d, aid):
    '''
    ある位置の１文対複数文の類似度のセット計算
    第５引数は、複数文の増分（5なら、最大1+5=6文までまとめて計算する）
    '''

    data = defaultdict(dict)
    len0 = (len(jass[j]) + len(koss[k])) / 2 # １文どうしの際の長さの平均
    data[0][0] = get_sim_range(jass, koss, [j], [k], len0, aid)
    
    # １文対１文に相関がない場合は、そこから伸びる全てのノードの類似度を半分にする
    # 類似度を0ににしてしまうと経路が見つからない場合があった（例えば 200102 2387788）
    # 前向きアルゴリズムのバグだと思われるが、回避のためいったんこうしておく(2018.02.13)
    ### 以上、perl版より転記（おそらく未解決）
    
    fl_cancel = True if data[0][0] == 0 else False
    
    js = [j]
    for jj in range(1, d + 1):
        if j - jj >= 0:
            js.insert(0, j - jj)
            sim_range = get_sim_range(jass, koss, js, [k], len0, aid)
            data[jj][0] = sim_range / 2 if fl_cancel else sim_range # 回避
        else:
            break
    ks = [k]
    for kk in range(1, d + 1):
        if k - kk >= 0:
            ks.insert(0, k - kk)
            sim_range = get_sim_range(jass, koss, [j], ks, len0, aid)
            data[0][kk] = sim_range / 2 if fl_cancel else sim_range # 回避
    return dict(data) 

def get_all_sims(jass, koss, aid):
    '類似度計算'
    
    if len(jass) == 0 or len(koss) == 0:
        return dict()
    
    jwidth = 5 # 計算範囲の日本語側の幅
    kwidth = int(jwidth * len(koss) / len(jass) + 0.5) # 韓国語側の幅
    sims = defaultdict(dict) # ２次元のdictを作る
    for j in range(len(jass)):
        k0 = int(j * len(koss) / len(jass) + 0.5)
        k1 = k0 - kwidth if k0 - kwidth > 0 else 0
        k2 = k0 + kwidth if k0 + kwidth < len(koss) - 1 else len(koss) - 1
        for k in range(k1, k2 + 1):
            if not j in sims or not k in sims[j]:
                sims[j][k] = get_sim_set(jass, koss, j, k, 20, aid)

    return dict(sims)

