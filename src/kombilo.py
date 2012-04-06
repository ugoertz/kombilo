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

import time
import os
import sys
import cPickle
from copy import copy, deepcopy
from string import split, find, join, strip, replace, digits, maketrans, translate, lower
import glob
import re
from array import *
from configobj import ConfigObj

from Tkinter import *
from ttk import *
from tkMessageBox import *
from ScrolledText import ScrolledText
import tkFileDialog
from tkCommonDialog import Dialog
from tkSimpleDialog import askstring
from tooltip.tooltip import ToolTip

from kombiloNG import *


from Pmw import ScrolledFrame
import Pmw

from vsl.vl import VScrolledList


from board import *
import v

import libkombilo as lk
from sgf import Node, Cursor


KOMBILO_RELEASE = '0.7.2'

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
    return apply(chooseDirectory, (), options).show()

#---------------------------------------------------------------------------------------

class BoardWC(Board):
    """ Board with support for wildcards and selection
        of search-relevant region. Furthermore, snapshot returns a dictionary which
        describes the current board position. It can then be restored with restore."""

    
    def __init__(self, master, boardsize, canvasSize, fuzzy, labelFontsize, focus, callOnChange, boardImg, blackImg, whiteImg, use_PIL=True, onlyOneMouseButton = 0):
        Board.__init__(self, master, boardsize, canvasSize, fuzzy, labelFontsize, focus, callOnChange, boardImg, blackImg, whiteImg, use_PIL)

        self.wildcards = {}

        self.selection = ((0,0),(self.boardsize-1,self.boardsize-1))

        self.fixedColor = IntVar()
        self.smartFixedColor = IntVar()

        self.onlyOneMouseButton = 'init'
        self.rebindMouseButtons(onlyOneMouseButton)

        self.bounds1 = self.bind('<Shift-1>', self.wildcard)

        self.invertSelection = IntVar()


    def rebindMouseButtons(self, onlyOneMouseButton):
        if self.onlyOneMouseButton != 'init': # do not do this during the first run (since self.bound3m, self.bound3 do not exist yet)
            if self.onlyOneMouseButton:
                click, motion = self.onlyOneMouseButton.split(';')
                self.unbind(click, self.bound3m)
                self.unbind(motion, self.bound3)
            else:
                self.unbind('<B3-Motion>', self.bound3m)
                self.unbind('<3>', self.bound3)
        self.onlyOneMouseButton = onlyOneMouseButton
        if onlyOneMouseButton:
            click, motion = onlyOneMouseButton.split(';')
            self.bound3 = self.bind(click, self.selStart)  # '<M2-Button-1>'
            self.bound3m = self.bind(motion, self.selDrag) # '<M2-B1-Motion>'
        else:
            self.bound3 = self.bind('<Button-3>', self.selStart)
            self.bound3m = self.bind('<B3-Motion>', self.selDrag)


    def resize(self, event = None):
        """ Resize the board. Take care of wildcards and selection here. """
        
        Board.resize(self, event)
        for x,y in self.wildcards: self.place_wildcard(x,y,self.wildcards[(x,y)][1])

        self.delete('selection')
        if self.selection != ((0,0),(self.boardsize-1,self.boardsize-1)) and self.selection[1] != (0,0):
            p0 = self.getPixelCoord(self.selection[0],1)
            p1 = self.getPixelCoord((self.selection[1][0]+1, self.selection[1][1]+1), 1)
            min = self.getPixelCoord((0,0), 1)[0]+1
            max = self.getPixelCoord((self.boardsize,self.boardsize),1)[1]-1
            if self.canvasSize[1] <= 7:
                self.create_rectangle(p0[0], p0[1], p1[0], p1[1], tags=('selection', 'non-bg'))
            elif self.invertSelection.get():
                self.create_rectangle(p0[0], p0[1], p1[0], p1[1], fill='brown', stipple='gray50', outline='', tags='selection')
            else:
                if p0[1] > min:
                    self.create_rectangle(min, min, max, p0[1], fill='brown', stipple='gray50', outline='', tags='selection')
                if p0[0] > min and p0[1] < max:
                    self.create_rectangle(min, p0[1], p0[0], max, fill='brown', stipple='gray50', outline='', tags='selection')
                if p1[1] < max:
                    self.create_rectangle(p0[0], p1[1], p1[0], max, fill='brown', stipple='gray50', outline='', tags='selection')
                if p1[0] < max and p0[1] < max:
                    self.create_rectangle(p1[0], p0[1], max, max, fill='brown', stipple='gray50', outline='', tags='selection')
            self.tkraise('non-bg')
            
        self.update_idletasks()

    def place_wildcard(self, x, y, wc_type):
        x1, x2, y1, y2 = self.getPixelCoord((x,y),1)
        if self.canvasSize[1]<=7: margin = 5
        else: margin = 4
        self.wildcards[(x,y)] = (self.create_oval(x1+margin, x2+margin, y1-margin, y2-margin, fill = { '*':'green', 'x':'black', 'o':'white'}[wc_type], tags=('wildcard','non-bg')), wc_type)
        self.tkraise('label')

    def wildcard(self, event):
        """ Place/delete a wildcard at position of click. """
        
        x, y = self.getBoardCoord((event.x, event.y), 1)
        if not (0 <= x < self.boardsize and 0 <= y and self.getStatus(x,y) == ' '): return

        if (x,y) in self.wildcards:
            wc, wc_type = self.wildcards[(x,y)]
            self.delete(wc)
            del self.wildcards[(x,y)]

            if wc_type == '*': self.place_wildcard(x,y,'x')
            elif wc_type == 'x': self.place_wildcard(x,y,'o')
        else:
            self.place_wildcard(x,y,'*')
        self.renew_labels()
        self.changed.set(1)        


    def delWildcards(self):
        """ Delete all wildcards. """
        
        if self.wildcards: self.changed.set(1)
        self.delete('wildcard')
        self.wildcards = {}


    def placeLabel(self, pos, typ, text=None, color=None):
        """ Place a label; take care of wildcards at same position. """
        
        if self.wildcards.has_key(pos):
            override = { '*': ('black', ''), 'o': ('black', ''), 'x': ('white', '') }[self.wildcards[pos][1]]
        else: override = None

        Board.placeLabel(self, pos, typ, text, color, override)

                              
    # ---- selection of search-relevant section -----------------------------------

    def selStart(self, event):
        """ React to right-click. """
        self.delete('selection')
        x, y = self.getBoardCoord((event.x, event.y), 1)
        x = max(x, 0)
        y = max(y, 0)
        self.selection = ((x,y), (-1,-1))
        if self.smartFixedColor.get(): self.fixedColor.set(1)
        self.changed.set(1)


    def selDrag(self, event):
        """ React to right-mouse-key-drag. """
        pos = self.getBoardCoord((event.x, event.y), 1)
        if pos[0] >= self.selection[0][0] and pos[1] >= self.selection[0][1]:
            self.setSelection(self.selection[0], pos)
            

    def setSelection(self, pos0, pos1):
        self.selection = (pos0, pos1)
        self.delete('selection')
        p0 = self.getPixelCoord(pos0,1)
        p1 = self.getPixelCoord((pos1[0]+1, pos1[1]+1), 1)
        min = self.getPixelCoord((0,0), 1)[0]+1
        max = self.getPixelCoord((self.boardsize,self.boardsize),1)[1]-1
        if self.canvasSize[1] <= 7:
            self.create_rectangle(p0[0], p0[1], p1[0], p1[1], tags=('selection', 'non-bg'))
        elif self.invertSelection.get():
            self.create_rectangle(p0[0], p0[1], p1[0], p1[1], fill='brown', stipple='gray50', outline='', tags='selection')
        else:
            if p0[1] > min:
                self.create_rectangle(min, min, max, p0[1], fill='brown', stipple='gray50', outline='', tags='selection')
            if p0[0] > min and p0[1] < max:
                self.create_rectangle(min, p0[1], p0[0], max, fill='brown', stipple='gray50', outline='', tags='selection')
            if p1[1] < max:
                self.create_rectangle(p0[0], p1[1], p1[0], max, fill='brown', stipple='gray50', outline='', tags='selection')
            if p1[0] < max and p0[1] < max:
                self.create_rectangle(p1[0], p0[1], max, max, fill='brown', stipple='gray50', outline='', tags='selection')
            
        self.tkraise('non-bg')
        
        if self.smartFixedColor.get():
            if self.selection == ((0,0), (self.boardsize-1,self.boardsize-1)):
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
        self.selection = ((0,0),(self.boardsize-1,self.boardsize-1))

        if self.smartFixedColor.get(): self.fixedColor.set(1)


    # ---- snapshot & restore (for 'back' button)

    def snapshot(self):
        """ Return a dictionary which contains the data of all the objects
            currently displayed on the board, which are not stored in the SGF file.
            This means, at the moment: wildcards, and selection. """
        
        data = {}
        data['boardsize'] = self.boardsize
        data['status'] = [ [ self.getStatus(i,j) for j in range(self.boardsize) ] for i in range(self.boardsize) ]
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
                        self.setStatus(i,j,d['status'][i][j])
                        self.placeStone((i,j), d['status'][i][j])
            if not small:
                for p in d['labels']:
                    typ, text, dummy, color = d['labels'][p]
                    self.placeLabel(p, typ, text, color)

        for x,y in d['wildcards']: self.place_wildcard(x,y, d['wildcards'][(x,y)][1])
        if d['selection'] != ((0,0),(self.boardsize-1, self.boardsize-1)) and d['selection'][1] != (0,0):
            self.setSelection(d['selection'][0], d['selection'][1])


class BoardWCNoLabels(BoardWC):
    '''Used for the small boards in the list of previous searches. Does not display text labels.'''

    def __init__(self, *args, **kwargs):
        BoardWC.__init__(self, *args, **kwargs)

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
        
        Button(self.buttonFrame, text='Include game list', command=self.includeGameList).pack(side=LEFT)


    def includeGameList(self):
        separator = ' %%%\n' if self.style=='wiki' else '\n' # wiki/plain style
        self.text.insert(END, '\n\n!Game list\n\n' + separator.join(self.mster.gamelist.get_all()))
        

# -------------------------------------------------------------------------------------

class DataWindow(v.DataWindow):

    def get_geometry(self):
        self.win.update_idletasks()
        try:
            l = [ str(self.win.sash_coord(i)[1]) for i in range(5) ]
        except: # allow for DataWindow column having only five panes, if prevSearches are a tab in right hand column
            l = [ str(self.win.sash_coord(i)[1]) for i in range(4) ]
        return join(l, '|%')


    def set_geometry(self, s):
        l = split(s, '|%')
        for i in [4, 3, 2, 1, 0]:
            try:
                self.win.sash_place(i, 1, int(l[i]))
                self.win.update_idletasks()
            except: # allow win to have only 5 panes
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
        VScrolledList.__init__(self, parent, 500, 0, self.get_data, get_data_ic=self.get_data_ic)
        self.listbox.config(width=52, height=6) 
        self.onSelectionChange = self.printGameInfo
        for key, command in [ ('<Return>', self.handleDoubleClick), ('<Control-a>', self.printSignature), ]:
            self.listbox.bind(key, command)
        for key, command in [ ('<Button-1>', self.onSelectionChange), ('<Double-1>', self.handleDoubleClick), ('<Shift-1>', self.handleShiftClick), ('<Button-3>', self.rightMouseButton) ]:
            self.listbox.bind(key, command)
        self.noGamesLabel = noGamesLabel
        self.winPercLabel = winPercLabel
        self.gameinfo = gameinfo


    def get_data(self, i):
        return GameList.get_data(self, i, showTags = self.mster.options.showTags.get())

    def get_all(self):
        return [ GameList.get_data(self, i, showTags = self.mster.options.showTags.get()) for i in range(len(self.gameIndex)) ]


    def get_data_ic(self, i):
        """Return taglook for specified line. (ic = itemconfig).
        """
        try:
            db, game = self.getIndex(i)
            ID, pos = self.DBlist[db]['data'].currentList[game]
            taglist = self.DBlist[db]['data'].getTagsID(ID,0)
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

        self.mster.logger.insert(END, GameList.printSignature(self, index)+ '\n')

    def printSignature(self, event):
        try:
            index = self.get_index(int(self.listbox.curselection()[0]))
        except:
            return

        self.mster.logger.insert(END, GameList.printSignature(self, index)+ '\n')


    def addTag(self, tag, index):
        GameList.addTag(self, tag, index)
        self.mster.selecttags(self.getTags(index))
        self.upd()


    def setTags(self, tags):
        try:
            index = self.get_index(int(self.listbox.curselection()[0]))
        except:
            return
        if index == -1: return
        DBindex, index = self.getIndex(index)
        if DBindex == -1: return
        newtags = set(tags)
        oldtags = set(self.DBlist[DBindex]['data'].getTags(index))

        for t in newtags-oldtags:
            self.DBlist[DBindex]['data'].setTag(t, index, index+1)
        for t in oldtags-newtags:
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
        self.noGamesLabel.config(text = `noOfG` + ' games')
        if noOfG:
            self.winPercLabel.config(text='B: %1.1f%%, W: %1.1f%%' % (Bperc, Wperc))
        else: self.winPercLabel.config(text='')
        VScrolledList.reset(self)


    def printGameInfo(self, event, index = -1):
        """ Write game info of selected game to text frame below the list of games. """

        if index == -1:
            index = self.get_index(self.listbox.nearest(event.y))
            self.focus()
        try:
            t, t2 = GameList.printGameInfo(self, index)
        except: return

        self.gameinfo.configure(text_state=NORMAL)
        self.gameinfo.delete('1.0', END)
        self.gameinfo.insert('1.0', t)
        if t2:
            if t[-1]!='\n': self.gameinfo.insert(END, '\n')
            self.gameinfo.insert(END, t2, 'blue')
        self.gameinfo.configure(text_state=DISABLED)

        self.mster.selecttags(self.getIndicesTaglist(self.getTags(index)))


    def getIndicesTaglist(self, tags):
        l = [ int(x) for x in self.customTags.keys() ]
        l.sort()
        d = dict([ [ y,x+1 ] for x,y in enumerate(l) ])   # note x+1 because enumerate starts with 0, but we want to start with 1
        return [ d[t] for t in tags ]



    def rightMouseButton(self, event):
        
        index = self.get_index(self.listbox.nearest(event.y))
        if index == -1: return
        DBindex, index = self.getIndex(index)
        if DBindex == -1: return

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
            showwarning('Error', 'I/O Error')
            return
        except lk.SGFError:
            showwarning('Error', 'SGF error')
            return
        
        # backup = copy(rootNode.data)

        newRootNode = self.mster.gameinfo(rootNode)
        if (not newRootNode is None): # FIXME  and backup != newRootNode.data:
            c.updateRootNode(newRootNode, gameNumber)
            try:
                s = c.output()
                file = open(filename, 'w')
                file.write(s)
                file.close()
            except IOError:
                showwarning('I/O Error', 'Could not write to file ' + filename)


    def handleDoubleClick(self, event):
        """ This is called upon double-clicks."""
        
        index = self.get_index(int(self.listbox.curselection()[0]))
        self.addTag(SEEN_TAG, index)
        self.mster.openViewer(index)


    def handleShiftClick(self, event):
        index = self.listbox.nearest(event.y)
        index1 = self.listbox.curselection()
        if index1: self.listbox.select_clear(index1[0])
        self.listbox.select_set(index)
        self.onSelectionChange(event)
        self.addTag(SEEN_TAG, index)
        self.mster.altOpenViewer(index)


    def clearGameInfo(self):
        self.gameinfo.configure(text_state=NORMAL)
        self.gameinfo.delete('1.0', END)
        self.gameinfo.configure(text_state=DISABLED)


# ---------------------------------------------------------------------------------------

class PrevSearchesStack:

    """ This class provides a stack which contains the data of the previous searches,
    s.t. one can return to the previous search with the back button.
    
    self.data is a list of lists [copy(kwargs), b, onHold], where
    * kwargs is the keyword dictionary passed to append(), the keywords being boardData, snapshot_ids, modeVar, cursorSn (see def append())
    * b is the copy of the board at this point
    * the third argument determines whether this item is protected agains deletion (0=no, 1=yes)
    
    
    """


    def __init__(self, maxLength, boardChanged, prevSF, master):
        self.data = []
        self.mster = master
        
        self.maxLength = maxLength
        self.boardChanged = boardChanged

        self.prevSF = prevSF
        self.labelSize = IntVar()
        self.labelSize.set(4)

        self.selected = -1
        self.prev_select = -1

        self.popupMenu = None

        
    def append(self, **kwargs):
        ''' keywords are
        boardData = self.board.snapshot()
        snapshot_ids = [ db['data'].snapshot() for db in self.gamelist.DBlist if not db['disabled'] ],
        modeVar=self.modeVar.get()
        cursorSn = [self.cursor, self.cursor.currentGame, v.pathToNode(self.cursor.currentN)]
        '''
        
        if self.mster.options.maxLengthSearchesStack.get() and len(self.data) >= self.mster.options.maxLengthSearchesStack.get():
            for i, d in enumerate(self.data):
                if not d[2]:
                    self.delete(i)
                    break
            
        b = BoardWCNoLabels(self.prevSF.interior(), self.mster.board.boardsize, (9,5), 0, self.labelSize, 1, None, self.mster.boardImg, None, None) # small board
        b.resizable = 0
        b.pack(side=LEFT, expand=YES, fill=Y)
        b.update_idletasks()
        b.bound1 = b.bind('<1>', lambda event, self=self, l=len(self.data): self.click(l))
        if b.onlyOneMouseButton:
            b.unbind('<M2-B1-Motion>', b.bound3m)
            b.unbind('<M2-Button-1>', b.bound3)
        else:
            b.unbind('<B3-Motion>', b.bound3m)
            b.unbind('<3>', b.bound3)
        b.unbind('<Configure>', b.boundConf)
        b.bound3 = b.bind('<3>', lambda event, self=self, l = len(self.data): self.postMenu(event, l))
        b.unbind('<Shift-1>', b.bounds1)
        b.restore(kwargs['boardData'])
        b.tkraise('non-bg')
        b.resizable = 0

        self.prevSF.reposition()
        self.data.append([copy(kwargs), b, 0])
        self.select(len(self.data)-1)

        
    def postMenu(self, event, boardid):
        self.popupMenu = Menu(self.mster.dataWindow.window)
        self.popupMenu.config(tearoff=0)
        self.popupMenu.add_command(label = 'Delete', command = lambda self=self, boardid=boardid: self.unpostAndDelete(boardid))

        if self.data[boardid][2]:
            self.popupMenu.add_command(label = 'Release', command = lambda self=self, boardid=boardid: self.unpostAndRelease(boardid))
        else:
            self.popupMenu.add_command(label = 'Hold', command = lambda self=self, boardid=boardid: self.unpostAndHold(boardid))
            
        self.popupMenu.tk_popup(event.x_root, event.y_root)


    def unpost(self):
        if self.popupMenu:
            self.popupMenu.unpost()
            self.popupMenu = None
        
        
    def unpostAndDelete(self, boardid):
        self.unpost()
        self.delete(boardid)


    def unpostAndHold(self, boardid):
        self.unpost()
        self.data[boardid][2] = 1
        c = self.data[boardid][1].getPixelCoord((21,21), 1)[0]
        self.data[boardid][1].create_rectangle(6,6,c-4,c-4, fill='', outline='blue', width=2, tags='hold')
        

    def unpostAndRelease(self, boardid):
        self.unpost()
        self.data[boardid][2] = 0
        self.data[boardid][1].delete('hold')


    def delete(self, boardid):
        s, b, dummy = self.data[boardid]
        del self.data[boardid]

        if not b: return
        b.delete(ALL)
        b.unbind('<1>', b.bound1)
        b.unbind('<3>', b.bound3)
        b.pack_forget()
        b.destroy()
        
        if boardid == self.selected: self.selected = -1
        if boardid == self.prev_select: self.prev_select = -1
        if boardid < self.selected: self.selected -= 1
        if boardid < self.prev_select: self.prev_select -= 1
        
        for i, d in enumerate(self.data):
            s, b, dummy = d
            if b:
                b.bound1 = b.bind('<1>', lambda event, self=self, l=i: self.click(l))
                b.bound3 = b.bind('<3>', lambda event, self=self, l=i: self.postMenu(event, l))

        self.prevSF.reposition()


    def deleteFile(self, cursor):
        d = []
        for i, da in enumerate(self.data):
            if da[0]['cursorSn'][0] == cursor:
                d.append(i)
        d.reverse()
        for i in d:
            self.delete(i)


    def deleteGame(self, cursor, game):
        d = []
        for i, da in enumerate(self.data):
            if da[0]['cursorSn'][0] == cursor:
                if da[0]['cursorSn'][1] == game :
                    d.append(i)
                elif da[0]['cursorSn'][1] > game:
                    da[0]['cursorSn'][1] -= 1
        d.reverse()
        for i in d:
            self.delete(i)


    def exchangeGames(self, cursor, index1, index2):
        if index1 < index2:
            for da in self.data:
                if da[0]['cursorSn'][0] == cursor:
                    if da[0]['cursorSn'][1] == index1:
                        da[0]['cursorSn'][1] = index2
                    elif index1 < da[0]['cursorSn'][1] <= index2:
                        da[0]['cursorSn'][1] -= 1
        elif index1 > index2:
            for da in self.data:
                if da[0]['cursorSn'][0] == cursor:
                    if da[0]['cursorSn'][1] == index1:
                        da[0]['cursorSn'][1] = index2
                    elif index2 <= da[0]['cursorSn'][1] < index1:
                        da[0]['cursorSn'][1] += 1


    def deleteNode(self, cursor, game, pathToNode):
        d = []
        for i, da in enumerate(self.data):
            if da[0]['cursorSn'][0] == cursor and da[0]['cursorSn'][1] == game:
                j = 0
                p = da[0]['cursorSn'][2]
                
                while j < len(p) and j < len(pathToNode) and p[j] == pathToNode[j]:
                    j += 1

                if j == len(pathToNode):
                    d.append(i)

                if j < len(pathToNode) and j < len(p) and p[j] > pathToNode[j]:
                    da[0]['cursorSn'][2][j] -= 1
        d.reverse()
        for i in d:
            self.delete(i)
        
        
    def see(self, board):
        if board == END: self.prevSF.xview('moveto', 1.0)
        else:
            self.prevSF.xview('moveto', 1.0 / (len(self.data)+1) * board)


    def select(self, board):
        
        if board == -1 or board >= len(self.data): return

        if not self.data[board][1]: return
        else: b = self.data[board][1]
            
        self.select_clear()
        
        c = b.getPixelCoord((21,21), 1)[0]
        b.create_rectangle(2,2, c-2,c-2, width=3, outline = 'red', tags = 'sel')
        
        self.selected = board
        self.see(board)


    def click(self, board):
        self.select(board)
        self.mster.back(self.data[self.selected][0], self.selected)

        
    def select_clear(self):
        if 0 <= self.selected < len(self.data):
            self.data[self.selected][1].delete('sel')
            self.prev_select = self.selected 
            self.selected = -1


    def pop(self):

        if not self.data or self.selected == 0:
            self.select_clear()
            return None, None

        if self.selected == -1:
            if self.prev_select == -1: return None, None
            else: self.selected = self.prev_select + 1
        else:
            se = self.selected
            self.select_clear()
            self.selected = se
            
        self.selected -= 1

        if self.data[self.selected][1]:
            return (self.data[self.selected][0], self.selected)
        else:
            return (self.data[self.selected][0], -1)


    def clear(self):
        for db in self.mster.gamelist.DBlist:
            if db['disabled']: continue
            db['data'].delete_all_snapshots()
        while self.data: self.delete(0)
        self.selected = -1
        self.prev_select = -1

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
        self.config(state=DISABLED)


    def delete(self, pos1, pos2):
        self.config(state=NORMAL)
        ScrolledText.delete(self, pos1, pos2)
        self.config(state=DISABLED)

# ---------------------------------------------------------------------------------------




class App(v.Viewer, KEngine):
    """ The main class of Kombilo. """


    def displayDateProfile(self):
        """
        Display date profile of current game list.
        """

        d = self.dateProfileRelative()
        m = max((y*1.0/z if z else 0) for x,y,z in d)
        if m == 0:
            self.displayBarChart(self.dateProfileCanv, 'stat', title='-')
            return

        data = [ { 'black': y*1.0/(z*m) if z else 0, 'label': [ '%d' % x[0], '-', '%d' % (x[1]-1,) ], 'label_top': [ '%d/' % y, '%d' % z ] } for x, y, z in d ]
        self.displayBarChart(self.dateProfileCanv, 'stat', data=data, colors = ['black'], title='Date profile, %d games' % self.gamelist.noOfGames())


    def displayStatistics(self):
        """
        Display statistical information on the last search on self.statisticsCanv.
        """

        noMatches = self.noMatches
        if not noMatches: return

        Bperc = self.Bwins * 100.0 / noMatches
        Wperc = self.Wwins * 100.0 / noMatches
           
        if not self.continuations:
            self.displayBarChart(self.statisticsCanv, 'stat', title = '%d matches (%d/%d), B: %1.1f%%, W: %1.1f%%' % (noMatches, self.noMatches-self.noSwitched, self.noSwitched, Bperc, Wperc))
            return

        maxHeight = self.continuations[0][0]
        data = []
        for i, (total, x, y, B, wB, lB, tB, W, wW, lW, tW, label) in enumerate(self.continuations[:12]):
            data.append({ 'black': (B-tB) * 1.0/maxHeight, self.options.Btenuki.get(): tB*1.0/maxHeight,
                          'white': (W-tW) * 1.0/maxHeight, self.options.Wtenuki.get(): tW*1.0/maxHeight,
                          'label': [ label, '%1.1f' % (wW*100.0/W) if W else '-', '%1.1f' % (wB*100.0/B) if B else '-' ],
                          'label_top': [ '%d' % (B+W) ], })

        self.displayBarChart(self.statisticsCanv, 'stat',
                             data=data, colors= [ self.options.Btenuki.get(), 'black', 'white', self.options.Wtenuki.get() ],
                             title = '%d matches (%d/%d), B: %1.1f%%, W: %1.1f%%' % (noMatches, self.noMatches-self.noSwitched, self.noSwitched, Bperc, Wperc))


    def displayBarChart(self, canvas, tag, colors=[], data=[], title=''):
        """
        Display a bar chart on canvas.

        color is a list of colors, e.g. ['black', 'yellow', 'white'].

        title is printed above the bar chart

        data is a list, one entry per column to be displayed.

        Each entry of data is a dictionary which maps each color to a number
        betwwen 0 and 1, and optionally has entries "label": list of
        text_of_label for labels below bar, 'label_top': text of label above
        bar.
        """

        canvas.delete(tag)
        font = (self.options.statFont.get(), self.options.statFontSize.get(), self.options.statFontStyle.get())
        smallfont = (self.options.statFont.get(), self.options.statFontSizeSmall.get(), self.options.statFontStyle.get())

        W, H = 400, 250  # width, height of statisticsCanv
        bar_width = W//14
        A, B = 12, 8


        canvas.create_text(5, 5, text=title, font=font, anchor='nw', tags=tag)

        for i, column in enumerate(data):
            ht = 30
            for l in column.get('label', []):
                canvas.create_text((i+1)*bar_width, H-ht, text=l, font=font, tags=tag)
                ht -= 10
            ht = 0
            for c in colors:
                if column[c]:
                    v = int(column[c] * (H-110))
                    canvas.create_rectangle((i+1)*bar_width-A, H-50-ht-v, (i+1)*bar_width+B, H-50-ht, fill=c, outline='', tags=tag)
                    ht += v
            for j, l in enumerate(column.get('label_top', [])):
                canvas.create_text((i+1)*bar_width, H-60-ht-10*(len(column['label_top'])-j), font = font, text=l, tags=tag)


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
        if not self.history_GIsearch: return
        self.history_GIS_index -= 1
        if self.history_GIS_index == -1: self.history_GIS_index = len(self.history_GIsearch)-1

        varList = [self.pbVar, self.pwVar, self.pVar, self.evVar, self.frVar, self.toVar, self.awVar, self.sqlVar, self.referencedVar]

        for i, var in enumerate(varList):
            var.set(self.history_GIsearch[self.history_GIS_index][i])


    def historyGI_fwd(self):
        if not self.history_GIsearch: return
        self.history_GIS_index += 1
        if self.history_GIS_index == len(self.history_GIsearch): self.history_GIS_index = 0
        varList = [self.pbVar, self.pwVar, self.pVar, self.evVar, self.frVar, self.toVar, self.awVar, self.sqlVar, self.referencedVar]

        for i, var in enumerate(varList):
            var.set(self.history_GIsearch[self.history_GIS_index][i])


    def doGISearch(self):
        """ Carry out the search for the parameters in *Var. All non-empty Var's
        have to match at the same time. In the case of pbVar, pwVar, pVar, evVar,
        the string has to occur somewhere in PB[ ...] (...), not necessarily at the
        beginning. For the date, the first four-digit number in DT[] is compared
        to frVar and toVar."""

        if not self.gamelist.noOfGames(): self.reset()

        pbVar = self.pbVar.get().encode('utf-8')
        pwVar = self.pwVar.get().encode('utf-8')
        pVar  = self.pVar.get().encode('utf-8')
        evVar = self.evVar.get().encode('utf-8')
        frVar = self.frVar.get()
        toVar = self.toVar.get()
        awVar = self.awVar.get().encode('utf-8')
        sqlVar = self.sqlVar.get().encode('utf-8')
        refVar = self.referencedVar.get()

        self.history_GIsearch.append((pbVar, pwVar, pVar, evVar, frVar, toVar, awVar, sqlVar, refVar))
        self.history_GIS_index = len(self.history_GIsearch) - 1

        if frVar:
            if re.match('\d\d\d\d-\d\d-\d\d', frVar): pass
            elif re.match('\d\d\d\d-\d\d', frVar): frVar += '-01'
            elif re.match('\d\d\d\d', frVar): frVar += '-01-01'
            else: frVar = ''

        if toVar:
            if re.match('\d\d\d\d-\d\d-\d\d', toVar): pass
            elif re.match('\d\d\d\d-\d\d', toVar): toVar += '-31'
            elif re.match('\d\d\d\d', toVar): toVar += '-12-31'
            else: toVar = ''

        if not (pbVar or pwVar or pVar or evVar or frVar or toVar or awVar or sqlVar or refVar): return

        queryl = []
        for key, val in [('PB', pbVar), ('PW', pwVar), ('ev', '%' + evVar), ('sgf', '%'+awVar)]:
            if val and val != '%':
                queryl.append("%s like '%s%%'" % (key, val))
        if pVar: queryl.append("(PB like '%s%%' or PW like '%s%%')" % (pVar, pVar))
        if frVar: queryl.append("DATE >= '%s'" % frVar)
        if toVar: queryl.append("DATE <= '%s'" % toVar)
        if sqlVar: queryl.append("(%s)" % sqlVar)

        if refVar: self.tagSearch(None, self.gamelist.customTags[str(REFERENCED_TAG)][0])
        if not (pbVar or pwVar or pVar or evVar or frVar or toVar or awVar or sqlVar): return

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
                showwarning('Error', 'SGF Error')
                
        self.gameinfoSearch(query)
        self.progBar.stop()
        self.logger.insert(END, 'Game info search, query "%s", %1.1f seconds\n' % (query, time.time() - currentTime))
        self.notebookTabChanged()
        self.configButtons(NORMAL)



    def sigSearch(self):
        """ Search a game by its Dyer signature (sgf coord. of moves 20, 40, 60, 31, 51, 71)."""

        if not self.gamelist.noOfGames(): self.reset()

        window = Toplevel(takefocus=0)
        window.title('Signature Search')

        m20 = StringVar()
        m40 = StringVar()
        m60 = StringVar()
        m31 = StringVar()
        m51 = StringVar()
        m71 = StringVar()
        
        l1 = Label(window, text='Move 20')
        e1 = Entry(window, width=4, textvariable=m20)
        l2 = Label(window, text='Move 40')
        e2 = Entry(window, width=4, textvariable=m40)
        l3 = Label(window, text='Move 60')
        e3 = Entry(window, width=4, textvariable=m60)
        l4 = Label(window, text='Move 31')
        e4 = Entry(window, width=4, textvariable=m31)
        l5 = Label(window, text='Move 51')
        e5 = Entry(window, width=4, textvariable=m51)
        l6 = Label(window, text='Move 71')
        e6 = Entry(window, width=4, textvariable=m71)

        for i, (label, entry ) in enumerate([ (l1, e1), (l2, e2), (l3, e3) ]):
            label.grid(row=1, column=2*i)
            entry.grid(row=1, column=2*i+1)

        for i, (label, entry ) in enumerate([ (l4, e4), (l5, e5), (l6, e6) ]):
            label.grid(row=2, column=2*i)
            entry.grid(row=2, column=2*i+1)

        e1.focus()
        
        bs = Button(window, text='Search', command = lambda self=self, window=window, m20=m20, m40=m40, m60=m60, m31=m31, m51=m51, m71=m71: self.doSigSearch(window, m20, m40, m60, m31, m51, m71))
        bq = Button(window, text='Cancel', command = window.destroy)

        window.protocol('WM_DELETE_WINDOW', window.destroy)

        bo = v.Board(window, 19, (5, 18), 0, None, 0, None, self.boardImg, None, None)
        bo.state('normal', lambda pos, self=self, window=window, 
                 e1=e1, e2=e2, e3=e3, e4=e4, e5=e5, e6=e6, m20=m20, m40=m40, m60=m60, m31=m31,
                 m51=m51, m71=m71: self.sigSearchGetCoord(pos, window, e1, e2, e3, e4, e5, e6, m20, m40, m60, m31, m51, m71))
        bo.shadedStoneVar.set(1)
        bo.grid(row=0, column=0, columnspan=6)
        bq.grid(row=3, column=4, columnspan = 2)
        bs.grid(row=3, column=2, columnspan = 2)
        
        window.update_idletasks()  
        # window.focus()
        window.grab_set()
        window.wait_window()


    def sigSearchGetCoord(self, pos, window, e1, e2, e3, e4, e5, e6, m20, m40, m60, m31, m51, m71):
        """ This writes the coordinates of a clicked-at point on the board to
        the currently focused entry. """

        f = window.focus_get()
        m = None
        
        for f_old, f_new, m_new in [ (e1, e2, m20), (e2, e3, m40), (e3, e4, m60), (e4, e5, m31), (e5, e6, m51), (e6, e1, m71) ]:
            if f is f_old:
                f_new.focus()
                m = m_new
                break

        p = chr(pos[0]+ord('a')) + chr(pos[1]+ord('a'))
        if m: m.set(p)


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
            try: self.displayLabels(self.cursor.currentNode())
            except: pass

        self.signatureSearch(sig)
        self.progBar.stop()
        self.logger.insert(END, 'Signature search, %1.1f seconds, searching for\n%s\n' % (time.time() - currentTime, sig))
        self.notebookTabChanged()
        self.configButtons(NORMAL)



    def back(self, prev=None, selected=None):
        """ Go back to previous search (restore board, game list etc.)
        If an SGF file is currently loaded (and was loaded at the time of
        the previous search too), the position of its cursor is
        restored too."""

        self.leaveNode()

        if not prev:
            prev, selected = self.prevSearches.pop()
            if prev is None:
                self.reset()
                return

        self.comments.delete('1.0', END)
        self.gamelist.clearGameInfo()
        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0

        cu = prev['cursorSn']
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
                    try: self.cursor.game(self.cursor.currentGame)
                    except:
                        showwarning('Error', 'SGF Error')
                        return
                self.board.newPosition()
                self.moveno.set('0')
                self.capB, self.capW = 0, 0 
                self.displayNode(self.cursor.getRootNode(self.cursor.currentGame))
                for i in cu[2]:
                    self.next(i,0)
                self.cursor.seeCurrent()
                
                self.board.restore(prev['boardData'], fromSGF=True)
                self.sel = self.board.selection      # used in self.showCont()                    
                self.capVar.set('Cap - B: ' + str(self.capB) + ', W: ' + str(self.capW))
            else:
                showwarning('Error', 'SGF File not found')

        # restore variables
        mv, fc, fa, ml, nextM = prev['variables']
        self.modeVar.set(mv)
        self.fixedColorVar.set(fc)
        self.fixedAnchorVar.set(fa)
        self.moveLimit.set(ml)
        self.nextMoveVar.set(nextM)

        for i, sid in prev['snapshot_ids']:
            self.gamelist.DBlist[i]['data'].restore(sid)

        # restore currentSearchPattern
        i, sid = prev['snapshot_ids'][0]
        self.currentSearchPattern = self.gamelist.DBlist[i]['data'].mrs_pattern

        self.continuations = []
        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0 

        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            gl = db['data']
            self.lookUpContinuations(gl)

        self.setLabels()
        if self.showContinuation.get(): self.showCont()
        self.board.changed.set(0)
        self.displayStatistics()
        self.gamelist.update()        
        self.prevSearches.select(selected)
        self.notebookTabChanged()


    def completeReset(self):
        self.reset()
        self.board.newPosition()
        self.changeCurrentFile(None, 0)
        for i in range(len(self.filelist)):
            self.delFile()
        
        self.gotoVar.set('')

        self.clearGI()
        self.history_GIsearch = []
        self.history_GIS_index = -1

        self.moveLimit.set(250)
        if not self.options.smartFixedColor.get(): self.fixedColorVar.set(0)
        self.fixedAnchorVar.set(0)
        self.nextMoveVar.set(0)
        
        self.showContinuation.set(0)
        self.oneClick.set(0)
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
            except: pass
        self.notebookTabChanged()


        

    def showCont(self):
        """ Toggle 'show continuations'. """
        
        if not self.currentSearchPattern: return
        if self.showContinuation.get():
            self.board.delLabels() # FIXME is this what we want to do?

            for c in self.continuations:
                if not c[3]: color = 'white'
                elif not c[7]: color = 'black'
                else: color = self.options.labelColor.get()
                self.board.placeLabel((c[1]+self.sel[0][0], c[2]+self.sel[0][1]), '+LB', c[-1], color)

        else:
            self.board.delLabels()
            if self.cursor:
                try: self.displayLabels(self.cursor.currentNode())
                except: pass

    def doubleClick(self, event):
        if not self.oneClick.get(): self.search()


    # ---- putting stones on the board, and navigation in SGF file ----------------------

    def nextMove(self, pos):
        self.board.delLabels()
        self.board.delMarks()
        
        if self.board.wildcards.has_key(pos):
            self.board.delete(self.board.wildcards[pos])
            del self.board.wildcards[pos]
            
        v.Viewer.nextMove(self, pos)

        if self.oneClick.get() and (self.board.selection[1] == (0,0) or \
                                    (self.board.selection[0][0] <= pos[0] <= self.board.selection[1][0] and self.board.selection[0][1] <= pos[1] <= self.board.selection[1][1])):
            self.search()

                   
    def next(self, n=0, markCurrent=True):
        if not self.cursor or self.cursor.atEnd: return
        self.board.delLabels()
        self.board.delWildcards()
        
        if v.Viewer.next(self, n, markCurrent): return 1
        return 0

    
    def prev(self, markCurrent=1):
        if not self.cursor or self.cursor.atStart: return
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
        if not x*y: return

        if self.board.wildcards.has_key((x,y)):
            self.board.delete(self.board.wildcards[(x,y)])
            del self.board.wildcards[(x,y)]
        else: Viewer.delStone(self, event)


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
        dialog.title('Export position')
        dialog.protocol('WM_DELETE_WINDOW', lambda: None)

        f1 = Frame(dialog)
        f2 = Frame(dialog)
        f3 = Frame(dialog)

        for f in [f1, f2, f3]: f.pack(side=TOP, fill=BOTH, expand=YES, pady=5)
        
        Label(f1, text='Number of moves to be shown (0-9):').pack(side=TOP)
        Entry(f1, textvariable=numberOfMoves).pack(side=TOP)

        Label(f2, text='Export mode:').pack(side=LEFT)
        Radiobutton(f2, text='ASCII', variable=exportMode, value='ascii', highlightthickness=0).pack(side=LEFT)
        Radiobutton(f2, text='Wiki', variable=exportMode, value='wiki', highlightthickness=0).pack(side=LEFT)

        Button(f3, text='OK', command=dialog.destroy).pack(anchor=E)

        dialog.update_idletasks()  
        dialog.focus()
        dialog.grab_set()
        dialog.wait_window()
        
        n = numberOfMoves.get()

        l = []
        t = []

        for i in range(19): l.append(['. ']*19) # TODO boardsize

        for i in range(19):
            for j in range(19):
                if self.board.getStatus(j,i) == 'B':    l[i][j] = 'X '
                elif self.board.getStatus(j,i) == 'W':  l[i][j] = 'O '
                if self.board.wildcards.has_key((j,i)): l[i][j] = '* '

        # mark hoshis with ,'s

        for i in range(3): # TODO boardsize
            for j in range(3):
                ii = 3 + 6*i 
                jj = 3 + 6*j 
                if l[ii][jj] == '. ': l[ii][jj] = ', '

        remarks = []
        nextMove = 'B'

        node = self.cursor.currentNode()
        
        for i in range(1, min(n, 10)+1):
            if i == 10: ii = '0 '
            else: ii = `i` + ' '

            node = Node(node.next)
            if not node: break
            if 'B' in node: color = 'B'
            elif 'W' in node: color = 'W'
            else: continue

            if i == 1: nextMove = color

            pos = self.convCoord(node[color][0])
            if not pos: continue
        
            if l[pos[1]][pos[0]] in ['. ', ', ']: l[pos[1]][pos[0]] = ii
            elif l[pos[1]][pos[0]] in [`i`+' ' for i in range(10)]:
                remarks.append(ii + 'at ' + l[pos[1]][pos[0]] + '\n')
            elif l[pos[1]][pos[0]] in ['X ', 'O ']:
                remarks.append(ii + 'at ' + 'ABCDEFGHJKLMNOPQRST'[pos[0]] + `18-pos[1]+1` + '\n') # TODO boardsize

        if exportMode.get() == 'ascii':
            for i in range(19):
                l[i].insert(0, '%2d  ' % (19-i))

            l.insert(0, '')
            l.insert(0, '    A B C D E F G H J K L M N O P Q R S T')

            if n:
                if nextMove == 'B': remarks.append('Black = 1\n')
                elif nextMove == 'W': remarks.append('White = 1\n')
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

        ESR_TextEditor(self, exportMode.get(), join(t, ''), self.sgfpath, (self.options.exportFont, self.options.exportFontSize, self.options.exportFontStyle))



    def exportText(self):
        """Export some information on the previous search in a small text editor,
        where it can be edited and saved to a file. """

        exportMode = StringVar()

        dialog = Toplevel()
        dialog.title('Export position')
        dialog.protocol('WM_DELETE_WINDOW', lambda: None)

        f1 = Frame(dialog)
        f2 = Frame(dialog)
        f3 = Frame(dialog)

        for f in [f1, f2, f3]: f.pack(side=TOP, fill=BOTH, expand=YES, pady=5)
        
        Label(f1, text='Export mode:').pack(side=LEFT)
        Radiobutton(f1, text='ASCII', variable=exportMode, value='ascii', highlightthickness=0).pack(side=LEFT)
        Radiobutton(f1, text='Wiki', variable=exportMode, value='wiki', highlightthickness=0).pack(side=LEFT)

        showAllCont = IntVar()
        Checkbutton(f2, text='Show all continuations', variable=showAllCont, highlightthickness=0).pack(side=LEFT)

        Button(f3, text='OK', command=dialog.destroy).pack(anchor=E)

        dialog.update_idletasks()  
        dialog.focus()
        dialog.grab_set()
        dialog.wait_window()

        t = self.patternSearchDetails(exportMode.get(), showAllCont.get())
        
        ESR_TextEditor(self, exportMode.get(), join(t, ''), self.sgfpath, (self.options.exportFont, self.options.exportFontSize, self.options.exportFontStyle))

    def printPattern(self, event=None):
        if self.currentSearchPattern:
            self.logger.insert(END, self.currentSearchPattern.printPattern() + '\n')


    # ----------------------------------------------------------------------------------

    def openViewer_external(self, filename, gameNumber, moveno):
        if self.options.altViewerVar1.get():
            # if moveno refers to a hit in a variation, it is a tuple with several entries
            # an external viewer can (probably) not understand this
            if len(moveno) != 1: moveno = 0
            else: moveno = moveno[0]

            if sys.platform[:3] == 'win': filenameQU = '"' + filename + '"'
            else: filenameQU = filename

            s1 = self.options.altViewerVar1.get()
            if os.name == 'posix':
                s1 = s1.replace('~', os.getenv('HOME'))

            s2 = replace(self.options.altViewerVar2.get(), '%f', filenameQU)
            s2 = replace(s2, '%F', filename)
            s2 = replace(s2, '%n', str(moveno))
            s2 = replace(s2, '%g', str(gameNumber))

            try:

                if sys.platform[:3] == 'win':
                    os.spawnv(os.P_DETACH, s1, ('"'+s1+'"',)+tuple(split(s2)))
                        # it is necessary to quote the
                        # path if it contains blanks

                elif os.path.isfile(s1):
                    pid = os.fork()
                    if pid == 0:
                        os.execv(s1, (s1,)+tuple(split(s2)))
                        showwarning('Error', 'Error starting SGF viewer')
                else: showwarning('Error', s1 + ' not found.')
            except OSError:
                showwarning('Error', 'Error starting SGF viewer')

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
        else: # open internal viewer
            self.openViewer_internal(filename, gameNumber, moveno)

                    
    def altViewer(self):
        """ Ask for alternative SGF viewer. """
        
        window = Toplevel()
        window.title('Alternative SGF viewer')

        f = Frame(window)
        f.pack()
        
        l1 = Label(f, text='Enter the command to launch the SGF viewer')
        e1 = Entry(f, width=40, textvariable=self.options.altViewerVar1)
        l2 = Label(f, text='Enter the command line options, with %f for the filename')
        e2 = Entry(f, width=40, textvariable=self.options.altViewerVar2)

        b = Button(f, text='OK', command = window.destroy) 

        window.protocol('WM_DELETE_WINDOW', lambda: None)
        
        l1.pack(side=TOP, anchor=W)
        e1.pack(side=TOP)
        l2.pack(side=TOP, anchor=W)
        e2.pack(side=TOP)
        b.pack(side=RIGHT)

        window.update_idletasks()  
        window.focus()
        window.grab_set()
        window.wait_window()

    # ---- administration of DBlist ----------------------------------------------------


    def addDB(self):
        self.editDB_OK.config(state=DISABLED)
        self.saveProcMess.config(state=DISABLED)

        dbp = str(askdirectory(initialdir = self.datapath))
            
        if not dbp:
            self.editDB_OK.config(state=NORMAL)
            self.saveProcMess.config(state=NORMAL)
            return
        else:
            dbp = os.path.normpath(dbp)
            
        self.datapath = os.path.split(dbp)[0]

        if self.options.storeDatabasesSeparately.get() and self.options.whereToStoreDatabases.get():
            datap = (self.options.whereToStoreDatabases.get(), '')
            if os.path.exists(datap[0]) and not os.path.isdir(datap[0]):
                showwarning('Error', datap[0] + ' is not a directory.')
                self.editDB_OK.config(state=NORMAL)
                self.saveProcMess.config(state=NORMAL)
                return
            elif not os.path.exists(datap[0]):
                if askokcancel('Error', 'Directory ' + datap[0] + ' does not exist. Create it?'):
                    try:
                        os.makedirs(datap[0])
                    except:
                        showwarning('Error', datap[0] + ' could not be created.')
                        self.editDB_OK.config(state=NORMAL)
                        self.saveProcMess.config(state=NORMAL)
                        return
                else:
                    self.editDB_OK.config(state=NORMAL)
                    self.saveProcMess.config(state=NORMAL)
                    return          
        else: datap = ('', '#') # this means: same as dbpath

        self.callAddDB(dbp, datap)

        self.editDB_OK.config(state=NORMAL)
        self.saveProcMess.config(state=NORMAL)


    def callAddDB(self, dbp, datap, index=None):
        tagAsPro = { 'Never': 0, 'All games' : 1, 'All games with p-rank players' : 2, }[self.options.tagAsPro.get()]
        algos = 0
        if self.options.algo_hash_full.get(): algos |= lk.ALGO_HASH_FULL
        if self.options.algo_hash_corner.get(): algos |= lk.ALGO_HASH_CORNER
        KEngine.addDB(self, dbp, datap, recursive=self.options.recProcess.get(), filenames=self.filenamesVar.get(),
                      acceptDupl=self.options.acceptDupl.get(), strictDuplCheck=self.options.strictDuplCheck.get(),
                      tagAsPro = tagAsPro, processVariations=self.options.processVariations.get(), algos=algos,
                      messages=self.processMessages, progBar=self.progBar, showwarning=showwarning, index=index)



    def addOneDB(self, arguments, dbpath, dummy):        # dummys needed for os.path.walk
        if KEngine.addOneDB(self, arguments, dbpath, dummy):
            index = arguments[-1] if not arguments[-1] is None else END
            db = self.gamelist.DBlist[int(index) if index != END else -1]
            db_date = getDateOfFile(os.path.join(db['name'][0], db['name'][1]+'.da'))
            self.db_list.insert(index, dbpath + ' (%s, %d games)' % (db_date, db['data'].size()) )
            self.db_list.list.see(index)
            self.prevSearches.clear()

     
    def removeDB(self):
        while self.db_list.list.curselection():
            index = self.db_list.list.curselection()[0]
            self.db_list.delete(index)
            i = int(index)
            datap = self.gamelist.DBlist[i]['name']
            dbpath = self.gamelist.DBlist[i]['sgfpath']
            del self.gamelist.DBlist[i]['data'] # make sure memory is freed and db connection closed
                                                # (otherwise, on Windows, we might not be able to delete the db file)
            del self.gamelist.DBlist[i]

            try:
                os.remove(os.path.join(datap[0], datap[1]+'.db'))
                os.remove(os.path.join(datap[0], datap[1]+'.da'))
            except:
                showwarning('I/O Error', 'Could not delete the database files.')
            try: # these files will only be present if hashing algos were used, so do not issue a warning when they are not found
                os.remove(os.path.join(datap[0], datap[1]+'.db1'))
                os.remove(os.path.join(datap[0], datap[1]+'.db2'))
            except:
                pass
            self.processMessages.insert(END, 'Removed ' + dbpath + '.\n')
            
        self.gamelist.reset()
        self.prevSearches.clear()
        self.currentSearchPattern = None
                                 

    def reprocessDB(self):
        
        # export all tags
        from tempfile import NamedTemporaryFile
        f = NamedTemporaryFile(delete=False)
        tagfilename = f.name
        f.close()
        self.gamelist.exportTags(tagfilename,  [ int(x) for x in self.gamelist.customTags.keys() if not int(x) == lk.HANDI_TAG ])

        # delete and add all selected databases
        for index in self.db_list.list.curselection():
            i = int(index)
        
            self.editDB_OK.config(state=DISABLED)
            self.saveProcMess.config(state=DISABLED)
            self.prevSearches.clear()
            self.currentSearchPattern = None
        
            dbpath = self.gamelist.DBlist[i]['sgfpath']
            datap = self.gamelist.DBlist[i]['name']
            del self.gamelist.DBlist[i]['data'] # make sure memory is freed and db connection closed
                                                # (otherwise, on Windows, we might not be able to delete the db file)
            del self.gamelist.DBlist[i]

            try:
                os.remove(os.path.join(datap[0], datap[1]+'.db'))
                os.remove(os.path.join(datap[0], datap[1]+'.da'))
            except:
                showwarning('I/O Error', 'Could not delete the database files %s %s .' % datap)
            try: # these files will only be present if hashing algos were used, so do not issue a warning when they are not found
                os.remove(os.path.join(datap[0], datap[1]+'.db1'))
                os.remove(os.path.join(datap[0], datap[1]+'.db2'))
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

            db_date = getDateOfFile(os.path.join(db['name'][0], db['name'][1]+'.da'))

            if db['disabled']:
                db['disabled'] = 0
                db['data'] = lkGameList(os.path.join(db['name'][0], db['name'][1]+'.db'))                
                self.db_list.delete(i)
                self.db_list.insert(i, db['sgfpath'] + ' (%s, %d games)' % (db_date, db['data'].size()) )
                self.db_list.list.select_set(i)
                self.db_list.list.see(i)
            else:
                db['disabled'] = 1
                db_size = db['data'].size()
                db['data'] = None
                self.db_list.delete(i)
                self.db_list.insert(i, 'DISABLED - ' + db['sgfpath'] + ' (%s, %d games)' % (db_date, db_size) )
                self.db_list.list.select_set(i)
                self.db_list.list.see(i)
        self.gamelist.reset()
        self.prevSearches.clear()
        self.currentSearchPattern = None
        

    def saveMessagesEditDBlist(self):
        filename = tkFileDialog.asksaveasfilename(initialdir = os.curdir)
        try:
            file = open(filename, 'w')
            file.write(self.processMessages.get('1.0', END))
            file.close()
        except IOError:
            showwarning('Error', 'Could not write to ' + filename)


    def DBlistClick(self, event):
        self.db_list.clickedLast = self.db_list.list.nearest(event.y)
        self.db_list.dragLast = -1


    def DBlistDrag(self, event):
        i = self.db_list.list.nearest(event.y)
        if self.db_list.dragLast == -1:
            if self.db_list.clickedLast == i: return
            else: self.db_list.dragLast = self.db_list.clickedLast        
        if self.db_list.dragLast != i:
            s = self.db_list.list.get(self.db_list.dragLast)
            self.db_list.delete(self.db_list.dragLast)
            self.db_list.insert(i, s)
            self.db_list.list.select_set(i)
            self.db_list.dragLast = i 
        return 'break'


    def DBlistRelease(self, event):
        if self.db_list.dragLast == -1: return
        
        i = self.db_list.list.nearest(event.y)

        if self.db_list.dragLast != i:
            s = self.db_list.list.get(self.db_list.dragLast)
            self.db_list.delete(self.db_list.dragLast)
            self.db_list.insert(i, s)
            self.db_list.list.select_set(i)
            self.db_list.dragLast = i

        if self.db_list.clickedLast != i:
            db = self.gamelist.DBlist[self.db_list.clickedLast]
            del self.gamelist.DBlist[self.db_list.clickedLast]
            self.gamelist.DBlist.insert(i, db)
            self.gamelist.reset()
            self.prevSearches.clear()
            self.currentSearchPattern = None


    def browseDatabases(self):
        initdir = self.options.whereToStoreDatabases.get() or os.curdir
        filename = askdirectory(initialdir = initdir)
        if filename: filename = str(filename)
        self.options.whereToStoreDatabases.set(filename)
        

    def toggleWhereDatabases(self):
        if self.options.storeDatabasesSeparately.get():
            self.whereDatabasesEntry.config(state=NORMAL)
            if not self.options.whereToStoreDatabases.get(): self.browseDatabases()
        else:
            self.whereDatabasesEntry.config(state=DISABLED)


    def finalizeEditDB(self):
        self.dateProfileWholeDB = self.dateProfile()
        self.editDB_window.destroy()
        self.notebookTabChanged()


        
    def editDBlist(self):
        self.gamelist.clearGameInfo()

        window = Toplevel()
        self.editDB_window = window
        window.transient(self.master)

        window.title('Edit database list')

        f1 = Frame(window)
        f1.grid(row=0, sticky=NSEW)
        f2 = Frame(window)
        f2.grid(row=1, sticky=NSEW)
        for i in range(4): f2.columnconfigure(i, weight=1)

        f2a = Frame(window)
        f2a.grid(row=2, sticky=NSEW)
        f3 = Frame(window)
        f3.grid(row=3, sticky=NSEW)
        f3.columnconfigure(0, weight=1)
        f4 = Frame(window)
        f4.grid(row=4, sticky=NSEW)

        window.rowconfigure(0, weight=1)
        window.rowconfigure(4, weight=2)
        window.columnconfigure(0, weight=1)
                
        self.db_list = v.ScrolledList(f1)
        self.db_list.list.config(width=60, selectmode = EXTENDED)
        self.db_list.pack(side=LEFT, expand=YES, fill=BOTH)

        self.db_list.list.bind('<1>', self.DBlistClick)
        self.db_list.list.bind('<B1-Motion>', self.DBlistDrag)
        self.db_list.list.bind('<ButtonRelease-1>', self.DBlistRelease)

        for db in self.gamelist.DBlist:
            db_date = getDateOfFile(os.path.join(db['name'][0], db['name'][1]+'.da'))

            if db['disabled']:
                self.db_list.insert(END, 'DISABLED - ' + db['sgfpath'] + ' (' + db_date  + ')' )
            else:
                self.db_list.insert(END, db['sgfpath'] + ' (%s, %d games)' % (db_date, db['data'].size_all()) )

        for i, (text, command, ) in enumerate([('Add DB', self.addDB), ('Toggle normal/disabled', self.toggleDisabled),
                                               ('Remove DB', self.removeDB), ('Reprocess DB', self.reprocessDB)]):
            Button(f2, text=text, command=command).grid(row=0, column=i, sticky=NSEW)
            
        Label(f3, text='Processing options', justify=LEFT, font=('Helvetica', 10, 'bold')).grid(row=0, column=0, sticky=W)


        self.filenamesVar = StringVar()
        filenamesLabel = Label(f3, anchor='w', text='Files:', pady=10)
        filenamesLabel.grid(row=1, column=0, sticky=E)
        filenamesMenu = Combobox(f3, textvariable = self.filenamesVar, values = ['*.sgf', '*.sgf, *.mgt', 'All files'], state='readonly')
        filenamesMenu.set('*.sgf')
        filenamesMenu.grid(row=1, column=1, sticky=W)

        # self.encodingVar = StringVar()
        # 
        # enclist = ['utf-8', 'latin1', 'iso8859_2', 'iso8859_3', 'koi8_r', 'gb2312', 'gbk', 'gb18030', 'hz', 'big5', 'cp950', 'cp932',
        #            'shift-jis', 'shift-jisx0213', 'euc-jp', 'euc-jisx0213', 'iso-2022-jp', 'iso-2022-jp-1',
        #            'iso-2022-jp-2', 'iso-2022-jp-3', 'iso-2022-jp-ext', 'cp949', 'euc-kr', 'johab', 'iso-2022-kr',
        #           ]
        # encLabel = Label(f3, anchor='w', text='Encoding:', pady=10)
        # encLabel.grid(row=1, column=3, sticky=E)
        # encodingMenu = Combobox(f3, textvariable = self.encodingVar, values = enclist, state='readonly')
        # encodingMenu.set('utf-8')
        # encodingMenu.grid(row=1, column=4, sticky=W)
        # 
        # self.encoding1Var = StringVar()
        # encoding1Menu = Combobox(f3, textvariable = self.encoding1Var, values = ['Do not change SGF', 'Add CA tag', 'Transcode SGF to utf-8'], state='readonly')
        # encoding1Menu.set('Add CA tag')
        # encoding1Menu.grid(row=1, column=5, sticky=W)

        recursionButton = Checkbutton(f3, text = "Recursively add subdirectories", highlightthickness=0, variable = self.options.recProcess, pady=5)
        recursionButton.grid(row=2, column=0, columnspan=2, sticky=W)

        duplButton = Checkbutton(f3, text="Accept duplicates", highlightthickness=0, variable = self.options.acceptDupl, pady=5)
        duplButton.grid(row=3, column=0, sticky=W, columnspan=2)

        strictDuplCheckButton = Checkbutton(f3, text="Strict duplicate check", highlightthickness=0, variable = self.options.strictDuplCheck, pady=5)
        strictDuplCheckButton.grid(row=3, column=2, sticky=W, columnspan=2)

        processVariations = Checkbutton(f3, text="Process variations", highlightthickness=0, variable = self.options.processVariations, pady=5)
        processVariations.grid(row=5, column=0, sticky=W, columnspan=2)
       
        profTagLabel = Label(f3, anchor='e', text='Tag as professional:', font=('Helvetica', 10), pady=8)
        profTagLabel.grid(row=6, column=0, sticky=W, )
        profTag = Combobox(f3, justify='left', textvariable = self.options.tagAsPro,
                               values = ['Never', 'All games', 'All games with p-rank players',  ], state='readonly')
        profTag.grid(row=6, column=1, columnspan=2, sticky=W)

        sep = Separator(f3, orient='horizontal')
        sep.grid(row=7, column=0, columnspan=7, sticky=NSEW)
        whereDatabasesButton = Checkbutton(f3, text = 'Store databases separately from SGF files', highlightthickness=0,
                                           command = self.toggleWhereDatabases, variable = self.options.storeDatabasesSeparately, padx=8)
        whereDatabasesButton.grid(row=8, column=0, columnspan=3, sticky=W)

        self.whereDatabasesEntry = Entry(f3, textvariable = self.options.whereToStoreDatabases, )
        self.whereDatabasesEntry.grid(row=8, column=2, columnspan=3, sticky=NSEW)
        if not self.options.storeDatabasesSeparately.get(): self.whereDatabasesEntry.config(state=DISABLED)

        browseButton = Button(f3, text='Browse', command = self.browseDatabases)
        browseButton.grid(row=8, column=5)
        f3.grid_columnconfigure(0, weight=1)
        f3.grid_columnconfigure(1, weight=2)
        f3.grid_columnconfigure(2, weight=2)
        f3.grid_columnconfigure(3, weight=2)

        sep1 = Separator(f3, orient='horizontal')
        sep1.grid(row=9, column=0, columnspan=7, sticky=NSEW)

        self.algo_hash_full = Checkbutton(f3, text = 'Use hashing for full board positions', highlightthickness = 0, variable = self.options.algo_hash_full, pady=5)
        self.algo_hash_full.grid(row=10, column = 0, columnspan=2)

        self.algo_hash_corner = Checkbutton(f3, text = 'Use hashing for corner positions', highlightthickness = 0, variable = self.options.algo_hash_corner, pady=5)
        self.algo_hash_corner.grid(row=10, column = 3, columnspan=2)

        self.processMessages = Message(f4)
        self.processMessages.pack(side=TOP, expand=YES, fill=BOTH)

        self.editDB_OK = Button(f2a, text='OK', command = self.finalizeEditDB)
        self.editDB_OK.pack(side=RIGHT)

        self.saveProcMess = Button(f4, text='Save messages', command = self.saveMessagesEditDBlist)
        self.saveProcMess.pack(side=RIGHT)

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
            dir = askdirectory(initialdir=self.datapath)
            if not dir: return
            dir = str(dir)

        if not os.path.exists(dir) and askokcancel('Error', 'Directory ' + dir + ' does not exist. Create it?'):
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
                if not askokcancel('Confirm deletion', 'There are unsaved changes. Discard them?'): return
                else: break
        
        try:
            defaultfile = open(os.path.join(self.basepath,'default.cfg'))
            c = ConfigObj(infile=defaultfile)
            defaultfile.close()
            if os.path.exists(os.path.join(self.optionspath,'kombilo.cfg')):
                configfile = open(os.path.join(self.optionspath,'kombilo.cfg'))
                c.merge(ConfigObj(infile=configfile))
                configfile.close()

            c['main']['sgfpath']  = self.sgfpath
            c['main']['datapath'] = self.datapath
            self.saveOptions(c['options'])
            c['databases'] = {}
            for counter, db in enumerate(self.gamelist.DBlist):
                c['databases']['d%d%s' % (counter, 'disabled' if db['disabled'] else '')] = [ db['sgfpath'], db['name'][0], db['name'][1] ]
            c['tags'] = self.gamelist.customTags
            c['taglook'] = self.gamelist.taglook
            c.filename = os.path.join(self.optionspath,'kombilo.cfg')
            c.write()
        except:
            showwarning('IOError', 'Could not write kombilo.cfg')

        self.master.quit()
        

    def configButtons(self, state):
        """ Disable buttons and board during search, reset them afterwards. """

        for b in [self.resetButtonS, self.backButtonS, self.searchButtonS, self.nextMove1S, self.nextMove2S, self.nextMove3S]:
            b.config(state=state)
        
        if state==NORMAL: self.board.state('normal', self.nextMove)
        elif state == DISABLED: self.board.state('disabled')


    def helpAbout(self):
        """ Display the 'About ...' window with the logo and some basic information. """

        t = []
        
        t.append('Kombilo %s - written by Ulrich Goertz (ug@geometry.de)\n\n' % KOMBILO_RELEASE)
        t.append('Kombilo is a go database program.\n')
        t.append('You can find more information on Kombilo and the newest ')
        t.append('version at http://www.u-go.net/kombilo/\n\n')
        
        t.append('Kombilo is free software; for more information ')
        t.append('see the documentation.\n\n')
        
        window = Toplevel()
        window.title('About Kombilo ...')

        if self.logo:
            canv = Canvas(window, width=75,height=23)
            canv.pack()
            canv.create_image(0,0,image=self.logo, anchor=NW)

        text = Text(window, height=15, width=60, relief=FLAT, wrap=WORD)
        text.insert(1.0, join(t, ''))
 
        text.config(state=DISABLED)
        text.pack()

        b = Button(window, text="OK", command = window.destroy)
        b.pack(side=RIGHT)
        
        window.update_idletasks()
        
        window.focus()
        window.grab_set()
        window.wait_window()


    def helpLicense(self):
        """ Display the GNU General Public License. """
        try:
            file = open(os.path.join(self.basepath, 'license.rst'))
            t = file.read()
            file.close()
        except:
            t = 'Kombilo was written by Ulrich Goertz (ug@geometry.de).\n' 
            t = t + 'It is open source software, published under the MIT License.'
            t = t + 'See the documentation for more information. ' 
            t = t + 'This program is distributed WITHOUT ANY WARRANTY!\n\n'
        self.textWindow(t,'Kombilo license')




    def showFilenameInGamelist(self):
        self.gamelist.showFilename = self.options.showFilename.get()
        self.reset()

        
    def showDateInGamelist(self):
        self.gamelist.showDate = self.options.showDate.get()
        self.reset()


    def gotoChange(self, event):
        if event.char == '': return
        if ord(event.char[0]) < 32: return

        t = self.gotoVar.get() + event.char

        i = self.gamelist.listbox.curselection()
        start = self.gamelist.get_index(0) if not i else self.gamelist.get_index(int(i[0]))
        
        criterion = self.options.sortCriterion.get()
        increment = (2*self.options.sortReverse.get() - 1) if self.gamelist.sortCrit(start, criterion)[:len(t)] > t else (-2*self.options.sortReverse.get() + 1)  # (= -1 or 1)

        if increment == 1:
            if self.options.sortReverse.get():
                while start < len(self.gamelist.gameIndex)-1 and self.gamelist.sortCrit(start, criterion)[:len(t)] > t: start += 1
            else:
                while start < len(self.gamelist.gameIndex)-1 and self.gamelist.sortCrit(start, criterion) < t: start += 1
        else:
            if self.options.sortReverse.get():
                while start > 0 and self.gamelist.sortCrit(start, criterion) < t: start -= 1
            else:
                while start > 0 and self.gamelist.sortCrit(start, criterion)[:len(t)] > t: start -= 1
        
        if i: self.gamelist.listbox.select_clear(i)
        self.gamelist.listbox.virt_select_set_see(start)
        self.gamelist.printGameInfo(None, start)


    def rebindMouseButtons(self):
        self.board.rebindMouseButtons(self.options.onlyOneMouseButton.get())



    def initMenusK(self):
        """ Initialize the menus, and a few options variables. """

        # --------- FILE ---------------------------------
        self.filemenu.insert_separator(6)
        self.filemenu.insert_command(7, label='Complete reset', command = self.completeReset)


        # --------- DATABASE ---------------------------------

        self.dbmenu = Menu(self.mainMenu)
        self.mainMenu.insert_cascade(3, label='Database', underline=0, menu=self.dbmenu)
        self.dbmenu.add_command(label='Edit DB list', underline = 0, command=self.editDBlist)
        self.dbmenu.add_command(label='Export search results', command=self.exportText)
        self.dbmenu.add_command(label='Export current position', command=self.exportCurrentPos)
        self.dbmenu.add_command(label='Export tags to file', command=self.exportTags)
        self.dbmenu.add_command(label='Import tags from file', command=self.importTags)
        self.dbmenu.add_command(label='Copy current SGF files to folder', command=self.copyCurrentGamesToFolder)

        self.dbmenu.add_command(label='Signature search', command=self.sigSearch)


        self.optionsmenu.add_checkbutton(label='Jump to match', underline = 0, variable = self.options.jumpToMatchVar)
        self.optionsmenu.add_checkbutton(label='Smart FixedColor', underline = 1, variable = self.options.smartFixedColor)

        # ------ game list submenu ------------

        gamelistMenu = Menu(self.optionsmenu)
        self.optionsmenu.add_cascade(label='Game list', underline = 0, menu = gamelistMenu)

        for text, value in [ ('Sort by white player', GL_PW, ), ('Sort by black player', GL_PB, ), ('Sort by filename', GL_FILENAME, ), ('Sort by date', GL_DATE, ) ]:
            gamelistMenu.add_radiobutton(label=text, variable = self.options.sortCriterion, value = value, command=self.gamelist.update)
        gamelistMenu.add_checkbutton(label='Reverse order', variable=self.options.sortReverse, command=self.gamelist.update)

        gamelistMenu.add_separator()

        gamelistMenu.add_checkbutton(label='Show filename', variable = self.options.showFilename, command = self.showFilenameInGamelist)
        gamelistMenu.add_checkbutton(label='Show date', variable = self.options.showDate, command = self.showDateInGamelist)

        # -------------------------------------

        # self.options.invertSelection = self.board.invertSelection
        # self.optionsmenu.add_checkbutton(label='Invert selection', variable = self.options.invertSelection)
        advOptMenu = Menu(self.optionsmenu)
        self.optionsmenu.add_cascade(label='Advanced', underline=0, menu=advOptMenu)
        advOptMenu.add_checkbutton(label='Open games in external viewer', variable = self.options.externalViewer)
        advOptMenu.add_command(label='Alternative SGF viewer', underline=0, command=self.altViewer)


    def balloonHelpK(self):

        for widget, text in [ (self.resetButtonS, 'Reset game list'), (self.backButtonS, 'Back to previous search pattern'), (self.showContButtonS, 'Show continuations'),
                              (self.oneClickButtonS, '1-click mode'), (self.colorButtonS, "(Don't) allow color swap in search pattern"),
                              (self.anchorButtonS, "(Don't) translate search pattern"), (self.nextMove1S, 'Black or white plays next (or no continuation)'),
                              (self.nextMove2S, 'Black plays next'), (self.nextMove3S, 'White plays next'),
                              (self.scaleS, 'Pattern has to occur before move n (250=no limit)'), (self.searchButtonS, 'Start pattern search'),
                              (self.GIstart, 'Start game info search'), (self.GIclear, 'Clear all entries'),
                              (self.GI_bwd, 'Restore entries of previous game info search'), (self.GI_fwd, 'Restore entries of next game info search'),
                              (self.tagsearchButton, 'Search for tagged games.\nE.g.: H and not S'), (self.tagsetButton, 'Set tags of selected game.'),
                              (self.tagallButton, 'Tag all games currently listed with given tag.'), (self.untagallButton, 'Remove given tag from all games currently listed.'),
                              (self.tagaddButton, 'Define a new tag (give one-letter abbreviation and description).'), (self.tagdelButton, 'Remove a tag.'),
                            ]:
            ToolTip(widget, text)


    def search(self):
        '''Do a pattern search in the current game list, for the pattern currently on the board.'''

        # print 'enter pattern search'
        if not self.gamelist.noOfGames(): self.reset()
        self.gamelist.clearGameInfo()
        currentTime = time.time()
        self.configButtons(DISABLED)
        self.progBar.start(50)

        boardData = self.board.snapshot()
        self.board.delLabels()

        # --- get pattern from current board position
        dp = ''
        d = ''

        if self.board.selection[0][0] > self.board.selection[1][0] or self.board.selection[0][1] > self.board.selection[1][1]:
            self.board.selection = ((0,0), (self.board.boardsize-1, self.board.boardsize-1))

        self.sel = self.board.selection # copy this because the selection on the board may
                                        # be changed by the user although the search is not yet finished
        # print 'selection', self.sel

        contdict = []
        for i in range(self.sel[0][1], self.sel[1][1]+1):
            for j in range(self.sel[0][0], self.sel[1][0]+1):
                if (j,i) in self.board.wildcards:
                    dp += self.board.wildcards[(j,i)][1]
                    d += self.board.wildcards[(j,i)][1]
                elif self.board.getStatus(j,i) == ' ':
                    dp += '.' if (not i in [3, 9, 15] or not j in [3,9,15]) else ','
                    d += '.'
                else: 
                    inContdict = False
                    if self.cursor and 'LB' in self.cursor.currentNode():
                        # check whether position (j,i) is labelled by a number
                        # (in which case we will not in the initial pattern, but in the contlist)

                        pos = chr(j+97) + chr(i+97)
                        labels = self.cursor.currentNode()['LB']
                        for l in labels:
                            p, mark = l.split(':')
                            if pos == p:
                                try: # will fail if int(mark) does not work
                                    contdict.append((int(mark), '%s[%s]' % (self.board.getStatus(j,i),  pos, )))
                                    dp += mark
                                    d += '.'
                                    inContdict = True
                                    break
                                except ValueError:
                                    pass
                    if not inContdict:
                        dp += { 'B':'X', 'W':'O' }[self.board.getStatus(j,i)]
                        d += { 'B':'X', 'W':'O' }[self.board.getStatus(j,i)]

        contdict.sort()
        contlist = ';' + ';'.join([ x[1] for x in contdict ]) if contdict else None
        # print 'contlist', contlist

        if self.sel == ((0,0), (self.board.boardsize-1,self.board.boardsize-1)): patternType = lk.FULLBOARD_PATTERN
        elif self.sel[0] == (0,0): patternType = lk.CORNER_NW_PATTERN
        elif (self.sel[0][0], self.sel[1][1]) == (0, self.board.boardsize-1): patternType = lk.CORNER_SW_PATTERN
        elif (self.sel[0][1], self.sel[1][0]) == (0, self.board.boardsize-1): patternType = lk.CORNER_NE_PATTERN
        elif self.sel[1] == (self.board.boardsize-1, self.board.boardsize-1): patternType = lk.CORNER_SE_PATTERN
        elif self.sel[0][0] == 0: patternType = lk.SIDE_W_PATTERN
        elif self.sel[0][1] == 0: patternType = lk.SIDE_N_PATTERN
        elif self.sel[1][0] == self.board.boardsize-1: patternType = lk.SIDE_E_PATTERN
        elif self.sel[1][1] == self.board.boardsize-1: patternType = lk.SIDE_S_PATTERN
        else: patternType = lk.CENTER_PATTERN

        sizeX = self.sel[1][0] - self.sel[0][0] + 1 # number of columns
        sizeY = self.sel[1][1] - self.sel[0][1] + 1 # number of rows

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
                    x,y = self.convCoord(p)
                    if self.sel[0][0] <= x <= self.sel[1][0] and self.sel[0][1] <= y <= self.sel[1][1]:
                        if text[0] in self.contLabels: self.contLabels = self.contLabels.replace(text[0], '')
                        self.fixedLabels[(x-self.sel[0][0], y-self.sel[0][1])] = text[0]
                        fixedLabs[x-self.sel[0][0] + (y-self.sel[0][1])*sizeX] = text[0]
        except:
            showwarning('Error', 'SGF Error')
        fixedLabs = ''.join(fixedLabs)

        CSP = Pattern(d, anchors=(self.sel[0][0], self.sel[0][0], self.sel[0][1], self.sel[0][1]),
                      boardsize=self.board.boardsize, sizeX=sizeX, sizeY=sizeY, contLabels=fixedLabs, contlist=contlist, topleft=self.sel[0]) if self.fixedAnchorVar.get() \
         else Pattern(d, ptype=patternType, boardsize=self.board.boardsize, sizeX=sizeX, sizeY=sizeY, contLabels=fixedLabs, contlist=contlist, topleft=self.sel[0])
        self.searchOptions = lk.SearchOptions(self.fixedColorVar.get(), self.nextMoveVar.get(), self.moveLimit.get() if self.moveLimit.get() < 250 else 1000)
        self.searchOptions.searchInVariations = self.searchInVariations.get()
        self.searchOptions.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST
        if self.algo_hash_full_search.get(): self.searchOptions.algos |= lk.ALGO_HASH_FULL
        if self.algo_hash_corner_search.get(): self.searchOptions.algos |= lk.ALGO_HASH_CORNER

        self.patternSearch(CSP, self.searchOptions, self.contLabels, self.fixedLabels, self.progBar)

        if self.showContinuation.get(): self.showCont()
        elif self.cursor:
            try:
                self.leaveNode()
                self.displayLabels(self.cursor.currentNode())
            except: pass
        self.displayStatistics()
        self.progBar.stop()
        self.logger.insert(END, 'Pattern search, %1.1f seconds\n' % (time.time() - currentTime))

        # append the result of this search to self.prevSearches
        self.prevSearches.append(boardData=boardData,
                                 snapshot_ids = [ (i, db['data'].snapshot()) for i, db in enumerate(self.gamelist.DBlist) if not db['disabled'] ],
                                 modeVar=self.modeVar.get(), # in gl.snapshot?
                                 cursorSn = [self.cursor, self.cursor.currentGame, self.cursor.currentNode().pathToNode()],
                                 variables = [ self.modeVar.get(), self.fixedColorVar.get(), self.fixedAnchorVar.get(), self.moveLimit.get(), self.nextMoveVar.get(), ],
                                )
        self.notebookTabChanged()
        self.configButtons(NORMAL)



    # ------------  TAGGING ----------------------------------------------

    def inittags(self):
        self.taglist = v.ScrolledList(self.tagFrameS, selectmode=EXTENDED, width=30)
        self.taglist.pack(expand=True, fill=BOTH)
        self.updatetaglist()

        # self.taglist.list.bind('<<ListboxSelect>>', self.updatetags)

        self.tagFrame2 = Frame(self.tagFrameS)
        self.tagFrame2.pack(expand=True, fill=X)
        self.tagSearchVar = StringVar()
        self.tagentry = Entry(self.tagFrame2, textvariable=self.tagSearchVar)
        self.tagentry.pack(side=LEFT, fill=X, expand=True)
        self.tagentry.bind('<Return>', self.tagSearch)

        self.tagButtonF = Frame(self.tagFrame2)
        self.tagButtonF.pack(side=LEFT)
        self.tagsearchButton = Button(self.tagButtonF, text = 'Search', command = self.tagSearch)
        self.tagsearchButton.pack(side=LEFT)
        self.tagsetButton = Button(self.tagButtonF, text = 'Set', command = self.tagSet)
        self.tagsetButton.pack(side=LEFT)
        self.tagallButton = Button(self.tagButtonF, text = 'Tag all', command = self.tagAllCurrent)
        self.tagallButton.pack(side=LEFT)
        self.untagallButton = Button(self.tagButtonF, text = 'Untag all', command = self.untagAllCurrent)
        self.untagallButton.pack(side=LEFT)
        self.tagaddButton = Button(self.tagButtonF, text = 'Add tag', command = self.addTag)
        self.tagaddButton.pack(side=LEFT)
        self.tagdelButton = Button(self.tagButtonF, text = 'Del tag', command = self.deleteTagPY)
        self.tagdelButton.pack(side=LEFT)


    def updatetaglist(self):
        self.taglist.list.delete(0, END)
        l = [ int(x) for x in self.gamelist.customTags.keys() ]
        l.sort()
        for ctr, t in enumerate(l):
            self.taglist.list.insert(END, '[%s] %s' % (self.gamelist.customTags[str(t)][0], self.gamelist.customTags[str(t)][1]))
            self.taglist.list.itemconfig(ctr, **self.gamelist.taglook.get(str(t), {}))


    def addTag(self):
        """
        Creates a new tag.
        """

        # parse input
        abbr = self.tagSearchVar.get().split()[0]
        description = self.tagSearchVar.get().split()[1:]

        # check that abbr does not exist yet
        if abbr in [ self.gamelist.customTags[x][0] for x in self.gamelist.customTags.keys() ]:
            showwarning('Error', 'This tag abbreviation exists already.')
            return

        # find unused handle
        l = [ int(x) for x in self.gamelist.customTags.keys() ]
        l.sort()
        handle = str(max(l[-1] + 1, 10)) # allow for 9 "built-in" tags

        # add tag to dict of custom tags
        self.gamelist.customTags[handle] = (abbr, ' '.join(description), )
        self.logger.insert(END, 'Added tag %s %s.\n' % self.gamelist.customTags[handle])
        self.updatetaglist()


    def getTagHandle(self):
        q = self.tagSearchVar.get()
        if len(q) != 1:
            self.logger.insert(END, 'Not a tag abbreviation: %s.\n' % q)

        # delete tag from dict of custom tags
        for t in self.gamelist.customTags:
            if self.gamelist.customTags[t][0] == q: return int(t) # find the integer handle corresponding to the given abbreviation
        else:
            self.logger.insert(END, 'Not a tag abbreviation.\n')
            return


    def deleteTagPY(self):
        t = self.getTagHandle()
        if t is None: return
        if t < 10:
            showwarning('Error', 'You cannot delete built-in tags.')
            return
        self.logger.insert(END, 'Delete tag [%s] %s.\n' % tuple(self.gamelist.customTags[str(t)]))
        del self.gamelist.customTags[str(t)]

        # delete tag from all tagged games
        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            db['data'].deleteTag(t, -1)

        self.updatetaglist()


    def tagAllCurrent(self):
        t = self.getTagHandle()
        if t is None: return
        for dummy, DBindex, index in self.gamelist.gameIndex:
            self.gamelist.DBlist[DBindex]['data'].setTag(t, index, index+1)

        self.gamelist.upd()
        if self.gamelist.listbox.curselection():
            index = self.gamelist.get_index(int(self.gamelist.listbox.curselection()[0]))
            DBindex, index = self.gamelist.getIndex(index)
            self.selecttags(self.gamelist.DBlist[DBindex]['data'].getTags(index))


    def untagAllCurrent(self):
        t = self.getTagHandle()
        if t is None: return
        for dummy, DBindex, index in self.gamelist.gameIndex:
            self.gamelist.DBlist[DBindex]['data'].deleteTag(t, index)
        self.logger.insert(END, 'Deleted tag %s %s from %d games.\n' % (self.gamelist.customTags[str(t)][0], self.gamelist.customTags[str(t)][1], len(self.gamelist.gameIndex),))
        
        self.gamelist.upd()
        if self.gamelist.listbox.curselection():
            index = self.gamelist.get_index(int(self.gamelist.listbox.curselection()[0]))
            DBindex, index = self.gamelist.getIndex(index)
            self.selecttags(self.gamelist.DBlist[DBindex]['data'].getTags(index))


    def tagSearch(self, event=None, tag=None):
        if not self.gamelist.noOfGames(): self.reset()
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
                showwarning('Error', 'SGF Error')
        tag = tag or self.tagSearchVar.get()
        KEngine.tagSearch(self, tag)

        self.progBar.stop()
        self.logger.insert(END, 'Tag search %s, %1.1f seconds\n' % (tag, time.time() - currentTime))
        self.notebookTabChanged()
        self.configButtons(NORMAL)


    def tagSet(self):
        l = [ int(x) for x in self.gamelist.customTags.keys() ]
        l.sort()
        # print "set tags", [ l[int(x)] for x in self.taglist.list.curselection()]
        self.gamelist.setTags([ l[int(x)] for x in self.taglist.list.curselection()])
        self.gamelist.upd()


    def selecttags(self, tags):
        self.taglist.list.select_clear(0,END)
        for t in tags: self.taglist.list.select_set(t-1)


    def exportTags(self):

        filename = tkFileDialog.asksaveasfilename(initialdir = os.curdir)
        which_tags = [ int(x) for x in self.gamelist.customTags.keys() ]
        which_tags.remove(lk.HANDI_TAG) # no need to export HANDI tags since they are automatically assigned during processing
        self.gamelist.exportTags(filename, which_tags)


    def importTags(self):

        filename = tkFileDialog.askopenfilename(initialdir = os.curdir)
        self.gamelist.importTags(filename)
        self.updatetaglist()

    # -------------------------------------------------

    def notebookTabChanged(self, event=None):
        if self.notebook.select() == self.dateProfileFS.winfo_pathname(self.dateProfileFS.winfo_id()):
            self.displayDateProfile()

    # -------------------------------------------------




    def saveOptions(self, d):
        """ Save options to dictionary d. """
        self.options.windowGeomK.set(self.master.geometry())
        self.options.dataWindowGeometryK.set(self.dataWindow.get_geometry())
        self.mainframe.update_idletasks()
        l = [ str(self.mainframe.sash_coord(i)[0]) for i in range(2) ]
        self.options.sashPosK.set(join(l, '|%'))
        self.options.saveToDisk(d)


    def loadOptions(self, d):
        """ Load options from dictionary d. """

        self.options.loadFromDisk(d)



    def evalOptions(self):
        self.dataWindow.comments.configure(text_font=(self.options.commentfont.get(), self.options.commentfontSize.get(), self.options.commentfontStyle.get()))
        if self.options.showCoordinates.get():
            self.board.coordinates = 1
            self.board.resize()
        if self.options.windowGeomK.get():
            self.master.geometry(self.options.windowGeomK.get())
        if self.options.dataWindowGeometryK.get():
            self.dataWindow.set_geometry(self.options.dataWindowGeometryK.get())


    def evalOptionsK(self):
        try:
            self.mainframe.update_idletasks()
            l = self.options.sashPosK.get().split('|%')
            for i in [1,0]:
                self.mainframe.sash_place(i, int(l[i]), 1)
                self.mainframe.update_idletasks()
        except: pass

    def init_key_bindings(self):
        v.Viewer.init_key_bindings(self)
        self.master.bind_all('<Control-s>', lambda e, self = self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.searchStat.winfo_id()))) # select statistics tab
        self.master.bind_all('<Control-o>', lambda e, self = self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.patternSearchOptions.winfo_id()))) # select options tab
        self.master.bind_all('<Control-g>', lambda e, self = self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.giSFS.winfo_id()))) # select game info search tab
        self.master.bind_all('<Control-d>', lambda e, self = self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.dateProfileFS.winfo_id()))) # select date profile tab
        self.master.bind_all('<Control-t>', lambda e, self = self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.tagFS.winfo_id()))) # select tags tab
        self.master.bind_all('<Control-p>', lambda e, self = self: self.search()) # start pattern search
        self.master.bind_all('<Control-r>', lambda e, self = self: self.reset()) # reset game list
        self.master.bind_all('<Control-e>', lambda e, self = self: self.printPattern()) # print previous search pattern to log tab 


    def __init__(self, master):

        KEngine.__init__(self)

        # Initialization of the Viewer class
        v.Viewer.__init__(self, master, BoardWC, DataWindow)

        self.board.labelFontsize = self.options.labelFontSize
        self.fixedColorVar = self.board.fixedColor
        self.board.smartFixedColor = self.options.smartFixedColor 

        self.board.bind('<Double-1>', self.doubleClick)


        # ------------ the search window

        self.searchWindow = Frame(self.mainframe)
        self.mainframe.add(self.searchWindow)
        # self.searchWindow.withdraw()
        # self.searchWindow.geometry('400x550')
        # self.searchWindow.protocol('WM_DELETE_WINDOW', lambda: 0)
        # self.searchWindow.title('Kombilo: game list')

        self.frameS = Frame(self.searchWindow)   # suffix S means 'in search/results window'
        self.frameS.pack(fill=BOTH, expand=YES)

        self.topFrameS = Frame(self.frameS)
        self.listFrameS = Frame(self.frameS)
        self.toolbarFrameS = Frame(self.frameS)
        self.notebookFrameS = Frame(self.frameS, height=400)
        self.notebook = Notebook(self.notebookFrameS)
        
        self.searchStat = Frame(self.notebook)
        self.notebook.add(self.searchStat, text='Statistics')
        self.patternSearchOptions = Frame(self.notebook)
        self.notebook.add(self.patternSearchOptions, text='Options')
        self.giSFS = Frame(self.notebook)
        self.notebook.add(self.giSFS, text='Game info')
        self.gameinfoSearchFS = Frame(self.giSFS)
        self.dummyGISFS = Frame(self.giSFS)

        self.dateProfileFS = Frame(self.notebook)
        self.notebook.add(self.dateProfileFS, text='Date profile')

        self.tagFS = Frame(self.notebook)
        self.notebook.add(self.tagFS, text='Tags')
        self.tagFrameS = Frame(self.tagFS)
        self.tagFrameS.pack(expand=YES, fill=BOTH)

        self.logFS = Frame(self.notebook)
        self.notebook.add(self.logFS, text='Log')
        self.logFrameS = Frame(self.logFS)
        self.logger = Message(self.logFrameS)
        self.logFrameS.pack(expand=YES, fill=BOTH)
        self.logger.pack(expand=YES, fill=BOTH)

        self.gameinfoSearchFS.pack(side=LEFT, expand=True, fill=X)
        self.dummyGISFS.pack(expand=YES, fill=BOTH)
                
        self.notebook.pack(fill=BOTH, expand=YES, pady=0)
        self.notebook.bind('<<NotebookTabChanged>>', self.notebookTabChanged)

        noGamesLabel = Label(self.topFrameS, text=' ', width=18, height=1)
        noGamesLabel.grid(row=0, column=0)

        winPercLabel = Label(self.topFrameS, text=' ', width=18, height=1)
        winPercLabel.grid(row=0, column=1)

        self.gameinfoS = Pmw.ScrolledText(self.frameS, usehullsize=1, hull_height=80, text_wrap=WORD,
                                          text_font=(self.options.gameinfoFont.get(), self.options.gameinfoFontSize.get()))
        self.gameinfoS.configure(text_state=DISABLED)
        self.gameinfoS.tag_config('blue', foreground='blue')

        self.gamelist = GameListGUI(self.listFrameS, self, noGamesLabel, winPercLabel, self.gameinfoS)
        self.gamelist.pack(expand=YES, fill=BOTH, side=TOP)

        # search history

        if self.options.search_history_as_tab.get():
            self.prevSearchF = Frame(self.notebook)
            self.notebook.insert(5, self.prevSearchF, text='History')
            self.master.bind_all('<Control-h>', lambda e, self = self: self.notebook.select(self.dateProfileFS.winfo_pathname(self.prevSearchF.winfo_id()))) # select history tab
        else:
            self.prevSearchF = Frame(self.dataWindow.win)
            self.dataWindow.win.add(self.prevSearchF)
            self.dataWindow.set_geometry(self.options.dataWindowGeometryK.get())
        self.prevSF = ScrolledFrame(self.prevSearchF, usehullsize=1, hull_width=300, hull_height=135, hscrollmode='static', vscrollmode='none', vertflex='elastic')
        self.prevSF.pack(expand=YES, fill=X)
        self.prevSearches = PrevSearchesStack(self.options.maxLengthSearchesStack, self.board.changed, self.prevSF, self)
        self.board.callOnChange = self.prevSearches.select_clear

        self.initMenusK()

        # evaluate kombilo.cfg file (default databases etc.)

        self.datapath = self.config['main']['datapath'] if 'datapath' in self.config['main'] else self.basepath

        # read databases section
        self.gamelist.populateDBlist(self.config['databases'])

        # read custom tags
        if 'tags' in self.config: self.gamelist.customTags = self.config['tags']
        if 'taglook' in self.config: self.gamelist.taglook = self.config['taglook']

        # self.searchWindow.deiconify()

        self.buttonFrame1S = Frame(self.toolbarFrameS)
        self.buttonFrame1S.pack(side=LEFT, expand=NO)

        self.resetButtonS = Button(self.buttonFrame1S, text = 'Reset', command = self.reset)
        self.searchButtonS = Button(self.buttonFrame1S, text = 'Pattern ?', command = self.search)
        self.backButtonS = Button(self.buttonFrame1S, text = 'Back', command = self.back)

        self.showContinuation = IntVar()
        self.showContinuation.set(1)
        self.showContButtonS = Checkbutton(self.buttonFrame1S, text = 'Cont', variable = self.showContinuation, indicatoron=0, command=self.showCont)

        self.oneClick = IntVar()
        self.oneClickButtonS = Checkbutton(self.buttonFrame1S, text = '1 click', variable = self.oneClick, indicatoron=0)

        for ii, b in enumerate([ self.resetButtonS, self.searchButtonS, self.backButtonS, self.showContButtonS, self.oneClickButtonS ]): b.grid(row=0, column=ii)

        # -------------------------

        self.statisticsCanv = Canvas(self.searchStat, width=400, height=250, highlightthickness=0)
        self.statisticsCanv.pack(side=BOTTOM, expand=YES, fill=BOTH)

        self.dateProfileCanv = Canvas(self.dateProfileFS, width=400, height=250, highlightthickness=0)
        self.dateProfileCanv.pack(side=BOTTOM, expand=YES, fill=BOTH)

        sep2 = Separator(self.toolbarFrameS, orient='vertical')
        sep2.pack(padx = 5, fill=Y, side=LEFT)
        self.colorButtonS = Checkbutton(self.toolbarFrameS, text='Fixed Color', highlightthickness=0, variable = self.fixedColorVar)
        self.colorButtonS.pack(side=LEFT)

        sep1 = Separator(self.toolbarFrameS, orient='vertical')
        sep1.pack(padx = 5, fill=Y, side=LEFT)
        l = Label(self.toolbarFrameS, text='Next:')
        l.pack(side=LEFT)

        self.nextMoveVar = IntVar() # 0 = either player, 1 = black, 2 = white
        self.nextMove1S = Radiobutton(self.toolbarFrameS, text='B/W', highlightthickness=0, indicatoron=0, variable = self.nextMoveVar, value=0)
        self.nextMove1S.pack(side=LEFT)
        self.nextMove2S = Radiobutton(self.toolbarFrameS, text='B', highlightthickness=0, indicatoron=0, variable = self.nextMoveVar, value=1)
        self.nextMove2S.pack(side=LEFT)
        self.nextMove3S = Radiobutton(self.toolbarFrameS, text='W', highlightthickness=0, indicatoron=0, variable = self.nextMoveVar, value=2)
        self.nextMove3S.pack(side=LEFT)

        self.fixedAnchorVar = IntVar()
        self.anchorButtonS = Checkbutton(self.patternSearchOptions, text='Fixed Anchor', highlightthickness=0, variable = self.fixedAnchorVar)
        self.anchorButtonS.grid(row=0, column=0, columnspan=2, sticky=W)
        
        self.searchInVariations = IntVar()
        self.searchInVariations.set(1)
        self.searchInVariationsButton = Checkbutton(self.patternSearchOptions, text='Search in variations', highlightthickness=0, variable = self.searchInVariations)
        self.searchInVariationsButton.grid(row=1, column=0, columnspan=2, sticky=W)

        self.mvLimLabel = Label(self.patternSearchOptions, text='Move limit')
        self.mvLimLabel.grid(row=2, column=0, sticky=W)
        self.moveLimit = IntVar()
        self.moveLimit.set(250)
        self.scaleS = Scale(self.patternSearchOptions, highlightthickness=0, length=160, variable = self.moveLimit, from_=1, to=250, tickinterval = 149, showvalue=YES, orient='horizontal')
        self.scaleS.grid(row=2, column=1)

        sep1 = Separator(self.patternSearchOptions, orient='horizontal')
        sep1.grid(row=3, column=0, columnspan=2, sticky=NSEW)

        self.algo_hash_full_search = IntVar()
        self.algo_hash_full_search.set(1)
        self.algo_hash_full = Checkbutton(self.patternSearchOptions, text = 'Use hashing for full board positions', highlightthickness = 0, variable = self.algo_hash_full_search, pady=5)
        self.algo_hash_full.grid(row=4, column = 0, columnspan=2, sticky=W)

        self.algo_hash_corner_search = IntVar()
        self.algo_hash_corner_search.set(1)
        self.algo_hash_corner = Checkbutton(self.patternSearchOptions, text = 'Use hashing for corner positions', highlightthickness = 0, variable = self.algo_hash_corner_search, pady=5)
        self.algo_hash_corner.grid(row=5, column = 0, columnspan=2, sticky=W)


        self.progBar = Progressbar(self.frameS)
        self.progBar.start(50)

        self.topFrameS.pack(side=TOP, fill=X, expand=NO) 
        self.listFrameS.pack(side=TOP, fill=BOTH, expand=YES) 
        self.gameinfoS.pack(side=TOP, fill=X, expand=NO) 
        self.toolbarFrameS.pack(side=TOP, fill=X, expand=NO)
        self.notebookFrameS.pack(side=TOP, fill=X, expand=NO) 
        self.progBar.pack(side=TOP, fill=X, expand=NO)

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
        
        l1 = Label(f1, text='White', anchor=W)
        e1 = Entry(f1, width=16, textvariable=self.pwVar)
        l2 = Label(f1, text='Black', anchor=W)
        e2 = Entry(f1, width=16, textvariable=self.pbVar)
        l3 = Label(f1, text='Player', anchor=W)
        e3 = Entry(f1, width=33, textvariable=self.pVar)
        l4 = Label(f1, text='Event', anchor=W)
        e4 = Entry(f1, width=33, textvariable=self.evVar)
        l5 = Label(f1, text='From', anchor=W)
        e5 = Entry(f1, width=16, textvariable=self.frVar)
        l6 = Label(f1, text='To', anchor=W)
        e6 = Entry(f1, width=16, textvariable=self.toVar)

        l7 = Label(f1, text='Anywhere', anchor=W)
        e7 = Entry(f1, width=33, textvariable=self.awVar)

        l8 = Label(f1, text='SQL', anchor=W)
        e8 = Entry(f1, width=43, textvariable=self.sqlVar)

        self.referencedVar = IntVar()
        b1 = Checkbutton(f3, text='Referenced', variable = self.referencedVar, highlightthickness=0)
        
        self.GIstart = Button(f3, text='Start', command = self.doGISearch)
        self.GIclear = Button(f3, text='Clear', command = self.clearGI)

        self.GI_bwd = Button(f3, text = '<-', command = self.historyGI_back)
        self.GI_fwd = Button(f3, text = '->', command = self.historyGI_fwd)

        for e in [e1, e2, e3, e4, e5, e6, e7, e8]:
            e.bind('<Return>', lambda event, bs = self.GIstart: bs.invoke())
        
        l1.grid(row=0, column=0, sticky=E)
        e1.grid(row=0, column=1, sticky=NSEW)
        l2.grid(row=0, column=2, sticky=E)
        e2.grid(row=0, column=3, sticky=NSEW)
        l3.grid(row=2, column=0, sticky=E)
        e3.grid(row=2, column=1, columnspan = 3, sticky=NSEW)
        l4.grid(row=3, column=0,  sticky=E)
        e4.grid(row=3, column=1, columnspan = 3, sticky=NSEW)
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
        f4.pack(expand=True, fill=BOTH)
        
        f5 = Frame(self.gameinfoSearchFS)
        f5.pack(side=LEFT, expand=YES, fill=X)

        l1 = Label(f5, text='Go to:', anchor=W)
        l1.pack(side=LEFT)
        self.gotoVar = StringVar()
        e9 = Entry(f5, width=20, textvariable=self.gotoVar)
        e9.pack(side=LEFT, expand=YES, fill=X)
        for key, fct in [ ('<Key>', self.gotoChange), ('<Up>', self.gamelist.up), ('<Down>', self.gamelist.down), ('<Prior>', self.gamelist.pgup), ('<Next>', self.gamelist.pgdown) ]:
            e9.bind(key, fct)

        self.history_GIsearch = []
        self.history_GIS_index = -1

        self.inittags()

        # icons for the buttons
        for button, filename in [ (self.showContButtonS, 'abc-u.gif'), (self.backButtonS, 'edit-undo.gif'), (self.resetButtonS, 'go-home.gif'), (self.searchButtonS, 'system-search.gif'),
                                  (self.oneClickButtonS, 'mouse.gif'), (self.nextMove1S, 'bw.gif'), (self.nextMove2S, 'b.gif'), (self.nextMove3S, 'w.gif'),
                                  (self.GIstart, 'system-search.gif'), (self.GIclear, 'document-new.gif'), (self.GI_bwd, 'go-previous.gif'), (self.GI_fwd, 'go-next.gif'),
                                  (self.tagsearchButton, 'system-search.gif'), (self.tagaddButton, 'add.gif'), (self.tagdelButton, 'list-remove.gif'), 
                                  (self.tagallButton, 'edit-select-all.gif'), (self.untagallButton, 'edit-clear.gif'), (self.tagsetButton, 'bookmark-new.gif'),
                                ]:
            try:
                im = PhotoImage(file=os.path.join(self.basepath, 'icons', filename))
                self.tkImages.append(im)
                button.config(image=im)
            except:
                pass

        # load logo
        try:
            self.logo = PhotoImage(file=os.path.join(self.basepath,'icons/logok.gif'))
        except TclError:
            self.logo = None

        self.balloonHelpK()
        self.evalOptionsK()

        self.board.update_idletasks()
        # self.notebook.setnaturalsize()
        self.searchWindow.update_idletasks()

        # splash screen TODO

        if self.options.smartFixedColor.get(): self.fixedColorVar.set(1)
        self.gamelist.showFilename = self.options.showFilename.get()
        self.gamelist.showDate = self.options.showDate.get()
        self.parseReferencesFile(datafile = os.path.join(self.basepath, 'data', 'references'),
                                 options = self.config['references'] if 'references' in self.config else None)
        self.loadDBs(self.progBar, showwarning)

        self.logger.insert(END, 'Kombilo %s.\nReady ...\n' % KOMBILO_RELEASE)
        self.progBar.stop()


# ---------------------------------------------------------------------------------------

root = Tk()
root.withdraw()

if sys.path[0].endswith('library.zip'):
    # using an exe produced by py2exe?
    SYSPATH = os.path.split(sys.path[0])[0]
else:
    SYSPATH = sys.path[0]

try:
    if os.path.exists(os.path.join(SYSPATH, 'kombilo.app')):
        root.option_readfile(os.path.join(SYSPATH, 'kombilo.app'))
except TclError:
    showwarning('Error', 'Error reading kombilo.app')
    
app = App(root)

root.protocol('WM_DELETE_WINDOW', app.quit)
root.title('Kombilo: board')

app.boardFrame.focus_force()

for filename in sys.argv[1:]:              # load sgf files given as arguments
    app.openFile(os.path.split(filename)[0], os.path.split(filename)[1])

root.mainloop()
root.destroy()



