#! /usr/bin/env python
# File: kombilo.py

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

from __future__ import absolute_import

import time
import datetime
import os
import sys
from copy import copy
from string import split, find, join, strip, replace
import re
from array import *
from configobj import ConfigObj
import pkg_resources

from Tkinter import *
from ttk import *
from tkMessageBox import *
from ScrolledText import ScrolledText
import tkFileDialog
import tkFont
from tkCommonDialog import Dialog
from .tooltip.tooltip import ToolTip
from PIL import Image as PILImage
from PIL import ImageTk as PILImageTk
from Pmw import ScrolledFrame
import Pmw

from .vsl.vl import VScrolledList
from .sgf import Node, Cursor
from . import libkombilo as lk
from .board import *
import kombilo.v as v

import __builtin__
# make sure _ is defined as built-in, so that kombiloNG and custommenus do not
# define a dummy _ of their own
if '_' not in __builtin__.__dict__:
    __builtin__.__dict__['_'] = lambda s: s

from .kombiloNG import *
from .custommenus import CustomMenus





KOMBILO_RELEASE = '0.8'

# --------- GUI TOOLS -------------------------------------------------------------------


class chooseDirectory(Dialog):
    """ A wrapper tor the Tk chooseDirectory widget. """

    command = "tk_chooseDirectory"

    def _fixresult(self, widget, result):
        if result:
            self.options["initialdir"] = result
        self.directory = result
        return result


def askdirectory(**options):
    c = chooseDirectory(**options)
    return c.show()

#---------------------------------------------------------------------------------------


class BoardWC(Board):
    """ Board with support for wildcards and selection
        of search-relevant region. Furthermore, snapshot returns a dictionary which
        describes the current board position. It can then be restored with restore."""

    def __init__(self, *args, **kwargs):
        oOMB = kwargs.pop('onlyOneMouseButton', 0)

        Board.__init__(self, *args, **kwargs)

        self.wildcards = {}

        self.selection = ((0, 0), (self.boardsize - 1, self.boardsize - 1))

        self.fixedColor = IntVar()
        self.smartFixedColor = IntVar()

        self.onlyOneMouseButton = 'init'
        self.rebind_mouse_buttons(oOMB)

        self.bounds1 = self.bind('<Shift-1>', self.wildcard)

        self.invertSelection = IntVar()

    def unbind_third_mouse_button(self):
        """Unbinds the 'third' mouse button events (click, motion)."""
        if self.onlyOneMouseButton:
            click, motion = self.onlyOneMouseButton.split(';')
            self.unbind(click, self.bound3m)
            self.unbind(motion, self.bound3)
        else:
            self.unbind('<B3-Motion>', self.bound3m)
            self.unbind('<3>', self.bound3)

    def rebind_mouse_buttons(self, onlyOneMouseButton):
        if self.onlyOneMouseButton != 'init':  # do not do this during the first run (since self.bound3m, self.bound3 do not exist yet)
            self.unbind_third_mouse_button()
        self.onlyOneMouseButton = onlyOneMouseButton
        if onlyOneMouseButton:
            click, motion = onlyOneMouseButton.split(';')
            self.bound3 = self.bind(click, self.selStart)   # '<M2-Button-1>'
            self.bound3m = self.bind(motion, self.selDrag)  # '<M2-B1-Motion>'
        else:
            self.bound3 = self.bind('<Button-3>', self.selStart)
            self.bound3m = self.bind('<B3-Motion>', self.selDrag)

    def resize(self, event=None):
        """ Resize the board. Take care of wildcards and selection here. """

        Board.resize(self, event)
        for x, y in self.wildcards:
            self.place_wildcard(x, y, self.wildcards[(x, y)][1])

        self.delete('selection')
        self.drawSelection()

    def place_wildcard(self, x, y, wc_type):
        x1, x2, y1, y2 = self.getPixelCoord((x, y), 1)
        margin = max(0, self.canvasSize[1] - 7) // 4 + 1

        self.wildcards[(x, y)] = (self.create_oval(x1 + margin, x2 + margin, y1 - margin, y2 - margin,
                                                   fill={'*': 'green', 'x': 'black', 'o': 'white'}[wc_type],
                                                   tags=('wildcard', 'non-bg')),
                                  wc_type)
        self.tkraise('label')

    def wildcard(self, event):
        """ Place/delete a wildcard at position of click. """

        x, y = self.getBoardCoord((event.x, event.y), 1)
        if not (0 <= x < self.boardsize and 0 <= y and self.getStatus(x, y) == ' '):
            return

        if (x, y) in self.wildcards:
            wc, wc_type = self.wildcards.pop((x, y))
            self.delete(wc)

            if wc_type == '*':
                self.place_wildcard(x, y, 'x')
            elif wc_type == 'x':
                self.place_wildcard(x, y, 'o')
        else:
            self.place_wildcard(x, y, '*')
        self.renew_labels()
        self.changed.set(1)

    def delWildcards(self):
        """ Delete all wildcards."""

        if self.wildcards:
            self.changed.set(1)
        self.delete('wildcard')
        self.wildcards = {}

    def placeLabel(self, pos, typ, text=None, color=None):
        """ Place a label; take care of wildcards at same position. """

        if pos in self.wildcards:
            override = {'*': ('black', ''), 'o': ('black', ''), 'x': ('white', '')}[self.wildcards[pos][1]]
        else:
            override = None

        Board.placeLabel(self, pos, typ, text, color, override)

    # ---- selection of search-relevant section -----------------------------------

    def selStart(self, event):
        """ React to right-click.
        """

        self.delete('selection')
        x, y = self.getBoardCoord((event.x, event.y), 1)
        x = max(x, 0)
        y = max(y, 0)
        self.selection = ((x, y), (-1, -1))
        if self.smartFixedColor.get():
            self.fixedColor.set(1)
        self.changed.set(1)

    def selDrag(self, event):
        """ React to right-mouse-key-drag. """
        pos = self.getBoardCoord((event.x, event.y), 1)
        if pos[0] >= self.selection[0][0] and pos[1] >= self.selection[0][1]:
            self.setSelection(self.selection[0], pos)

    def drawSelection(self):
        pos0, pos1 = self.selection
        p0 = self.getPixelCoord(pos0, 1)
        p1 = self.getPixelCoord((pos1[0] + 1, pos1[1] + 1), 1)
        min = self.getPixelCoord((0, 0), 1)[0] + 1
        max = self.getPixelCoord((self.boardsize, self.boardsize), 1)[1] - 1
        rectangle_kwargs = {'fill': 'gray50', 'stipple': 'gray50', 'outline': '', 'tags': 'selection', }

        if self.canvasSize[1] <= 7:
            self.create_rectangle(p0[0], p0[1], p1[0], p1[1], tags=('selection', 'non-bg'))
        elif self.invertSelection.get():
            self.create_rectangle(p0[0], p0[1], p1[0], p1[1], **rectangle_kwargs)
        else:
            if p0[1] > min:
                self.create_rectangle(min, min, max, p0[1], **rectangle_kwargs)
            if p0[0] > min and p0[1] < max:
                self.create_rectangle(min, p0[1], p0[0], max, **rectangle_kwargs)
            if p1[1] < max:
                self.create_rectangle(p0[0], p1[1], p1[0], max, **rectangle_kwargs)
            if p1[0] < max and p0[1] < max:
                self.create_rectangle(p1[0], p0[1], max, max, **rectangle_kwargs)

        self.tkraise('non-bg')
        self.update_idletasks()

    def setSelection(self, pos0, pos1):
        self.selection = (pos0, pos1)
        self.delete('selection')
        self.drawSelection()

        if self.smartFixedColor.get():
            if self.selection == ((0, 0), (self.boardsize - 1, self.boardsize - 1)):
                self.fixedColor.set(1)
            else:
                self.fixedColor.set(0)

    def newPosition(self):
        """ Clear board, selection. """
        self.delete('selection')
        self.clear()
        self.delLabels()
        self.delMarks()
        self.delWildcards()
        self.selection = ((0, 0), (self.boardsize - 1, self.boardsize - 1))

        if self.smartFixedColor.get():
            self.fixedColor.set(1)

    # ---- snapshot & restore (for 'back' button)

    def snapshot(self):
        """ Return a dictionary which contains the data of all the objects
            currently displayed on the board, which are not stored in the SGF file.
            This means, at the moment: wildcards, and selection. """

        data = {}
        data['boardsize'] = self.boardsize
        data['status'] = [[self.getStatus(i, j) for j in range(self.boardsize)] for i in range(self.boardsize)]
        data['wildcards'] = copy(self.wildcards)
        data['selection'] = self.selection
        data['labels'] = copy(self.labels)
        return data

    def restore(self, d, small=False, **kwargs):
        """ Restore the data from a 'snapshot' dictionary. """

        if not 'fromSGF' in kwargs or not kwargs['fromSGF']:
            self.newPosition()
            self.boardsize = d['boardsize']
            for i in range(self.boardsize):
                for j in range(self.boardsize):
                    if d['status'][i][j] in ['B', 'W']:
                        self.setStatus(i, j, d['status'][i][j])
                        self.placeStone((i, j), d['status'][i][j])
            if not small:
                for p in d['labels']:
                    typ, text, dummy, color = d['labels'][p]
                    self.placeLabel(p, typ, text, color)

        for x, y in d['wildcards']:
            self.place_wildcard(x, y, d['wildcards'][(x, y)][1])
        if d['selection'] != ((0, 0), (self.boardsize - 1, self.boardsize - 1)) and d['selection'][1] != (0, 0):
            self.setSelection(d['selection'][0], d['selection'][1])


class SearchHistoryBoard(BoardWC):
    '''Used for the small boards in the list of previous searches. Does not display text labels.'''

    def __init__(self, *args, **kwargs):
        self.offset = kwargs.pop('offset', 0)

        for f in ['create_polygon', 'create_rectangle', 'create_line', 'create_image', 'create_oval', 'create_text']:
            setattr(self, f, self.add_offset(getattr(self, f)))
        BoardWC.__init__(self, *args, **kwargs)

    def add_offset(self, f):
        offset = self.offset

        def new_f(self, *args, **kwargs):
            new_args = [(x if i % 2 else x + offset) for i, x in enumerate(args)]
            f(self, *new_args, **kwargs)

        return new_f

    def placeLabel(self, pos, typ, text=None, color=None):
        """Labels are ignored. """

        return


# ---------------------------------------------------------------------------------------


class ESR_TextEditor(v.TextEditor):
    """The text editor which is used by the exportSearchResults function.
    It adds a button to include the complete game list to the TextEditor."""

    def __init__(self, master, style, t='', defpath='', font=None):
        v.TextEditor.__init__(self, t, defpath, font)
        self.mster = master
        self.style = style

        Button(self.buttonFrame, text=_('Include game list'), command=self.includeGameList).pack(side=LEFT)

    def includeGameList(self):
        separator = ' %%%\n' if self.style == 'wiki' else '\n'  # wiki/plain style
        self.text.insert(END, '\n\n!' + _('Game list') + '\n\n' + separator.join(self.mster.gamelist.get_all()))


# -------------------------------------------------------------------------------------

class DataWindow(v.DataWindow):

    def get_geometry(self):
        self.win.update_idletasks()
        try:
            l = [str(self.win.sash_coord(i)[1]) for i in range(5)]
        except:  # allow for DataWindow column having only five panes, if prevSearches are a tab in right hand column
            l = [str(self.win.sash_coord(i)[1]) for i in range(4)]
        return join(l, '|%')

    def set_geometry(self, s):
        l = split(s, '|%')
        for i in [4, 3, 2, 1, 0]:
            try:
                self.win.sash_place(i, 1, int(l[i]))
                self.win.update_idletasks()
            except:  # allow win to have only 5 panes
                pass

    def gamelistRelease(self, event):
        index1, index2 = v.DataWindow.gamelistRelease(self, event)
        if index1:
            self.mster.prevSearches.exchangeGames(self.mster.cursor, index1, index2)

# -------------------------------------------------------------------------------------


class GameListGUI(GameList, VScrolledList):
    """ This is a scrolled list which shows the game list. All the underlying data
        is contained in self.DBlist, which is a list of dictionaries containing the
        information for the single databases. self.DBlist[i] will contain the keys
        'name': name of the database, i.e. path to the *.db files
        'sgfpath': path to the SGF files
        'data': list of all games in the database.
                This is an instance of lkGameList
        """

    def __init__(self, parent, master, noGamesLabel, winPercLabel, gameinfo):

        self.mster = master
        GameList.__init__(self)

        self.taglook = {}

        # set up listbox
        VScrolledList.__init__(
                self,
                parent, 500, 0,
                self.get_data,
                get_data_ic=self.get_data_ic,
                font=master.standardFont)
        self.listbox.config(width=52, height=6)
        self.onSelectionChange = self.printGameInfo
        for key, command in [('<Return>', self.handleDoubleClick), ('<Control-v>', self.printSignature), ]:
            self.listbox.bind(key, command)
        for key, command in [('<Button-1>', self.onSelectionChange), ('<Double-1>', self.handleDoubleClick), ('<Shift-1>', self.handleShiftClick), ('<Button-3>', self.rightMouseButton)]:
            self.listbox.bind(key, command)
        self.noGamesLabel = noGamesLabel
        self.winPercLabel = winPercLabel
        self.gameinfo = gameinfo

    def get_data(self, i):
        return GameList.get_data(self, i, showTags=self.mster.options.showTags.get())

    def get_all(self):
        return [GameList.get_data(self, i, showTags=self.mster.options.showTags.get()) for i in range(len(self.gameIndex))]

    def get_data_ic(self, i):
        """Return taglook for specified line. (ic = itemconfig).
        """
        try:
            db, game = self.getIndex(i)
            ID, pos = self.DBlist[db]['data'].currentList[game]
            taglist = self.DBlist[db]['data'].getTagsID(ID, 0)
            if taglist:
                return self.taglook[str(taglist[0])]
        except:
            pass
        return {}

    def printSignature(self, event):
        try:
            index = self.get_index(int(self.listbox.curselection()[0]))
        except:
            return

        self.mster.logger.insert(END, GameList.printSignature(self, index) + '\n')

    def addTag(self, tag, index):
        GameList.addTag(self, tag, index)
        self.mster.selecttags(self.getTags(index))
        self.upd()

    def setTags(self, tags):
        try:
            index = self.get_index(int(self.listbox.curselection()[0]))
        except:
            return
        if index == -1:
            return
        DBindex, index = self.getIndex(index)
        if DBindex == -1:
            return
        newtags = set(tags)
        oldtags = set(self.DBlist[DBindex]['data'].getTags(index))

        for t in newtags - oldtags:
            self.DBlist[DBindex]['data'].setTag(t, index, index + 1)
        for t in oldtags - newtags:
            self.DBlist[DBindex]['data'].deleteTag(t, index)

    def reset(self):
        """ Reset the list, s.t. it includes all the games from self.data. """

        GameList.reset(self)
        self.clearGameInfo()

    def update(self):
        GameList.update(self, self.mster.options.sortCriterion.get(), self.mster.options.sortReverse.get())

        noOfG = self.noOfGames()
        if noOfG:
            Bperc = self.Bwins * 100.0 / noOfG
            Wperc = self.Wwins * 100.0 / noOfG
        self.total_in_list = noOfG
        self.noGamesLabel.config(
                text=_('%d games') % noOfG,
                font=self.mster.smallFont)
        if noOfG:
            self.winPercLabel.config(
                    text=_('B: {0:1.1f}%, W: {1:1.1f}%').format(Bperc, Wperc),
                    font=self.mster.smallFont)
        else:
            self.winPercLabel.config(
                    text='',
                    font=self.mster.smallFont)
        VScrolledList.reset(self)

    def printGameInfo(self, event, index=-1):
        """ Write game info of selected game to text frame below the list of games. """

        if index == -1:
            index = self.get_index(self.listbox.nearest(event.y))
            self.focus()
        try:
            t, t2 = GameList.printGameInfo(self, index)
        except:
            return

        self.gameinfo.configure(text_state=NORMAL)
        self.gameinfo.delete('1.0', END)
        self.gameinfo.insert('1.0', t)
        if t2:
            if t[-1] != '\n':
                self.gameinfo.insert(END, '\n')
            self.gameinfo.insert(END, t2, 'blue')
        self.gameinfo.configure(text_state=DISABLED)

        self.mster.selecttags(self.getIndicesTaglist(self.getTags(index)))

    def getIndicesTaglist(self, tags):
        l = [int(x) for x in self.customTags.keys()]
        l.sort()
        d = dict([[y, x + 1] for x, y in enumerate(l)])   # note x+1 because enumerate starts with 0, but we want to start with 1
        return [d[t] for t in tags]

    def rightMouseButton(self, event):

        index = self.get_index(self.listbox.nearest(event.y))
        if index == -1:
            return
        DBindex, index = self.getIndex(index)
        if DBindex == -1:
            return

        f1 = strip(os.path.join(self.DBlist[DBindex]['sgfpath'], self.DBlist[DBindex]['data'].getCurrent(index)[GL_FILENAME]))

        if find(f1, '[') != -1:
            f1, f2 = split(f1, '[')
            gameNumber = int(strip(f2)[:-1])
        else:
            gameNumber = 0

        filename = getFilename(f1)

        try:
            file = open(filename)
            sgf = file.read()
            file.close()
            c = Cursor(sgf, 1)
            rootNode = c.getRootNode(gameNumber)
        except IOError:
            showwarning(_('Error'), _('I/O Error'))
            return
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error'))
            return

        # backup = copy(rootNode.data)

        newRootNode = self.mster.gameinfo(rootNode)
        if (not newRootNode is None):  # FIXME  and backup != newRootNode.data:
            c.updateRootNode(newRootNode, gameNumber)
            try:
                s = c.output()
                file = open(filename, 'w')
                file.write(s)
                file.close()
            except IOError:
                showwarning(_('I/O Error'), _('Could not write to file ') + filename)

    def handleDoubleClick(self, event):
        """ This is called upon double-clicks."""

        index = self.get_index(int(self.listbox.curselection()[0]))
        self.addTag(SEEN_TAG, index)
        self.mster.openViewer(index)

    def handleShiftClick(self, event):
        index = self.listbox.nearest(event.y)
        index1 = self.listbox.curselection()
        if index1:
            self.listbox.select_clear(index1[0])
        self.listbox.select_set(index)
        self.onSelectionChange(event)
        self.addTag(SEEN_TAG, index)
        self.mster.altOpenViewer(index)

    def clearGameInfo(self):
        self.gameinfo.configure(text_state=NORMAL)
        self.gameinfo.delete('1.0', END)
        self.gameinfo.configure(text_state=DISABLED)

# ---------------------------------------------------------------------------------------


class TreeNode(list):
    """Node of a tree. self viewed as a list is the list of children. self.d is the data stored in the node."""

    def __init__(self, parent=None, data=None):
        self.parent = parent
        self.d = data if data else {}

    def add_child(self, data):
        list.append(self, TreeNode(parent=self, data=data))
        return self[-1]

    def level(self):
        return self.parent.level() + 1 if self.parent else 0

    def size(self):
        """Return number of elements in the tree with root *self*."""
        return 1 + sum([x.size() for x in self])

    def foreach(self, f, *args):
        """Apply f to each element in the tree."""
        f(self, *args)
        for x in self:
            x.foreach(f, *args)

    def traverse(self):
        yield self
        for child in self:
            for node in child.traverse():
                yield node

    def delete(self):
        # print 'TreeNode.delete', self.d.get('board', 'no board'), 'num children:', len(self)
        for child in self:
            child.parent = self.parent
        if self.parent:
            self.parent.extend(self)  # the children of node become children of its parent
            self.parent.remove(self)


class PrevSearchesStack(object):

    """ This class provides a tree which contains the data of the previous searches,
    s.t. one can return to the previous search with the back button.

    self.data is a tree of dicts with the following keys:
    * kw is the keyword dictionary passed to append(), the keywords being boardData, snapshot_ids, modeVar, cursorSn (see def append())
    * board is the copy of the board at this point
    * on_hold determines whether this item is protected agains deletion (0=no, 1=yes)

    *self.active* is a Boolean which states whether the current node is active
    (board has the red frame; position agrees with position on the large board)
    *self.current* is the node to which the back button will jump back
    """

    def __init__(self, maxLength, boardChanged, prevSF, master):
        self.data = TreeNode()
        self.data.d['root'] = True
        self.current = self.data
        self.active = False
        self.mster = master

        self.maxLength = maxLength
        self.boardChanged = boardChanged

        self.prevSF = prevSF
        self.labelSize = IntVar()
        self.labelSize.set(4)
        self.popupMenu = None

    def append(self, **kwargs):
        ''' keywords are
        boardData = self.board.snapshot()
        snapshot_ids = [ db['data'].snapshot() for db in self.gamelist.DBlist if not db['disabled'] ],
        modeVar=self.modeVar.get()
        cursorSn = [self.cursor, self.cursor.currentGame, v.pathToNode(self.cursor.currentN)]
        '''

        if self.mster.options.maxLengthSearchesStack.get() and self.data.size() >= self.mster.options.maxLengthSearchesStack.get():
            for node in self.data.traverse():
                if 'on_hold' in node.d and not node.d['on_hold']:
                    self.delete(node)
                    break

        b = SearchHistoryBoard(
                self.prevSF.interior(), self.mster.board.boardsize, (12, 6), 0,
                self.mster.labelFont, 1, None, self.mster.boardImg,
                self.mster.blackStones, self.mster.whiteStones,
                use_PIL=True, onlyOneMouseButton=0,
                square_board=False,
                offset=min(10 * self.current.level(), 100))  # small board
        b.resizable = 0
        b.pack(side=LEFT, expand=YES, fill=Y)
        b.update_idletasks()
        b.unbind_third_mouse_button()
        b.unbind('<Configure>', b.boundConf)
        b.unbind('<Shift-1>', b.bounds1)
        b.restore(kwargs['boardData'])
        b.tkraise('non-bg')
        b.resizable = 0

        self.prevSF.reposition()
        node = self.current.add_child(data={'kw': copy(kwargs), 'board': b, 'on_hold': False, })
        b.bound1 = b.bind('<1>', lambda event, self=self, l=node: self.click(l))
        b.bound3 = b.bind('<3>', lambda event, self=self, l=node: self.postMenu(event, l))
        self.select(node)
        self.prevSF.xview('moveto', 1.0)

        self.redraw()

    def postMenu(self, event, node):
        self.popupMenu = Menu(self.mster.dataWindow.window)
        self.popupMenu.config(tearoff=0)
        self.popupMenu.add_command(label=_('Delete'), command=lambda self=self, node=node: self.unpost_and_delete(node))

        if node.d['on_hold']:
            self.popupMenu.add_command(label=_('Release'), command=lambda self=self, node=node: self.unpost_and_release(node))
        else:
            self.popupMenu.add_command(label=_('Hold'), command=lambda self=self, node=node: self.unpost_and_hold(node))

        self.popupMenu.tk_popup(event.x_root, event.y_root)

    def unpost(self):
        if self.popupMenu:
            self.popupMenu.unpost()
            self.popupMenu = None

    def unpost_and_delete(self, node):
        self.unpost()
        self.delete(node)

    def unpost_and_hold(self, node):
        self.unpost()
        node.d['on_hold'] = True
        c = node.d['board'].getPixelCoord((21, 21), 1)[0]
        node.d['board'].create_rectangle(7, 7, c - 10, c - 10, fill='', outline='blue', width=2, tags='hold')

    def unpost_and_release(self, node):
        self.unpost()
        node.d['on_hold'] = False
        node.d['board'].delete('hold')

    def delete(self, node, reposition=True):
        node.delete()
        if not 'board' in node.d:
            # the root node, so there is nothing to do
            return

        b = node.d['board']
        if not b:
            return
        b.delete(ALL)
        b.unbind('<1>', b.bound1)
        b.unbind('<3>', b.bound3)
        b.pack_forget()
        b.destroy()

        if node == self.current:
            self.current = node.parent
            self.active = False

        #  Comment out the rebind code because I do not understand (anymore?) why it should
        #  be needed. Also, if we do this, shouldn't we unbind before binding?
        #
        #  def rebind(n):
        #      if 'board' in n.d:
        #          b = n.d['board']
        #          b.bound1 = b.bind('<1>', lambda event, self=self, l=n: self.click(l))
        #          b.bound3 = b.bind('<3>', lambda event, self=self, l=n: self.postMenu(event, l))
        #  self.data.foreach(rebind)

        if reposition:
            self.prevSF.reposition()

    def deleteFile(self, cursor):
        def f(node, del_fct):
            if 'kw' in node.d and node.d['kw']['cursorSn'][0] == cursor:
                del_fct(node, False)
        self.data.foreach(f, self.delete)
        self.prevSF.reposition()

    def deleteGame(self, cursor, game):
        def f(node, del_fct):
            if 'kw' in node.d and node.d['kw']['cursorSn'][0] == cursor:
                if node.d['kw']['cursorSn'][1] == game:
                    del_fct(node, False)
                elif da[0]['cursorSn'][1] > game:
                    da[0]['cursorSn'][1] -= 1
        self.data.foreach(f, self.delete)
        self.prevSF.reposition()

    def exchangeGames(self, cursor, index1, index2):
        if index1 == index2:
            return

        if index1 < index2:

            def f(node):
                if 'kw' in node.d and node.d['kw']['cursorSn'][0] == cursor:
                    if node.d['kw']['cursorSn'][1] == index1:
                        node.d['kw']['cursorSn'][1] = index2
                    elif index1 < da[0]['cursorSn'][1] <= index2:
                        node.d['kw']['cursorSn'][1] -= 1
        elif index1 > index2:

            def f(node):
                if 'kw' in node.d and node.d['kw']['cursorSn'][0] == cursor:
                    if node.d['kw']['cursorSn'][1] == index1:
                        node.d['kw']['cursorSn'][1] = index2
                    elif index2 <= node.d['kw']['cursorSn'][1] < index1:
                        node.d['kw']['cursorSn'][1] += 1
        self.data.foreach(f)

    def deleteNode(self, cursor, game, pathToNode):

        def f(node, del_fct):
            if 'kw' in node.d and node.d['kw']['cursorSn'][0] == cursor and node.d['kw']['cursorSn'][1] == game:
                j = 0
                p = node.d['kw']['cursorSn'][2]

                while j < len(p) and j < len(pathToNode) and p[j] == pathToNode[j]:
                    j += 1

                if j == len(pathToNode):
                    del_fct(node, False)
                elif j < len(pathToNode) and j < len(p) and p[j] > pathToNode[j]:
                    node.d['kw']['cursorSn'][2][j] -= 1
        self.data.foreach(f, self.delete)
        self.prevSF.reposition()

    def select(self, node):

        if node is None or node == self.data:
            return
        b = node.d['board']
        self.select_clear()

        c = b.getPixelCoord((21, 21), 1)[0]
        b.create_rectangle(7, 7, c - 9, c - 9, width=3, outline='red', tags='sel')

        self.active = True
        self.current = node
        l, r = self.prevSF.xview()
        if b.winfo_x() * 1.0/ self.prevSF.interior().winfo_width() < l:
            # b is to the left of the currently visible region (probably come here by "back to previous search" button),
            # so move the ScrolledFrame appropriately
            self.prevSF.xview('moveto', (b.winfo_x() * 1.0/ self.prevSF.interior().winfo_width()))

    def click(self, node):
        self.select(node)
        self.mster.back(self.current)

    def select_clear(self):
        if self.active:
            self.current.d['board'].delete('sel')
            self.active = False

    def pop(self):
        self.select_clear()
        if not self.data or self.current == self.data or self.current.parent == self.data:
            return

        self.current = self.current.parent
        return self.current

    def redraw(self):
        def unpack(node):
            if 'board' in node.d:
                node.d['board'].pack_forget()
        self.data.foreach(unpack)

        def pack(node):
            if 'board' in node.d:
                node.d['board'].pack(side=LEFT, expand=YES, fill=Y)
        self.data.foreach(pack)

    def clear(self):
        for db in self.mster.gamelist.DBlist:
            if db['disabled']:
                continue
            db['data'].delete_all_snapshots()

        def f(node, del_fct):
            if not 'root' in node.d:
                del_fct(node, False)
        self.data.foreach(f, self.delete)
        self.prevSF.reposition()
        self.active = False
        assert self.current == self.data

# ---------------------------------------------------------------------------------------


class Message(ScrolledText):
    """ A ScrolledText widget which is usually DISABLED (i.e. the user cannot
        enter any text), and which automatically scrolls down upon insertion. """

    def __init__(self, window):
        ScrolledText.__init__(self, window, height=8, width=45, relief=SUNKEN, wrap=WORD)
        self.config(state=DISABLED)

    def insert(self, pos, text):
        self.config(state=NORMAL)
        ScrolledText.insert(self, pos, text)
        self.see(END)
        self.update_idletasks()
        self.config(state=DISABLED)

    def delete(self, pos1, pos2):
        self.config(state=NORMAL)
        ScrolledText.delete(self, pos1, pos2)
        self.config(state=DISABLED)

# ---------------------------------------------------------------------------------------


class App(v.Viewer, KEngine):
    """ The main class of Kombilo. """

    def resize_statistics_canvas(self, event):
        self.statisticsCanv.config(width=event.width, height=event.height)
        self.dateProfileCanv.config(width=event.width, height=event.height)

    def display_date_profile(self):
        """
        Display date profile of current game list.
        """

        d = self.dateProfileRelative()
        m = max((y * 1.0 / z if z else 0) for x, y, z in d)
        if m == 0:
            self.display_bar_chart(self.dateProfileCanv, 'stat', title='-')
            return

        data = [{
            'black': y * 1.0 / (z * m) if z else 0,
            'label': ['%d' % x[0], '-', '%d' % (x[1] - 1, )],
            'label_top': ['%d/' % y, '%d' % z]} for x, y, z in d]

        fr = self.options.date_profile_from.get()
        to = self.options.date_profile_to.get()
        self.display_bar_chart_dates(
                self.dateProfileCanv, 'stat',
                data=self.gamelist.dates_relative(
                    fr=(fr - lk.DATE_PROFILE_START) * 12,
                    to=(to + 1 - lk.DATE_PROFILE_START) * 12 - 1,
                    chunk_size=self.options.date_profile_chunk_size.get()),
                fr=fr, to=to,
                title=_('Date profile (Each bar represents %d months)')
                    % self.options.date_profile_chunk_size.get())
        self.redo_date_profile = False

    def display_x_indices(self, canvas, fr, to, tag, canvas_fr, canvas_to):
        """
        Indices on x-axis for date profile etc.

        fr, to are years,

        canvas_fr, canvas_to are the left and right coordinates (given as canvas
        pixel coordinates) where the first/final year should be located
        """

        smallfont = self.smallFont
        xoffset = canvas_fr
        W = canvas_to - canvas_fr
        H = int(self.statisticsCanv.cget('height'))

        for i in range(6):
            year = fr + i * (to - fr) // 5
            coord = canvas_fr + i * W // 5
            canvas.create_text(
                    coord - 10, H * 16 // 18,
                    text=repr(year),
                    font=smallfont, anchor='nw', tags=tag)
            canvas.create_rectangle(
                    coord, H * 16 // 18 - 10,
                    coord + 1, H * 16 // 18,
                    outline='', fill='black', tags='stat')

        canvas.create_rectangle(
                -10 + xoffset,
                H * 16 // 18 - 5,
                W + 20 + xoffset,
                int(self.statisticsCanv.cget('height')) * 16 // 18 - 5,
                outline='', fill='black', tags='stat')

    def display_statistics(self):
        """
        Display statistical information on the last search on self.statisticsCanv.
        """

        noMatches = self.noMatches
        if not noMatches:
            return

        Bperc = self.Bwins * 100.0 / noMatches
        Wperc = self.Wwins * 100.0 / noMatches

        if not self.continuations:
            self.display_bar_chart(
                    self.statisticsCanv, 'stat',
                    title=_('{0} matches ({1}/{2}), B: {3:1.1f}%, W: {4:1.1f}%').format(noMatches, self.noMatches - self.noSwitched, self.noSwitched, Bperc, Wperc))
            return

        if self.options.statistics_by_date.get():
            font = self.smallFont
            smallfont = self.smallFont

            self.statisticsCanv.delete('stat')
            self.statisticsCanv.create_text(
                    20, 5,
                    text=_('{0} matches ({1}/{2}), B: {3:1.1f}%, W: {4:1.1f}%').format(
                        noMatches, self.noMatches - self.noSwitched, self.noSwitched, Bperc, Wperc),
                    font=font, anchor='nw', tags='stat')

            fr = self.options.date_profile_from.get()
            to = max(self.options.date_profile_to.get(), fr + 1)

            xoffset = int(self.statisticsCanv.cget('width')) // 6  # coordinate of first year
            W = int(self.statisticsCanv.cget('width')) * 6 // 7        # coordinate of last year
            yoffset = int(self.statisticsCanv.cget('height')) // 7
            H = int(self.statisticsCanv.cget('height')) * 6 // 7 - yoffset
            self.display_x_indices(
                    self.statisticsCanv, fr, to, 'stat', xoffset, W)

            def get_coord_for_date(dt):
                if dt < fr:
                    return xoffset
                elif dt > to:
                    return W
                return (dt - fr) * (W - xoffset) // (to - fr) + xoffset

            # split continuations up according to B/W
            continuations = []
            for cont in self.continuations:
                if cont.B:
                    cB = lk.Continuation(cont.gamelist)
                    cB.add(cont)
                    cB.W = 0
                    cB.x, cB.y, cB.label = cont.x, cont.y, cont.label
                    continuations.append(cB)
                if cont.W:
                    cW = lk.Continuation(cont.gamelist)
                    cW.add(cont)
                    cW.B = 0
                    cW.x, cW.y, cW.label = cont.x, cont.y, cont.label
                    continuations.append(cW)
            continuations.sort(cont_sort_criteria[self.untranslate_cont_sort_crit()])

            i = 0
            ctr = 0
            while i < 12 and ctr < len(continuations):
                cont = continuations[ctr]
                earliest = cont.earliest_B() if cont.B else cont.earliest_W()
                latest = cont.latest_B() if cont.B else cont.latest_W()
                average_date = cont.average_date_B() if cont.B else cont.average_date_W()
                became_popular = cont.became_popular_B() if cont.B else cont.became_popular_W()
                became_unpopular = cont.became_unpopular_B() if cont.B else cont.became_unpopular_W()
                ctr += 1

                if earliest > to or latest < fr:
                    continue

                left = get_coord_for_date(earliest)
                right = get_coord_for_date(latest)

                #print earliest, latest, average_date, became_popular, became_unpopular

                average_date = get_coord_for_date(average_date)
                became_popular = get_coord_for_date(became_popular)
                became_unpopular = get_coord_for_date(became_unpopular)

                self.statisticsCanv.create_text(
                        left - 15, i * H//12 + yoffset,
                        text=cont.label, font=font, tags='stat')
                self.statisticsCanv.create_text(
                        left - 25 - 5 * len(repr(cont.total())), i * H//12 + yoffset + 1,
                        text=repr(cont.total()), font=smallfont, tags='stat')
                self.statisticsCanv.create_rectangle(
                        left, i * H//12 + yoffset - 3,
                        right, i * H//12 + yoffset + 3,
                        fill='black' if cont.B else 'white',
                        outline='black' if cont.B else 'white', tags='stat')

                for dt, clr in [(average_date, 'green'), (became_popular, 'yellow'), (became_unpopular, 'red'), ]:
                    if xoffset < dt < W and right - left > 5:
                        self.statisticsCanv.create_rectangle(
                                dt - 3, i * H//12 + yoffset - 6,
                                dt + 3, i * H//12 + yoffset + 7,
                                fill=clr, outline=clr, tags='stat')

                i += 1

        else:
            width = int(self.statisticsCanv.cget('width')) * 15 // 18
            maxHeight = max(x.total() for x in self.continuations[:12])
            data = []
            for cont in self.continuations[:12]:
                data.append({
                    'black': (cont.B - cont.tB) * 1.0 / maxHeight,
                    self.options.Btenuki.get(): cont.tB * 1.0 / maxHeight,
                    'white': (cont.W - cont.tW) * 1.0 / maxHeight,
                    self.options.Wtenuki.get(): cont.tW * 1.0 / maxHeight,
                    'label': [
                        cont.label, '%1.1f' % (cont.wW * 100.0 / cont.W) if cont.W else '-',
                        '%1.1f' % (cont.wB * 100.0 / cont.B) if cont.B else '-'],
                    'label_top': ['%d' % (cont.B + cont.W)], })

            self.display_bar_chart(
                    self.statisticsCanv, 'stat',
                    data=data,
                    colors=[
                        self.options.Btenuki.get(),
                        'black',
                        'white',
                        self.options.Wtenuki.get()],
                    title=_('{0} matches ({1}/{2}), B: {3:1.1f}%, W: {4:1.1f}%').format(
                        noMatches, self.noMatches - self.noSwitched, self.noSwitched, Bperc, Wperc))

    def display_bar_chart_dates(self, canvas, tag, data, title='', fr=None, to=None):
        canvas.delete(tag)
        font = self.smallFont
        smallfont = self.smallFont

        canvas.create_text(20, 5, text=title, font=font, anchor='nw', tags=tag)
        if not data:
            return

        W = int(self.statisticsCanv.cget('width')) * 6 // 7 # x-coord of right-most bar
        xoffset = W // 8                             # x-coord of left-most bar
        H = int(self.statisticsCanv.cget('height')) * 6//7  # y-coord of lower edge of bars
        yoffset = int(self.statisticsCanv.cget('height')) // 6

        self.display_x_indices(canvas, fr, to, 'stat', xoffset, W)

        canvas.create_text(
                5, H - 10, text='0 %', font=smallfont, anchor='nw', tags=tag)
        if sum(data) == 0:
            return

        # indices on y-axis
        mx = max(data)
        canvas.create_text(
                2, yoffset - 10, text='%1.1f %%' % (mx * 100), font=smallfont, anchor='nw', tags=tag)
        canvas.create_text(
                4, (H+yoffset)//2 - 10,
                text='%1.1f %%' % (mx * 50), font=smallfont, anchor='nw', tags=tag)

        for x, y  in enumerate(data):
            xx = xoffset + int(x * (W-xoffset) / len(data))
            yy = (H - int(y * (H-yoffset) / mx)) if mx else 0
            if yy < H:
                canvas.create_rectangle(
                        xx, H,
                        xx + 4, yy, fill='black', tags=(tag, ))

    def display_bar_chart(self, canvas, tag, colors=[], data=[], title=''):
        """
        Display a bar chart on canvas.

        color is a list of colors, e.g. ['black', 'yellow', 'white'].

        title is printed above the bar chart

        data is a list, one entry per column to be displayed.

        Each entry of data is a dictionary which maps each color to a number
        between 0 and 1, and optionally has entries "label": list of
        text_of_label for labels below bar, 'label_top': text of label above
        bar.
        """

        canvas.delete(tag)

        font = self.smallFont
        smallfont = self.smallFont

        W = int(self.statisticsCanv.cget('width')) * 6 // 7
        H = int(self.statisticsCanv.cget('height'))
        bar_width = W // 12
        text_height = H // 18

        canvas.create_text(5, 5, text=title, font=font, anchor='nw', tags=tag)

        for i, column in enumerate(data):
            ht = 3 * text_height
            for l in column.get('label', []):
                canvas.create_text((i + 1) * bar_width, H - ht, text=l, font=smallfont, tags=tag)
                ht -= text_height

            ht = 0
            for c in colors:
                if column[c]:
                    v = int(column[c] * (H - 8*text_height))
                    canvas.create_rectangle(
                            (i + 1) * bar_width - bar_width // 2 + 4,
                            H - 4*text_height - ht - v,
                            (i + 2) * bar_width - bar_width // 2 - 4,
                            H - 4*text_height - ht, fill=c, outline='', tags=tag)
                    ht += v
            for j, l in enumerate(column.get('label_top', [])):
                canvas.create_text(
                        (i + 1) * bar_width,
                        H - 5*text_height - ht - 10 * (len(column['label_top']) - j),
                        font=smallfont, text=l, tags=tag)

    def clearGI(self):
        self.pbVar.set('')
        self.pwVar.set('')
        self.pVar.set('')
        self.evVar.set('')
        self.frVar.set('')
        self.toVar.set('')
        self.awVar.set('')
        self.sqlVar.set('')
        self.referencedVar.set(0)

    def historyGI_back(self):
        if not self.history_GIsearch:
            return
        self.history_GIS_index -= 1
        if self.history_GIS_index == -1:
            self.history_GIS_index = len(self.history_GIsearch) - 1

        varList = [self.pbVar, self.pwVar, self.pVar, self.evVar, self.frVar, self.toVar, self.awVar, self.sqlVar, self.referencedVar]

        for i, var in enumerate(varList):
            var.set(self.history_GIsearch[self.history_GIS_index][i])

    def historyGI_fwd(self):
        if not self.history_GIsearch:
            return
        self.history_GIS_index += 1
        if self.history_GIS_index == len(self.history_GIsearch):
            self.history_GIS_index = 0
        varList = [self.pbVar, self.pwVar, self.pVar, self.evVar, self.frVar, self.toVar, self.awVar, self.sqlVar, self.referencedVar]

        for i, var in enumerate(varList):
            var.set(self.history_GIsearch[self.history_GIS_index][i])

    def doGISearch(self):
        """ Carry out the search for the parameters in *Var. All non-empty Var's
        have to match at the same time. In the case of pbVar, pwVar, pVar, evVar,
        the string has to occur somewhere in PB[ ...] (...), not necessarily at the
        beginning. For the date, the first four-digit number in DT[] is compared
        to frVar and toVar."""

        if not self.gamelist.noOfGames():
            self.reset()

        pbVar = self.pbVar.get().encode('utf-8')
        pwVar = self.pwVar.get().encode('utf-8')
        pVar = self.pVar.get().encode('utf-8')
        evVar = self.evVar.get().encode('utf-8')
        frVar = self.frVar.get()
        toVar = self.toVar.get()
        awVar = self.awVar.get().encode('utf-8')
        sqlVar = self.sqlVar.get().encode('utf-8')
        refVar = self.referencedVar.get()

        self.history_GIsearch.append((pbVar, pwVar, pVar, evVar, frVar, toVar, awVar, sqlVar, refVar))
        self.history_GIS_index = len(self.history_GIsearch) - 1

        if frVar:
            if re.match('\d\d\d\d-\d\d-\d\d', frVar):
                pass
            elif re.match('\d\d\d\d-\d\d', frVar):
                frVar += '-01'
            elif re.match('\d\d\d\d', frVar):
                frVar += '-01-01'
            else:
                frVar = ''

        if toVar:
            if re.match('\d\d\d\d-\d\d-\d\d', toVar):
                pass
            elif re.match('\d\d\d\d-\d\d', toVar):
                toVar += '-31'
            elif re.match('\d\d\d\d', toVar):
                toVar += '-12-31'
            else:
                toVar = ''

        if not (pbVar or pwVar or pVar or evVar or frVar or toVar or awVar or sqlVar or refVar):
            return

        queryl = []
        for key, val in [('PB', pbVar), ('PW', pwVar), ('ev', '%' + evVar), ('sgf', '%' + awVar)]:
            if val and val != '%':
                queryl.append("%s like '%s%%'" % (key, val.replace("'", "''")))
        if pVar:
            queryl.append("(PB like '%s%%' or PW like '%s%%')" % (pVar.replace("'", "''"), pVar.replace("'", "''")))
        if frVar:
            queryl.append("DATE >= '%s'" % frVar)
        if toVar:
            queryl.append("DATE <= '%s'" % toVar)
        if sqlVar:
            queryl.append("(%s)" % sqlVar)

        if refVar:
            self.tagSearch(None, self.gamelist.customTags[str(REFERENCED_TAG)][0])
        if not (pbVar or pwVar or pVar or evVar or frVar or toVar or awVar or sqlVar):
            return

        query = ' and '.join(queryl)

        self.gamelist.clearGameInfo()
        self.configButtons(DISABLED)
        self.progBar.start(50)
        currentTime = time.time()

        self.board.delLabels()
        if self.cursor:
            try:
                self.leaveNode()
                self.displayLabels(self.cursor.currentNode())
            except:
                showwarning(_('Error'), _('SGF Error'))

        try:
            self.gameinfoSearch(query)
        except lk.DBError:
            self.logger.insert(END, (_('Game info search, query "%s"') % query.decode('utf8')) + ', ' + _('Database error\n') + '\n')
            self.gamelist.reset()
        else:
            self.logger.insert(END, (_('Game info search, query "%s"') % query.decode('utf8')) + ', ' + _('%1.1f seconds') % (time.time() - currentTime) + '\n')

        self.progBar.stop()
        self.redo_date_profile = True
        self.notebookTabChanged()
        self.configButtons(NORMAL)


    def find_duplicates_GUI(self):
        self.logger.insert('end', _('Searching for duplicates') + '\n\n')
        text = []
        d = self.find_duplicates(strict=self.options.strictDuplCheck.get())
        dbs = {}
        i = 0
        text.append(_('Databases:') + '\n')
        for index, db in enumerate(self.gamelist.DBlist):
            if db['disabled']:
                continue
            text.append('[%d] %s\n' % (i, db['sgfpath']))
            dbs[i] = index
            i += 1
        text.append('-----------------------------------------------\n\n')

        for k in d:
            for game in [d[k][i:i+2] for i in range(0, len(d[k]), 2)]:
                DBindex = dbs[game[0]]
                index = self.gamelist.DBlist[DBindex]['data'].find_by_ID(game[1])
                text.append('[%d] %s: %s - %s\n' % (game[0], self.gamelist.DBlist[DBindex]['data'][index][GL_FILENAME],
                                                    self.gamelist.DBlist[DBindex]['data'][index][GL_PW],
                                                    self.gamelist.DBlist[DBindex]['data'][index][GL_PB]))
            text.append('-----------------------------------------------\n')
        v.TextEditor(''.join(text), self.sgfpath, self.monospaceFont)


    def sigSearch(self):
        """ Search a game by its Dyer signature (sgf coord. of moves 20, 40, 60, 31, 51, 71)."""

        if not self.gamelist.noOfGames():
            self.reset()

        window = Toplevel(takefocus=0)
        window.title(_('Signature Search'))

        m20 = StringVar()
        m40 = StringVar()
        m60 = StringVar()
        m31 = StringVar()
        m51 = StringVar()
        m71 = StringVar()

        l1 = Label(window, text=_('Move 20'))
        e1 = Entry(window, width=4, textvariable=m20)
        l2 = Label(window, text=_('Move 40'))
        e2 = Entry(window, width=4, textvariable=m40)
        l3 = Label(window, text=_('Move 60'))
        e3 = Entry(window, width=4, textvariable=m60)
        l4 = Label(window, text=_('Move 31'))
        e4 = Entry(window, width=4, textvariable=m31)
        l5 = Label(window, text=_('Move 51'))
        e5 = Entry(window, width=4, textvariable=m51)
        l6 = Label(window, text=_('Move 71'))
        e6 = Entry(window, width=4, textvariable=m71)

        for i, (label, entry) in enumerate([(l1, e1), (l2, e2), (l3, e3)]):
            label.grid(row=1, column=2 * i)
            entry.grid(row=1, column=2 * i + 1)

        for i, (label, entry) in enumerate([(l4, e4), (l5, e5), (l6, e6)]):
            label.grid(row=2, column=2 * i)
            entry.grid(row=2, column=2 * i + 1)

        e1.focus()

        bs = Button(window, text=_('Search'),
                    command=lambda self=self, window=window, m20=m20, m40=m40, m60=m60, m31=m31, m51=m51, m71=m71: self.doSigSearch(window, m20, m40, m60, m31, m51, m71))
        bq = Button(window, text=_('Cancel'), command=window.destroy)

        window.protocol('WM_DELETE_WINDOW', window.destroy)

        bo = v.Board(window, 19, (5, 18), 0, self.labelFont, 0, None, self.boardImg, self.blackStones, self.whiteStones)
        bo.state('normal', lambda pos, self=self, window=window,
                 e1=e1, e2=e2, e3=e3, e4=e4, e5=e5, e6=e6, m20=m20, m40=m40, m60=m60, m31=m31,
                 m51=m51, m71=m71: self.sigSearchGetCoord(pos, window, e1, e2, e3, e4, e5, e6, m20, m40, m60, m31, m51, m71))
        bo.shadedStoneVar.set(1)
        bo.grid(row=0, column=0, columnspan=6)
        bq.grid(row=3, column=4, columnspan=2)
        bs.grid(row=3, column=2, columnspan=2)

        window.update_idletasks()
        # window.focus()
        window.grab_set()
        window.wait_window()

    def sigSearchGetCoord(self, pos, window, e1, e2, e3, e4, e5, e6, m20, m40, m60, m31, m51, m71):
        """ This writes the coordinates of a clicked-at point on the board to
        the currently focused entry. """

        f = window.focus_get()
        m = None

        for f_old, f_new, m_new in [(e1, e2, m20), (e2, e3, m40), (e3, e4, m60), (e4, e5, m31), (e5, e6, m51), (e6, e1, m71)]:
            if f is f_old:
                f_new.focus()
                m = m_new
                break

        p = chr(pos[0] + ord('a')) + chr(pos[1] + ord('a'))
        if m:
            m.set(p)

    def doSigSearch(self, window, m20, m40, m60, m31, m51, m71):
        window.destroy()
        self.configButtons(DISABLED)
        self.gamelist.clearGameInfo()
        self.progBar.start(50)
        currentTime = time.time()
        self.board.delLabels()

        sig = ''
        for m in [m20, m40, m60, m31, m51, m71]:
            if len(m.get()) != 2 or not (m.get()[0] in 'abcdefghijklmnopqrst' and m.get()[1] in 'abcdefghijklmnopqrst'):
                sig += '__'
            else:
                sig += m.get()

        if self.cursor:
            try:
                self.displayLabels(self.cursor.currentNode())
            except:
                pass

        self.signatureSearch(sig)
        self.progBar.stop()
        self.logger.insert(END, (_('Signature search, %1.1f seconds, searching for') % (time.time() - currentTime)) + '\n%s\n' % sig)
        self.redo_date_profile = True
        self.notebookTabChanged()
        self.configButtons(NORMAL)

    def back(self, target=None):
        """ Go back to target_values search (restore board, game list etc.)
        If an SGF file is currently loaded (and was loaded at the time of
        the target_valuesious search too), the position of its cursor is
        restored too.

        target: a node entry in the search history tree; the board etc. will be restored to the information in here

        If this is called without arguments, then target_values and selected are
        retrieved from prevSearches.pop.
        """

        self.leaveNode()

        if target is None:
            target = self.prevSearches.pop()
            if target is None:
                self.reset()
                return
        target_values = target.d['kw']

        self.comments.delete('1.0', END)
        self.gamelist.clearGameInfo()
        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0

        cu = target_values['cursorSn']
        if cu:
            found = 0
            for i, fi in enumerate(self.filelist):
                if fi[3] == cu[0]:
                    if i != self.currentFileNum:
                        self.changeCurrentFile(None, i)
                    found = 1
            if found:
                if cu[1] != self.cursor.currentGame:
                    self.changeCurrentGame(None, cu[1])
                else:
                    try:
                        self.cursor.game(self.cursor.currentGame)
                    except:
                        showwarning(_('Error'), _('SGF Error'))
                        return
                self.board.newPosition()
                self.moveno.set('0')
                self.capB, self.capW = 0, 0
                self.displayNode(self.cursor.getRootNode(self.cursor.currentGame))
                for i in cu[2]:
                    self.next(i, 0)
                self.cursor.seeCurrent()

                self.board.restore(target_values['boardData'], fromSGF=True)
                self.sel = self.board.selection      # used in self.showCont()
                self.capVar.set(_('Cap - B: {0}, W: {1}').format(self.capB, self.capW))
            else:
                showwarning(_('Error'), _('SGF File not found'))

        # restore variables
        mv, fc, fa, ml, nextM = target_values['variables']
        self.modeVar.set(mv)
        self.board.currentColor = mv[:5]
        self.fixedColorVar.set(fc)
        self.fixedAnchorVar.set(fa)
        self.moveLimit.set(ml)
        self.nextMoveVar.set(nextM)

        for i, sid in target_values['snapshot_ids']:
            self.gamelist.DBlist[i]['data'].restore(sid)

        # restore currentSearchPattern
        i, sid = target_values['snapshot_ids'][0]
        self.currentSearchPattern = self.gamelist.DBlist[i]['data'].mrs_pattern

        self.continuations = []
        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0

        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
            gl = db['data']
            self.lookUpContinuations(gl)

        self.set_labels(self.untranslate_cont_sort_crit())
        if self.showContinuation.get():
            self.showCont()
        self.board.changed.set(0)
        self.display_statistics()
        self.gamelist.update()
        self.prevSearches.select(target)
        self.redo_date_profile = True
        self.notebookTabChanged()

    def completeReset(self):
        self.reset()
        self.board.newPosition()
        self.prevSearches.clear()
        self.changeCurrentFile(None, 0)
        for i in range(len(self.filelist)):
            self.delFile()

        self.gotoVar.set('')

        self.clearGI()
        self.history_GIsearch = []
        self.history_GIS_index = -1

        self.moveLimit.set(250)
        if not self.options.smartFixedColor.get():
            self.fixedColorVar.set(0)
        self.fixedAnchorVar.set(0)
        self.nextMoveVar.set(0)

        self.showContinuation.set(1)
        self.oneClick.set(0)
        self.redo_date_profile = True
        self.notebookTabChanged()

    def reset(self):
        """ Reset the game list. """

        self.gamelist.reset()

        self.progBar.stop()
        self.statisticsCanv.delete('stat')
        self.board.delLabels()
        if self.cursor:
            try:
                self.leaveNode()
                self.displayLabels(self.cursor.currentNode())
            except:
                pass
        self.redo_date_profile = True
        self.notebookTabChanged()
        self.prevSearches.select_clear()
        self.prevSearches.current = self.prevSearches.data

    def reset_start(self):
        self.reset()
        self.start()

    def showCont(self):
        """ Toggle 'show continuations'. """

        if not self.currentSearchPattern:
            return
        if self.showContinuation.get():
            # need to test for this here since showCont is invoked as command
            # from menu upon changing this option

            # There might be labels on the board, but we just leave them: Either
            # there are "overwritten" by one of the continuations below, or they
            # do not correspond to a continuation and hence should stay. (The
            # pattern search takes care of not using labels which are
            # already on the board.)

            for c in self.continuations:
                if not c.B:
                    color = 'white'
                elif not c.W:
                    color = 'black'
                else:
                    color = self.options.labelColor.get()
                self.board.placeLabel((c.x + self.sel[0][0], c.y + self.sel[0][1]), '+LB', c.label, color)
        else:
            self.board.delLabels()
            if self.cursor:
                try:
                    self.displayLabels(self.cursor.currentNode())
                except:
                    pass

    def doubleClick(self, event):
        if not self.oneClick.get():
            self.search()

    # ---- putting stones on the board, and navigation in SGF file ----------------------

    def nextMove(self, pos):
        self.board.delLabels()
        self.board.delMarks()

        if pos in self.board.wildcards:
            self.board.delete(self.board.wildcards.pop(pos))

        v.Viewer.nextMove(self, pos)

        if self.oneClick.get() and (self.board.selection[1] == (0, 0) or
                                    (self.board.selection[0][0] <= pos[0] <= self.board.selection[1][0] and self.board.selection[0][1] <= pos[1] <= self.board.selection[1][1])):
            self.search()

    def next(self, n=0, markCurrent=True):
        if not self.cursor or self.cursor.atEnd:
            return
        self.board.delLabels()
        self.board.delWildcards()

        if v.Viewer.next(self, n, markCurrent):
            return 1
        return 0

    def prev(self, markCurrent=1):
        if not self.cursor or self.cursor.atStart:
            return
        self.board.delLabels()

        self.board.delWildcards()

        v.Viewer.prev(self, markCurrent)

    def start(self, update=1):
        self.board.newPosition()
        v.Viewer.start(self, update)

        self.statisticsCanv.delete('stat')

        self.board.delWildcards()

    def end(self):
        v.Viewer.end(self)

    def delStone(self, event):
        x, y = self.board.getBoardCoord((event.x, event.y), 1)
        if not x * y:
            return

        if (x, y) in self.board.wildcards:
            self.board.delete(self.board.wildcards.pop((x, y)))
        else:
            Viewer.delStone(self, event)

    def delVar(self):
        self.prevSearches.deleteNode(self.cursor, self.cursor.currentGame, self.cursor.currentNode().pathToNode())
        v.Viewer.delVar(self)

    def delGame(self):
        self.prevSearches.deleteGame(self.cursor, self.cursor.currentGame)
        v.Viewer.delGame(self)

    def delFile(self):
        self.prevSearches.deleteFile(self.cursor)
        return v.Viewer.delFile(self)

    # -------------------------------------------------

    def exportCurrentPos(self):

        # TODO put part of this into board.abstractBoard

        numberOfMoves = IntVar()
        exportMode = StringVar()

        dialog = Toplevel()
        dialog.title(_('Export position'))
        dialog.protocol('WM_DELETE_WINDOW', lambda: None)

        f1 = Frame(dialog)
        f2 = Frame(dialog)
        f3 = Frame(dialog)

        for f in [f1, f2, f3]:
            f.pack(side=TOP, fill=BOTH, expand=YES, pady=5)

        Label(f1, text=_('Number of moves to be shown (0-9):')).pack(side=TOP)
        Entry(f1, textvariable=numberOfMoves).pack(side=TOP)

        Label(f2, text=_('Export mode:')).pack(side=LEFT)
        Radiobutton(f2, text=_('ASCII'), variable=exportMode, value='ascii', highlightthickness=0).pack(side=LEFT)
        Radiobutton(f2, text=_('Wiki'), variable=exportMode, value='wiki', highlightthickness=0).pack(side=LEFT)

        Button(f3, text=_('OK'), command=dialog.destroy).pack(anchor=E)

        dialog.update_idletasks()
        dialog.focus()
        dialog.grab_set()
        dialog.wait_window()

        n = numberOfMoves.get()

        l = []
        t = []

        for i in range(19):
            l.append(['. '] * 19)  # TODO boardsize

        for i in range(19):
            for j in range(19):
                if self.board.getStatus(j, i) == 'B':
                    l[i][j] = 'X '
                elif self.board.getStatus(j, i) == 'W':
                    l[i][j] = 'O '
                if (j, i) in self.board.wildcards:
                    l[i][j] = '* '

        # mark hoshis with ,'s

        for i in range(3):  # TODO boardsize
            for j in range(3):
                ii = 3 + 6 * i
                jj = 3 + 6 * j
                if l[ii][jj] == '. ':
                    l[ii][jj] = ', '

        remarks = []
        nextMove = 'B'

        node = self.cursor.currentNode()

        for i in range(1, min(n, 10) + 1):
            if i == 10:
                ii = '0 '
            else:
                ii = repr(i) + ' '

            node = Node(node.next)
            if not node:
                break
            if 'B' in node:
                color = 'B'
            elif 'W' in node:
                color = 'W'
            else:
                continue

            if i == 1:
                nextMove = color

            pos = self.convCoord(node[color][0])
            if not pos:
                continue

            if l[pos[1]][pos[0]] in ['. ', ', ']:
                l[pos[1]][pos[0]] = ii
            elif l[pos[1]][pos[0]] in [repr(i) + ' ' for i in range(10)]:
                remarks.append(ii + 'at ' + l[pos[1]][pos[0]] + '\n')
            elif l[pos[1]][pos[0]] in ['X ', 'O ']:
                remarks.append(ii + 'at ' + 'ABCDEFGHJKLMNOPQRST'[pos[0]] + repr(18 - pos[1] + 1) + '\n')  # TODO boardsize

        if exportMode.get() == 'ascii':
            for i in range(19):
                l[i].insert(0, '%2d  ' % (19 - i))

            l.insert(0, '')
            l.insert(0, _('    A B C D E F G H J K L M N O P Q R S T'))

            if n:
                if nextMove == 'B':
                    remarks.append(_('Black = 1\n'))
                elif nextMove == 'W':
                    remarks.append(_('White = 1\n'))
        else:
            for i in range(19):
                l[i].insert(0, '$$ | ')
                l[i].append('|')

            l.insert(0, '$$  ---------------------------------------')
            l.insert(0, '$$' + nextMove)
            l.append('$$  ---------------------------------------')

        for line in l:
            t.append(join(line, '') + '\n')

        t.append('\n')
        t.extend(remarks)

        ESR_TextEditor(self, exportMode.get(), join(t, ''), self.sgfpath, self.monospaceFont)

    def exportText(self):
        """Export some information on the previous search in a small text editor,
        where it can be edited and saved to a file. """

        exportMode = StringVar()

        dialog = Toplevel()
        dialog.title(_('Export position'))
        dialog.protocol('WM_DELETE_WINDOW', lambda: None)

        f1 = Frame(dialog)
        f2 = Frame(dialog)
        f3 = Frame(dialog)

        for f in [f1, f2, f3]:
            f.pack(side=TOP, fill=BOTH, expand=YES, pady=5)

        Label(f1, text=_('Export mode:')).pack(side=LEFT)
        Radiobutton(f1, text=_('ASCII'), variable=exportMode, value='ascii', highlightthickness=0).pack(side=LEFT)
        Radiobutton(f1, text=_('Wiki'), variable=exportMode, value='wiki', highlightthickness=0).pack(side=LEFT)

        showAllCont = IntVar()
        Checkbutton(f2, text=_('Show all continuations'), variable=showAllCont, highlightthickness=0).pack(side=LEFT)

        Button(f3, text=_('OK'), command=dialog.destroy).pack(anchor=E)

        dialog.update_idletasks()
        dialog.focus()
        dialog.grab_set()
        dialog.wait_window()

        t = self.patternSearchDetails(exportMode.get(), showAllCont.get())

        ESR_TextEditor(self, exportMode.get(), join(t, ''), self.sgfpath, self.monospaceFont)

    def printPattern(self, event=None):
        if self.currentSearchPattern:
            self.logger.insert(END, self.currentSearchPattern.printPattern() + '\n')

    # ----------------------------------------------------------------------------------

    def openViewer_external(self, filename, gameNumber, moveno):
        if self.options.altViewerVar1.get():
            # if moveno refers to a hit in a variation, it is a tuple with several entries
            # an external viewer can (probably) not understand this
            if len(moveno) != 1:
                moveno = 0
            else:
                moveno = moveno[0]

            if sys.platform[:3] == 'win':
                filenameQU = '"' + filename + '"'
            else:
                filenameQU = filename

            s1 = self.options.altViewerVar1.get()
            if os.name == 'posix':
                s1 = s1.replace('~', os.getenv('HOME'))

            s2 = replace(self.options.altViewerVar2.get(), '%f', filenameQU)
            s2 = replace(s2, '%F', filename)
            s2 = replace(s2, '%n', str(moveno))
            s2 = replace(s2, '%g', str(gameNumber))

            try:

                if sys.platform[:3] == 'win':
                    os.spawnv(os.P_DETACH, s1, ('"' + s1 + '"', ) + tuple(split(s2)))
                        # it is necessary to quote the
                        # path if it contains blanks

                elif os.path.isfile(s1):
                    pid = os.fork()
                    if pid == 0:
                        os.execv(s1, (s1, ) + tuple(split(s2)))
                        showwarning(_('Error'), _('Error starting SGF viewer'))
                else:
                    showwarning(_('Error'), _('%s not found.') % s1)
            except OSError:
                showwarning(_('Error'), _('Error starting SGF viewer'))

        else:
            window = Toplevel()
            window.withdraw()

            viewer = v.Viewer(window)
            viewer.frame.focus_force()

            window.protocol('WM_DELETE_WINDOW', viewer.quit)

            viewer.openFile(*os.path.split(filename))
            viewer.changeCurrentFile(None, 1)
            viewer.delFile()

            if gameNumber:
                viewer.dataWindow.gamelist.list.select_clear(0)
                viewer.dataWindow.gamelist.list.select_set(gameNumber)
                viewer.dataWindow.gamelist.list.see(gameNumber)
                viewer.changeCurrentGame(None, gameNumber)

            if self.options.jumpToMatchVar.get():
                viewer.jumpToNode(moveno)

            viewer.frame.update_idletasks()
            viewer.boardFrame.update_idletasks()
            viewer.boardFrame.focus()
        self.gamelist.listbox.focus()

    def openViewer_internal(self, filename, gameNumber, moveno):

        self.openFile(*os.path.split(filename), do_not_change_sgfpath=True)

        if gameNumber:
            self.dataWindow.gamelist.list.select_clear(0)
            self.dataWindow.gamelist.list.select_set(gameNumber)
            self.dataWindow.gamelist.list.see(gameNumber)
            self.changeCurrentGame(None, gameNumber)

        if self.options.jumpToMatchVar.get():
            self.jumpToNode(moveno)
        self.boardFrame.focus()

    def altOpenViewer(self, no):
        """ Open game from game list in SGF viewer - "alternative mode", i.e. if the default is to
        open an external viewer, this method will load the game into the internal list, and vice versa."""

        filename, gameNumber, moveno = self.getFilename(no)
        if not self.options.externalViewer.get():
            self.openViewer_external(filename, gameNumber, moveno)
        else:
            self.openViewer_internal(filename, gameNumber, moveno)

    def openViewer(self, no):
        """ Open game from game list in SGF viewer. """

        filename, gameNumber, moveno = self.getFilename(no)
        if self.options.externalViewer.get():
            self.openViewer_external(filename, gameNumber, moveno)
        else:  # open internal viewer
            self.openViewer_internal(filename, gameNumber, moveno)

    # ---- administration of DBlist ----------------------------------------------------

    def addDB(self):
        self.editDB_OK.config(state=DISABLED)
        self.saveProcMess.config(state=DISABLED)

        dbp = str(askdirectory(parent=self.editDBlistWindow, initialdir=self.datapath))

        if not dbp:
            self.editDB_OK.config(state=NORMAL)
            self.saveProcMess.config(state=NORMAL)
            return
        else:
            dbp = os.path.normpath(dbp)

        self.datapath = os.path.split(dbp)[0]

        if self.options.storeDatabasesSeparately.get() and self.options.whereToStoreDatabases.get():
            datap = (self.options.whereToStoreDatabases.get(), 'kombilo')
            if os.path.exists(datap[0]) and not os.path.isdir(datap[0]):
                showwarning(_('Error'), _('%s is not a directory.') % datap[0])
                self.editDB_OK.config(state=NORMAL)
                self.saveProcMess.config(state=NORMAL)
                return
            elif not os.path.exists(datap[0]):
                if askokcancel(_('Error'), _('Directory %s does not exist. Create it?') % datap[0]):
                    try:
                        os.makedirs(datap[0])
                    except:
                        showwarning(_('Error'), _('%s could not be created.') % datap[0])
                        self.editDB_OK.config(state=NORMAL)
                        self.saveProcMess.config(state=NORMAL)
                        return
                else:
                    self.editDB_OK.config(state=NORMAL)
                    self.saveProcMess.config(state=NORMAL)
                    return
        else:
            datap = ('', '#')  # this means: same as dbpath

        self.callAddDB(dbp, datap)

        self.editDB_OK.config(state=NORMAL)
        self.saveProcMess.config(state=NORMAL)

    def callAddDB(self, dbp, datap, index=None):
        tagAsPro = {'Never': 0, 'All games': 1, 'All games with p-rank players': 2, }[self.untranslate_tagAsPro()]
        algos = 0
        if self.options.algo_hash_full.get():
            algos |= lk.ALGO_HASH_FULL
        if self.options.algo_hash_corner.get():
            algos |= lk.ALGO_HASH_CORNER
        KEngine.addDB(self, dbp, datap, recursive=self.options.recProcess.get(), filenames=self.filenamesVar.get(),
                      acceptDupl=self.options.acceptDupl.get(), strictDuplCheck=self.options.strictDuplCheck.get(),
                      tagAsPro=tagAsPro, processVariations=self.options.processVariations.get(), algos=algos,
                      messages=self.processMessages, progBar=self.progBar, showwarning=showwarning, index=index)

    def addOneDB(self, arguments, dbpath):
        if KEngine.addOneDB(self, arguments, dbpath):
            index = arguments[-1] if not arguments[-1] is None else END
            db = self.gamelist.DBlist[int(index) if index != END else -1]
            db_date = getDateOfFile(os.path.join(db['name'][0], db['name'][1] + '.da'))
            self.db_list.insert(index, dbpath + ' (%s, %d %s)' % (db_date, db['data'].size(), _('games')))
            self.db_list.list.see(index)
            self.prevSearches.clear()

    def removeDB(self):
        while self.db_list.list.curselection():
            index = self.db_list.list.curselection()[0]
            self.db_list.delete(index)
            i = int(index)
            datap = self.gamelist.DBlist[i]['name']
            dbpath = self.gamelist.DBlist[i]['sgfpath']
            del self.gamelist.DBlist[i]['data']  # make sure memory is freed and db connection closed
                                                 # (otherwise, on Windows, we might not be able to delete the db file)
            del self.gamelist.DBlist[i]

            try:
                os.remove(os.path.join(datap[0], datap[1] + '.db'))
                os.remove(os.path.join(datap[0], datap[1] + '.da'))
            except:
                showwarning(_('I/O Error'), _('Could not delete the database files.'))
            try:  # these files will only be present if hashing algos were used, so do not issue a warning when they are not found
                os.remove(os.path.join(datap[0], datap[1] + '.db1'))
                os.remove(os.path.join(datap[0], datap[1] + '.db2'))
            except:
                pass
            self.processMessages.insert(END, _('Removed %s.') % dbpath + '\n')

        self.gamelist.reset()
        self.prevSearches.clear()
        self.currentSearchPattern = None

    def reprocessDB(self):

        # export all tags
        from tempfile import NamedTemporaryFile
        f = NamedTemporaryFile(delete=False)
        tagfilename = f.name
        f.close()
        self.gamelist.exportTags(tagfilename, [int(x) for x in self.gamelist.customTags.keys() if not int(x) == lk.HANDI_TAG])

        # delete and add all selected databases
        for index in self.db_list.list.curselection():
            i = int(index)

            self.editDB_OK.config(state=DISABLED)
            self.saveProcMess.config(state=DISABLED)
            self.prevSearches.clear()
            self.currentSearchPattern = None

            dbpath = self.gamelist.DBlist[i]['sgfpath']
            datap = self.gamelist.DBlist[i]['name']
            del self.gamelist.DBlist[i]['data']  # make sure memory is freed and db connection closed
                                                 # (otherwise, on Windows, we might not be able to delete the db file)
            del self.gamelist.DBlist[i]

            try:
                os.remove(os.path.join(datap[0], datap[1] + '.db'))
                os.remove(os.path.join(datap[0], datap[1] + '.da'))
            except:
                showwarning(_('I/O Error'), _('Could not delete the database files {0}/{1}.').format(*datap))
            try:  # these files will only be present if hashing algos were used, so do not issue a warning when they are not found
                os.remove(os.path.join(datap[0], datap[1] + '.db1'))
                os.remove(os.path.join(datap[0], datap[1] + '.db2'))
            except:
                pass

            self.db_list.delete(index)
            self.callAddDB(dbpath, datap, index=i)
            self.db_list.list.select_set(i)

        # import previously saved tags
        self.gamelist.importTags(tagfilename)
        os.remove(tagfilename)
        self.updatetaglist()

        # cleaning up
        self.gamelist.reset()
        self.editDB_OK.config(state=NORMAL)
        self.saveProcMess.config(state=NORMAL)

    def toggleDisabled(self):
        for index in self.db_list.list.curselection():
            i = int(index)

            db = self.gamelist.DBlist[i]

            db_date = getDateOfFile(os.path.join(db['name'][0], db['name'][1] + '.da'))

            if db['disabled']:
                db['disabled'] = 0
                db['data'] = lkGameList(os.path.join(db['name'][0], db['name'][1] + '.db'))
                self.db_list.delete(i)
                self.db_list.insert(i, db['sgfpath'] + ' (%s, %d %s)' % (db_date, db['data'].size(), _('games')))

                self.db_list.list.select_set(i)
                self.db_list.list.see(i)
            else:
                db['disabled'] = 1
                db_size = db['data'].size()
                db['data'] = None
                self.db_list.delete(i)
                self.db_list.insert(i, _('DISABLED - ') + db['sgfpath'] + ' (%s, %d %s)' % (db_date, db_size, _('games')))
                self.db_list.list.select_set(i)
                self.db_list.list.see(i)

        self.reset()
        self.currentSearchPattern = None

    def saveMessagesEditDBlist(self):
        filename = tkFileDialog.asksaveasfilename(initialdir=os.curdir)
        try:
            file = open(filename, 'w')
            file.write(self.processMessages.get('1.0', END))
            file.close()
        except IOError:
            showwarning(_('Error'), _('Could not write to ') + filename)

    def DBlistClick(self, event):
        self.db_list.clickedLast = self.db_list.list.nearest(event.y)
        self.db_list.dragLast = -1

    def DBlistDrag(self, event):
        i = self.db_list.list.nearest(event.y)
        if self.db_list.dragLast == -1:
            if self.db_list.clickedLast == i:
                return
            else:
                self.db_list.dragLast = self.db_list.clickedLast
        if self.db_list.dragLast != i:
            s = self.db_list.list.get(self.db_list.dragLast)
            self.db_list.delete(self.db_list.dragLast)
            self.db_list.insert(i, s)
            self.db_list.list.select_set(i)
            self.db_list.dragLast = i
        return 'break'

    def DBlistRelease(self, event):
        if self.db_list.dragLast == -1:
            return

        i = self.db_list.list.nearest(event.y)

        if self.db_list.dragLast != i:
            s = self.db_list.list.get(self.db_list.dragLast)
            self.db_list.delete(self.db_list.dragLast)
            self.db_list.insert(i, s)
            self.db_list.list.select_set(i)
            self.db_list.dragLast = i

        if self.db_list.clickedLast != i:
            db = self.gamelist.DBlist.pop(self.db_list.clickedLast)
            self.gamelist.DBlist.insert(i, db)
            self.gamelist.reset()
            self.prevSearches.clear()
            self.currentSearchPattern = None

    def browseDatabases(self):
        initdir = self.options.whereToStoreDatabases.get() or os.curdir
        filename = askdirectory(parent=self.editDBlistWindow, initialdir=initdir)
        if filename:
            filename = str(filename)
        self.options.whereToStoreDatabases.set(filename)

    def toggleWhereDatabases(self):
        if self.options.storeDatabasesSeparately.get():
            self.whereDatabasesEntry.config(state=NORMAL)
            if not self.options.whereToStoreDatabases.get():
                self.browseDatabases()
        else:
            self.whereDatabasesEntry.config(state=DISABLED)

    def finalizeEditDB(self):
        self.dateProfileWholeDB = self.dateProfile()
        self.editDB_window.destroy()
        self.redo_date_profile = True
        self.notebookTabChanged()

    def editDBlist(self):
        self.gamelist.clearGameInfo()

        window = Toplevel()
        self.editDB_window = window
        window.transient(self.master)

        window.title(_('Edit database list'))

        f1 = Frame(window)
        f1.grid(row=0, sticky=NSEW)
        f2 = Frame(window)
        f2.grid(row=1, sticky=NSEW)
        for i in range(4):
            f2.columnconfigure(i, weight=1)

        f3 = Frame(window)
        f3.grid(row=3, sticky=NSEW)
        f3.columnconfigure(0, weight=1)
        f4 = Frame(window)
        f4.grid(row=4, sticky=NSEW)
        f5 = Frame(window)
        f5.grid(row=5, sticky=NSEW)

        window.columnconfigure(0, weight=1)

        self.db_list = v.ScrolledList(f1)
        self.db_list.list.config(width=60, selectmode=EXTENDED)
        self.db_list.pack(side=LEFT, expand=YES, fill=BOTH)

        self.db_list.list.bind('<1>', self.DBlistClick)
        self.db_list.list.bind('<B1-Motion>', self.DBlistDrag)
        self.db_list.list.bind('<ButtonRelease-1>', self.DBlistRelease)

        for db in self.gamelist.DBlist:
            db_date = getDateOfFile(os.path.join(db['name'][0], db['name'][1] + '.da'))

            if db['disabled']:
                self.db_list.insert(END, _('DISABLED') + ' - ' + db['sgfpath'] + ' (' + db_date + ')')
            else:
                self.db_list.insert(END, db['sgfpath'] + ' (%s, %d %s)' % (db_date, db['data'].size_all(), _('games')))

        for i, (text, command, ) in enumerate([(_('Add DB'), self.addDB), (_('Toggle normal/disabled'), self.toggleDisabled),
                                               (_('Remove DB'), self.removeDB), (_('Reprocess DB'), self.reprocessDB)]):
            Button(f2, text=text, command=command).grid(row=0, column=i, sticky=NSEW)
        self.editDB_OK = Button(f2, text=_('OK'), command=self.finalizeEditDB)
        self.editDB_OK.grid(row=0, column=4, sticky=NSEW)

        Label(f3, text=_('Processing options'), justify=LEFT, font=self.boldFont
                ).grid(row=0, column=0, sticky=W)

        recursionButton = Checkbutton(f3, text=_('Recursively add subdirectories'), highlightthickness=0, variable=self.options.recProcess, pady=5)
        recursionButton.grid(row=1, column=0, columnspan=2, sticky=W)

        self.filenamesVar = StringVar()
        filenamesLabel = Label(f3, anchor='w', text=_('Files:'), pady=10)
        filenamesLabel.grid(row=1, column=2, sticky=E)
        filenamesMenu = Combobox(f3, textvariable=self.filenamesVar, values=['*.sgf', '*.sgf, *.mgt', _('All files')], state='readonly')
        filenamesMenu.set('*.sgf')
        filenamesMenu.grid(row=1, column=3, sticky=W)

        # self.encodingVar = StringVar()
        #
        # enclist = ['utf-8', 'latin1', 'iso8859_2', 'iso8859_3', 'koi8_r', 'gb2312', 'gbk', 'gb18030', 'hz', 'big5', 'cp950', 'cp932',
        #            'shift-jis', 'shift-jisx0213', 'euc-jp', 'euc-jisx0213', 'iso-2022-jp', 'iso-2022-jp-1',
        #            'iso-2022-jp-2', 'iso-2022-jp-3', 'iso-2022-jp-ext', 'cp949', 'euc-kr', 'johab', 'iso-2022-kr',
        #           ]
        # encLabel = Label(f3, anchor='w', text=_('Encoding:'), pady=10)
        # encLabel.grid(row=1, column=3, sticky=E)
        # encodingMenu = Combobox(f3, textvariable = self.encodingVar, values = enclist, state='readonly')
        # encodingMenu.set('utf-8')
        # encodingMenu.grid(row=1, column=4, sticky=W)
        #
        # self.encoding1Var = StringVar()
        # encoding1Menu = Combobox(f3, textvariable = self.encoding1Var, values = [_('Do not change SGF'), _('Add CA tag'), _('Transcode SGF to utf-8')], state='readonly')
        # encoding1Menu.set(_('Add CA tag'))
        # encoding1Menu.grid(row=1, column=5, sticky=W)

        duplButton = Checkbutton(f3, text=_('Accept duplicates'), highlightthickness=0, variable=self.options.acceptDupl, pady=5)
        duplButton.grid(row=3, column=0, sticky=W, columnspan=2)

        strictDuplCheckButton = Checkbutton(f3, text=_('Strict duplicate check'), highlightthickness=0, variable=self.options.strictDuplCheck, pady=5)
        strictDuplCheckButton.grid(row=3, column=2, sticky=W, columnspan=2)

        processVariations = Checkbutton(f3, text=_('Process variations'), highlightthickness=0, variable=self.options.processVariations, pady=5)
        processVariations.grid(row=5, column=0, sticky=W, columnspan=2)

        profTagLabel = Label(f3, anchor='e', text=_('Tag as professional:'), pady=8)
        profTagLabel.grid(row=6, column=0, sticky=W, )
        profTag = Combobox(f3, justify='left', textvariable=self.options.tagAsPro,
                               values=[_('Never'), _('All games'), _('All games with p-rank players'), ], state='readonly')
        profTag.grid(row=6, column=1, columnspan=2, sticky=W)

        sep = Separator(f3, orient='horizontal')
        sep.grid(row=7, column=0, columnspan=7, sticky=NSEW)
        whereDatabasesButton = Checkbutton(f3, text=_('Store databases separately from SGF files'), highlightthickness=0,
                                           command=self.toggleWhereDatabases, variable=self.options.storeDatabasesSeparately, padx=8)
        whereDatabasesButton.grid(row=8, column=0, columnspan=3, sticky=W)

        self.whereDatabasesEntry = Entry(f3, textvariable=self.options.whereToStoreDatabases, )
        self.whereDatabasesEntry.grid(row=8, column=3, columnspan=3, sticky=NSEW)
        if not self.options.storeDatabasesSeparately.get():
            self.whereDatabasesEntry.config(state=DISABLED)

        browseButton = Button(f3, text=_('Browse'), command=self.browseDatabases)
        browseButton.grid(row=8, column=5)
        f3.grid_columnconfigure(0, weight=1)
        f3.grid_columnconfigure(1, weight=2)
        f3.grid_columnconfigure(2, weight=2)
        f3.grid_columnconfigure(3, weight=2)

        sep1 = Separator(f3, orient='horizontal')
        sep1.grid(row=9, column=0, columnspan=7, sticky=NSEW)

        self.algo_hash_full = Checkbutton(f3, text=_('Use hashing for full board positions'), highlightthickness=0, variable=self.options.algo_hash_full, pady=5)
        self.algo_hash_full.grid(row=10, column=0, columnspan=2)

        self.algo_hash_corner = Checkbutton(f3, text=_('Use hashing for corner positions'), highlightthickness=0, variable=self.options.algo_hash_corner, pady=5)
        self.algo_hash_corner.grid(row=10, column=3, columnspan=2)

        self.saveProcMess = Button(f4, text=_('Save messages'), command=self.saveMessagesEditDBlist)
        self.saveProcMess.pack(side=RIGHT)
        self.processMessages = Message(f5)
        self.processMessages.pack(side=TOP, expand=YES, fill=BOTH)

        self.editDBlistWindow = window
        window.update_idletasks()
        window.focus()
        window.grab_set()
        window.wait_window()

        del self.db_list
        del self.processMessages
        del self.saveProcMess
        del self.editDB_OK
        del self.whereDatabasesEntry

    # --------------------------------------------------------------------

    def copyCurrentGamesToFolder(self, dir=None):
        if dir is None:
            dir = askdirectory(parent=self.master, initialdir=self.datapath)
            if not dir:
                return
            dir = str(dir)

        if not os.path.exists(dir) and askokcancel(_('Error'), _('Directory %s does not exist. Create it?') % dir):
            try:
                os.makedirs(dir)
            except:
                return

        KEngine.copyCurrentGamesToFolder(self, dir)

    def openFile(self, path=None, filename=None, do_not_change_sgfpath=False):
        self.board.newPosition()
        v.Viewer.openFile(self, path, filename, do_not_change_sgfpath=do_not_change_sgfpath)

    def quit(self):
        for i in range(len(self.filelist)):
            s = self.dataWindow.filelist.list.get(i)
            if self.options.confirmDelete.get() and s[0:2] == '* ':
                if not askokcancel(_('Confirm deletion'), _('There are unsaved changes. Discard them?')):
                    return
                else:
                    break

        try:
            c = self.get_config_obj()
            c['main']['version'] = 'kombilo%s' % KOMBILO_VERSION
            c['main']['sgfpath'] = self.sgfpath
            c['main']['datapath'] = self.datapath
            self.saveOptions(c['options'])
            c['databases'] = {}
            for counter, db in enumerate(self.gamelist.DBlist):
                c['databases']['d%d%s' % (counter, 'disabled' if db['disabled'] else '')] = [db['sgfpath'], db['name'][0], db['name'][1]]
            c['tags'] = self.gamelist.customTags
            c['taglook'] = self.gamelist.taglook
            c.filename = os.path.join(v.get_configfile_directory(), 'kombilo.cfg')
            c.write()
        except ImportError:
            showwarning(_('I/O Error'), _('Could not write kombilo.cfg'))

        self.master.quit()

        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
            db['data'].delete_all_snapshots()

    def configButtons(self, state):
        """ Disable buttons and board during search, reset them afterwards. """

        for b in [self.resetButtonS, self.resetstartButtonS, self.backButtonS, self.searchButtonS, self.nextMove1S, self.nextMove2S, self.nextMove3S]:
            b.config(state=state)

        if state == NORMAL:
            self.board.state('normal', self.nextMove)
        elif state == DISABLED:
            self.board.state('disabled')

    def helpAbout(self):
        """ Display the 'About ...' window with the logo and some basic information. """

        t = []

        t.append(_('Kombilo %s - written by') % KOMBILO_RELEASE + ' Ulrich Goertz (ug@geometry.de)' + '\n\n')
        t.append(_('Kombilo is a go database program.') + '\n')
        t.append(_('You can find more information on Kombilo and the newest version at') + ' http://www.u-go.net/kombilo/\n\n')

        t.append(_('Kombilo is free software; for more information see the documentation.') + '\n\n')

        window = Toplevel()
        window.title(_('About Kombilo ...'))

        if self.logo:
            canv = Canvas(window, width=300, height=94)
            canv.pack()
            canv.create_image(0, 0, image=self.logo, anchor=NW)

        text = Text(window, height=15, width=60, relief=FLAT, wrap=WORD)
        text.insert(1.0, join(t, ''))

        text.config(state=DISABLED)
        text.pack()

        b = Button(window, text=_('OK'), command=window.destroy)
        b.pack(side=RIGHT)

        window.update_idletasks()

        window.focus()
        window.grab_set()
        window.wait_window()

    def helpLicense(self):
        """ Display the Kombilo license. """
        try:
            t = pkg_resources.resource_string(__name__, 'license.rst')
        except:
            t = _('Kombilo was written by Ulrich Goertz (ug@geometry.de).') + '\n'
            t = t + _('It is open source software, published under the MIT License.')
            t = t + _('See the documentation for more information. ')
            t = t + _('This program is distributed WITHOUT ANY WARRANTY!') + '\n\n'
        self.textWindow(t, _('Kombilo license'))

    def showFilenameInGamelist(self):
        self.gamelist.showFilename = self.options.showFilename.get()
        self.reset()

    def showDateInGamelist(self):
        self.gamelist.showDate = self.options.showDate.get()
        self.reset()

    def gotoChange(self, event):
        if event.char == '':
            return
        if ord(event.char[0]) < 32:
            return

        t = self.gotoVar.get() + event.char

        i = self.gamelist.listbox.curselection()
        start = self.gamelist.get_index(0) if not i else self.gamelist.get_index(int(i[0]))

        criterion = self.options.sortCriterion.get()
        increment = (2 * self.options.sortReverse.get() - 1) if self.gamelist.sortCrit(start, criterion)[:len(t)] > t else (-2 * self.options.sortReverse.get() + 1)  # (= -1 or 1)

        if increment == 1:
            if self.options.sortReverse.get():
                while start < len(self.gamelist.gameIndex) - 1 and self.gamelist.sortCrit(start, criterion)[:len(t)] > t:
                    start += 1
            else:
                while start < len(self.gamelist.gameIndex) - 1 and self.gamelist.sortCrit(start, criterion) < t:
                    start += 1
        else:
            if self.options.sortReverse.get():
                while start > 0 and self.gamelist.sortCrit(start, criterion) < t:
                    start -= 1
            else:
                while start > 0 and self.gamelist.sortCrit(start, criterion)[:len(t)] > t:
                    start -= 1

        if i:
            self.gamelist.listbox.select_clear(i)
        self.gamelist.listbox.virt_select_set_see(start)
        self.gamelist.printGameInfo(None, start)

    def initMenusK(self):
        """ Initialize the menus, and a few options variables. """

        # --------- FILE ---------------------------------
        self.filemenu.insert_separator(6)
        self.filemenu.insert_command(7, label=_('Complete reset'), command=self.completeReset)

        # --------- DATABASE ---------------------------------

        self.dbmenu = Menu(self.mainMenu)
        self.mainMenu.insert_cascade(3, **v.get_addmenu_options(label=_('_Database'), menu=self.dbmenu))
        self.dbmenu.add_command(v.get_addmenu_options(label=_('_Edit DB list'), command=self.editDBlist))
        self.dbmenu.add_command(v.get_addmenu_options(label=_('Export search _results'), command=self.exportText))
        self.dbmenu.add_command(v.get_addmenu_options(label=_('Export current _position'), command=self.exportCurrentPos))
        self.dbmenu.add_command(v.get_addmenu_options(label=_('SGF _tree'), command=self.do_sgf_tree))
        self.dbmenu.add_command(label=_('Export tags to file'), command=self.exportTags)
        self.dbmenu.add_command(label=_('Import tags from file'), command=self.importTags)
        self.dbmenu.add_command(v.get_addmenu_options(label=_('_Copy current SGF files to folder'), command=self.copyCurrentGamesToFolder))

        self.dbmenu.add_command(label=_('Signature search'), command=self.sigSearch)
        self.dbmenu.add_command(label=_('Find duplicates'), command=self.find_duplicates_GUI)

        self.optionsmenu.add_checkbutton(v.get_addmenu_options(label=_('_Jump to match'), variable=self.options.jumpToMatchVar))
        self.optionsmenu.add_checkbutton(v.get_addmenu_options(label=_('S_mart FixedColor'), variable=self.options.smartFixedColor))

        # ------ game list submenu ------------

        gamelistMenu = Menu(self.optionsmenu)
        self.optionsmenu.add_cascade(v.get_addmenu_options(label=_('_Game list'), menu=gamelistMenu))

        for text, value in [(_('Sort by white player'), GL_PW, ), (_('Sort by black player'), GL_PB, ), (_('Sort by filename'), GL_FILENAME, ), (_('Sort by date'), GL_DATE, )]:
            gamelistMenu.add_radiobutton(label=text, variable=self.options.sortCriterion, value=value, command=self.gamelist.update)
        gamelistMenu.add_checkbutton(label=_('Reverse order'), variable=self.options.sortReverse, command=self.gamelist.update)

        gamelistMenu.add_separator()

        gamelistMenu.add_checkbutton(label=_('Show filename'), variable=self.options.showFilename, command=self.showFilenameInGamelist)
        gamelistMenu.add_checkbutton(label=_('Show date'), variable=self.options.showDate, command=self.showDateInGamelist)

        # -------------------------------------

        # self.options.invertSelection = self.board.invertSelection
        # self.optionsmenu.add_checkbutton(label=_('Invert selection'), variable = self.options.invertSelection)

        self.custom_menus = CustomMenus(self)
        self.optionsmenu.insert_command(1, label=_('Custom Menus'), command=self.custom_menus.change)

    def balloonHelpK(self):

        for widget, text in [(self.resetButtonS, _('Reset game list')), (self.resetstartButtonS, _('Reset game list and board')),
                             (self.backButtonS, _('Back to previous search pattern')), (self.showContButtonS, _('Show continuations')),
                             (self.oneClickButtonS, _('1-click mode')),
                             (self.statByDateButtonS, _('Show date information for continuations')),
                             (self.colorButtonS, _("(Don't) allow color swap in search pattern")),
                             (self.anchorButtonS, _("(Don't) translate search pattern")), (self.nextMove1S, _('Black or white plays next (or no continuation)')),
                             (self.nextMove2S, _('Black plays next')), (self.nextMove3S, _('White plays next')),
                             (self.scaleS, _('Pattern has to occur before move n (250=no limit)')), (self.searchButtonS, _('Start pattern search')),
                             (self.GIstart, _('Start game info search')), (self.GIclear, _('Clear all entries')),
                             (self.GI_bwd, _('Restore entries of previous game info search')), (self.GI_fwd, _('Restore entries of next game info search')),
                             (self.tagsearchButton, _('Search for tagged games.\nE.g.: H and not S')), (self.tagsetButton, _('Set tags of selected game.')),
                             (self.tagallButton, _('Tag all games currently listed with given tag.')), (self.untagallButton, _('Remove given tag from all games currently listed.')),
                             (self.tagaddButton, _('Define a new tag (give one-letter abbreviation and description).')), (self.tagdelButton, _('Remove a tag.')),
                            ]:
            ToolTip(widget, text)

    def get_pattern_from_board(self):
        #print 'get_pattern_from_board'
        if self.board.selection[0][0] > self.board.selection[1][0] or self.board.selection[0][1] > self.board.selection[1][1]:
            self.board.selection = ((0, 0), (self.board.boardsize - 1, self.board.boardsize - 1))

        self.sel = self.board.selection  # copy this because the selection on the board may
                                         # be changed by the user although the search is not yet finished
        # print 'selection', self.sel

        dp, d, contlist = self.pattern_string_from_board(self.board, self.sel, self.cursor)

        if self.sel == ((0, 0), (self.board.boardsize - 1, self.board.boardsize - 1)):
            patternType = lk.FULLBOARD_PATTERN
        elif self.sel[0] == (0, 0):
            patternType = lk.CORNER_NW_PATTERN
        elif (self.sel[0][0], self.sel[1][1]) == (0, self.board.boardsize - 1):
            patternType = lk.CORNER_SW_PATTERN
        elif (self.sel[0][1], self.sel[1][0]) == (0, self.board.boardsize - 1):
            patternType = lk.CORNER_NE_PATTERN
        elif self.sel[1] == (self.board.boardsize - 1, self.board.boardsize - 1):
            patternType = lk.CORNER_SE_PATTERN
        elif self.sel[0][0] == 0:
            patternType = lk.SIDE_W_PATTERN
        elif self.sel[0][1] == 0:
            patternType = lk.SIDE_N_PATTERN
        elif self.sel[1][0] == self.board.boardsize - 1:
            patternType = lk.SIDE_E_PATTERN
        elif self.sel[1][1] == self.board.boardsize - 1:
            patternType = lk.SIDE_S_PATTERN
        else:
            patternType = lk.CENTER_PATTERN

        sizeX = self.sel[1][0] - self.sel[0][0] + 1  # number of columns
        sizeY = self.sel[1][1] - self.sel[0][1] + 1  # number of rows

        # print "size:", sizeX, 'columns', sizeY, 'rows'
        # print 'pattern search for'
        # print '\n'.join([ dp[i*sizeX:(i+1)*sizeX] for i in range(sizeY) ])
        # print 'pattern type:', patternType
        # print time.time() - currentTime

        self.contLabels = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789' if self.options.uppercaseLabels.get() else 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789'
        fixedLabs = ['.'] * (sizeX * sizeY)
        self.fixedLabels = {}
        try:
            if self.cursor and self.cursor.currentNode().has_key('LB'):
                for p1 in self.cursor.currentNode()['LB']:
                    p, text = split(p1, ':')
                    x, y = self.convCoord(p)
                    if self.sel[0][0] <= x <= self.sel[1][0] and self.sel[0][1] <= y <= self.sel[1][1]:
                        if text[0] in self.contLabels:
                            self.contLabels = self.contLabels.replace(text[0], '')
                        self.fixedLabels[(x - self.sel[0][0], y - self.sel[0][1])] = text[0]
                        fixedLabs[x - self.sel[0][0] + (y - self.sel[0][1]) * sizeX] = text[0]
        except:
            showwarning(_('Error'), _('SGF Error'))
        fixedLabs = ''.join(fixedLabs)

        return Pattern(d, anchors=(self.sel[0][0], self.sel[0][0], self.sel[0][1], self.sel[0][1]),
                       boardsize=self.board.boardsize, sizeX=sizeX, sizeY=sizeY, contLabels=fixedLabs, contlist=contlist, topleft=self.sel[0]) if self.fixedAnchorVar.get()\
          else Pattern(d, ptype=patternType, boardsize=self.board.boardsize, sizeX=sizeX, sizeY=sizeY, contLabels=fixedLabs, contlist=contlist, topleft=self.sel[0])

    def get_search_options(self):
        so = lk.SearchOptions(self.fixedColorVar.get(), self.nextMoveVar.get(), self.moveLimit.get() if self.moveLimit.get() < 250 else 1000)
        so.searchInVariations = self.searchInVariations.get()
        so.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST
        if self.algo_hash_full_search.get():
            so.algos |= lk.ALGO_HASH_FULL
        if self.algo_hash_corner_search.get():
            so.algos |= lk.ALGO_HASH_CORNER
        return so

    def search(self):
        '''Do a pattern search in the current game list, for the pattern currently on the board.'''

        # print 'enter pattern search'
        if not self.gamelist.noOfGames():
            self.reset()
        self.gamelist.clearGameInfo()
        currentTime = time.time()
        self.configButtons(DISABLED)
        self.progBar.start(50)

        boardData = self.board.snapshot()

        CSP = self.get_pattern_from_board()
        self.searchOptions = self.get_search_options()

        self.patternSearch(CSP, self.searchOptions, self.contLabels, self.fixedLabels, self.progBar,
                           self.untranslate_cont_sort_crit())

        if self.showContinuation.get():
            self.showCont()
        elif self.cursor:
            try:
                self.leaveNode()
                self.displayLabels(self.cursor.currentNode())
            except:
                pass
        self.display_statistics()
        self.progBar.stop()
        self.logger.insert(END, _('Pattern search') + ', ' + _('%1.1f seconds\n') % (time.time() - currentTime))

        # append the result of this search to self.prevSearches
        self.prevSearches.append(boardData=boardData,
                                 snapshot_ids=[(i, db['data'].snapshot()) for i, db in enumerate(self.gamelist.DBlist) if not db['disabled']],
                                 modeVar=self.modeVar.get(),  # in gl.snapshot?
                                 cursorSn=[self.cursor, self.cursor.currentGame, self.cursor.currentNode().pathToNode()],
                                 variables=[self.modeVar.get(), self.fixedColorVar.get(), self.fixedAnchorVar.get(), self.moveLimit.get(), self.nextMoveVar.get(), ],
                                )
        self.redo_date_profile = True
        self.notebookTabChanged()
        self.configButtons(NORMAL)

    def do_sgf_tree(self):
        options_window = Toplevel()
        options_window.transient(self.master)
        options_window.title(_('SGF tree options'))
        row_ctr = 0

        class Container:
            pass
        variables = Container()

        entry_list = [('min_number_of_hits', _('Minimum number of hits'), '20'),
                      ('max_number_of_branches', _('Maximum number of branches'), '10'),
                      ('depth', _('Depth'), '10'),
                      ('comment_head', _('Comment head'), '@@monospace'),
                      ]

        for s, t, v in entry_list:
            s_var = StringVar()
            s_var.set(v)
            setattr(variables, s, s_var)
            s_label = Label(options_window, anchor='e', text=t)
            s_label.grid(row=row_ctr, column=0)
            setattr(variables, s + '_l', s_label)
            s_entry = Entry(options_window, textvariable=s_var, )
            s_entry.grid(row=row_ctr, column=1)
            setattr(variables, s + '_e', s_entry)
            row_ctr += 1

        sort_options_l = Label(options_window, anchor='e', text=_('Sort continuations by'))
        sort_options_l.grid(row=row_ctr, column=0)
        sort_option_cb = Combobox(
                options_window, justify='left',
                textvariable=self.options.continuations_sort_crit,
                values=(_('total'), _('earliest'), _('latest'), _('average'), _('became popular'), _('became unpopular'), ),
                state='readonly')
        sort_option_cb.grid(row=row_ctr, column=1)
        row_ctr += 1

        new_cursor_var = IntVar()
        new_cursor_var.set(0)
        new_cursor_button = Checkbutton(options_window, text=_('Put results into new SGF file'), highlightthickness=0, variable=new_cursor_var, pady=5)
        new_cursor_button.grid(row=row_ctr, column=0)
        row_ctr += 1

        reset_game_list_var = IntVar()
        reset_game_list_var.set(0)
        reset_game_list_button = Checkbutton(options_window, text=_('Reset game list'), highlightthickness=0, variable=reset_game_list_var, pady=5)
        reset_game_list_button.grid(row=row_ctr, column=0)
        row_ctr += 1

        cancel = []

        def ok_fct():
            options_window.destroy()

        def cancel_fct():
            cancel.append(1)
            options_window.destroy()

        ok_button = Button(options_window, text=_('OK'), command=ok_fct)
        ok_button.grid(row=row_ctr, column=0)
        cancel_button = Button(options_window, text=_('Cancel'), command=cancel_fct)
        cancel_button.grid(row=row_ctr, column=1)
        row_ctr += 1

        options_window.update_idletasks()
        options_window.focus()
        options_window.grab_set()
        options_window.wait_window()

        if cancel:
            return

        self.progBar.start(50)
        currentTime = time.time()
        self.configButtons(DISABLED)

        CSP = self.get_pattern_from_board()
        searchOptions = self.get_search_options()

        options_dict = {s: getattr(variables, s).get() for s, t, v in entry_list}
        options_dict.update({'reset_game_list': reset_game_list_var.get(),
                             'sort_criterion': self.untranslate_cont_sort_crit(),
                             'boardsize': CSP.boardsize,
                             'sizex': CSP.sizeX, 'sizey': CSP.sizeY,
                             'anchors': (CSP.left, CSP.right, CSP.top, CSP.bottom),
                             'selection': self.sel,
                             })
        options = ConfigObj(options_dict)

        if new_cursor_var.get():
            B_list = []
            W_list = []
            sgf_str = '(;GM[1]FF[4]SZ[19]AP[Kombilo]'
            for i in range(CSP.boardsize):
                for j in range(CSP.boardsize):
                    if self.board.getStatus(i,j) == 'B':
                        B_list.append(chr(i + ord('a')) + chr(j + ord('a')))
                    elif self.board.getStatus(i,j) == 'W':
                        W_list.append(chr(i + ord('a')) + chr(j + ord('a')))
            if B_list:
                sgf_str += 'AB' + ''.join([('[%s]' % s) for s in B_list])
            if W_list:
                sgf_str += 'AW' + ''.join([('[%s]' % s) for s in W_list])
            sgf_str += ')'
            # print sgf_str
            cursor = Cursor(sgf_str)
            current_game = 0
        else:
            if self.cursor.noChildren():
                showwarning(_('Error'), _('The node where the SGF tree starts must have no children.'))
                return
            cursor = self.cursor
            current_game = self.cursor.currentGame
            self.leaveNode()
            path_to_initial_node = self.cursor.currentNode().pathToNode()

        self.currentFileChanged()
        self.sgf_tree(cursor, current_game, options, searchOptions, messages=self.logger, progBar=self.progBar, )

        if new_cursor_var.get():
            self.newFile(cursor)
        else:
            self.cursor.game(self.cursor.currentGame)
            self.displayNode(self.cursor.currentNode())  # make sure the Comment of this node is not
                                                         # killed by the following self.start()

            # go back to initial node
            self.start()
            for i in path_to_initial_node:
                self.next(i)

        self.logger.insert(END, _('Finished computing sgf tree') + ', ' + _('%1.1f seconds\n') % (time.time() - currentTime))
        self.progBar.stop()
        self.configButtons(NORMAL)

    # ------------  TAGGING ----------------------------------------------

    def inittags(self):
        self.taglist = v.ScrolledList(self.tagFrameS, selectmode=EXTENDED, width=30, height=5)
        self.taglist.pack(side=TOP, expand=True, fill=BOTH)
        self.updatetaglist()

        # self.taglist.list.bind('<<ListboxSelect>>', self.updatetags)

        self.tagFrame2 = Frame(self.tagFrameS)
        self.tagFrame2.pack(side=TOP, expand=False, fill=X)
        self.tagSearchVar = StringVar()
        self.tagentry = Entry(self.tagFrame2, textvariable=self.tagSearchVar)
        self.tagentry.pack(side=LEFT, fill=X, expand=True)
        self.tagentry.bind('<Return>', self.tagSearch)

        self.tagButtonF = Frame(self.tagFrame2)
        self.tagButtonF.pack(side=LEFT)
        self.tagsearchButton = Button(self.tagButtonF, text=_('Search'), command=self.tagSearch)
        self.tagsearchButton.pack(side=LEFT)
        self.tagsetButton = Button(self.tagButtonF, text=_('Set tags'), command=self.tagSet)
        self.tagsetButton.pack(side=LEFT)
        self.tagallButton = Button(self.tagButtonF, text=_('Tag all'), command=self.tagAllCurrent)
        self.tagallButton.pack(side=LEFT)
        self.untagallButton = Button(self.tagButtonF, text=_('Untag all'), command=self.untagAllCurrent)
        self.untagallButton.pack(side=LEFT)
        self.tagaddButton = Button(self.tagButtonF, text=_('Add tag'), command=self.addTag)
        self.tagaddButton.pack(side=LEFT)
        self.tagdelButton = Button(self.tagButtonF, text=_('Delete tag'), command=self.deleteTagPY)
        self.tagdelButton.pack(side=LEFT)

    def updatetaglist(self):
        self.taglist.list.delete(0, END)
        l = [int(x) for x in self.gamelist.customTags.keys()]
        l.sort()
        for ctr, t in enumerate(l):
            self.taglist.list.insert(END, '[%s] %s' % (self.gamelist.customTags[str(t)][0], _(self.gamelist.customTags[str(t)][1])))
            self.taglist.list.itemconfig(ctr, **self.gamelist.taglook.get(str(t), {}))

    def addTag(self):
        """
        Creates a new tag.
        """

        # parse input
        try:
            abbr = self.tagSearchVar.get().split()[0]
            description = self.tagSearchVar.get().split()[1:]
        except:
            return

        # check that abbr does not exist yet
        if abbr in [self.gamelist.customTags[x][0] for x in self.gamelist.customTags.keys()]:
            showwarning(_('Error'), _('This tag abbreviation exists already.'))
            return

        # find unused handle
        l = [int(x) for x in self.gamelist.customTags.keys()]
        l.sort()
        handle = str(max(l[-1] + 1, 10))  # allow for 9 "built-in" tags

        # add tag to dict of custom tags
        self.gamelist.customTags[handle] = (abbr, ' '.join(description), )
        self.logger.insert(END, _('Added tag {0} {1}.\n').format(*self.gamelist.customTags[handle]))
        self.updatetaglist()

    def getTagHandle(self):
        q = self.tagSearchVar.get()
        if len(q) != 1:
            self.logger.insert(END, _('Not a tag abbreviation: %s.\n') % q)

        # delete tag from dict of custom tags
        for t in self.gamelist.customTags:
            if self.gamelist.customTags[t][0] == q:
                return int(t)  # find the integer handle corresponding to the given abbreviation
        else:
            self.logger.insert(END, _('Not a tag abbreviation: %s.\n') % q)
            return

    def deleteTagPY(self):
        t = self.getTagHandle()
        if t is None:
            return
        if t < 10:
            showwarning(_('Error'), _('You cannot delete built-in tags.'))
            return
        self.logger.insert(END, _('Delete tag [{0}] {1}.\n').format(*self.gamelist.customTags.pop(str(t))))

        # delete tag from all tagged games
        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
            db['data'].deleteTag(t, -1)

        self.updatetaglist()

    def tagAllCurrent(self):
        t = self.getTagHandle()
        if t is None:
            return
        for dummy, DBindex, index in self.gamelist.gameIndex:
            self.gamelist.DBlist[DBindex]['data'].setTag(t, index, index + 1)

        self.gamelist.upd()
        if self.gamelist.listbox.curselection():
            index = self.gamelist.get_index(int(self.gamelist.listbox.curselection()[0]))
            DBindex, index = self.gamelist.getIndex(index)
            self.selecttags(self.gamelist.DBlist[DBindex]['data'].getTags(index))

    def untagAllCurrent(self):
        t = self.getTagHandle()
        if t is None:
            return
        for dummy, DBindex, index in self.gamelist.gameIndex:
            self.gamelist.DBlist[DBindex]['data'].deleteTag(t, index)
        self.logger.insert(END, _('Deleted tag [{0}] {1} from {2} games.\n').format(self.gamelist.customTags[str(t)][0], self.gamelist.customTags[str(t)][1], len(self.gamelist.gameIndex)))

        self.gamelist.upd()
        if self.gamelist.listbox.curselection():
            index = self.gamelist.get_index(int(self.gamelist.listbox.curselection()[0]))
            DBindex, index = self.gamelist.getIndex(index)
            self.selecttags(self.gamelist.DBlist[DBindex]['data'].getTags(index))

    def tagSearch(self, event=None, tag=None):
        if not self.gamelist.noOfGames():
            self.reset()
        self.gamelist.clearGameInfo()
        self.configButtons(DISABLED)
        self.progBar.start(50)
        currentTime = time.time()

        self.board.delLabels()
        if self.cursor:
            try:
                self.leaveNode()
                self.displayLabels(self.cursor.currentNode())
            except:
                showwarning(_('Error'), _('SGF Error'))
        tag = tag or self.tagSearchVar.get()
        KEngine.tagSearch(self, tag)

        self.progBar.stop()
        self.logger.insert(END, (_('Tag search %s') % tag) + ', ' + _('%1.1f seconds') % (time.time() - currentTime) + '\n')
        self.redo_date_profile = True
        self.notebookTabChanged()
        self.configButtons(NORMAL)

    def tagSet(self):
        l = [int(x) for x in self.gamelist.customTags.keys()]
        l.sort()
        # print "set tags", [ l[int(x)] for x in self.taglist.list.curselection()]
        self.gamelist.setTags([l[int(x)] for x in self.taglist.list.curselection()])
        self.gamelist.upd()

    def selecttags(self, tags):
        self.taglist.list.select_clear(0, END)
        for t in tags:
            self.taglist.list.select_set(t - 1)

    def exportTags(self):

        filename = tkFileDialog.asksaveasfilename(initialdir=os.curdir)
        which_tags = [int(x) for x in self.gamelist.customTags.keys()]
        which_tags.remove(lk.HANDI_TAG)  # no need to export HANDI tags since they are automatically assigned during processing
        self.gamelist.exportTags(filename, which_tags)

    def importTags(self):

        filename = tkFileDialog.askopenfilename(initialdir=os.curdir)
        self.gamelist.importTags(filename)
        self.updatetaglist()

    # -------------------------------------------------

    def notebookTabChanged(self, event=None):
        if self.notebook.select() == self.dateProfileFS.winfo_pathname(self.dateProfileFS.winfo_id()):
            if self.redo_date_profile:
                self.display_date_profile()

    # -------------------------------------------------

    def untranslate_cont_sort_crit(self):
        """
        "Untranslate" continuations_sort_crit to English - we need to store the
        translation to chosen language in the variable in order to use it as the
        variable for the Tkinter widget. In the options file and for passing it
        to libkombilo we need the English translation, however.
        """

        try:
            return {_(s): s for s in [
                'total', 'earliest', 'latest', 'average',
                'became popular', 'became unpopular', ]}[self.options.continuations_sort_crit.get()]
        except KeyError:
            return self.options.continuations_sort_crit.get()

    def untranslate_tagAsPro(self):
        try:
            return {_(s): s for s in [
                'Never', 'All games', 'All games with p-rank players', ]}[self.options.tagAsPro.get()]
        except KeyError:
            return self.options.tagAsPro.get()

    def saveOptions(self, d):
        """ Save options to dictionary d. """
        self.options.windowGeomK.set(self.master.geometry())
        self.options.dataWindowGeometryK.set(self.dataWindow.get_geometry())

        self.mainframe.update_idletasks()
        l = [str(self.mainframe.sash_coord(i)[0]) for i in range(2)]
        self.options.sashPosK.set(join(l, '|%'))

        self.frameS.update_idletasks()
        l = [str(self.frameS.sash_coord(i)[1]) for i in range(2)]
        self.options.sashPosKS.set(join(l, '|%'))

        try:
            self.options.continuations_sort_crit.set(self.untranslate_cont_sort_crit())
            self.options.tagAsPro.set(self.untranslate_tagAsPro())
        except KeyError:
            # Can happen if language has been changed; for simplicity we just reset to "total" then.
            self.options.continuations_sort_crit.set('total')

        self.options.saveToDisk(d)

    def loadOptions(self, d):
        """ Load options from dictionary d. """

        self.options.loadFromDisk(d)
        self.options.date_profile_to.set(datetime.datetime.today().year)

    def evalOptions(self):
        self.dataWindow.comments.configure(text_font=self.standardFont)
        if self.options.showCoordinates.get():
            self.board.coordinates = 1
            self.board.resize()
        if self.options.windowGeomK.get():
            self.master.geometry(self.options.windowGeomK.get())
        if self.options.dataWindowGeometryK.get():
            self.dataWindow.set_geometry(self.options.dataWindowGeometryK.get())

    def evalOptionsK(self):
        # restore sizes of panes in PanedWindows
        for win, var, orientation in [
                (self.mainframe, self.options.sashPosK, 'horizontal'),
                (self.frameS, self.options.sashPosKS, 'vertical'), ]:
            try:
                win.update_idletasks()
                l = var.get().split('|%')
                for i in range(len(l)-1, -1, -1):
                    if orientation == 'horizontal':
                        win.sash_place(i, int(l[i]), 1)
                    elif orientation == 'vertical':
                        win.sash_place(i, 1, int(l[i]))
                    win.update_idletasks()
            except:
                pass

    def switch_language(self, lang, show_warning=False):
        self.options.continuations_sort_crit.set(self.untranslate_cont_sort_crit())
        self.options.tagAsPro.set(self.untranslate_tagAsPro())

        v.Viewer.switch_language(self, lang, show_warning)

        for var in [self.options.continuations_sort_crit, self.options.tagAsPro, ]:
            var.set(_(var.get()))

    def init_key_bindings(self):
        v.Viewer.init_key_bindings(self)
        self.master.bind_all('<Control-s>', lambda e, self=self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.searchStat.winfo_id())))  # select statistics tab
        self.master.bind_all('<Control-o>', lambda e, self=self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.patternSearchOptions.winfo_id())))  # select options tab
        self.master.bind_all('<Control-g>', lambda e, self=self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.giSFS.winfo_id())))  # select game info search tab
        self.master.bind_all('<Control-d>', lambda e, self=self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.dateProfileFS.winfo_id())))  # select date profile tab
        self.master.bind_all('<Control-t>', lambda e, self=self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.tagFS.winfo_id())))  # select tags tab
        self.master.bind_all('<Control-p>', lambda e, self=self: self.search())  # start pattern search
        self.master.bind_all('<Control-b>', lambda e, self=self: self.back())  # go back to previous pattern search
        self.master.bind_all('<Control-r>', lambda e, self=self: self.reset())  # reset game list
        self.master.bind_all('<Control-a>', lambda e, self=self: self.reset_start())  # reset game list and clear board
        self.master.bind_all('<Control-e>', lambda e, self=self: self.printPattern())  # print previous search pattern to log tab
        self.master.bind_all('<Control-j>', lambda e, self=self: self.oneClick.set(1 - self.oneClick.get()))  # toggle 1-click mode


        def _button_release(event):
            if event.num == 8:
                self.back()
            elif event.num == 9:
                self.search()

        self.master.bind('<ButtonRelease>', _button_release)

    def __init__(self, master):

        KEngine.__init__(self)

        # Initialization of the Viewer class
        v.Viewer.__init__(self, master, BoardWC, DataWindow)

        if sys.platform.startswith('win') and self.options.maximize_window.get():
            try:
                master.state('zoomed')
            except:
                pass

        self.board.labelFontsize = self.options.labelFontSize
        self.fixedColorVar = self.board.fixedColor
        self.board.smartFixedColor = self.options.smartFixedColor
        self.redo_date_profile = True

        self.board.bind('<Double-1>', self.doubleClick)

        # ------------ the search window

        self.searchWindow = Frame(self.mainframe)
        self.mainframe.add(self.searchWindow)
        # self.searchWindow.withdraw()
        # self.searchWindow.geometry('400x550')
        # self.searchWindow.protocol('WM_DELETE_WINDOW', lambda: 0)
        # self.searchWindow.title('Kombilo: game list')

        self.topFrameS = Frame(self.searchWindow)
        self.topFrameS.pack(side=TOP, fill=X, expand=NO)

        self.frameS = PanedWindow(self.searchWindow, orient='vertical')   # suffix S means 'in search/results window'
        self.frameS.pack(fill=BOTH, expand=YES)

        self.listFrameS = Frame(self.frameS)
        self.frameS.add(self.listFrameS, minsize=100, sticky="NSEW")
        self.gameinfoS = Pmw.ScrolledText(self.frameS, usehullsize=1, hull_height=160, text_wrap=WORD,
                                          text_font=self.standardFont)
        self.gameinfoS.configure(text_state=DISABLED)
        self.gameinfoS.tag_config('blue', foreground='blue')
        self.frameS.add(self.gameinfoS, minsize=100, sticky="NSEW")

        self.nbFrameS = Frame(self.frameS)   # will contain toolbar and notebook
        self.frameS.add(self.nbFrameS, minsize=50, sticky="NSEW")
        self.toolbarFrameS = Frame(self.nbFrameS)
        self.notebookFrameS = Frame(self.nbFrameS)
        self.notebook = Notebook(self.notebookFrameS)

        self.searchStat = Frame(self.notebook)
        self.notebook.add(self.searchStat, text=_('Statistics'))
        self.dateProfileFS = Frame(self.notebook)
        self.notebook.add(self.dateProfileFS, text=_('Date profile'))
        self.patternSearchOptions = Frame(self.notebook)
        self.notebook.add(self.patternSearchOptions, text=_('Options'))
        self.giSFS = Frame(self.notebook)
        self.notebook.add(self.giSFS, text=_('Game info'))
        self.gameinfoSearchFS = Frame(self.giSFS)
        self.tagFS = Frame(self.notebook)
        self.notebook.add(self.tagFS, text=_('Tags'))
        self.tagFrameS = Frame(self.tagFS)
        self.tagFrameS.pack(expand=YES, fill=BOTH)
        self.logFS = Frame(self.notebook)
        self.notebook.add(self.logFS, text=_('Log'))
        self.logFrameS = Frame(self.logFS)
        self.logger = Message(self.logFrameS)
        self.logFrameS.pack(expand=YES, fill=BOTH)
        self.logger.pack(expand=YES, fill=BOTH)

        self.gameinfoSearchFS.pack(side=TOP, expand=False, fill='both')

        self.notebook.pack(fill=BOTH, expand=YES, pady=0)
        self.notebook.bind('<<NotebookTabChanged>>', self.notebookTabChanged)

        noGamesLabel = Label(self.topFrameS, text=' ', width=18, height=1)
        noGamesLabel.grid(row=0, column=0)

        winPercLabel = Label(self.topFrameS, text=' ', width=18, height=1)
        winPercLabel.grid(row=0, column=1)

        self.gamelist = GameListGUI(self.listFrameS, self, noGamesLabel, winPercLabel, self.gameinfoS)
        self.gamelist.pack(expand=YES, fill=BOTH, side=TOP)

        self.progBar = Progressbar(self.nbFrameS)
        self.progBar.start(50)

        self.toolbarFrameS.pack(side=TOP, fill=X, expand=NO)
        self.progBar.pack(side=BOTTOM, fill=X, expand=NO)
        self.notebookFrameS.pack(side=TOP, fill=BOTH, expand=YES)

        # search history

        if self.options.search_history_as_tab.get():
            self.prevSearchF = Frame(self.notebook)
            self.notebook.insert(5, self.prevSearchF, text=_('History'))
            self.master.bind_all('<Control-h>', lambda e, self=self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.prevSearchF.winfo_id())))  # select history tab
        else:
            self.prevSearchF = Frame(self.dataWindow.win)
            self.dataWindow.win.add(self.prevSearchF)
            self.dataWindow.set_geometry(self.options.dataWindowGeometryK.get())

        self.prevSF = ScrolledFrame(self.prevSearchF, usehullsize=1, hull_width=300, hull_height=235, hscrollmode='static', vscrollmode='none', vertflex='elastic')

        self.prevSF.pack(expand=YES, fill=BOTH)
        self.prevSearches = PrevSearchesStack(self.options.maxLengthSearchesStack, self.board.changed, self.prevSF, self)
        self.board.callOnChange = self.prevSearches.select_clear

        self.initMenusK()

        # evaluate kombilo.cfg file (default databases etc.)

        self.datapath = self.config['main']['datapath'] if 'datapath' in self.config['main'] else v.get_configfile_directory()

        # read databases section
        self.gamelist.populateDBlist(self.config['databases'])

        # read custom tags
        if 'tags' in self.config:
            self.gamelist.customTags = self.config['tags']
        if 'taglook' in self.config:
            self.gamelist.taglook = self.config['taglook']

        # self.searchWindow.deiconify()

        self.buttonFrame1S = Frame(self.toolbarFrameS)
        self.buttonFrame1S.pack(side=LEFT, expand=NO)

        self.resetButtonS = Button(self.buttonFrame1S, text=_('Reset'), command=self.reset)
        self.resetstartButtonS = Button(self.buttonFrame1S, text=_('Reset/start'), command=self.reset_start)
        self.searchButtonS = Button(self.buttonFrame1S, text=_('Pattern search'), command=self.search)
        self.backButtonS = Button(self.buttonFrame1S, text=_('Back'), command=self.back)

        self.showContinuation = IntVar()
        self.showContinuation.set(1)
        self.showContButtonS = Checkbutton(self.buttonFrame1S, text=_('Continuations'), variable=self.showContinuation, indicatoron=0, command=self.showCont)

        self.oneClick = IntVar()
        self.oneClickButtonS = Checkbutton(self.buttonFrame1S, text=_('1 click'), variable=self.oneClick, indicatoron=0)

        self.statByDateButtonS = Checkbutton(self.buttonFrame1S, text=_('Statistics by Date'), variable=self.options.statistics_by_date, indicatoron=0, command=self.display_statistics)

        for ii, b in enumerate([self.searchButtonS, self.resetstartButtonS, self.resetButtonS, self.backButtonS, self.showContButtonS, self.oneClickButtonS, self.statByDateButtonS]):
            b.grid(row=0, column=ii)

        # -------------------------

        self.statisticsCanv = Canvas(self.searchStat, highlightthickness=0)
        self.statisticsCanv.bind('<Configure>', self.resize_statistics_canvas)
        self.statisticsCanv.pack(side=BOTTOM, expand=YES, fill=BOTH)

        self.dateProfileCanv = Canvas(self.dateProfileFS, highlightthickness=0)
        self.dateProfileCanv.bind('<Configure>', self.resize_statistics_canvas)
        self.dateProfileCanv.pack(side=BOTTOM, expand=YES, fill=BOTH)

        sep2 = Separator(self.toolbarFrameS, orient='vertical')
        sep2.pack(padx=5, fill=Y, side=LEFT)
        self.colorButtonS = Checkbutton(
                self.toolbarFrameS,
                text=_('Fixed Color'),
                highlightthickness=0,
                variable=self.fixedColorVar)
        self.colorButtonS.pack(side=LEFT)

        sep1 = Separator(self.toolbarFrameS, orient='vertical')
        sep1.pack(padx=5, fill=Y, side=LEFT)
        l = Label(self.toolbarFrameS, text=_('Next:'))
        l.pack(side=LEFT)

        self.nextMoveVar = IntVar()  # 0 = either player, 1 = black, 2 = white
        self.nextMove1S = Radiobutton(self.toolbarFrameS, text=_('B/W'), highlightthickness=0, indicatoron=0, variable=self.nextMoveVar, value=0, bg='#999999')
        self.nextMove1S.pack(side=LEFT)
        self.nextMove2S = Radiobutton(self.toolbarFrameS, text=_('B'), highlightthickness=0, indicatoron=0, variable=self.nextMoveVar, value=1, bg='#999999')
        self.nextMove2S.pack(side=LEFT)
        self.nextMove3S = Radiobutton(self.toolbarFrameS, text=_('W'), highlightthickness=0, indicatoron=0, variable=self.nextMoveVar, value=2, bg='#999999')
        self.nextMove3S.pack(side=LEFT)

        self.fixedAnchorVar = IntVar()
        self.anchorButtonS = Checkbutton(self.patternSearchOptions, text=_('Fixed Anchor'), highlightthickness=0, variable=self.fixedAnchorVar)
        self.anchorButtonS.grid(row=0, column=0, columnspan=2, sticky=W)

        self.searchInVariations = BooleanVar()
        self.searchInVariations.set(True)
        self.searchInVariationsButton = Checkbutton(self.patternSearchOptions, text=_('Search in variations'), highlightthickness=0, variable=self.searchInVariations)
        self.searchInVariationsButton.grid(row=1, column=0, columnspan=2, sticky=W)

        self.mvLimLabel = Label(self.patternSearchOptions, text=_('Move limit'))
        self.mvLimLabel.grid(row=2, column=0, sticky=W)
        self.moveLimit = IntVar()
        self.moveLimit.set(250)
        self.scaleS = Scale(self.patternSearchOptions, highlightthickness=0, length=160, variable=self.moveLimit, from_=1, to=250, tickinterval=149, showvalue=YES, orient='horizontal')
        self.scaleS.grid(row=2, column=1)

        sep1 = Separator(self.patternSearchOptions, orient='horizontal')
        sep1.grid(row=3, column=0, columnspan=2, sticky=NSEW)

        self.algo_hash_full_search = IntVar()
        self.algo_hash_full_search.set(1)
        self.algo_hash_full = Checkbutton(self.patternSearchOptions, text=_('Use hashing for full board positions'), highlightthickness=0, variable=self.algo_hash_full_search, pady=5)
        self.algo_hash_full.grid(row=4, column=0, columnspan=2, sticky=W)

        self.algo_hash_corner_search = IntVar()
        self.algo_hash_corner_search.set(1)
        self.algo_hash_corner = Checkbutton(self.patternSearchOptions, text=_('Use hashing for corner positions'), highlightthickness=0, variable=self.algo_hash_corner_search, pady=5)
        self.algo_hash_corner.grid(row=5, column=0, columnspan=2, sticky=W)

        sep2 = Separator(self.patternSearchOptions, orient='horizontal')
        sep2.grid(row=6, column=0, columnspan=2, sticky=NSEW)

        # add widgets for date profile options

        self.patternSearchOptions_dp = Frame(self.patternSearchOptions)
        self.patternSearchOptions_dp.grid(row=7, columnspan=6, sticky=NSEW)
        self.dp_label = Label(self.patternSearchOptions_dp, text=_('Date profile options'))
        self.dp_label.grid(row=7, column=0, columnspan=4)
        self.dp_from_lb = Label(self.patternSearchOptions_dp, text=_('From'))
        self.dp_from = Entry(self.patternSearchOptions_dp, width=6, textvariable=self.options.date_profile_from)
        self.dp_from_lb.grid(row=8, column=0, padx=3)
        self.dp_from.grid(row=8, column=1, padx=3)
        self.dp_to_lb = Label(self.patternSearchOptions_dp, text=_('To'))
        self.dp_to = Entry(self.patternSearchOptions_dp, width=6, textvariable=self.options.date_profile_to)
        self.dp_to_lb.grid(row=8, column=2, padx=3)
        self.dp_to.grid(row=8, column=3, padx=3)
        self.dp_chunk_size_lb = Label(self.patternSearchOptions_dp, text=_('Months/bar'))
        self.dp_chunk_size = Entry(self.patternSearchOptions_dp, width=4, textvariable=self.options.date_profile_chunk_size)
        self.dp_chunk_size_lb.grid(row=8, column=4, padx=3)
        self.dp_chunk_size.grid(row=8, column=5, padx=3)
        self.patternSearchOptions_dp1 = Frame(self.patternSearchOptions)
        self.patternSearchOptions_dp1.grid(row=8, columnspan=8, sticky=NSEW)
        self.dp_sort_crit_lb = Label(self.patternSearchOptions_dp1, text=_('Sort continuations by'))
        self.dp_sort_crit_lb.grid(row=0, column=0)
        self.dp_sort_crit = Combobox(self.patternSearchOptions_dp1, values=(_('total'), _('earliest'), _('latest'), _('average'), _('became popular'), _('became unpopular'), ), textvariable=self.options.continuations_sort_crit,
                                     state='readonly', width=25)
        self.dp_sort_crit.grid(row=0, column=1, padx=3)

        # validation for date profile options, and triggering of date profile update when options are changed

        def validate(var, default):
            try:
                assert int(var.get()) >= 1
            except:
                var.set(default)
            self.redo_date_profile = True

        self.options.date_profile_from.trace('w', lambda dummy1, dummy2, dummy3, var=self.options.date_profile_from, default=1930: validate(var, default))
        self.options.date_profile_to.trace('w', lambda dummy1, dummy2, dummy3, var=self.options.date_profile_to, default=datetime.datetime.today().year: validate(var, default))
        self.options.date_profile_chunk_size.trace('w', lambda dummy1, dummy2, dummy3, var=self.options.date_profile_chunk_size, default=6: validate(var, default))

        # ------------------------------------------------------------------------------

        # game info search frame

        f1 = Frame(self.gameinfoSearchFS, borderwidth=1)
        f1.pack(expand=YES, fill=X)
        f1.columnconfigure(1, weight=1)
        f1.columnconfigure(3, weight=1)
        f3 = Frame(self.gameinfoSearchFS)
        f3.pack(expand=YES, fill=BOTH)

        self.pbVar = StringVar()
        self.pwVar = StringVar()
        self.pVar = StringVar()
        self.evVar = StringVar()
        self.frVar = StringVar()
        self.toVar = StringVar()
        self.awVar = StringVar()
        self.sqlVar = StringVar()

        l1 = Label(f1, text=_('White'), anchor=W)
        e1 = Entry(f1, width=16, textvariable=self.pwVar)
        l2 = Label(f1, text=_('Black'), anchor=W)
        e2 = Entry(f1, width=16, textvariable=self.pbVar)
        l3 = Label(f1, text=_('Player'), anchor=W)
        e3 = Entry(f1, width=33, textvariable=self.pVar)
        l4 = Label(f1, text=_('Event'), anchor=W)
        e4 = Entry(f1, width=33, textvariable=self.evVar)
        l5 = Label(f1, text=_('From'), anchor=W)
        e5 = Entry(f1, width=16, textvariable=self.frVar)
        l6 = Label(f1, text=_('To'), anchor=W)
        e6 = Entry(f1, width=16, textvariable=self.toVar)

        l7 = Label(f1, text=_('Anywhere'), anchor=W)
        e7 = Entry(f1, width=33, textvariable=self.awVar)

        l8 = Label(f1, text=_('SQL'), anchor=W)
        e8 = Entry(f1, width=43, textvariable=self.sqlVar)

        self.referencedVar = IntVar()
        b1 = Checkbutton(f3, text=_('Referenced'), variable=self.referencedVar, highlightthickness=0)

        self.GIstart = Button(f3, text=_('Start'), command=self.doGISearch)
        self.GIclear = Button(f3, text=_('Clear'), command=self.clearGI)

        self.GI_bwd = Button(f3, text='<-', command=self.historyGI_back)
        self.GI_fwd = Button(f3, text='->', command=self.historyGI_fwd)

        for e in [e1, e2, e3, e4, e5, e6, e7, e8]:
            e.bind('<Return>', lambda event, bs=self.GIstart: bs.invoke())

        l1.grid(row=0, column=0, sticky=E)
        e1.grid(row=0, column=1, sticky=NSEW)
        l2.grid(row=0, column=2, sticky=E)
        e2.grid(row=0, column=3, sticky=NSEW)
        l3.grid(row=2, column=0, sticky=E)
        e3.grid(row=2, column=1, columnspan=3, sticky=NSEW)
        l4.grid(row=3, column=0,  sticky=E)
        e4.grid(row=3, column=1, columnspan=3, sticky=NSEW)
        l5.grid(row=4, column=0, sticky=E)
        e5.grid(row=4, column=1, sticky=NSEW)
        l6.grid(row=4, column=2, sticky=E)
        e6.grid(row=4, column=3, sticky=NSEW)

        l7.grid(row=5, column=0, sticky=E)
        e7.grid(row=5, column=1, columnspan=3, sticky=NSEW)

        l8.grid(row=6, column=0, sticky=E)
        e8.grid(row=6, column=1, columnspan=3, sticky=NSEW)

        b1.pack(side=LEFT, padx=10)
        self.GI_fwd.pack(side=RIGHT)
        self.GI_bwd.pack(side=RIGHT)
        self.GIstart.pack(side=RIGHT)
        self.GIclear.pack(side=RIGHT)

        f4 = Separator(self.gameinfoSearchFS, orient='horizontal')
        f4.pack(side=TOP, expand=False, fill=BOTH, pady=20)

        f5 = Frame(self.gameinfoSearchFS)
        f5.pack(side=TOP, expand=False, fill=X)

        l1 = Label(f5, text=_('Go to:'), anchor=W)
        l1.pack(side=LEFT)
        self.gotoVar = StringVar()
        e9 = Entry(f5, width=20, textvariable=self.gotoVar)
        e9.pack(side=LEFT, expand=YES, fill=X)
        for key, fct in [('<Key>', self.gotoChange), ('<Up>', self.gamelist.up), ('<Down>', self.gamelist.down), ('<Prior>', self.gamelist.pgup), ('<Next>', self.gamelist.pgdown)]:
            e9.bind(key, fct)

        self.history_GIsearch = []
        self.history_GIS_index = -1

        self.inittags()

        # icons for the buttons
        for button, filename in [
                (self.showContButtonS, 'abc-u'),
                (self.backButtonS, 'actions-edit-undo'),
                (self.resetButtonS, 'actions-go-home'),
                (self.resetstartButtonS, 'go-home-start'),
                (self.searchButtonS, 'actions-system-search'),
                (self.oneClickButtonS, 'devices-input-mouse'),
                (self.statByDateButtonS, 'apps-office-calendar'),
                (self.nextMove1S, 'bw'),
                (self.nextMove2S, 'b'),
                (self.nextMove3S, 'w'),
                (self.GIstart, 'actions-system-search'),
                (self.GIclear, 'actions-document-new'),
                (self.GI_bwd, 'actions-go-previous'),
                (self.GI_fwd, 'actions-go-next'),
                (self.tagsearchButton, 'actions-system-search'),
                (self.tagaddButton, 'actions-list-add'),
                (self.tagdelButton, 'actions-list-remove'),
                (self.tagallButton, 'actions-edit-select-all'),
                (self.untagallButton, 'actions-edit-clear'),
                (self.tagsetButton, 'actions-bookmark-new'),
                ]:
            v.load_icon(button, filename, self.tkImages, self.options.scaling.get())

        self.custom_menus.path = v.get_configfile_directory()
        self.custom_menus.buildMenus()

        # load logo
        try:
            self.logo = PILImageTk.PhotoImage(PILImage.open(pkg_resources.resource_stream(__name__, 'icons/kombilo_logo.png')))
        except TclError:
            self.logo = None

        self.balloonHelpK()
        self.evalOptionsK()

        self.board.update_idletasks()
        # self.notebook.setnaturalsize()
        self.searchWindow.update_idletasks()

        # splash screen TODO

        if self.options.smartFixedColor.get():
            self.fixedColorVar.set(1)
        self.gamelist.showFilename = self.options.showFilename.get()
        self.gamelist.showDate = self.options.showDate.get()
        self.parseReferencesFile(datafile=pkg_resources.resource_stream(__name__, 'data/references'),
                                 options=self.config['references'] if 'references' in self.config else None)
        self.loadDBs(self.progBar, showwarning)

        self.logger.insert(END, 'Kombilo %s.\n' % KOMBILO_RELEASE + _('Ready ...') + '\n')
        self.progBar.stop()

# ---------------------------------------------------------------------------------------

def run():
    root = Tk()
    root.withdraw()
    root.option_add("*Font", "TkDefaultFont")

    try:
        if os.path.exists(os.path.join(v.get_configfile_directory(), 'kombilo.app')):
            root.option_readfile(os.path.join(v.get_configfile_directory(), 'kombilo.app'))
    except TclError:
        showwarning(_('Error'), _('Error reading kombilo.app file.'))

    app = App(root)

    root.protocol('WM_DELETE_WINDOW', app.quit)
    root.title('Kombilo')

    app.boardFrame.focus_force()

    for filename in sys.argv[1:]:              # load sgf files given as arguments
        app.openFile(os.path.split(filename)[0], os.path.split(filename)[1])

    root.mainloop()
    root.destroy()

if __name__ == '__main__':
    run()

