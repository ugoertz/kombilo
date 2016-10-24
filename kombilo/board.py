# file: board.py

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


from Tkinter import *
import tkFont
from PIL import Image as PILImage
from PIL import ImageTk as PILImageTk
from random import randint, choice
import math
import sys
import libkombilo as lk
from abstractboard import abstractBoard


class Board(abstractBoard, Canvas):
    """ This is a go board, displayed on the associated canvas.
        canvasSize is a pair, the first entry is the size of the border, the second
        entry is the distance between two go board lines, both in pixels.

        The most important methods are:

        - play: play a stone of some color at some position (if that is a legal move)
        - undo: undo one (or several) moves
        - state: activate (state("normal", f) - the function f is called when a stone
                 is placed on the board) or disable (state("disabled")) the board;

        - placeMark: place a colored label (slightly smaller than a stone) at some position
        - delMarks: delete all these labels
        - placeLabel: place a label (a letter, a circle, square, triangle or cross)

        As an "interface" to dealing with SGF files:
        - B, W, AB, AW, AE: take care of the corresponding actions (black/white play; add black/white stone; delete stone)
          these methods take a position (B, W) or a list of positions (AB, AW, AE).
          B and W return a tuple of captured stones.

        Here, color is either "black" or "white" (this is different from the underlying class abstractBoard, where "B" and "W" are used!)
    """

    def __init__(self, master, boardsize=19, canvasSize=(30, 25), fuzzy=1, labelFont=None,
                 focus=1, callOnChange=None, boardImg=None, blackImg=None, whiteImg=None, use_PIL=True,
                 square_board=True):
        # FIXME should refactor code: use_PIL not used anymore
        """
        blackImg and whiteImg are lists of PILImage instances (as returned by PILImage.open(...)
        Upon placing a stone on the board, a random item of the respective list
        is chosen. (Typically the blackImg list will have only one item.)
        """

        self.square_board = square_board
        self.focus = focus
        self.coordinates = 0

        self.canvasSize = canvasSize
        size = 2 * canvasSize[0] + (boardsize - 1) * canvasSize[1]  # size of the canvas in pixel
        Canvas.__init__(self, master, height=size, width=size, highlightthickness=0)

        abstractBoard.__init__(self, boardsize)

        self.changed = IntVar()  # this is set to 1 whenever a change occurs (placing stone, label etc.)
        self.changed.set(0)      # this is used for Kombilo's 'back' method

        self.callOnChange = callOnChange if callOnChange else lambda: None
        self.noChanges = 0

        self.fuzzy = IntVar()   # if self.fuzzy is true, the stones are not placed precisely
        self.fuzzy.set(fuzzy)   # on the intersections, but randomly a pixel off

        if labelFont is None:
            self.labelFontBold = tkFont.Font(family='Helvetica', size=5, weight='bold')
            self.labelFont = tkFont.Font(family='Helvetica', size=5)
        else:
            self.labelFontBold = labelFont
            self.labelFont = tkFont.Font(family=labelFont['family'], size=labelFont['size'])
        self.labelFontSizeOrig = self.labelFont['size']

        self.shadedStoneVar = IntVar()   # if this is true, there is a 'mouse pointer' showing
        self.shadedStonePos = (-1, -1)   # where the next stone would be played, given the current
                                         # mouse position

        self.currentColor = "black"     # the expected color of the next move

        self.stones = {}            # references to the ovals placed on the canvas, used for removing stones
        self.marks = {}             # references to the (colored) marks on the canvas
        self.labels = {}

        self.boundConf = self.bind("<Configure>", self.resize)
        self.resizable = 1

        self.use3Dstones = IntVar()
        self.use3Dstones.set(1)

        if boardImg and blackImg and whiteImg:
            self.img = boardImg
            self.blackStones = blackImg
            self.whiteStones = whiteImg
        else:
            raise ValueError('Image files for board/stones not found.')

        self.drawBoard()

    def drawBoard(self):
        """ Displays the background picture, and draws the lines and hoshi points of
            the go board.
            This also creates the PhotoImages for black, white stones. """

        sres = self.resizable
        self.resizable = False
        self.delete('non-bg')     # delete everything except for background image
        c0, c1 = self.canvasSize
        size = 2 * c0 + (self.boardsize - 1) * c1
        self.config(height=size, width=size)
        self.labelFont.configure(size=self.labelFontSizeOrig + c1//7 - 3)
        self.labelFontBold.configure(size=self.labelFontSizeOrig + c1//7)

        self.delete('board')
        for i in range(size // 200 + 2):
            for j in range(size // 200 + 4):   # add a lot of "board space" for search history boards
                self.create_image(200 * i, 200 * j, image=self.img, tags='board')

        if self.square_board:
            # place a gray rectangle over the board background picture
            # in order to make the board quadratic
            self.create_rectangle(size + 1, 0, size + 1000, size + 1000, fill='grey88', outline='', tags='non-bg')
            self.create_rectangle(0, size + 1, size + 1000, size + 1000, fill='grey88', outline='', tags='non-bg')

        color = 'black'

        for i in range(self.boardsize):
            self.create_line(c0, c0 + c1 * i, c0 + (self.boardsize - 1) * c1, c0 + c1 * i, fill=color, tags='non-bg')
            self.create_line(c0 + c1 * i, c0, c0 + c1 * i, c0 + (self.boardsize - 1) * c1, fill=color, tags='non-bg')

        # draw hoshi's:

        if c1 > 7:

            if self.boardsize in [13, 19]:
                b = (self.boardsize - 7) // 2
                for i in range(3):
                    for j in range(3):
                        self.create_oval(c0 + (b * i + 3) * c1 - 2, c0 + (b * j + 3) * c1 - 2,
                                         c0 + (b * i + 3) * c1 + 2, c0 + (b * j + 3) * c1 + 2, fill="black", tags='non-bg')
            elif self.boardsize == 9:
                self.create_oval(c0 + 4 * c1 - 2, c0 + 4 * c1 - 2,
                                 c0 + 4 * c1 + 2, c0 + 4 * c1 + 2, fill="black", tags='non-bg')

        # draw coordinates:

        if self.coordinates:
            for i in range(self.boardsize):
                a = 'ABCDEFGHJKLMNOPQRST'[i]
                self.create_text(c0 + c1 * i, c1 * self.boardsize + 3 * c0 // 4 + 4, text=a,
                                 font=self.labelFont, tags='non-bg')
                self.create_text(c0 + c1 * i, c0 // 4 + 1, text=a, font=self.labelFont, tags='non-bg')
                self.create_text(c0 // 4 + 1, c0 + c1 * i, text=repr(self.boardsize - i), font=self.labelFont, tags='non-bg')
                self.create_text(c1 * self.boardsize + 3 * c0 // 4 + 4, c0 + c1 * i, text=repr(self.boardsize - i), font=self.labelFont, tags='non-bg')

        self.bStones = [
                PILImageTk.PhotoImage(bs.resize((c1 + 1, c1 + 1), PILImage.LANCZOS))
                for bs in self.blackStones]
        self.wStones = [
                PILImageTk.PhotoImage(ws.resize((c1 + 1, c1 + 1), PILImage.LANCZOS))
                for ws in self.whiteStones]

        self.update_idletasks()
        self.resizable = sres

    def renew_labels(self):
        self.delete('label')
        self.delete('labelbg')
        for x in self.labels:
            self.placeLabel(x, '+' + self.labels[x][0], self.labels[x][1])

    def resize(self, event=None):
        """ This is called when the window containing the board is resized. """

        if not self.resizable:
            return

        self.noChanges = 1

        if event:
            w, h = event.width, event.height
        else:
            w, h = int(self.cget('width')), int(self.cget('height'))
        m = min(w, h)
        self.canvasSize = (m // 20 + 4, (m - 2 * (m // 20 + 4)) // (self.boardsize - 1))

        self.drawBoard()

        for x in self.status_keys():
            self.placeStone(x, self.getStatus(*x))
        for x in self.marks:
            self.placeMark(x, self.marks[x])
        for x in self.labels:
            self.placeLabel(x, '+' + self.labels[x][0], self.labels[x][1])

        self.tkraise('sel')  # this is for the list of previous search patterns ...
        self.noChanges = 0

    def play(self, pos, color=None):
        """ Play a stone of color (default is self.currentColor) at pos. """

        if color is None:
            color = self.currentColor
        if abstractBoard.play(self, pos, color):                    # legal move?
            captures = self.undostack_top_captures()                # retrieve list of captured stones
            for x in captures:
                self.delete(self.stones[x])
                del self.stones[x]
            self.placeStone(pos, color)
            self.currentColor = 'black' if color == 'white' else 'white'
            self.delShadedStone()
            return 1
        else:
            return 0

    def B(self, pos):
        if not self.play(pos, 'black'):
            return
        return self.undostack_top_captures()

    def W(self, pos):
        if not self.play(pos, 'white'):
            return
        return self.undostack_top_captures()

    def AB(self, poslist):
        for pos in poslist:
            self.setStatus(pos[0], pos[1], 'B')
            self.placeStone(pos, 'black')
            self.undostack_push(lk.Move(pos[0], pos[1], lk.AB))

    def AW(self, poslist):
        for pos in poslist:
            self.setStatus(pos[0], pos[1], 'W')
            self.placeStone(pos, 'white')
            self.undostack_push(lk.Move(pos[0], pos[1], lk.AW))

    def AE(self, poslist):
        for pos in poslist:
            x, y = pos
            if self.getStatus(x, y) == 'B':
                self.undostack_push(lk.Move(x, y, lk.AEB))
            elif self.getStatus(x, y) == 'W':
                self.undostack_push(lk.Move(x, y, lk.AEW))
            else:
                continue
            self.setStatus(x, y, ' ')
            self.delete(self.stones[pos])
            del self.stones[pos]

    def state(self, s, f=None):
        """ s in "normal", "disabled": accepting moves or not
            f the function to call if a move is entered
            [More elegant solution might be to replace this by an overloaded bind method,
            for some event "Move"?!]  """

        if s == "normal":
            self.callOnMove = f
            self.bound1 = self.bind("<Button-1>", self.onMove)
            self.boundm = self.bind("<Motion>", self.shadedStone)
            self.boundl = self.bind("<Leave>", self.delShadedStone)
        elif s == "disabled":
            self.delShadedStone()
            try:
                self.unbind("<Button-1>", self.bound1)
                self.unbind("<Motion>", self.boundm)
                self.unbind("<Leave>", self.boundl)
            except TclError:
                pass                     # if board was already disabled, unbind will fail

    def onMove(self, event):
        # compute board coordinates from the pixel coordinates of the mouse click

        if self.focus:
            self.master.focus()
        x, y = self.getBoardCoord((event.x, event.y), self.shadedStoneVar.get())
        if not (0 <= x < self.boardsize and 0 <= y < self.boardsize):
            return

        if abstractBoard.play(self, (x, y), self.currentColor):  # would this be a legal move?
            # print 'pl'
            abstractBoard.undo(self)
            self.callOnMove((x, y))
        # else: print 'no pl', x, y

    def onChange(self):
        if self.noChanges:
            return
        self.callOnChange()
        self.changed.set(1)

    def getPixelCoord(self, pos, nonfuzzy=0):
        """ transform go board coordinates into pixel coord. on the canvas of size canvSize
        """

        fuzzy1 = 0 if nonfuzzy else randint(-1, 1) * self.fuzzy.get()
        fuzzy2 = 0 if nonfuzzy else randint(-1, 1) * self.fuzzy.get()
        c1 = self.canvasSize[1]
        a = self.canvasSize[0] - self.canvasSize[1] // 2
        b = self.canvasSize[0] + self.canvasSize[1] // 2
        return (c1 * pos[0] + a + fuzzy1, c1 * pos[1] + a + fuzzy2, c1 * pos[0] + b + fuzzy1, c1 * pos[1] + b + fuzzy2)

    def getBoardCoord(self, pos, sloppy=1):
        """ transform pixel coordinates on canvas into go board coord. in [0,..,boardsize-1]x[0,..,boardsize-1]
            sloppy refers to how far the pixel may be from the intersection in order to
            be accepted """

        a, b = (self.canvasSize[0] - self.canvasSize[1] // 2, self.canvasSize[1] - 1) if sloppy else (self.canvasSize[0] - self.canvasSize[1] // 4, self.canvasSize[1] // 2)
        x = (pos[0] - a) // self.canvasSize[1] + 1 if (pos[0] - a) % self.canvasSize[1] <= b else 0
        y = (pos[1] - a) // self.canvasSize[1] + 1 if (pos[1] - a) % self.canvasSize[1] <= b else 0

        if x <= 0 or y <= 0 or x > self.boardsize or y > self.boardsize:
            x = y = 0

        return (x - 1, y - 1)

    def placeMark(self, pos, color, outln='', size=''):
        """ Place colored mark at pos. """
        x1, x2, y1, y2 = self.getPixelCoord(pos, 1)

        if size == 'small':
            tmp1 = (y1 - x1) / 4
            tmp2 = (y2 - x2) / 4
        else:
            tmp1 = 3
            tmp2 = 3
        self.create_oval(x1 + tmp1, x2 + tmp2, y1 - tmp1, y2 - tmp2, fill=color,
                         width=3, outline=outln, tags=('marks', 'non-bg'))
        self.marks[pos] = color
        self.onChange()

    def delMarks(self):
        """ Delete all marks. """
        if self.marks:
            self.onChange()
        self.marks = {}
        self.delete('marks')

    def delLabels(self):
        """ Delete all labels. """
        if self.labels:
            self.onChange()
        self.labels = {}
        self.delete('label')
        self.delete('labelbg')

    def remove(self, pos, removeFromUndostack=False):
        """ Remove the stone at pos.

        If not removeFromUndostack, append this as capture to undostack.
        Otherwise, find the placement of this stone in undostack, and remove it from there. (This is relevant when a stone is removed which was placed as AB/AW in same sgf node.)
        """
        if self.getStatus(pos[0], pos[1]) != ' ':
            self.onChange()
            self.delete(self.stones[pos])
            del self.stones[pos]
            abstractBoard.remove(self, pos[0], pos[1], removeFromUndostack)
            self.update_idletasks()
            return 1
        else:
            return 0

    def placeLabel(self, pos, typ, text=None, color=None, override=None):
        """ Place label of typ typ at pos; used to display labels
            from SGF files. If typ has the form +XX, add a label of typ XX.
            Otherwise, add or delete the label, depending on if there is no label at pos,
            or if there is one."""

        if typ[0] != '+':
            if pos in self.labels:
                if self.labels[pos][0] == typ:
                    for item in self.labels[pos][2]:
                        self.delete(item)
                    del self.labels[pos]
                    return
                else:
                    for item in self.labels[pos][2]:
                        self.delete(item)
                    del self.labels[pos]

            self.onChange()

        else:
            typ = typ[1:]

        labelIDs = []

        if override:
            fcolor = override[0]
            fcolor2 = override[1]
        elif self.getStatus(pos[0], pos[1]) and self.getStatus(pos[0], pos[1]) in ['b', 'B']:
            fcolor = 'white'
            fcolor2 = ''
        elif self.getStatus(pos[0], pos[1]) and self.getStatus(pos[0], pos[1]) in ['w', 'W']:
            fcolor = 'black'
            fcolor2 = ''
        else:
            fcolor = color or 'black'
            fcolor2 = '#D8A542'

        x1, x2, y1, y2 = self.getPixelCoord(pos, 1)
        if typ == 'LB':
            labelIDs.append(self.create_oval(x1 + 3, x2 + 3, y1 - 3, y2 - 3, fill=fcolor2, outline='', tags=('labelbg', 'non-bg')))
            labelIDs.append(self.create_text((x1 + y1) // 2, (x2 + y2) // 2, text=text, fill=fcolor,
                                             font=self.labelFontBold, tags=('label', 'non-bg')))
        elif typ == 'SQ':
            w = self.canvasSize[1] / 3
            labelIDs.append(self.create_rectangle(x1 + w, x2 + w, y1 - w, y2 - w, width=2, fill='', outline=fcolor, tags=('label', 'non-bg')))
        elif typ == 'CR':
            w = self.canvasSize[1] / 3
            labelIDs.append(self.create_oval(x1 + w, x2 + w, y1 - w, y2 - w, width=2, fill='', outline=fcolor, tags=('label', 'non-bg')))
        elif typ == 'TR':
            w = self.canvasSize[1] / 3
            labelIDs.append(self.create_polygon((x1 + y1) // 2, x2 + w, x1 + w, y2 - w, y1 - w, y2 - w,
                                                width=2, fill='', outline=fcolor,
                                                tags=('label', 'non-bg')))
        elif typ == 'MA':
            labelIDs.append(self.create_oval(x1 + 3, x2 + 3, y1 - 3, y2 - 3, fill=fcolor2, outline='',
                             tags=('labelbg', 'non-bg')))
            labelIDs.append(self.create_text((x1 + y1) // 2, (x2 + y2) // 2, text='X', fill=fcolor,
                                             font=self.labelFontBold, tags=('label', 'non-bg')))

        self.labels[pos] = (typ, text, labelIDs, color)

    def placeStone(self, pos, co):
        # assert pos[0] >= 0 and pos[1] >= 0
        if co in ['black', 'white']:
            color = co
        elif co in ['B', 'W']:
            color = 'black' if co == 'B' else 'white'
        else:
            return
        self.onChange()
        p = self.getPixelCoord(pos)
        if not self.use3Dstones.get() or self.canvasSize[1] <= 7:
            self.stones[pos] = self.create_oval(*p, fill=color, tags='non-bg')
        else:
            if color == 'black':
                self.stones[pos] = self.create_image(
                        ((p[0] + p[2]) // 2, (p[1] + p[3]) // 2),
                        image=choice(self.bStones),
                        tags='non-bg')
            elif color == 'white':
                self.stones[pos] = self.create_image(
                        ((p[0] + p[2]) // 2, (p[1] + p[3]) // 2),
                        image=choice(self.wStones),
                        tags='non-bg')

    def undo(self, no=1, changeCurrentColor=1):
        """ Undo the last no moves.
            abstractBoard.undo is not invoked here.
        """

        for i in range(no):
            if self.undostack:
                self.onChange()
                pos = self.undostack_top_pos()
                color = self.undostack_top_color()
                captures = self.undostack_top_captures()
                # print pos, color, captures
                self.undostack_pop()
                if color in ['B', 'W'] and self.getStatus(pos[0], pos[1]) != ' ':
                    self.setStatus(pos[0], pos[1], ' ')
                    self.delete(self.stones[pos])
                    del self.stones[pos]
                    for p in captures:
                        self.placeStone(p, 'black' if color == 'W' else 'white')
                        self.setStatus(p[0], p[1], 'B' if color == 'W' else 'W')
                elif color in [lk.AB, lk.AW]:
                    self.setStatus(pos[0], pos[1], ' ')
                    self.delete(self.stones[pos])
                    del self.stones[pos]
                elif color == lk.AEB:
                    self.setStatus(pos[0], pos[1], 'B')
                    self.placeStone(pos, 'black')
                elif color == lk.AEW:
                    self.setStatus(pos[0], pos[1], 'W')
                    self.placeStone(pos, 'white')

                # self.update_idletasks()
                if changeCurrentColor:
                    self.currentColor = 'black' if self.currentColor == 'white' else 'white'

    def clear(self):
        """ Clear the board. """
        abstractBoard.clear(self)
        for x in self.stones:
            self.delete(self.stones[x])
        self.stones = {}
        self.currentColor = 'black'
        self.onChange()

    def ptOnCircle(self, size, degree):
        radPerDeg = math.pi / 180
        r = size / 2
        x = int(r * math.cos((degree - 90) * radPerDeg) + r)
        y = int(r * math.sin((degree - 90) * radPerDeg) + r)
        return (x, y)

    def shadedStone(self, event):
        x, y = self.getBoardCoord((event.x, event.y), 1)
        if (x, y) == self.shadedStonePos:
            return     # nothing changed

        self.delShadedStone()

        if (x >= 0 and y >= 0) and self.shadedStoneVar.get() and abstractBoard.play(self, (x, y), self.currentColor):
            abstractBoard.undo(self)

            if sys.platform[:3] == 'win':     # 'stipple' is ignored under windows for
                                              # create_oval, so we'll draw a polygon ...
                l = self.getPixelCoord((x, y), 1)
                m = []

                for i in range(18):
                    help = self.ptOnCircle(l[2] - l[0], i * 360 // 18)
                    m.append(help[0] + l[0])
                    m.append(help[1] + l[1])

                self.create_polygon(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9],
                                    m[10], m[11], m[12], m[13], m[14], m[15], m[16], m[17],
                                    m[18], m[19], m[20], m[21], m[22], m[23], m[24], m[25],
                                    m[26], m[27], m[28], m[29], m[30], m[31], m[32], m[33],
                                    m[34], m[35],
                                    fill=self.currentColor, stipple='gray50',
                                    outline='', tags=('shaded', 'non-bg'))
            elif sys.platform.startswith('darwin'):
                x1, x2, y1, y2 = self.getPixelCoord((x, y), 1)
                pcoord = x1 + 2, x2 + 2, y1 - 2, y2 - 2
                self.create_oval(pcoord, fill=self.currentColor, outline='', tags=('shaded', 'non-bg'))
            else:
                self.create_oval(self.getPixelCoord((x, y), 1), fill=self.currentColor, stipple='gray50',
                                 outline='', tags=('shaded', 'non-bg'))

            self.shadedStonePos = (x, y)

    def delShadedStone(self, event=None):
        self.delete('shaded')
        self.shadedStonePos = (-1, -1)

    def fuzzyStones(self):
        """ switch fuzzy/non-fuzzy stone placement according to self.fuzzy """
        for i in range(self.boardsize):
            for j in range(self.boardsize):
                if not self.getStatus(i, j) in ['B', 'W']:
                    continue
                p = (i, j)
                self.delete(self.stones[p])
                del self.stones[p]
                self.placeStone(p, self.getStatus(i, j))
        self.tkraise('marks')
        self.tkraise('labelbg')
        self.tkraise('label')
