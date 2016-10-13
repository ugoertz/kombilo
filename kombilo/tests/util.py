#!/usr/bin/env python

# File: examples/test_patternsearch/final_position.py

##   Copyright (C) 2001-16 Ulrich Goertz (ug@geometry.de)

##   Kombilo is a go database program.

## Permission is hereby granted, free of charge, to any person obtaining a copy of 
## this software and associated documentation files (the "Software"), to deal in 
## the Software without restriction, including without limitation the rights to 
## use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
## of the Software, and to permit persons to whom the Software is furnished to do 
## so, subject to the following conditions:
## 
## The above copyright notice and this permission notice shall be included in all 
## copies or substantial portions of the Software.
## 
## THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
## IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
## FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
## AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
## LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
## OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
## SOFTWARE.

'''
Miscellaneous utilities for the test suite.
'''

from __future__ import absolute_import

import os
from .. import libkombilo as lk
from ..kombiloNG import *


def create_db(sgfs):
    pop = lk.ProcessOptions()
    pop.rootNodeTags = 'PW,PB,RE,DT,EV'
    pop.sgfInDB = True
    pop.professional_tag = False
    pop.processVariations = True
    pop.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL | lk.ALGO_HASH_CORNER

    gls = lk.vectorGL()

    os.system('rm -f %s' % os.path.join(os.path.dirname(__file__), 'db/kombilo.d*'))
    gl = lkGameList(os.path.join(os.path.dirname(__file__), 'db/kombilo.db'), 'DATE', '[[filename.]],,,[[id]],,,[[PB]],,,[[PW]],,,[[winner]],,,signaturexxx,,,[[date]],,,', pop, 19, 5000)

    path = 'sgfs'

    gl.start_processing()
    for fn, sgf in sgfs.items():
        gl.process(sgf, path, fn, gls, '', lk.CHECK_FOR_DUPLICATES)

    gl.finalize_processing()


