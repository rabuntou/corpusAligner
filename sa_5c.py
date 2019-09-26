#!/usr/bin/env python

tbl_5c_src = '''
＝@	―　
≠P	―１
≠T	―５
≠U	―６
≠V	―７
ャE	ソウ
ャN	ソク
ャ`	ソチ
ャt	ソフ
ャv	ソプ
ャ刀A	ソン、
ャ唐ｪ	ソンが
ャ唐ｾ	ソンだ
ャ唐ﾌ	ソンの
ャ塔f	ソンデ
ャ塔E	ソンウ
ャ塔e	ソンテ
ャ塔h	ソンド
ャ塔{	ソンボ
ャ刀E	ソン・
ャ刀j	ソン）
メE	ソ・
メ[	ソー
ャ梼＝i	ソン氏（
嵐閨B	予定。
嵐閨v	予定」
嵐閧ﾅ	予定で
卵z	予想
落Z	予算
洛ｩ	予見
嵐C	予辰
蘭h	予防
署l	十人
助ｪ	十分
庶噤i	十字（
諸N	十年
署F	十色
魔ｩ	暴か
穀z	構築
垂ｵ	申し
錐嵩d	申告電
瑞ｿ	申請
狽ｪ	能が
狽ｾ	能だ
狽ﾆ	能と
狽ﾈ	能な
狽ﾉ	能に
舶ｪ	能分
迫ﾍ	能力
柏ｫ	能性
薄ﾊ	能面
普v	表」
浮ｪ	表が
浮ｵ	表し
浮ｷ	表す
浮ﾆ	表と
浮ﾈ	表な
普E	表・
蕪I	表的
普i	表（
普j	表）
赴L	表記
戟j	圭）
薛g鉉	薛琦鉉
金桙ｪ	金薫が
表情ｪ	表情は
金鉉凾ｪ	金鉉埈
ｪっかり	がっかり
鰍ｪ	が
ｪ	寛
西告謳ｶ	西厓先生
丁若辮謳ｶ	丁若鏞
朴婉歯ｶ学村	朴 婉緒文学村
ｶ	郎
浮ﾌ	表の
浮ﾍ	表は
浮ｳ	表さ
阜ｻ	表現
侮ｦ	表示
濫ﾌ	予備の
絡垂ｵ	予告し
絡垂ｷ	予告す
告ｬ	構成
国｢	構造
'''[1:-1]

def make_5c_tbl(src=tbl_5c_src):
    '''5c文字化け修正テーブル作成'''
    tbl = dict()
    lens = set() # keyの長さ
    for ln in src.split('\n'):
        k, v = ln.split('\t')
        tbl[k] = v
    lens = set(map(lambda x: len(x), tbl.keys())) # key長    
    return tbl, min(lens), max(lens) # key長の最小と最大も返却

def search_5c_tbl(s0, tbl_5c):
    '''5cテーブルを利用して文字化け修正'''
    tbl, lmin, lmax = tbl_5c
    klen = lmax
    s = s0
    while klen >= lmin:
        s = ''
        i = 0
        while i < len(s0):
            k = s0[i:i+klen]
            if k in tbl:
                s += tbl[k]
                i += klen
            else:
                s += s0[i:i+1]
                i += 1
        s0 = s
        klen -= 1
    return s

