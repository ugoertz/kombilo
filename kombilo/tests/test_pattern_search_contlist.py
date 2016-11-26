#!/usr/bin/env python

# File: kombilo/tests/test_pattern_search.py

##   Copyright (C) 2001- Ulrich Goertz (ug@geometry.de)

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


from __future__ import absolute_import, division, unicode_literals

import pytest

from .. import libkombilo as lk
from ..kombiloNG import *

from .util import create_db


@pytest.fixture(scope='module')
def K():
    sgfs = {}
    for f in glob.glob(os.path.join(os.path.dirname(__file__), 'sgfs/contlist.sgf')):
        with open(f) as file:
            sgfs[f] = file.read()
    create_db(sgfs, 'kombilo-ptc')

    K = KEngine()

    # Adapt the paths according to your settings. '.' means that you need to put
    # the database files into the current directory.
    K.gamelist.populateDBlist({'1': ['sgfs', os.path.join(os.path.dirname(__file__), 'db'), 'kombilo-ptc', ], })

    K.loadDBs()
    yield K

    os.system('rm -f %s' % os.path.join(os.path.dirname(__file__), 'db/kombilo-ptc.d*'))


@pytest.fixture
def SOs():
    SOs = []

    so = lk.SearchOptions(0,0)
    so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL | lk.ALGO_HASH_CORNER
    so.trustHashFull = False
    SOs.append(so)

    so = lk.SearchOptions(0,0)
    so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL | lk.ALGO_HASH_CORNER
    so.trustHashFull = True
    SOs.append(so)

    so = lk.SearchOptions(0,0)
    so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL
    so.trustHashFull = False
    SOs.append(so)

    so = lk.SearchOptions(0,0)
    so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL
    so.trustHashFull = True
    SOs.append(so)

    so = lk.SearchOptions(0,0)
    so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST
    SOs.append(so)

    return SOs


def test_pattern_1(K, SOs):

    p = Pattern('''
               ...................
               ...................
               ...................
               ...............2...
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...1...............
               ...................
               ...................
               ...................
               ''', ptype=FULLBOARD_PATTERN, contsinpattern='X', )
    for so in SOs:
        K.gamelist.reset()
        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 1
        assert K.noMatches == 3
        assert len(K.continuations) == 2


def test_pattern_2(K, SOs):
    p = Pattern('''
                .......
                .......
                ...1...
                ....5..
                ...23..
                ...64..
                .......
                ''', ptype=CORNER_NE_PATTERN, sizeX=7, sizeY=7, contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()
        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 2
        assert len(K.continuations) == 1


def test_pattern_3(K, SOs):
    p = Pattern('''
               ..........
               ..........
               .....1....
               ..........
               .....2....
               ..........
               .....3....
               ..........
               .....4....
               ..........
               ''', ptype=CENTER_PATTERN,
               sizeX=10, sizeY=10,
               contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 1
        assert K.noMatches == 4  # note pattern non-symmetric + diff. cont's
        assert len(K.continuations) == 2


def test_pattern_4(K, SOs):
    p = Pattern('''
               .........
               .........
               ....1....
               .........
               ....2....
               .........
               ....3....
               .........
               ....4....
               .........
               ''', ptype=CENTER_PATTERN,
               sizeX=9, sizeY=10,
               contsinpattern='O')

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 1
        assert K.noMatches == 2
        assert len(K.continuations) == 1


def test_pattern_5(K, SOs):
    p = Pattern('''
               .........
               .........
               ....1....
               .........
               ....2....
               .........
               ....3....
               .........
               ....4....
               .........
               ''', ptype=CENTER_PATTERN,
               sizeX=9, sizeY=10,
               contsinpattern='O')

    for so in SOs:
        K.gamelist.reset()
        so.fixedColor = 1

        K.patternSearch(p, so)
        assert K.noMatches == 0


def test_pattern_6(K, SOs):
    p = Pattern('''
               ..........
               ..........
               .....1....
               ..........
               .....4....
               ..........
               .....3....
               ..........
               .....2....
               ..........
               ''', ptype=CENTER_PATTERN,
               sizeX=10, sizeY=10,
               contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        assert K.noMatches == 0


def test_pattern_7(K, SOs):
    p = Pattern('''
               ..........
               ..........
               ..........
               .....12...
               .....43...
               ..........
               ..........
               ..........
               ..........
               ..........
               ''', ptype=CENTER_PATTERN, sizeX=10, sizeY=10,
               contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()
        so.searchInVariations = True

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 2
        assert K.noMatches == 3


def test_pattern_7a(K, SOs):
    p = Pattern('''
               ..........
               ..........
               ..........
               .....12...
               .....43...
               ..........
               ..........
               ..........
               ..........
               ..........
               ''', ptype=CENTER_PATTERN, sizeX=10, sizeY=10,
               contsinpattern='O')

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 2
        assert K.noMatches == 3


def test_pattern_8(K, SOs):
    p = Pattern('''
               ..........
               ..........
               ..........
               .....12...
               .....43...
               ..........
               ..........
               ..........
               ..........
               ..........
               ''', ptype=CENTER_PATTERN, sizeX=10, sizeY=10,
               contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()
        so.searchInVariations = False

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 2
        assert K.noMatches == 2


def test_pattern_9X(K, SOs):
    p = Pattern('''
               ...
               .1.
               .2.
               .3.
               ...
               ''', ptype=CENTER_PATTERN, sizeX=3, sizeY=7,
               contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 1
        for i in range(K.gamelist.noOfGames()):
            print(K.gamelist.get_data(i))
        assert K.noMatches == 2  # symmetry (mirror horizontally)


def test_pattern_9(K, SOs):
    p = Pattern('''
               ........
               ........
               ........
               ...XO...
               ...OX...
               ........
               ........
               ........
               ''', ptype=CENTER_PATTERN, sizeX=8, sizeY=8,
               ) # contsinpattern='X')

    for so in SOs[:1]:
        K.gamelist.reset()
        so.searchInVariations = True

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 2

        assert K.noMatches == 3


def test_pattern_9A(K, SOs):
    p = Pattern('''
               ........
               ........
               ........
               ...12...
               ...43...
               ........
               ........
               ........
               ''', ptype=CENTER_PATTERN, sizeX=8, sizeY=8,
               contsinpattern='X')

    for so in SOs:
        K.gamelist.reset()
        so.searchInVariations = False

        K.patternSearch(p, so)
        assert K.gamelist.noOfGames() == 2
        assert K.noMatches == 2


