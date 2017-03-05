#!/usr/bin/env python

# File: examples/basic_pattern_search.py

##   Copyright (C) 2001-12 Ulrich Goertz (ug@geometry.de)

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


'''This script loads a Kombilo database, does a pattern search and a signature
search and prints some information about the results after each search.
'''

from __future__ import print_function

import sys, time
sys.path.append('../src')

from kombilo.kombiloNG import *



if __name__ == '__main__':

    K = KEngine()

    # Adapt the paths according to your settings. '.' means that you need to put
    # the database files into the current directory.
    K.gamelist.DBlist.append({'sgfpath': '.', 'name':('.', 'kombilo1'), 'data': None, 'disabled': 0})

    K.loadDBs()

    print(K.gamelist.noOfGames(), 'games in database.\n')

    print('Date profile:')
    ct = time.time()
    print(K.dateProfile())
    print(time.time() - ct)

    # p = Pattern('''
    #             ...................
    #             ...................
    #             ...................
    #             ...............2...
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...1...........3...
    #             ...................
    #             ...................
    #             ...................
    #             ''', ptype=FULLBOARD_PATTERN, contsinpattern='X', ) #contlist=';W[dd];B[pp]')
    
    # p = Pattern('''
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ...................
    #             ''', ptype=FULLBOARD_PATTERN, )
    
    p = Pattern('''
                .......
                .......
                ...1...
                ....5..
                ...23..
                ...64..
                .......
                ''', ptype=CORNER_NE_PATTERN, sizeX=7, sizeY=7, contsinpattern='X')

    so = lk.SearchOptions(0,0)
    # so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_CORNER  | lk.ALGO_HASH_FULL
    # so.trustHashFull = True

    print()
    print('Pattern search:')
    K.patternSearch(p, so)
    print(K.patternSearchDetails())
    # K.gamelist.reset()

    print(K.gamelist.noOfGames(), 'games in database.')
    for i in range(min(20, K.gamelist.noOfGames())):
        print(K.gamelist.get_data(i))
    print()

    K.gamelist.reset()
    print('Signature search:')
    K.signatureSearch('dd____km____')
    print(K.gamelist.noOfGames(), 'games in database.')
    for i in range(min(10, K.gamelist.noOfGames())):
        print(K.gamelist.get_data(i))

