#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

from functools import cmp_to_key

from sa_g import *

def show_lattice(lat):
    '格子のデバッグ表示'
    for j in lat:
        dt0 = lat[j]
        for k in dt0:
            dt = dt0[k]
            total = dt[0]
            score = dt[1][0][0]
            pr_j = dt[1][0][1][0]
            pr_k = dt[1][0][1][1]
            print(j, k, total, score, pr_j, pr_k, file=sys.stderr)

def do_forward(sims):
    '前向きアルゴリズム'
    lat = defaultdict(dict) # 格子構造
    for j in sims:
        for k in sims[j]:
            ss = sims[j][k]
            total_max = 0 # 累積スコア最大値
            pres = [] # [自ノードのスコア, 前ノード座標]のリスト： [[sim1, [pre1_j, pre1_k]], ...]
            # jj、kkは今のノード位置からの戻りオフセット
            for jj in ss:
                for kk in ss[jj]:
                    s = ss[jj][kk] # 現ノードの類似度
                    j_pre, k_pre = j - jj - 1, k - kk - 1 # 前ノード座標
                    s_pre = lat[j_pre][k_pre][0] if k_pre in lat[j_pre] else 0 # 前ノードまでの累積スコア
                    pre = [j_pre, k_pre] if k_pre in lat[j_pre] else [-1, -1]
                    if s + s_pre > total_max:
                        total_max = s + s_pre
                        pres = [[s, [j_pre, k_pre]]]
                    elif s + s_pre == total_max:
                        pres.append([s, [j_pre, k_pre]])
            total_max = int(total_max * 10) / 10
            lat[j][k] = [total_max, pres]
            #fl = '*' if len(pres) > 1 else '' # 前ノードが複数ある場合
            #print(j, k, max, pres[0][0], pres[0][1][0], pres[0][1][1], fl, file=sys.stderr)
    return lat

def find_max_score(lat):
    '後ろ向きアルゴリズムのスタート地点を探す'
    ret = tuple() # トータルスコア最大地点のデータ
    total_max = 0
    for j in sorted(lat.keys(), reverse=True):
        dt0 = lat[j]
        for k in dt0:
            dt = dt0[k]
            total = dt[0]
            if total_max < total:
                score = dt[1][0][0]
                pr_j = dt[1][0][1][0]
                pr_k = dt[1][0][1][1]
                ret = j, k, total, score, pr_j, pr_k
                total_max = total
    return ret    

def get_better_inner_pair_sub(j, k, jp, kp):
    '''
    43, 42 -> 42, 39 から次の列を生成する
    　43,42,0,0
      43,42,0,1
      43,42,0,2
      43,41,0,0
      43,41,0,1
      43,40,0,0
    '''
    d_j = j - jp - 1
    d_k = k - kp - 1
    data = []
    for d in range(d_j + d_k + 1):
        start = int(j - d_j * d / (d_j + d_k))
        end = int(k - d_k * d / (d_j + d_k))
        for dd in range(d_j + d_k - d + 1):
            dd_j = int(d_j * dd / (d_j + d_k))
            dd_k = int(d_k * dd / (d_j + d_k))
            data.append([start, end, dd_j, dd_k])
    return data

def get_better_inner_pair(sims, j, k, sc, jp, kp):
    '''
    １文対複数文の時は、内部にもっと良い組み合わせがないか調べる
    　より良いスコアが存在する場合は以下を返す
       [スコア,起点のj座標,起点のk座標,jをいくつ戻るか,kをいくつ戻るか]
      より良いスコアが存在しない場合は、空の配列 [] を返す
    '''
    args = get_better_inner_pair_sub(j, k, jp, kp)
    sc_max = sc
    argmax = []
    for a0, a1, a2, a3 in args:
        if a0 in sims and a1 in sims[a0] and a2 in sims[a0][a1] and a3 in sims[a0][a1][a2]:
            sc2 = sims[a0][a1][a2][a3]
            if sc2 > sc_max:
                sc_max = sc2
                argmax = [a0, a1, a2, a3]
    if sc_max != sc:
        return [sc_max, *argmax]
    else:
        return []
    
def do_backward(lat, sims):
    '後ろ向きアルゴリズム（複数パスは想定していない）'
    path = []
    start = find_max_score(lat) # j, k, total, score, pr_j, pr_k
    if len(start) != 6:
        return path
    j = start[0]
    k = start[1]
    while True:
        if j in lat and k in lat[j]:
            nd = lat[j][k]
            sc_sum = nd[0]
            sc = nd[1][0][0]
            pre = nd[1][0][1]
            # １文対複数文の時は、内部にもっと良い組み合わせがないか調べる
            pair = []
            if j - pre[0] > 1 or k - pre[1] > 1:
                # より良いスコアが存在する場合は以下を返す
                #  [スコア,起点のj座標,起点のk座標,jをいくつ戻るか,kをいくつ戻るか]
                # より良いスコアが存在しない場合は、空の配列 [] を返す
                pair0 = get_better_inner_pair(sims, j, k, sc, *pre)
                if len(pair0) == 5:
                    sc2, j2, k2, jb, kb = pair0
                    pair = [j2, k2, sc2, j2 - jb - 1, k2 - kb - 1]
            path.insert(0, [j, k, sc, *pre, *pair])
            j, k = pre[:2]
        else:
            #print('Error', file=sys.stderr)
            break
        if j == -1 or k == -1:
            break
    return path

def node2lines(j, k, sc, jp, kp):
    '''
    43,42->42,39(j,k,jp,kp)から次の列(jj,kk)を生成
     43,40
     43,41
     43,42
    '''
    d_j = j - jp - 1
    d_k = k - kp - 1
    dd_j = 0 if d_j + d_k == 0 else int(d_j / (d_j + d_k))
    dd_k = 0 if d_j + d_k == 0 else int(d_k / (d_j + d_k))
    jjp = -1
    kkp = -1
    data = []
    for d in range(d_j + d_k + 1):
        jj = jp + 1 + d * dd_j
        kk = kp + 1 + d * dd_k
        data.append([g_same if jj == jjp else jj,
                     g_same if kk == kkp else kk,
                     sc if d == 0 else g_same,
                     g_same if jj == jjp else 'ja',
                     g_same if kk == kkp else 'ko'])
        jjp = jj
        kkp = kk
    return data

def get_outsiders(nd):
    'パスのノードから対応付けに参加しないIDを見つける'
    j, k, _, jp, kp, j2, k2, _, jp2, kp2 = nd
    os = defaultdict(dict)
    for jj in range(jp + 1, j + 1):
        if jj < jp2 + 1 or jj > j2:
            if jj in os['j']:
                os['j'][jj] += 1
            else:
                os['j'][jj] = 1
    for kk in range(kp + 1, k + 1):
        if kk < kp2 + 1 or kk > k2:
            if kk in os['k']:
                os['k'][kk] += 1
            else:
                os['k'][kk] = 1
    return dict(os)

def mycmp(a, b):
    '基本のcmp関数'
    if a < b: return -1
    elif a == b: return 0
    elif a > b: return 1

def mycmpitem(a, b):
    'perl的なcmp関数'
    if a[0] is not None and b[0] is not None and a[0] != g_same and b[0] != g_same and a[0] != g_none and b[0] != g_none:
        if mycmp(a[0], b[0]) != 0:
            return mycmp(a[0], b[0])
    return mycmp(a[1], b[1])

def path2output(path):
    'パスを出力形式に変換'
    data = []
    for nd in path:
        j, k, sc, jp, kp, *rest = nd
        if sc == 0: # 対応付けできない文
            for i in range(jp + 1, j + 1):
                data.append([i, g_none, g_none, 'ja', g_none])
            for i in range(kp + 1, k + 1):
                data.append([g_none, i, g_none, g_none, 'ko'])
        else:
            # １文対１文
            if len(rest) == 0:
                dt = node2lines(j, k, sc, jp, kp)
                data += dt
            # １文対複数文のブロック
            elif len(rest) == 5:
                j2, k2, sc2, jp2, kp2 = rest
                data2 = []
                # ブロックの中に対応付けにふさわしくない文を除く（ブロックとは分けて表示する）
                os = get_outsiders(nd)
                if 'j' in os:
                    for i in sorted(os['j']):
                        data2.append([i, None, g_none, 'ja', g_none])
                if 'k' in os:
                    for i in sorted(os['k']):
                        data2.append([None, i, g_none, g_none, 'ko'])
                    
                dt2 = node2lines(j2, k2, sc2, jp2, kp2)
                data2 += dt2
                
                # ブロック内をソートする
                data3 = sorted(data2, key=cmp_to_key(mycmpitem))
                for i in range(0, len(data3)):
                    if data3[i][0] is None:
                        data3[i][0] = g_none
                    if data3[i][1] is None :
                        data3[i][1] = g_none
                data += data3
    return data

def pickup_uleft_lright(o_form, aid, len_jass, len_koss):
    '左上と右下にパスに参加していないノード（文）があれば表示形式に追加'
    j_min = min(nd[0] for nd in o_form if isinstance(nd[0], int))
    k_min = min(nd[1] for nd in o_form if isinstance(nd[1], int))
    uleft = []
    for j in range(j_min):
        uleft.append([j, g_none, g_none, 'ja', g_none])
    for k in range(k_min):
        uleft.append([g_none, k, g_none, g_none, 'ko'])
    
    j_max = max(nd[0] for nd in o_form if isinstance(nd[0], int))
    k_max = max(nd[1] for nd in o_form if isinstance(nd[1], int))
    lright = []
    for j in range(j_max + 1, len_jass):
        lright.append([j, g_none, g_none, 'ja', g_none])
    for k in range(k_max + 1, len_koss):
        lright.append([g_none, k, g_none, g_none, 'ko'])
    
    # 連結によって o_form は新しい変数になるので、呼び出し元は変更されない
    # ここは「参照渡し」のperlとは違うので注意！（なので、returnする）
    if len(uleft) > 0:
        o_form = uleft + o_form
    if len(lright) > 0:
        o_form = o_form + lright        
    return o_form

def compute_sim_matrix(aid, sims, len_jass, len_koss):
    '''文アラインメントのコア部分'''    
    # 前向きアルゴリズム：格子構造の作成
    lat = do_forward(sims)
#    show_lattice(lat) # 格子の表示 显示所有累计 含复数对复数

    # 後ろ向きアルゴリズム：最適パスの算出
    ### パスのノードは以下のように10要素からなる：
    ###  ブロック右下のj,k座標、ブロックのスコア、次のブロックの右下のj,k座標
    ###  （さらに、以下は１文対複数文で内部により良いスコアのサブブロックがある時に付加）
    ###   より良いスコア、サブブロックの右下のj,k座標、サブブロックの左上に隣接するj,k座標
    path = do_backward(lat, sims)
    
    # 最適パスを出力形式に変換
    o_form = []
    if len(path) > 0:
        o_form = path2output(path)
    
    # 左上と右下にパスに参加していないノード（文）があれば表示形式に追加
    if len(o_form) > 0:
        o_form = pickup_uleft_lright(o_form, aid, len_jass, len_koss)

    return o_form

