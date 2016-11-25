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


from __future__ import absolute_import

import pytest

from .. import libkombilo as lk
from ..kombiloNG import *

from .util import create_db


@pytest.fixture(scope='module')
def K():
    sgfs = {}
    for f in glob.glob(os.path.join(os.path.dirname(__file__), 'sgfs/Gosei*.sgf')):
        with open(f) as file:
            sgfs[f] = file.read()
    create_db(sgfs, 'kombilo-pt')

    K = KEngine()

    # Adapt the paths according to your settings. '.' means that you need to put
    # the database files into the current directory.
    K.gamelist.populateDBlist({'1': ['sgfs', os.path.join(os.path.dirname(__file__), 'db'), 'kombilo-pt', ], })

    K.loadDBs()
    yield K

    # os.system('rm ./db/kombilo-pt.d*')


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


def test_num_of_games(K):
    K.gamelist.reset()
    assert K.gamelist.noOfGames() == 30


def test_gisearch(K):
    K.gamelist.reset()

    K.gameinfoSearch("PB = 'Kobayashi Koichi'")
    assert K.gamelist.noOfGames() == 2
    K.gamelist.reset()
    K.gameinfoSearch("PB like 'Kobayashi Ko%'")
    assert K.gamelist.noOfGames() == 2
    K.gamelist.reset()
    K.gameinfoSearch("PB like 'Kobayashi Ko%'")
    K.gameinfoSearch("PW like 'Lee%'")
    assert K.gamelist.noOfGames() == 0

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
        assert K.gamelist.noOfGames() == 30
        K.patternSearch(p, so)

        assert K.gamelist.noOfGames() == 6
        assert K.gamelist.get_data(0).endswith(
                'Gosei-Gos23-T14: Nakano Yasuhiro - Kobayashi Koichi (B), 2C, ')
        assert len(K.continuations) == 3

        assert K.continuations[0].x == 15
        assert K.continuations[0].y == 15


def test_pattern_2(K, SOs):
    p = Pattern('''
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
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ...................
               ''', ptype=FULLBOARD_PATTERN, )

    for so in SOs:
        K.gamelist.reset()
        so.fixedColor = 1
        K.patternSearch(p, so)

        assert K.gamelist.noOfGames() == 30
        assert K.gamelist.get_data(0).endswith(
                'Gosei-Gos23-T10: Omori Yasushi - Ryu Shikun (W), 0A, ')
        assert len(K.continuations) == 3

        assert K.continuations[0].x == 15
        assert K.continuations[0].y == 15
        assert K.continuations[0].B == 17
        assert K.continuations[0].W == 0
        assert K.continuations[1].x == 16
        assert K.continuations[1].y == 15
        assert K.continuations[1].B == 12
        assert K.continuations[1].W == 0
        assert K.continuations[2].x == 16
        assert K.continuations[2].y == 14
        assert K.continuations[2].B == 1
        assert K.continuations[2].W == 0


def test_pattern_3(K, SOs):
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

        assert K.gamelist.noOfGames() == 4
        assert K.gamelist.get_data(2).endswith(
                'Gosei-Gos23-T16: Akiyama Jiro - Sonoda Yuichi (B), 11B-, ')
        assert K.gamelist.get_data(3).endswith(
                'Gosei-Gos23-T28: Kobayashi Koichi - Sonoda Yuichi (B), 9A-, ')
        assert len(K.continuations) == 2

        assert K.continuations[0].x == 1
        assert K.continuations[0].y == 2
        assert K.continuations[0].B == 3
        assert K.continuations[0].W == 0
        assert K.continuations[1].x == 2
        assert K.continuations[1].y == 3
        assert K.continuations[1].B == 1
        assert K.continuations[1].W == 0



def test_pattern_4(K, SOs):
    p = Pattern('''
               ..........
               ..........
               ..........
               ..........
               ..........
               ..........
               ..........
               ..........
               ..........
               ..........
               ''', ptype=CORNER_NE_PATTERN, sizeX=10, sizeY=10)

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        # sort by filename because some games in this list have the same date
        K.gamelist.update(GL_FILENAME, True)

        assert K.noMatches == 120
        assert K.gamelist.noOfGames() == 30
        assert K.gamelist.get_data(2).endswith(
                'Gosei-Gos23-T28: Kobayashi Koichi - Sonoda Yuichi (B), 0A, 0B-, 0A, 0A-, ')
        assert K.gamelist.get_data(3).endswith(
                'Gosei-Gos23-T27: Omori Yasushi - O Rissei (B), 0A, 0A-, 0B, 0A-, ')
        assert len(K.continuations) == 4

        assert K.continuations[0].x == 6
        assert K.continuations[0].y == 3
        assert K.continuations[0].B == 68
        assert K.continuations[0].W == 0
        assert K.continuations[1].x == 7
        assert K.continuations[1].y == 3
        assert K.continuations[1].B == 45
        assert K.continuations[1].W == 0
        assert K.continuations[2].x == 7
        assert K.continuations[2].y == 4
        assert K.continuations[2].B == 5
        assert K.continuations[2].W == 0
        assert K.continuations[3].x == 7
        assert K.continuations[3].y == 2
        assert K.continuations[3].B == 2
        assert K.continuations[3].W == 0


def test_pattern_5(K, SOs):
    p = Pattern('''
               ,.....,...
               ..........
               ..........
               ..........
               ..........
               ..........
               ,.....,...
               ..........
               ..........
               ..........
               ''', ptype=CORNER_NE_PATTERN, sizeX=10, sizeY=10)

    for so in SOs:
        K.gamelist.reset()
        so.fixedColor = 1

        K.patternSearch(p, so)
        # sort by filename because some games in this list have the same date
        K.gamelist.update(GL_FILENAME, True)

        assert K.noMatches == 120
        assert K.gamelist.noOfGames() == 30
        assert K.gamelist.get_data(2).endswith(
                'Gosei-Gos23-T28: Kobayashi Koichi - Sonoda Yuichi (B), 0A, 0B, 0A, 0A, ')
        assert K.gamelist.get_data(3).endswith(
                'Gosei-Gos23-T27: Omori Yasushi - O Rissei (B), 0A, 0A, 0B, 0A, ')
        assert len(K.continuations) == 4

        assert K.gamelist.Bwins == 68
        assert K.gamelist.Wwins == K.noMatches - K.gamelist.Bwins
        assert K.gamelist.BwinsG == 17
        assert K.gamelist.WwinsG == K.gamelist.noOfGames() - K.gamelist.BwinsG

        assert K.continuations[0].x == 6
        assert K.continuations[0].y == 3
        assert K.continuations[0].B == 30
        assert K.continuations[0].W == 38
        assert K.continuations[1].x == 7
        assert K.continuations[1].y == 3
        assert K.continuations[1].B == 31
        assert K.continuations[1].W == 14
        assert K.continuations[2].x == 7
        assert K.continuations[2].y == 4
        assert K.continuations[2].B == 2
        assert K.continuations[2].W == 3
        assert K.continuations[3].x == 7
        assert K.continuations[3].y == 2
        assert K.continuations[3].B == 0
        assert K.continuations[3].W == 2


def test_pattern_6(K, SOs):
    p = Pattern('''
               ,.....,...
               ..........
               ..........
               ..........
               ..........
               ..........
               ,.....,...
               ..........
               ..........
               ..........
               ''', ptype=CORNER_NE_PATTERN, sizeX=10, sizeY=10)

    for so in SOs:
        K.gamelist.reset()
        so.nextMove = 1

        K.patternSearch(p, so)
        # sort by filename because some games in this list have the same date
        K.gamelist.update(GL_FILENAME, True)

        assert K.noMatches == 120
        assert K.gamelist.noOfGames() == 30
        assert K.gamelist.get_data(2).endswith(
                'Gosei-Gos23-T28: Kobayashi Koichi - Sonoda Yuichi (B), 0A, 0B-, 0A, 0A-, ')
        assert K.gamelist.get_data(3).endswith(
                'Gosei-Gos23-T27: Omori Yasushi - O Rissei (B), 0A, 0A-, 0B, 0A-, ')
        assert len(K.continuations) == 4

        assert K.continuations[0].x == 6
        assert K.continuations[0].y == 3
        assert K.continuations[0].B == 68
        assert K.continuations[0].W == 0
        assert K.continuations[1].x == 7
        assert K.continuations[1].y == 3
        assert K.continuations[1].B == 45
        assert K.continuations[1].W == 0
        assert K.continuations[2].x == 7
        assert K.continuations[2].y == 4
        assert K.continuations[2].B == 5
        assert K.continuations[2].W == 0
        assert K.continuations[3].x == 7
        assert K.continuations[3].y == 2
        assert K.continuations[3].B == 2
        assert K.continuations[3].W == 0


def test_pattern_7(K, SOs):
    p = Pattern('''
               ,.....,...
               ..........
               ..........
               ..........
               ..........
               ..........
               ,.....,...
               ..........
               ..........
               ..........
               ''', ptype=CORNER_NE_PATTERN, sizeX=10, sizeY=10)

    for so in SOs:
        K.gamelist.reset()

        so.nextMove = 1
        so.fixedColor = 1
        K.patternSearch(p, so)
        # sort by filename because some games in this list have the same date
        K.gamelist.update(GL_FILENAME, True)

        assert K.noMatches == 63
        assert K.gamelist.noOfGames() == 30
        assert K.gamelist.get_data(2).endswith(
                'Gosei-Gos23-T28: Kobayashi Koichi - Sonoda Yuichi (B), 0B, 0B, ')
        assert K.gamelist.get_data(3).endswith(
                'Gosei-Gos23-T27: Omori Yasushi - O Rissei (B), 0B, 0A, ')
        assert len(K.continuations) == 3

        assert K.continuations[0].x == 7
        assert K.continuations[0].y == 3
        assert K.continuations[0].B == 31
        assert K.continuations[0].W == 0
        assert K.continuations[1].x == 6
        assert K.continuations[1].y == 3
        assert K.continuations[1].B == 30
        assert K.continuations[1].W == 0
        assert K.continuations[2].x == 7
        assert K.continuations[2].y == 4
        assert K.continuations[2].B == 2
        assert K.continuations[2].W == 0


def test_pattern_8(K, SOs):
    p = Pattern('''
               .........
               .X...O...
               ...O..X..
               .o...X...
               .........
               ......X..
               .........
               .........
               .........
               .....,...
               ''', ptype=CORNER_NE_PATTERN, sizeX=9, sizeY=10)

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        # sort by filename because some games in this list have the same date
        K.gamelist.update(GL_FILENAME, True)

        assert K.noMatches == 1
        assert K.gamelist.noOfGames() == 1
        assert len(K.continuations) == 1

        assert K.continuations[0].x == 4
        assert K.continuations[0].y == 3
        assert K.continuations[0].B == 0
        assert K.continuations[0].W == 1


def test_pattern_9(K, SOs):
    p = Pattern('''
               .........
               .X...O...
               ...O..X..
               .x...X...
               .........
               ......X..
               .........
               .........
               .........
               .....,...
               ''', ptype=CORNER_NE_PATTERN, sizeX=9, sizeY=10)

    for so in SOs:
        K.gamelist.reset()

        K.patternSearch(p, so)
        # sort by filename because some games in this list have the same date
        K.gamelist.update(GL_FILENAME, True)

        assert K.noMatches == 0
        assert K.gamelist.noOfGames() == 0


