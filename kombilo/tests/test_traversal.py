#!/usr/bin/env python

# File: src/tests/test_traversal.py

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

from __future__ import absolute_import, division, unicode_literals

import os.path

from kombilo import sgf


def traverse(n, f):
    if n:
        f(n)
    else:
        print('oops')
    if n.next:
        traverse(n.next, f)
    if n.down:
        traverse(n.down, f)

class Counter():
    def __init__(self):
        self.ctr = 0

    def incr(self):
        self.ctr += 1


def test_traverse():
    files_sigs = [
            ('Agon-Agon02-2.sgf', 269, 134, 134),
            ('Agon-Agon23-P02.sgf', 216, 108, 107),
            ('Gosei-Gos23-T12.sgf', 107, 53, 53),
            ('KK1st-KK58-15.sgf', 220, 110, 109),
            ('Oza-Oza54-Oza-2006-r2b.sgf', 172, 86, 85),
            ]

    for f, a, b, w in files_sigs:
        with open(os.path.join(os.path.dirname(__file__), 'sgfs', f)) as file:
            s = file.read()
            c = sgf.Cursor(s, 1)

            ctr = Counter()
            Bctr = Counter()
            Wctr = Counter()

            def f(n):
                ctr.incr()
                if n.gpv('B'):
                    Bctr.incr()
                if n.gpv('W'):
                    Wctr.incr()

            traverse(c.root.next, f)

            assert ctr.ctr == a
            assert Bctr.ctr == b
            assert Wctr.ctr == w

