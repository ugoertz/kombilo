# file: abstractboard.py

##   This file is part of Kombilo, a go database program
##   It contains classes implementing an abstract go board and a go
##   board displayed on the screen.

##   Copyright (C) 2001-12 Ulrich Goertz (ug@geometry.de)

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


import libkombilo as lk


class abstractBoard(lk.abstractBoard):

    def __init__(self, boardsize=19):
        lk.abstractBoard.__init__(self, boardsize)

    def play(self, pos, color):
        """ This plays a color=black/white stone at pos, if that is a legal move
            (disregarding ko), and deletes stones captured by that move.
            It returns 1 if the move has been played, 0 if not. """

        # try:
        #     assert 0 <= pos[0] <= 18
        #     assert 0 <= pos[1] <= 18
        # except AssertionError:
        #     print 'oops in board1.abstractBoard.play, %d %d' % pos
        return lk.abstractBoard.play(self, pos[0], pos[1], color)

    def status_keys(self):
        return [(i, j) for i in range(self.boardsize) for j in range(self.boardsize) if self.getStatus(i, j) not in [' ', '.']]
