#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time
import nltk#, re
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

import subprocess
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag_sents

#pennタグ　を　WordNetタグに変更
def penn_to_wn(tag):
    if tag in ['JJ', 'JJR', 'JJS']:
        return "a"
    elif tag in ['NN', 'NNS', 'NNP', 'NNPS']:
        return "n"
    elif tag in ['RB', 'RBR', 'RBS']:
        return "r"
    elif tag in ['VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ']:
        return "v"
    return None

'''
def truecase(text):
    truecased_sents = [] # list of truecased sentences
    # apply POS-tagging
    tagged_sent = nltk.pos_tag([word.lower() for word in nltk.word_tokenize(text)])
    # infer capitalization from POS-tags
    normalized_sent = [w.capitalize() if t in ["NN","NNS"] else w for (w,t) in tagged_sent]
    # capitalize first word in sentence
    normalized_sent[0] = normalized_sent[0].capitalize()
    # use regular expression to get punctuation right
    pretty_string = re.sub(" (?=[\.,'!?:;])", "", ' '.join(normalized_sent))
    return pretty_string
'''


def get_s_mecab(fn, mode, my_env):
    '''
    形態素解析結果を１つの文字列で返す
    入力はテキストファイル名であることに注意
    mode: jk 日本語, ko 韓国語
    '''
    d_path = my_env['mecab_jdic'] if mode == 'jk' else my_env['mecab_kdic']
    #cmd0 = my_env['mecab_ko'] + ' -d ' + d_path + ' < '
    cmd0 = my_env['mecab_ko'] + ' -b 5242880' + ' -d ' + d_path + ' < ' 
    #長い文が勝手に２文に切ってしまうケースがある。故に、文字サイズ制限を大きく設定し、ちゃんと一行を一文にする
    cmd = cmd0 + fn
    res = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    s_mecab = res.stdout.decode('utf-8')
    return s_mecab

def z2h(s):
    '''全角→半角'''
    src = 'ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｅｄｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ０１２３４５６７８９'
    tgt = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcedfghijklmnopqrstuvwxyz0123456789'
    return s.translate(s.maketrans(src, tgt))
            
def handle_joshi(s):
    '''|1은|0는 を分解する'''
    re1 = re.compile(r'\|\d')
    ws = ' '.join(ss for ss in re.split(re1, s) if len(ss) > 0)
    return ws
    
def trans_jk(s_mrphs_ja, sysdic):
    '''日韓単語翻訳結果を１つの文字列で返す'''
    res = ''
    for ln in s_mrphs_ja.split('\n'):
        ln = ln.rstrip()
        if len(ln) > 0:
            if ln == 'EOS':
                res += ln + '\n'
            else:
                w0, s_gs = ln.split('\t')
                # 品詞と基本形を取り出す
                pos, _, _, _, _, _, w, *rest = s_gs.split(',')
                if w == '*':
                    w = w0
                find = False
                if w in sysdic:
                    defs = sysdic[w]
                    w = ' '.join(map(handle_joshi, defs))
                    w = z2h(w)
                    res += w + '\t' + pos + '\n'
                    find = True
                elif len(w) >= 4: # ない場合は、先頭と末尾の一致も調べて登録する
                    for i in range(3, len(w)): # １文字は余計なマッチが多そうなので３文字からにする
                        w1, w2 = w[:i], w[-i:]
                        if w1 in sysdic:
                            defs = sysdic[w1]
                            w1 = ' '.join(defs)
                            w1 = z2h(w1)
                            res += w1 + '\t' + pos + '\n'
                            find = True
                        if w2 in sysdic:
                            defs = sysdic[w2]
                            w2 = ' '.join(defs)
                            w2 = z2h(w2)
                            res += w2 + '\t' + pos + '\n'
                            find = True
                #else:
                if not find:
                    w = z2h(w)
                    res += w + '\t' + pos + '\n'
    return res

def push_c2sen(sen, w):
    for i in range(len(w)):
        c = w[i]
        sen.append(c)

def div_compound(comp):
    '韓国語mecabの複合語を分解して配列で返す'
    ret = list(map(lambda x: x[:x.find('/')], comp.split('+')))
    return ret

def get_mrphs(s_src, mode):
    '''
    日韓単語翻訳結果および韓国語形態素解析結果の文字列（１ファイルぶん）を読み取り配列で返す
    sim_calc_noun.py の read_sens() をアレンジしている
    mode: jk 日本語, ko 韓国語
    '''
    data = []
    sen = []
    re1 = re.compile(r'^[\dA-Za-z]+$')
    re2 = re.compile(r'^名|副|接') #|動
    re3 = re.compile(r'[\p{P}\p{S}\p{Katakana}\p{Hiragana}]')
    re4 = re.compile(r'^N|MA|SN')
    
    
    for ln in s_src.split('\n'):
        ln = ln.rstrip()
        if len(ln) > 0:
            if ln == 'EOS':
                data.append(sen[:])
                sen = []
            else:
                w, pos = ln.split('\t')
                if mode == 'jk':
                    #sen.append(w)
                    if re.search(re1, w):
                        #sen.append(w)
                        sen.append(w.lower())
                        #push_c2sen(sen, w)
                    elif re.search(re2, pos[0]) : #and not re.search(re3, w)
                        sen.append(w)
                elif mode == 'ko':#日英はこれを使わない
                    if re.search(re1, w):
                        push_c2sen(sen, w)
                    else:
                        if re.search(re4, pos):
                            sen.append(w)
                        if 'Compound' in pos:
                            comp = pos[pos.rfind(',')+1:]
                            ps = div_compound(comp)
                            sen += ps
    return data

def get_jass(fn_j, my_env, sysdic):
    s_mecab_ja = get_s_mecab(fn_j, 'jk', my_env) # これはファイルが１つの文字列として返却される
    s_trans_jk = trans_jk(s_mecab_ja, sysdic) # これはファイルが１つの文字列として返却される

    jass = get_mrphs(s_trans_jk, 'jk')# 需要确认一下 日语翻译英语后， 有多个英语项时，会怎样
    return jass
    
def get_koss(fn_k, my_env, sysdic, stopdic):#日英の場合は英語
    #s_mecab_ko = get_s_mecab(fn_k, 'ko', my_env)
    #koss = get_mrphs(s_mecab_ko, 'ko')
    
    
    #英語はまずget_mrphsをしない
    infile = open(fn_k, 'r',encoding='UTF-8') #, encoding='UTF-8'
    koss = []
    lines = infile.readlines()

    sents = []
    for l in lines:
        t = word_tokenize(l.strip())
        #koss.append(t)
        sents.append(t)

    
    lemmatizer=WordNetLemmatizer()
    tags = pos_tag_sents(sents)


    for sent in tags:
        tmp = []
        for w_pair in sent:
            word = w_pair[0].lower() #单词先全部小写
            #if w_pair[1] in ["NN","NNS"]:
            #    word = word.capitalize()    
            postag = penn_to_wn(w_pair[1])
            if (word in stopdic):
                continue
            if (postag == None or postag == "v"):
                #tmp.append(word)
                continue
            else:
                tmp.append(lemmatizer.lemmatize(word, postag))

        koss.append(tmp)

    infile.close()
    return koss

