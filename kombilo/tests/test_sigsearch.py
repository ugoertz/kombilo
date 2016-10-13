#!/usr/bin/env python

# File: src/tests/test_sigsearch.py

##   Copyright (C) 2016- Ulrich Goertz (ug@geometry.de)

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

import os.path

from .. import libkombilo as lk
from ..kombiloNG import *

from .util import create_db


def flip_sig(sig, flip):
    l = []
    oa = ord('a')
    for i in range(6):
        l.append((ord(sig[2 * i]) - oa, ord(sig[2 * i + 1]) - oa))

    k1 = [flip(x[0], x[1]) for x in l]
    k2 = []
    for i in range(6):
        k2.append('_' if sig[2 * i] == '_' else chr(k1[i][0] + oa))
        k2.append('_' if sig[2 * i + 1] == '_' else chr(k1[i][1] + oa))
    return join(k2, '')


def test_sigsearch():
    files_sigs = [
            ('Agon-Agon02-2.sgf', 'cfkcrdbpqqle'),
            ('Agon-Agon23-P02.sgf', 'cfipjihqmenn'),
            ('Gosei-Gos23-T12.sgf', 'bilccphglfel'),
            ('KK1st-KK58-15.sgf', 'fikcagopeije'),
            ('Oza-Oza54-Oza-2006-r2b.sgf', 'ccfiqdfhledo'),
            ]

    sgfs = {}
    for f, _ in files_sigs:
        with open(os.path.join(os.path.dirname(__file__), 'sgfs', f)) as file:
            sgfs[f] = file.read()
    create_db(sgfs)

    K = KEngine()
    print os.path.join(os.path.dirname(__file__), 'db')
    K.gamelist.populateDBlist({'1': ['sgfs', os.path.join(os.path.dirname(__file__), 'db'), 'kombilo', ], })
    K.loadDBs()

    #  for i in range(K.gamelist.noOfGames()):
    #      print K.gamelist.printSignature(i)


    # ordinary signature search
    for fn, sig in files_sigs:
        K.gamelist.reset()
        K.signatureSearch(sig)
        assert K.gamelist.noOfGames() == 1
        assert K.gamelist.getProperty(0, GL_FILENAME) == fn.replace('.sgf', '')
        assert K.gamelist.printSignature(0) == sig


    # search for signature not in list
    sig = 'ffkcrdbpqqle'
    K.gamelist.reset()
    K.signatureSearch(sig)
    assert K.gamelist.noOfGames() == 0


    # test symmetrizing signatures
    fn, sig = files_sigs[0]
    var_sig = flip_sig(sig, lambda x, y: (y, x))
    assert lk.symmetrize(var_sig, 19) == sig
    K.gamelist.reset()
    K.signatureSearch(var_sig)
    assert K.gamelist.noOfGames() == 1
    assert K.gamelist.getProperty(0, GL_FILENAME) == fn.replace('.sgf', '')


    # test wildcards
    fn, sig = files_sigs[0]
    sig = 'cf____bpqqle'
    K.gamelist.reset()
    K.signatureSearch(sig)
    assert K.gamelist.noOfGames() == 1
    assert K.gamelist.getProperty(0, GL_FILENAME) == fn.replace('.sgf', '')

    sig = 'cf__________'
    K.gamelist.reset()
    K.signatureSearch(sig)
    assert K.gamelist.noOfGames() == 2

    sig = 'aa__________'
    K.gamelist.reset()
    K.signatureSearch(sig)
    assert K.gamelist.noOfGames() == 0

    # test symmetrizing signatures with wildcards
    fn, sig = files_sigs[0]
    sig = flip_sig('____' + sig[4:], lambda x, y: (18-x, y))
    K.gamelist.reset()
    K.signatureSearch(sig)
    assert K.gamelist.noOfGames() == 1
    assert K.gamelist.getProperty(0, GL_FILENAME) == fn.replace('.sgf', '')


