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
This script creates a database from the sgf files in the folder sgfs, and
searches for the final position of each game in the database. If the number of
results is different from 1, an error is thrown.

After searching for each final position, the script searches for the position
at move 50 in each game.
'''

from __future__ import absolute_import

import os
import os.path
import glob

from .. import libkombilo as lk
from ..kombiloNG import *

from .util import create_db


def search(K, moveno=6000):
    for i in range(K.gamelist.noOfGames()-1, -1, -1):
        so = lk.SearchOptions(0,0)
        c = Cursor(K.gamelist.getSGF(i))
        b = abstractBoard()

        def convCoord(x):
            p, q =  ord(x[0])-ord('a'), ord(x[1])-ord('a')
            if 0 <= p <= 18 and 0 <= q <= 18:
                return (p,q)

        for i in range(moveno):
            n = c.currentNode()
            if n.has_key('AB') and n['AB'][0]:
                for p in n['AB']: b.play(convCoord(p), 'b')
            if n.has_key('AW') and n['AW'][0]:
                for p in n['AW']: b.play(convCoord(p), 'w')

            if n.has_key('B') and n['B'][0]:
                p = convCoord(n['B'][0])
                if not p or not b.play(p, 'b'): b.undostack_append_pass()
            elif n.has_key('W') and n['W'][0]:
                p = convCoord(n['W'][0])
                if not p or not b.play(p, 'w'): b.undostack_append_pass()
            if c.atEnd: break
            c.next()

        p = Pattern(''.join({ ' ': '.', 'B': 'X', 'W': 'O' }[b.getStatus(i,j)] for i in range(19) for j in range(19)), ptype=FULLBOARD_PATTERN)
        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 1
        K.gamelist.reset()

        if not c.atEnd:
            so.moveLimit = moveno - 2
            K.patternSearch(p, so)
            assert K.gamelist.noOfGames() == 0
            K.gamelist.reset()

# TODO: vary orientation; apply color switch; take non-fullboard patterns;


def test_pattern_search_auto():
    sgfs = {}
    for f in glob.glob(os.path.join(os.path.dirname(__file__), 'sgfs/*.sgf')):
        with open(f) as file:
            sgfs[f] = file.read()
    create_db(sgfs)

    K = KEngine()
    K.gamelist.populateDBlist({'1': ['sgfs', os.path.join(os.path.dirname(__file__), 'db'), 'kombilo', ], })
    K.loadDBs()

    search(K)
    search(K, 20)
    search(K, 50)


