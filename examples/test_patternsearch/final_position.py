#!/usr/bin/env python

# File: examples/test_patternsearch/final_position.py

##   Copyright (C) 2001-12 Ulrich Goertz (u@g0ertz.de)

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
This script takes a database, and searches for the final position of each game
in the database. If the number of results is different from 1, the file names
of the games having this patterns are printed. (Typically these are games which
have duplicates in the database, or which are very short.)

After searching for each final position, the script searches for the position
at move 50 in each game.

Usage: invoke as ::

  ./various_tests.py s1

where ``s1`` is a subdirectory which contains data as for the
:py:mod:`profiler` script. Output is to the console (instead of an HTML file).
'''


import sys
basepath = sys.argv[1]
sys.path.insert(0, basepath)
sys.path.append('../../src')
import time, os, os.path

import libkombilo as lk
from kombiloNG import *


def timer(f, *args, **kwargs):
    t = time.time()
    result = f(*args, **kwargs)
    return result, time.time()-t

def search(K, moveno=1000):
    for i in range(K.gamelist.noOfGames()):
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
        if K.gamelist.noOfGames() != 1:
            print K.gamelist.noOfGames(), 'games in db'
            for i in range(K.gamelist.noOfGames()):
                print K.gamelist.get_data(i)
        K.gamelist.reset()


# TODO: vary orientation; apply color switch; take non-fullboard patterns;


if __name__ == '__main__':
    K = KEngine()
    K.gamelist.DBlist.append({'sgfpath': '', 'name':(os.path.abspath(basepath), 'kombilo3'), 'data': None, 'disabled': 0})

    print 'loading db, %1.1f seconds' % timer(K.loadDBs)[1]
    print '%d games in db' % K.gamelist.noOfGames()

    so = lk.SearchOptions(0,0)


    print 'searching for final position'
    search(K)

    print 'searching for position at move 50'
    search(K, 50)


