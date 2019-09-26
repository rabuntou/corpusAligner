#!/usr/bin/env python

import os
import sys
import io
from collections import defaultdict
import argparse
import regex as re
import time

from inspect import currentframe, getouterframes

g_none = '×'
g_same = '↑'

def pv(obj):
    'デバッグ用：オブジェクト名と値の表示'
    v_name = getouterframes(currentframe())[1].code_context[0].split('(')[1].split(')')[0]
    # print(v_name, ' =>')
    # print(str(obj))
    print(v_name, ' =>', str(obj), file=sys.stderr)

