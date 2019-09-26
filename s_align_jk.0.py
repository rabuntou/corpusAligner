#!/usr/bin/env python
mmm=''
len_mmm = len(mmm)

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

from sa_g import *
from sa_sysdic import *
from sa_pre import pre_proc
from sa_readdata import get_jass, get_koss
from sa_salign import s_align
from sa_post import print_filter, print_2Dlist

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stdin = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def rl(fn):
    '''
    テキストファイル読み込み簡易版
    '''
    with open(fn, 'r', encoding='utf-8') as f:
        return list(map(lambda x: x.rstrip(), f))

def wl(data, fn):
    '''
    二重配列のタブテキスト書き出し
    '''
    with open(fn, 'w', encoding='utf-8') as f:
        print(*('\t'.join(row) for row in data), sep='\n', file=f)

def get_sysdic(my_env):
    '''
    辞書は、dic.txt、内包辞書、dic.datの順番
    '''
    try:
        f = __file__
    except NameError:
        f = '.'
    d = os.path.abspath(os.path.dirname(f))
    sysdic = defaultdict()
    dictmode = 'no dict'
    if os.path.isfile(d + '/dic.txt'):
        sysdic = read_sysdic(d + '/dic.txt')
        dictmode = 'dic.txt'
    elif len_mmm > 0:
        sysdic = read_sysdic_bin_int(mmm)
        dictmode = 'inner dict'
    else:
        sysdic = read_sysdic_bin(my_env['sysdic'])
        dictmode = 'dic.dat'
    return sysdic        

def get_aids(d):
    '''
    日韓両方そろっているファイル名の拡張子を除いた部分をIDとして取得
    '''
    aids = [fn[:-3] for fn in os.listdir(d) if fn.endswith('.ja') and os.path.isfile(d + '/' + fn[:-3] + '.ko')]
    return sorted(aids)
    
def check_env(my_env):
    '''
    mecab-ko, mecab日本語辞書, mecab-ko-dic, システム辞書 dic.dat のチェック
    '''
    try:
        f = __file__
    except NameError:
        f = '.'
    d = os.path.abspath(os.path.dirname(f))
    if 'KDS_MRPH' in os.environ and 'KDS_MRPH_JDIC' in os.environ and 'KDS_MRPH_KDIC' in os.environ:        
        my_env['mecab_ko'] = os.environ['KDS_MRPH']
        my_env['mecab_jdic'] = os.environ['KDS_MRPH_JDIC']
        my_env['mecab_kdic'] = os.environ['KDS_MRPH_KDIC']
    else:
        return False
    
    # 一時ディレクトリ
    my_env['ramdisk'] = '.' # 下記が全て失敗した場合の保険
    for tmpd in ['/dev/shm', '/run/shm', '/tmp']:
        if os.access(tmpd, os.F_OK) and os.access(tmpd, os.W_OK):
            my_env['ramdisk'] = tmpd
            break
    
    # 東亜日報の処理（タイトル別扱い）
    if 'KDS_DONGA' in os.environ:
        my_env['donga'] = 'donga'
    
    if os.path.isfile(my_env['mecab_ko']):
        if os.path.isdir(my_env['mecab_jdic']):
            if os.path.isdir(my_env['mecab_kdic']):
                fl_ok = False
                if len_mmm > 0:
                    fl_ok = True
                elif os.path.isfile(d + '/dic.dat'):
                    my_env['sysdic'] = d + '/dic.dat'
                    fl_ok = True
                if fl_ok:
                    for k,v in my_env.items():
                        my_env[k] = v.rstrip('/') # パスの右端の'/'は削除する
                    return True
    return False

def main_each(d, aid, my_env, sysdic=None, f_out=sys.stdout, f_raw=None):
    '''
    １記事の処理：my_envを適切にセットすれば１記事のみの処理も可能
    '''
    # システム辞書の読み込み    
    if sysdic is None:
        sysdic = get_sysdic(my_env)
    
    # テキストは、必要な前処理をした上でRAMディスクに置く。読み込んだら削除。
    fn_ja, fn_ko = pre_proc(d, aid, my_env)
    # 必要データの読み込み
    # 読み込んだテキストデータは渡せないのでファイル名を渡して形態素解析
    txt_ja = rl(fn_ja)
    jass = get_jass(fn_ja, my_env, sysdic)
    txt_ko = rl(fn_ko)
    koss = get_koss(fn_ko, my_env)
    os.remove(fn_ja)
    os.remove(fn_ko)
    # 文アラインメントと出力
    sa = s_align(aid, txt_ja, txt_ko, jass, koss, my_env) # 二重配列で返却される
    if len(sa) > 0:
        if f_raw is not None: # そのままの出力（オプショナル）
            print_2Dlist(sa, f=f_raw)
        # 後処理をして出力
        print_filter(sa, my_env, f=f_out)

def main():
    '''
    日韓文アラインメントプログラム
    bin/s_align_jk.py ext/200102 align/200102.align
    '''
    my_env = dict()
    if not check_env(my_env):
        print('Error: See README.txt and set those paths.', file=sys.stderr)
        return
    
    parser = argparse.ArgumentParser(description='Japanese-Korean Sentence Alignment Program')
    parser.add_argument(dest='d', metavar='src_dir')
    parser.add_argument(dest='fn_out', metavar='output_file')
    parser.add_argument('--no_div', dest='no_div', action='store_true', help='no sentense division')
    parser.add_argument('--raw', dest='raw', type=str, help='output unfiltered alignment to "RAW" file')
    args = parser.parse_args()
    if args.no_div:
        my_env['no_div'] = 'no_div'
    if args.raw:
        my_env['raw'] = args.raw
    d = args.d
    fn_out = args.fn_out

    # 辞書は時間が掛かるのでここで読み込んでおく
    # dic.txtを _ とリネーム後gzip圧縮し先頭b'\x1f\x8b\x08\x08'を'KDS1'に置き換えたものがdic.dat
    sysdic = get_sysdic(my_env)

#    d = 'ext/200102'
#    fn_out = 'align/200102.align'
    aids = get_aids(d)
    if len(aids) > 0:
        # 以下はwith構文を使うためにifで場合分けしている
        if 'raw' in my_env:
            fn_raw = my_env['raw']
            with open(fn_out, 'w', encoding='utf-8') as f_out:
                with open(fn_raw, 'w', encoding='utf-8') as f_raw:
                    for aid in aids: # １記事の処理
                        main_each(d=d, aid=aid, my_env=my_env, sysdic=sysdic, f_out=f_out, f_raw=f_raw)
        else:
            with open(fn_out, 'w', encoding='utf-8') as f_out:
                for aid in aids: # １記事の処理
                    main_each(d=d, aid=aid, my_env=my_env, sysdic=sysdic, f_out=f_out)

if __name__ == '__main__':
    main()

