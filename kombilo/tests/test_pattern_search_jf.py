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
    for f in glob.glob(os.path.join(os.path.dirname(__file__), 'sgfs/1600J*06.sgf')):
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


def test_num_of_games(K):
    assert K.gamelist.noOfGames() == 1

def test_pattern_1(K):
    '''
    This pattern was not found by Kombilo 0.7.3.
    (Email from John Fairbairn, July 19, 2012.)
    '''

    p = Pattern('''
               .OOOOXX
               X.OXXOX
               OOOXOOO
               OXXXO.O
               XXX.XO.
               OO.XXXX
               ''', ptype=CORNER_SE_PATTERN, sizeX=7, sizeY=6)
    so = lk.SearchOptions(0,0)
    K.patternSearch(p, so)

    assert K.gamelist.noOfGames() == 1
    assert K.noMatches == 1
    assert K.gamelist.get_data(0).endswith(
            '1600JSTP06: Wang Hannian - Sheng Dayou (W), 141A, ')
    assert len(K.continuations) == 1

    assert K.continuations[0].x == 0
    assert K.continuations[0].y == 0

    K.gamelist.reset()

def test_sig_search(K):
    K.signatureSearch('dd____km____')
    assert K.gamelist.noOfGames() == 0
    K.gamelist.reset()
    K.signatureSearch('bdddodldoegq')
    assert K.gamelist.noOfGames() == 0
    K.gamelist.reset()
    K.signatureSearch('bdlhodldoegq')
    assert K.gamelist.noOfGames() == 1
    K.gamelist.reset()
    K.signatureSearch('bd____ld__gq')
    assert K.gamelist.noOfGames() == 1
    K.gamelist.reset()

