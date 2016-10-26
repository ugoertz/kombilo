#!/usr/bin/python
# File: v.py

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

from __future__ import absolute_import

import __builtin__
import os
import sys
import gettext
import glob
import pkg_resources
import webbrowser
from configobj import ConfigObj

from Tkinter import *
from ttk import *
from tkMessageBox import *
from ScrolledText import ScrolledText
import tkFileDialog
import tkFont

from .tooltip.tooltip import ToolTip
from PIL import Image as PILImage
from PIL import ImageTk as PILImageTk
import Pmw

from string import split, replace, join, strip
from math import sqrt
from random import randint

from .option_editor import OptionEditor
from . import libkombilo as lk
from .board import *
from .sgf import Node, Cursor, flip_mirror1, flip_mirror2, flip_rotate

KOMBILO_VERSION = 0.8

# ---------------------------------------------------------------------------------------

def get_configfile_directory():
    if sys.platform.startswith('win'):
        return os.path.join(os.environ.get('APPDATA'), 'kombilo', ('%s' % KOMBILO_VERSION).replace('.', ''))
    else:
        return os.path.expanduser('~/.kombilo/%s' % ('%s' % KOMBILO_VERSION).replace('.', ''))

def load_icon(button, filename, imagelist, buttonsize):
    try:
        im = PILImageTk.PhotoImage(PILImage.open(pkg_resources.resource_stream(__name__, 'icons/%s.png' % filename)).resize((buttonsize, buttonsize), PILImage.LANCZOS))
        button.config(image=im, width=buttonsize, height=buttonsize)
        imagelist.append(im)
    except AttributeError:
        pass

def get_addmenu_options(**kwargs):
    '''
    For i18n of menu entries, takes care of finding index of the letter which
    should be underlined. The given label should mark the concerning letter with
    an underscore before the letter, e.g., '_File', 'E_xit'. The function sets
    underline to the correct position (index of underscore), and removes the
    underscore from the label.'''

    pos = kwargs.get('label', '').find('_')

    if pos == -1:
        return kwargs

    kwargs['underline'] = pos
    kwargs['label'] = kwargs['label'].replace('_', '', 1)
    return kwargs


class BunchTkVar:
    """ This class is used to collect the Tk variables where the options
        are stored. """

    def saveToDisk(self, d):
        for x in self.__dict__:
            if isinstance(self.__dict__[x], BooleanVar):
                d[x] = 'True' if self.__dict__[x].get() else 'False'
            else:
                d[x] = self.__dict__[x].get()

    def loadFromDisk(self, d):
        for x in d:
            try:
                if d[x] in ['True', 'False']:
                    self.__dict__[x] = BooleanVar()
                    self.__dict__[x].set(d[x] == 'True')
                else:
                    int(d[x])
                    self.__dict__[x] = IntVar()
                    self.__dict__[x].set(int(d[x]))
            except:
                self.__dict__[x] = StringVar()
                self.__dict__[x].set(d[x])

# ---------------------------------------------------------------------------------------


class TextEditor:
    """ A very simple text editor, based on the Tkinter ScrolledText widget.
    You can perform very limited editing, and save the result to a file. """

    def __init__(self, t='', defpath='', font=None):

        if font is None:
            font = ('Courier', 10, '')

        self.window = Toplevel()

        self.window.protocol('WM_DELETE_WINDOW', self.quit)

        self.text = ScrolledText(self.window, width=70, height=30, font=font)
        self.text.pack(side=BOTTOM, fill=BOTH, expand=YES)
        self.text.insert(END, t)

        self.buttonFrame = Frame(self.window)
        self.buttonFrame.pack(side=TOP, expand=NO, fill=X)

        Button(self.buttonFrame, text=_('Quit'), command=self.quit).pack(side=RIGHT)
        Button(self.buttonFrame, text=_('Save as'), command=self.saveas).pack(side=RIGHT)

        # self.window.lift()
        self.window.focus()

        if defpath:
            self.defpath = defpath
        else:
            self.defpath = os.curdir

    def saveas(self):
        f = tkFileDialog.asksaveasfilename(initialdir=self.defpath)
        if not f:
            return
        try:
            file = open(f, 'w')
            file.write(self.text.get('1.0', END).encode('utf-8', 'ignore'))
            file.close()
        except IOError:
            showwarning(_('I/O Error'), _('Cannot write to ') + f)

    def quit(self):

        self.window.destroy()

# ------------------------------------------------------------------------


class ScrolledList(Frame):
    """ A listbox with dynamic vertical and horizontal scrollbars. """

    def __init__(self, parent, **kw):
        Frame.__init__(self, parent)

        self.sbar = Scrollbar(self)
        self.sbar1 = Scrollbar(self)
        self.checking = 0

        defaults = {'height': 12, 'width': 40, 'relief': SUNKEN, 'selectmode': SINGLE, 'takefocus': 1, 'exportselection': 0}
        if kw:
            defaults.update(kw)

        self.list = Listbox(self, defaults)
        self.sbar.config(command=self.list.yview)
        self.sbar1.config(command=self.list.xview, orient='horizontal')
        self.list.config(xscrollcommand=self.sbar1.set, yscrollcommand=self.sbar.set)
        self.list.grid(row=0, column=0, sticky=NSEW)
        self.sbar.grid(row=0, column=1, sticky=NSEW)
        self.sbar1.grid(row=1, column=0, sticky=NSEW)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.focus_force()

        self.onSelectionChange = None

        self.list.bind('<Up>', self.up)
        self.list.bind('<Down>', self.down)
        self.list.bind('<Prior>', self.pgup)
        self.list.bind('<Next>', self.pgdown)

        # self.unbind('<Configure>')
        self.bind('<Configure>', self.checkScrollbars)

        self.sbar.grid_forget()
        self.sbar1.grid_forget()

    def insert(self, index, data):
        if type(data) == type([]):
            apply(self.list.insert, [index] + data)
        else:
            self.list.insert(index, data)

        if self.list.yview() != (0.0, 1.0):
            self.sbar.grid(row=0, column=1, sticky=NSEW)
        if self.list.xview() != (0.0, 1.0):
            self.sbar1.grid(row=1, column=0, sticky=NSEW)

    def delete(self, index, data=None):
        if data:
            self.list.delete(index, data)
        else:
            self.list.delete(index)

        if self.list.yview() == (0.0, 1.0):
            self.sbar.grid_forget()

        if self.list.xview() == (0.0, 1.0):
            self.sbar1.grid_forget()

    def checkScrollbars(self, event=None):
        if self.checking:
            if self.list.yview() != (0.0, 1.0):
                self.sbar.grid(row=0, column=1, sticky=NSEW)
            else:
                self.sbar.grid_forget()
            if self.list.xview() != (0.0, 1.0):
                self.sbar1.grid(row=1, column=0, sticky=NSEW)
            else:
                self.sbar1.grid_forget()
        else:
            self.after(100, self.checkScrollbars)
        self.checking = 1 - self.checking

    def up(self, event):
        if not self.list.curselection() or len(self.list.curselection()) > 1:
            return
        index = int(self.list.curselection()[0])
        if index != 0:
            self.list.select_clear(index)
            self.list.select_set(index - 1)
            self.list.see(index - 1)
            if self.onSelectionChange:
                self.onSelectionChange(None, index - 1)

    def down(self, event):
        if not self.list.curselection() or len(self.list.curselection()) > 1:
            return
        index = int(self.list.curselection()[0])
        if index != self.list.size() - 1:
            self.list.select_clear(index)
            self.list.select_set(index + 1)
            self.list.see(index + 1)
            if self.onSelectionChange:
                self.onSelectionChange(None, index + 1)

    def pgup(self, event):
        if not self.list.curselection() or len(self.list.curselection()) > 1:
            return
        index = int(self.list.curselection()[0])
        if index >= 10:
            self.list.select_clear(index)
            self.list.select_set(index - 10)
            self.list.see(index - 10)
            if self.onSelectionChange:
                self.onSelectionChange(None, index - 10)
        elif self.list.size():
            self.list.select_clear(index)
            self.list.select_set(0)
            self.list.see(0)
            if self.onSelectionChange:
                self.onSelectionChange(None, 0)

    def pgdown(self, event):
        if not self.list.curselection() or len(self.list.curselection()) > 1:
            return
        index = int(self.list.curselection()[0])
        if index <= self.list.size() - 10:
            self.list.select_clear(index)
            self.list.select_set(index + 10)
            self.list.see(index + 10)
            if self.onSelectionChange:
                self.onSelectionChange(None, index + 10)
        elif self.list.size():
            self.list.select_clear(index)
            self.list.select_set(self.list.size() - 1)
            self.list.see(END)
            if self.onSelectionChange:
                self.onSelectionChange(None, self.list.size() - 1)

# ---------------------------------------------------------------------------------------


class SGFtreeCanvas(Frame):
    """ The canvas (in the data window) displaying the tree structure of the current game."""

    def __init__(self, parent, options, **args):

        Frame.__init__(self, parent)
        self.options = options

        self.UNIT = args.pop('unit', 40)

        defaults = {'height': 100, 'width': 150, 'relief': SUNKEN}
        if args:
            defaults.update(args)


        self.canvas = Canvas(self, background='lightyellow')
        apply(self.canvas.config, (), defaults)
        self.canvas.config(scrollregion=(0, 0, 1000, 30))

        self.sbar_vert = Scrollbar(self)
        self.sbar_hor = Scrollbar(self)

        self.sbar_vert.config(command=self.yview)
        self.sbar_hor.config(command=self.xview, orient='horizontal')
        self.canvas.config(xscrollcommand=self.sbar_hor.set, yscrollcommand=self.sbar_vert.set)

        self.movenoCanvas = Canvas(self, width=150, height=18, background='white')
        self.movenoCanvas.config(scrollregion=(0, 0, 1000, 18))
        # self.movenoCanvas.config(xscrollcommand = self.sbar_hor.set)

        self.updateMovenoCanvas()

        self.movenoCanvas.grid(row=0, column=0, sticky=NSEW)
        self.sbar_vert.grid(row=1, column=1, sticky=NSEW)
        self.sbar_hor.grid(row=2, column=0, sticky=NSEW)
        self.canvas.grid(row=1, column=0, sticky=NSEW)

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        # self.config(height=100, width=200)
        # self.canvSize = 200,100
        self.drawn = []

        self.lastbind = None

    def updateMovenoCanvas(self):
        """ Put numbers on the small white canvas above the SGF tree canvas, to indicate move numbers."""

        self.movenoCanvas.delete(ALL)
        for i in range(90):
            self.movenoCanvas.create_text(
                    int(self.UNIT * .75) + i * 5 *self.UNIT, 7, text=repr(5 * i),
                    font=(self.options.smallFont.get(), self.options.smallFontSize.get()))

    def xview(self, a1, a2=None, a3=None):
        if a1 == MOVETO:
            self.movenoCanvas.xview(a1, a2)
            self.canvas.xview(a1, a2)
        elif a1 == SCROLL:
            self.movenoCanvas.xview(a1, a2, a3)
            self.canvas.xview(a1, a2, a3)
        else:
            return

    def yview(self, a1, a2=None, a3=None):

        if a1 == MOVETO:
            self.canvas.yview(a1, a2)
        elif a1 == SCROLL:
            self.canvas.yview(a1, a2, a3)
        elif a1 == 'refresh':
            pass
        else:
            return

        self.canvas.update_idletasks()

        vert = self.sbar_vert.get()
        y0 = int(vert[0] * self.canvSize[1])
        y1 = int(vert[1] * self.canvSize[1])

        u = max(0, (y0 - 300) //self.UNIT)
        l = (y1 + 500) //self.UNIT

        # print 'yview', u,l

        nodelist = [(self.rootnode, 0, 0)]

        while nodelist:
            c, posx, posy = nodelist.pop()

            # print posx, posy

            if u <= posy <= l and not posy in self.drawn:
                self.mark(c, posx, posy)

                if c.previous:
                    if c.up and c.up.up:
                        self.link(posx, posy, c.posyD + 1)
                    else:
                        self.link(posx, posy, c.posyD)

                    if c.down and posy + c.down.posyD > l:
                        if c.up:
                            self.link(posx, posy + c.down.posyD, c.down.posyD + 1)
                        else:
                            self.link(posx, posy + c.down.posyD, c.down.posyD)

            if c != self.rootnode and c.down and posy + c.down.posyD <= l:
                d = c.down
                py = posy + d.posyD
                while d.down and py + d.down.posyD < u:
                    d = d.down
                    py += d.posyD
                nodelist.append((d, posx, py))

            if c.down and posy + c.down.posyD < u:
                continue

            while c.next:
                c = c.next
                posx += 1
                if u <= posy <= l and not posy in self.drawn:

                    self.mark(c, posx, posy)

                    if c.previous:
                        if c.up and c.up.up:
                            self.link(posx, posy, c.posyD + 1)
                        else:
                            self.link(posx, posy, c.posyD)

                        if c.down and posy + c.down.posyD > l:
                            if c.up:
                                delta2 = 1
                            else:
                                delta2 = 0
                            self.link(posx, posy + c.down.posyD, c.down.posyD + delta2)

                if c.down and posy + c.down.posyD <= l:
                    d = c.down
                    py = posy + d.posyD
                    while d.down and py + d.down.posyD < u:
                        d = d.down
                        py += d.posyD
                    nodelist.append((d, posx, py))

        self.canvas.lower('lines')

        for i in range(u, l):
            if not i in self.drawn:
                self.drawn.append(i)

    def mark(self, node, posx, posy):
        try:
            n = Node(node)
            if 'W' in n:
                color = 'white'
            elif 'B' in n:
                color = 'black'
            else:
                color = 'red'
        except:
            color = 'yellow'

        self.canvas.create_oval(self.UNIT * posx +self.UNIT // 2,
                                self.UNIT * posy +self.UNIT // 2,
                                self.UNIT * posx +self.UNIT,
                                self.UNIT * posy +self.UNIT, fill=color)

        try:
            if 'C' in n or 'TR' in n or 'SQ' in n or 'CR' in n or 'LB' in n or 'MA' in n:
                self.canvas.create_oval(self.UNIT * posx +self.UNIT * 2 // 3,
                                        self.UNIT * posy +self.UNIT * 2 // 3,
                                        self.UNIT * posx +self.UNIT * 5 // 6,
                                        self.UNIT * posy +self.UNIT * 5 // 6, fill='blue')
        except:
            pass

    def link(self, posx, posy, delta):

        s4 = self.UNIT // 4
        s34 = 3 * self.UNIT // 4

        if delta == 0:
            self.canvas.create_line(self.UNIT * posx - s4,
                                    self.UNIT * posy + s34,
                                    self.UNIT * posx + s34,
                                    self.UNIT * posy + s34,
                                    fill='blue', tags='lines', width=2)
        else:
            self.canvas.create_line(self.UNIT * posx - s4,
                                    self.UNIT * (posy - 1) + s34,
                                    self.UNIT * posx + s34,
                                    self.UNIT * posy + s34,
                                    fill='blue', tags='lines', width=2)
            if delta > 1:
                self.canvas.create_line(self.UNIT * posx - s4,
                                        self.UNIT * (posy - delta) + s34,
                                        self.UNIT * posx - s4,
                                        self.UNIT * (posy - 1) + s34,
                                        fill='blue', tags='lines', width=2)

# ---------------------------------------------------------------------------------------


class DataWindow:

    def __init__(self, master, window):
        self.mster = master

        window = window

        win = PanedWindow(window, orient='vertical')
        self.win = win
        win.pack(expand=YES, fill=BOTH)

        self.initPanes()

        self.SGFtreeC = SGFtreeCanvas(self.gametreeF, self.mster.options, unit=master.options.scaling.get() * 3 // 2)
        self.SGFtreeC.pack(side=LEFT, expand=YES, fill=BOTH)
        self.guessModeCanvas = Canvas(self.gametreeF, width=160, height=100, background='white')

        self.filelist = ScrolledList(self.filelistF)
        self.filelist.grid(row=0, column=0, rowspan=3, sticky=NSEW)
        self.filelistF.rowconfigure(2, weight=1)
        self.filelistF.columnconfigure(0, weight=1)

        self.filelistB1 = Button(self.filelistF, text=_('NEW'), command=self.mster.newFile)
        self.filelistB1.grid(row=0, column=1, sticky=S)
        self.filelistB2 = Button(self.filelistF, text=_('OPEN'), command=self.mster.openFile)
        self.filelistB2.grid(row=1, column=1, sticky=S)
        self.filelistB3 = Button(self.filelistF, text=_('DEL'), command=self.mster.delFile)
        self.filelistB3.grid(row=0, column=2, sticky=S)
        self.filelistB4 = Button(self.filelistF, text=_('split'), command=self.mster.splitCollection)
        self.filelistB4.grid(row=1, column=2, sticky=S)

        self.tkImages = []
        for button, filename in [
                (self.filelistB1, 'actions-document-new'),
                (self.filelistB2, 'actions-document-open'),
                (self.filelistB3, 'places-user-trash'),
                (self.filelistB4, 'actions-edit-cut')]:
            load_icon(button, filename, self.tkImages, self.mster.options.scaling.get())

        self.filelist.onSelectionChange = self.mster.changeCurrentFile
        self.filelist.list.bind('<1>', self.mster.changeCurrentFile)

        self.gamelist = ScrolledList(self.gamelistF)
        self.gamelist.grid(row=0, column=0, rowspan=3, sticky=NSEW)
        self.gamelistF.rowconfigure(2, weight=1)
        self.gamelistF.columnconfigure(0, weight=1)

        self.gamelistB1 = Button(self.gamelistF, text=_('NEW'), command=self.mster.newGame)
        self.gamelistB1.grid(row=0, column=1, sticky=S)
        self.gamelistB2 = Button(self.gamelistF, text=_('DEL'), command=self.mster.delGame)
        self.gamelistB2.grid(row=1, column=1, sticky=S)

        for button, filename in [
                (self.gamelistB1, 'actions-document-new'),
                (self.gamelistB2, 'places-user-trash')]:
            load_icon(button, filename, self.tkImages, self.mster.options.scaling.get())

        self.gamelist.onSelectionChange = self.mster.changeCurrentGame
        self.gamelist.list.bind('<1>', self.gamelistClick)
        self.gamelist.list.bind('<B1-Motion>', self.gamelistDrag)
        self.gamelist.list.bind('<ButtonRelease-1>', self.gamelistRelease)

        self.gamelist.clickedLast = -1
        self.gamelist.dragLast = -1

        self.gameinfo = Pmw.ScrolledText(self.gameinfoF, text_wrap=WORD)
        self.gameinfo.configure(text_state='disabled', text_font=self.mster.standardFont)
        self.gameinfo.pack(fill=BOTH, expand=YES)
        self.SNM = 0
        self.guessRightWrong = [0, 0]

        self.comments = Pmw.ScrolledText(self.commentsF, text_wrap='word')
        self.comments.pack(expand=YES, fill=BOTH)
        self.window = window

    def initPanes(self):
        self.filelistF = Frame(self.win)
        self.gamelistF = Frame(self.win)
        self.gameinfoF = Frame(self.win)
        self.gametreeF = Frame(self.win)
        self.commentsF = Frame(self.win)
        for fr in [self.filelistF, self.gamelistF, self.gameinfoF, self.gametreeF, self.commentsF]:
            self.win.add(fr)
        # self.win.config(showhandle=1)

    def toggleGuessMode(self):
        if self.mster.guessMode.get():
            if self.mster.mainframe.sash_coord(0)[0] < 300:
                self.remember_sash = self.mster.mainframe.sash_coord(0)[0]
                self.mster.mainframe.sash_place(0, 300, 1)
            else:
                self.remember_sash = None

            self.guessRightWrong = [0, 0]
            self.guessModeCanvas.pack(side=RIGHT, expand=NO, fill=BOTH)
            self.guessModeCanvas.delete(ALL)
            if self.mster.boardImg:
                self.guessModeCanvas.create_image(0, 0, image=self.mster.boardImg)
                self.guessModeCanvas.create_rectangle(10, 10, 90, 90, fill='', outline='black')
                for i in range(3):
                    for j in range(3):
                        self.guessModeCanvas.create_oval(10 + (80 / 6.0) + (80 / 3.0) * i - 1, 10 + (80 / 6.0) + (80 / 3.0) * j - 1, 10 + (80 / 6.0) + (80 / 3.0) * i + 1, 10 + (80 / 6.0) + (80 / 3.0) * j + 1, fill="black")
            else:
                self.guessModeCanvas.create_rectangle(10, 10, 90, 90, fill='', outline='black')

            if self.mster.options.showNextMoveVar.get():
                self.SNM = 1
                self.mster.options.showNextMoveVar.set(0)
                self.mster.showNextMove()
            else:
                self.SNM = 0
        else:
            self.guessModeCanvas.pack_forget()
            if self.SNM:
                self.mster.options.showNextMoveVar.set(1)
            self.mster.showNextMove()
            try:
                if not self.remember_sash is None:
                    self.mster.mainframe.sash_place(0, self.remember_sash, 1)
            except:
                pass

    def gamelistClick(self, event):
        self.gamelist.clickedLast = self.gamelist.list.nearest(event.y)
        self.gamelist.dragLast = -1
        self.mster.changeCurrentGame(event)

    def gamelistDrag(self, event):

        i = self.gamelist.list.nearest(event.y)
        if self.gamelist.dragLast == -1:
            if self.gamelist.clickedLast == i:
                return
            else:
                self.gamelist.dragLast = self.gamelist.clickedLast

        if self.gamelist.dragLast != i:
            s = self.gamelist.list.get(self.gamelist.dragLast)
            self.gamelist.delete(self.gamelist.dragLast)
            self.gamelist.insert(i, s)
            self.gamelist.list.select_set(i)
            self.gamelist.dragLast = i
        return 'break'

    def gamelistRelease(self, event):

        if self.gamelist.dragLast == -1:
            return None, None

        i = self.gamelist.list.nearest(event.y)

        if self.gamelist.dragLast != i:
            s = self.gamelist.list.get(self.gamelist.dragLast)
            self.gamelist.delete(self.gamelist.dragLast)
            self.gamelist.insert(i, s)
            self.gamelist.list.select_set(i)
            self.gamelist.dragLast = i

        if self.gamelist.clickedLast != i:

            try:
                n = self.mster.cursor.root.next
                for j in range(self.gamelist.clickedLast):
                    n = n.down

                m = self.mster.cursor.root.next
                for j in range(i):
                    m = m.down

                if n.up:
                    n.up.down = n.down
                else:
                    self.mster.cursor.root.next = n.down
                if n.down:
                    n.down.up = n.up

                if i < self.gamelist.clickedLast:   # insert n above m
                    n.up = m.up
                    if m.up:
                        m.up.down = n
                    else:
                        self.mster.cursor.root.next = n
                    m.up = n
                    n.down = m
                else:                               # insert n below m
                    n.down = m.down
                    if m.down:
                        m.down.up = n
                    m.down = n
                    n.up = m

                self.mster.cursor.updateGamelist(0)
                self.mster.cursor.currentGame = i
                self.gamelist.list.select_set(i)
                self.gamelist.list.see(i)
                self.updateGameInfo(self.mster.cursor)

                filelistIndex = self.mster.currentFileNum
                d = self.mster.filelist[filelistIndex][4]

                if i < self.gamelist.clickedLast:
                    p_last = d.get(self.gamelist.clickedLast, ())

                    jj = self.gamelist.clickedLast
                    while jj > i:
                        if jj - 1 in d:
                            d[jj] = d[jj - 1]
                        elif jj in d:
                            del d[jj]
                        jj -= 1

                    d[i] = p_last

                else:
                    p_i = d.get(i, ())
                    jj = self.gamelist.clickedLast
                    while jj < i:
                        if jj + 1 in d:
                            d[jj] = d[jj + 1]
                        elif jj in d:
                            del d[jj]
                        jj += 1

                    d[self.gamelist.clickedLast] = p_i

                return self.gamelist.clickedLast, i

            except lk.SGFError:
                showwarning(_('Error'), _('SGF Error') + '(gamelistRelease)')
            except:
                showwarning(_('Error'), _('An error occurred, please submit a bug report.'))

        return None, None

    def get_geometry(self):
        self.win.update_idletasks()
        l = [str(self.win.sash_coord(i)[1]) for i in range(4)]
        return join(l, '|%')

    def set_geometry(self, s):
        l = split(s, '|%')
        if len(l) != 4:
            return
        self.win.update_idletasks()
        for i in [3, 2, 1, 0]:
            self.win.sash_place(i, 1, int(l[i]))
            self.win.update_idletasks()

    def updateGameInfo(self, cursor):

        currentGame = cursor.currentGame

        try:
            node = cursor.getRootNode(currentGame)
        except:
            return

        t = []

        s1 = cursor.transcode('PW', node)
        t.append(s1 if s1 else ' ?')

        s1 = cursor.transcode('WR', node)
        if s1:
            t.append(', ')
            t.append(s1)

        t.append(' - ')

        s1 = cursor.transcode('PB', node)
        t.append(s1 if s1 else ' ?')

        s1 = cursor.transcode('BR', node)
        if s1:
            t.append(', ')
            t.append(s1)

        s1 = cursor.transcode('RE', node)
        if s1:
            t.append(', ' + s1)
        s1 = cursor.transcode('KM', node)
        if s1:
            t.append(' (' + _('Komi') + ' ' + s1 + ')')
        s1 = cursor.transcode('HA', node)
        if s1:
            t.append(' (' + _('Hcp') + ' ' + s1 + ')')

        t.append('\n')
        t.append(', '.join([cursor.transcode(prop, node) for prop in ['EV', 'RO', 'DT'] if prop in node]))
        t.append('\n')

        s1 = cursor.transcode('GC', node) or ''
        s1 = s1.replace('\n\r', ' ').replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')
        t.append(s1)

        self.gameinfo.configure(text_state='normal')
        self.gameinfo.delete('1.0', END)
        self.gameinfo.insert('1.0', join(t, ''))
        self.gameinfo.configure(text_state=DISABLED)

# -----------------------------------------------------------------------------------


class EnhancedCursor(Cursor):
    """
    This integrates the cursor of an SGF file with an SGFtreeCanvas.
    Adds a snapshot/restore feature to Cursor. """

    def __init__(self, sgf, comments, SGFtreeC, master, encoding='utf8'):

        try:
            Cursor.__init__(self, sgf, 1, encoding=encoding)
        except:
            raise lk.SGFError()
        self.mster = master

        self.currentGame = 0
        self.updateGamelist()

        self.comments = comments
        self.SGFtreeCanv = SGFtreeC

        self.SGFtreeCanv.canvSize = 1, 1
        self.SGFtreeCanv.drawn = []

        self.SGFtreeCanv.rootnode = self.root.next
        self.updateTree()

    def transcode(self, prop, node=None):
        d = Node(node) if node else self.currentNode()
        if not prop in d or not d[prop]:
            return ''
        s = d[prop][0]
        return s

    def updateTree(self, update=1):
        self.SGFtreeCanv.canvas.delete('all')
        self.SGFtreeCanv.drawn = []

        width = self.SGFtreeCanv.UNIT * (self.width + 1) + 30

        if self.SGFtreeCanv.rootnode.down:
            h = self.SGFtreeCanv.rootnode.down.posyD
        else:
            n = self.root.next
            h = 0
            while n.down:
                n = n.down
                h += n.posyD
            h = self.height - h

        height = self.SGFtreeCanv.UNIT * (h + 1) + 30

        self.SGFtreeCanv.canvSize = width, height
        self.SGFtreeCanv.canvas.config(scrollregion=(0, 0, width, height))
        self.SGFtreeCanv.movenoCanvas.config(scrollregion=(0, 0, width, 18))
        self.SGFtreeCanv.updateMovenoCanvas()

        if self.SGFtreeCanv.lastbind is not None:
            self.SGFtreeCanv.canvas.unbind('<1>', self.SGFtreeCanv.lastbind)
        self.SGFtreeCanv.lastbind = self.SGFtreeCanv.canvas.bind('<1>', self.onButton1)

        self.SGFtreeCanv.yview('refresh')

        if update:
            self.SGFtreeCanv.update_idletasks()
            self.seeCurrent()

    def updateGamelist(self, select=1):
        """Update the game list in the data window (i.e. the list of games in the SGF collection of self."""

        self.mster.dataWindow.gamelist.delete(0, END)
        i = 0
        n = Node(self.root.next)
        while n:
            s = '[%d] ' % i

            s += self.transcode('PW', n)
            s += ' - '
            s += self.transcode('PB', n)
            s1 = self.transcode('RE', n)
            if s1:
                s += ' (' + s1 + ')'

            self.mster.dataWindow.gamelist.insert(END, s)
            n = n.down
            i += 1

        if select:
            self.mster.dataWindow.gamelist.list.select_set(0)
            self.mster.dataWindow.gamelist.list.see(0)
            self.mster.dataWindow.updateGameInfo(self)

    def onButton1(self, event):
        try:
            # store coordinates of click in x,y
            x1 = self.SGFtreeCanv.canvas.canvasx(event.x)
            y1 = self.SGFtreeCanv.canvas.canvasy(event.y)
            x = (x1 - self.SGFtreeCanv.UNIT // 2) // self.SGFtreeCanv.UNIT
            y = (y1 - self.SGFtreeCanv.UNIT // 2) // self.SGFtreeCanv.UNIT

            # where are we now?
            p1 = self.currentNode().pathToNode()

            # set c to start of current game
            c = self.root.next
            for i in range(self.currentGame):
                c = c.down
            posx, posy = 0, 0

            # set c to position of click
            while (posx, posy) != (x, y):
                if not c.next:
                    return
                c = c.next
                posx += 1

                if posx > x:
                    break  # have arrived

                # do we have to go down here?
                while posy < y and c.down and posy + c.down.posyD <= y:
                    c = c.down
                    posy += c.posyD

            p2 = Node(c).pathToNode()

            i = 0
            while i < len(p1) and i < len(p2) and p1[i] == p2[i]:
                i += 1  # set i to minimum index where p1, p2 differ

            for j in range(len(p1) - i):
                self.mster.prev(0)          # go back in p1
            for j in range(i, len(p2)):
                self.mster.next(p2[j], 0)    # step forward in p2

            self.seeCurrent()

        except:
            showwarning(_('Error'), _('SGF Error') + '(onButton1)')

    def next(self, n=0, markCurrent=True):
        res = Cursor.next(self, n)
        if markCurrent:
            self.seeCurrent()
        return res

    def previous(self, markCurrent=1):
        res = Cursor.previous(self)
        if markCurrent:
            self.seeCurrent()
        return res

    def add(self, st, update=True):
        w = self.width
        Cursor.add(self, st)

        if update:
            if not self.currentN.up and not self.width > w:
                self.SGFtreeCanv.mark(self.currentN, self.posx, self.posy)
                self.SGFtreeCanv.link(self.posx, self.posy, 0)
                self.SGFtreeCanv.canvas.lower('lines')
                self.seeCurrent()
            else:
                self.updateTree()

    def game(self, n=0, update=1):
        Cursor.game(self, n)
        self.currentGame = n
        self.SGFtreeCanv.rootnode = self.currentN
        self.updateTree(update)

    def symmetry(self, flip):

        nodelist = [self.root.next]

        while nodelist:
            node = nodelist.pop()

            while node:
                try:
                    d = Node(node)
                    for prop in ['B', 'W', 'AB', 'AW', 'AE', 'CR', 'SQ', 'TR', 'MA', 'TB', 'TW', 'DD', 'L']:
                        if prop in d:
                            d[prop] = [flip(x) for x in d[prop]]

                    for prop in ['LB', 'VW']:
                        if prop in d:
                            d[prop] = [flip(split(x, ':')[0]) + ':' + split(x, ':')[1] for x in d[prop]]
                    for prop in ['LN', 'AR']:
                        if prop in d:
                            d[prop] = [flip(split(x, ':')[0]) + ':' + flip(split(x, ':')[1]) for x in d[prop]]
                except:
                    showwarning(_('Error'), _('SGF Error') + '(symmetry(self, flip))')

                try:
                    if node.down:
                        nodelist.append(node.down)
                    node = node.next
                except:
                    break

    def seeCurrent(self):

        x, y = self.posx, self.posy

        self.SGFtreeCanv.canvas.delete('curr')
        u = self.SGFtreeCanv.UNIT
        self.SGFtreeCanv.canvas.create_oval(x * u + u // 2,
                                            y * u + u // 2,
                                            (x + 1) * u,
                                            (y + 1) * u, fill='', outline='green',
                                            width=5, tags='curr')

        x = (x + .5) * u
        y = (y + .5) * u

        # print 'seecurrent', x, y

        self.SGFtreeCanv.update_idletasks()
        hor = self.SGFtreeCanv.sbar_hor.get()
        vert = self.SGFtreeCanv.sbar_vert.get()

        cv0, cv1 = self.SGFtreeCanv.canvSize

        # print 'x: %1.3f, [%1.3f, %1.3f], y: %1.3f, [%1.3f, %1.3f]' % (x*1.0/cv0, hor[0], hor[1], \
        #                                                               y*1.0/cv1, vert[0], vert[1])

        x1 = (hor[1] - hor[0]) * cv0
        y1 = (vert[1] - vert[0]) * cv1

        if x - 40 < hor[0] * cv0:
            self.SGFtreeCanv.xview('moveto', (x - 50) * 1.0 / cv0)
        elif x + 40 > hor[1] * cv0:
            self.SGFtreeCanv.xview('moveto', (x + 50 - x1) * 1.0 / cv0)

        if y1 < self.SGFtreeCanv.UNIT * 2:
            self.SGFtreeCanv.yview('moveto', y * 1.0 / cv1)
        else:
            if y - 40 < vert[0] * cv1:
                self.SGFtreeCanv.yview('moveto', (y - 50) * 1.0 / cv1)
            elif y + 40 > vert[1] * cv1:
                self.SGFtreeCanv.yview('moveto', (y + 50 - y1) * 1.0 / cv1)

        self.SGFtreeCanv.canvas.tag_raise('curr')

        # print 'x: %1.3f, [%1.3f, %1.3f], y: %1.3f, [%1.3f, %1.3f]' % (x*1.0/self.cv0, hor[0], hor[1], \
        #                                                               y*1.0/self.cv1, vert[0], vert[1])

# ---------------------------------------------------------------------------------------


class Viewer:
    """ This is the main class of v.py. """

    def convCoord(self, x):
        """ This takes coordinates in SGF style (aa - ss),
            and returns the corresponding
            integer coordinates (between 1 and boardsize). """

        try:
            p, q = ord(x[0]) - ord('a'), ord(x[1]) - ord('a')
            if 0 <= p < self.board.boardsize and 0 <= q < self.board.boardsize:
                return (p, q)
            else:
                return 0
        except:
            return 0

    def splitCollection(self):

        if self.cursor.root.numChildren <= 1:
            return

        filename = tkFileDialog.asksaveasfilename(filetypes=[(_('SGF files'), '*.sgf'), (_('All files'), '*')],
                                                  initialdir=self.sgfpath, defaultextension='.sgf')
        if not filename:
            return
        self.sgfpath = os.path.split(filename)[0]

        if filename[-4:] == '.sgf': filename = filename[:-4]

        i = 0

        n = self.cursor.root.next

        while n:
            try:
                f = open('%s%d.sgf' % (filename, i), 'w')
                try:
                    f.write('(' + self.cursor.outputVar(n) + ')')
                except lk.SGFError:
                    showwarning(_('Error'), _('SGF Error in game %d') % i)
                f.close()
            except IOError:
                showwarning(_('Error'), _('I/O Error when writing {0}{1}.sgf').format(filename, i))
                break
            n = n.down
            i += 1

    def mirrorSGF(self, flip):
        self.leaveNode()
        self.currentFileChanged()
        self.cursor.symmetry(flip)
        l = self.cursor.currentNode().pathToNode()
        self.start(0)
        for i in l:
            self.next(i, 0)

        self.cursor.seeCurrent()

    def update_window_title(self):
        if not self.options.doNotChangeWindowTitle.get():
            pw = self.cursor.transcode('PW').replace('\r', '').replace('\n', '')
            pb = self.cursor.transcode('PB').replace('\r', '').replace('\n', '')
            res = self.cursor.transcode('RE').replace('\r', '').replace('\n', '') or '?'
            self.master.title('%s - %s (%s)' % (pw, pb, res[0], ))

    def setup(self, gameNo=0, update=1):
        """ Set up initial position (clear board, put handi stones etc.). """

        if update:
            self.board.clear()
        self.board.delMarks()
        self.board.delLabels()

        if not self.cursor:
            return

        try:
            self.cursor.game(gameNo, update)
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error in game %d in current file.') % gameNo)
            return

        try:
            si = self.cursor.getRootNode(gameNo)['SZ'][0]
            if strip(si) != '19':
                showwarning(_('Error'), _('The board size of this game is not 19x19.'))
                return
        except:
            pass

        # display game name

        gameName = self.currentFile[:15]
        if self.cursor.root.numChildren > 1:
            gameName += '[%d]' % gameNo
        self.gameName.set(gameName)

        self.moveno.set('0')
        self.capW = 0
        self.capB = 0
        self.capVar.set(_('Cap - B: {0}, W: {1}').format(self.capB, self.capW))

        try:
            self.update_window_title()
            if 'AB' in self.cursor.currentNode():
                for x in self.cursor.currentNode()['AB']:
                    self.board.play(self.convCoord(x), 'black')
            if 'AW' in self.cursor.currentNode():
                for x in self.cursor.currentNode()['AW']:
                    self.board.play(self.convCoord(x), 'white')

            if 'B' in self.cursor.currentNode():
                self.board.play(self.convCoord(self.cursor.currentNode()['B'][0]), 'black')
            elif 'W' in self.cursor.currentNode():
                self.board.play(self.convCoord(self.cursor.currentNode()['B'][0]), 'white')

        except lk.SGFError:
            showwarning(_('SGF Error'), _('SGF Error') + '(def setup())')
            self.gameName.set('')
            self.currentFile = ''
            self.cursor = None
            return 0
        else:
            self.board.currentColor = 'black'
            self.modeVar.set('blackwhite')

        try:
            self.displayLabels(self.cursor.currentNode())
            self.markAll()
        except:
            pass
        return 1

    def markAll(self):
        """ Mark all variations for the next move. """

        if not self.cursor:
            return

        try:
            if self.options.showCurrMoveVar.get():
                c = self.cursor.currentNode()
                for color in ['B', 'W']:
                    if color in c and c[color][0] and self.convCoord(c[color][0]):
                        if color == 'B':
                            self.board.placeMark(self.convCoord(c[color][0]), '', 'white', 'small')
                        else:
                            self.board.placeMark(self.convCoord(c[color][0]), '', 'black', 'small')

            if self.cursor.atEnd:
                return

            for i in range(self.cursor.noChildren()):
                c = self.cursor.next(i, 0)

                for color in ['B', 'W']:
                    if color in c:
                        if c[color][0] and self.convCoord(c[color][0]):
                            if self.options.showNextMoveVar.get():
                                self.board.placeMark(self.convCoord(c[color][0]), '', 'black')
                        self.board.currentColor = 'black' if color == 'B' else 'white'

                self.cursor.previous(0)

        except lk.SGFError:
            showwarning(_('SGF Error'), _('SGF Error') + '(def markAll())')
            self.board.delMarks()

        if self.board.currentColor == 'black':
            if self.modeVar.get() == 'white':
                self.board.currentColor = 'white'
            if self.modeVar.get() == 'whiteblack':
                self.modeVar.set('blackwhite')
        elif self.board.currentColor == 'white':
            if self.modeVar.get() == 'black':
                self.board.currentColor = 'black'
            if self.modeVar.get() == 'blackwhite':
                self.modeVar.set('whiteblack')

    def showNextMove(self):
        """ Toggle 'show next move' option. """

        self.board.delMarks()
        self.markAll()

    def passFct(self):
        """ React to pass button: choose the 'pass variation' in the SGF file."""

        if not self.cursor:
            return
        self.leaveNode()

        nM = 'B' if self.modeVar.get()[:5] == 'black' else 'W'

        for i in range(self.cursor.noChildren()):
            try:
                c = self.cursor.next(i)
            except lk.SGFError:
                continue
            if ('B' in c and not self.convCoord(c['B'][0])) or ('W' in c and not self.convCoord(c['W'][0])):  # found
                self.board.delMarks()
                self.board.delLabels()
                self.moveno.set(str(int(self.moveno.get()) + 1))
                if self.guessMode.get():
                    self.guessSuccess()
                self.markAll()
                self.displayNode(c)
                return 1
            else:
                try:
                    self.cursor.previous()
                except lk.SGFError:
                    showwarning(_('Error'), _('Error in SGF file'))
                    break

        # not found

        if self.guessMode.get():
            self.guessFailure('', '')
            return 0

        if self.modeVar.get() == 'blackwhite':
            self.modeVar.set('whiteblack')
        elif self.modeVar.get() == 'whiteblack':
            self.modeVar.set('blackwhite')

        s = ';' + nM + '[]'

        try:
            self.cursor.add(s)
            c = self.cursor.currentNode()
            self.board.delMarks()
            self.board.delLabels()
            self.moveno.set(str(int(self.moveno.get()) + 1))
            self.displayNode(c)
            self.capVar.set(_('Cap - B: {0}, W: {1}').format(self.capB, self.capW))
            self.currentFileChanged()
            self.board.currentColor = self.modeVar.get()[:5]
        except lk.SGFError:
            pass

        return 0

    def gotoMove(self, event):

        x, y = self.board.getBoardCoord((event.x, event.y),
                                        self.board.shadedStoneVar.get())  # if self.board.shadedStoneVar.get(), the position is clearly visible, so we need not be
                                                                          # as strict, how close (event.x, event.y) is to this intersection
        if (not x * y):
            return
        pos = chr(x + ord('a')) + chr(y + ord('a'))

        try:
            c = self.cursor.currentNode()
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error') + '(gotoMove())')
            return

        if ('B' in c and c['B'][0] == pos) or ('W' in c and c['W'][0] == pos):
            return

        found = 0

        if not self.board.getStatus(x, y) == '.':
            i = 0
            n = self.cursor.currentN

            while n.next:
                i += 1
                n = n.next
                c = Node(n)
                if ('B' in c and c['B'][0] == pos) or ('W' in c and c['W'][0] == pos):
                    found = 1
                    break

            if found:
                for j in range(i):
                    self.next(0, 0)

                self.cursor.seeCurrent()
                return

        i = 0
        n = self.cursor.currentN

        while n.previous:
            i += 1
            n = n.previous
            c = Node(n)
            if ('B' in c and c['B'][0] == pos) or ('W' in c and c['W'][0] == pos):
                found = 1
                break

        if found:
            for j in range(i):
                self.prev(0)
            self.cursor.seeCurrent()

    def displayGuessPercentage(self):
        correct = self.dataWindow.guessRightWrong[0]
        total = self.dataWindow.guessRightWrong[0] + self.dataWindow.guessRightWrong[1]
        perc = ('%d%%' % (correct * 100 // total)) if total else '-'
        self.dataWindow.guessModeCanvas.create_text(130, 20, text='%d/%d' % (correct, total), tags='labels')
        self.dataWindow.guessModeCanvas.create_text(130, 40, text=perc, tags='labels')

    def guessSuccess(self):
        self.dataWindow.guessModeCanvas.delete('labels')
        self.dataWindow.guessModeCanvas.create_rectangle(20, 20, 80, 80, fill='green', outline='green', tags='labels')
        self.dataWindow.guessRightWrong[0] += 1
        self.displayGuessPercentage()
        if self.cursor.atEnd:
            self.dataWindow.guessModeCanvas.create_text(
                    50, 50, text='END',
                    font=(self.options.labelFont.get(), self.options.labelFontSize.get() + 10),
                    tags='labels')

    def guessFailure(self, right, pos):
        self.dataWindow.guessModeCanvas.delete('labels')

        if self.cursor.atEnd:
            self.dataWindow.guessModeCanvas.create_rectangle(20, 20, 80, 80, fill='green', tags='labels', outline='green')
            self.displayGuessPercentage()
            self.dataWindow.guessModeCanvas.create_text(
                    50, 50, text='END',
                    font=(self.options.labelFont.get(), self.options.labelFontSize.get() + 10),
                    tags='labels')
            return

        if not right or not pos:
            dx = 50
            dy = 50
            p0 = 40
            p1 = 40
        else:
            dist = int(4 * sqrt((right[0] - pos[0]) * (right[0] - pos[0]) + (right[1] - pos[1]) * (right[1] - pos[1])))

            dx = max(2, dist // 3 + randint(0, dist // 3))
            dy = max(2, dist // 3 + randint(0, dist // 3))

            p0 = right[0] * 4 + 2
            p1 = right[1] * 4 + 2

        self.dataWindow.guessModeCanvas.create_rectangle(p0 - dx + 10, p1 - dy + 10, min(80, p0 + dx) + 10, min(80, p1 + dx) + 10, fill='red', outline='', tags='labels')

        self.dataWindow.guessRightWrong[1] += 1
        self.displayGuessPercentage()

    def update_captures(self, c, undo=False):
        sign = -1 if undo else 1
        if 'B' in c:
            self.capB = self.capB + sign * len(self.board.undostack_top_captures())
        if 'W' in c:
            self.capW = self.capW + sign * len(self.board.undostack_top_captures())
        self.capVar.set(_('Cap - B: {0}, W: {1}').format(self.capB, self.capW))

    def nextMove(self, p):
        """ React to mouse-click on the board"""

        self.leaveNode()

        # print p
        x, y = p

        if self.modeVar.get() in ['black', 'white'] and not self.guessMode.get():
            nM = 'AB' if self.modeVar.get() == 'black' else 'AW'
            pos = chr(x + ord('a')) + chr(y + ord('a'))

            try:
                cn = self.cursor.currentNode()
                if 'AB' in cn or 'AW' in cn or 'AE' in cn:  # do not start new Node
                    if 'AE' in cn and pos in cn['AE']:
                        ll = cn['AE']
                        ll.remove(pos)
                        if ll:
                            cn['AE'] = ll
                        else:
                            cn.del_property_value('AE')
                    elif (not nM in cn) or (not pos in cn[nM]):
                        cn.add_property_value(nM, [pos, ])

                    if nM == 'AB':
                        self.board.AB([p])
                    if nM == 'AW':
                        self.board.AW([p])
                    self.board.currentColor = self.modeVar.get()

                else:
                    s = ';' + nM + '[' + pos + ']'
                    self.cursor.add(s)
                    c = self.cursor.currentNode()

                    self.board.delMarks()
                    self.board.delLabels()

                    self.moveno.set(str(int(self.moveno.get()) + 1))

                    self.displayNode(c)
                    self.board.currentColor = self.modeVar.get()

            except lk.SGFError:
                showwarning(_('Error'), _('SGF Error') + '(nextMove())')

            self.currentFileChanged()

            return 0

        if self.modeVar.get() == 'blackwhite':
            nM = 'B'
        elif self.modeVar.get() == 'whiteblack':
            nM = 'W'

        done = 0
        right_pos = ''  # (for guess mode)
        for i in range(self.cursor.noChildren()):             # look for the move in the SGF file
            if (not done):
                try:
                    c = self.cursor.next(i, 0)
                    if i == 0:
                        if nM in c:
                            right_pos = self.convCoord(c[nM][0])
                except:
                    continue
                if nM in c and self.convCoord(c[nM][0]) == p:  # found
                    self.cursor.seeCurrent()
                    self.board.delMarks()
                    self.board.delLabels()
                    done = 1
                    if self.guessMode.get():
                        self.guessSuccess()

                    if self.modeVar.get() == 'blackwhite':
                        self.modeVar.set('whiteblack')
                    elif self.modeVar.get() == 'whiteblack':
                        self.modeVar.set('blackwhite')

                    self.moveno.set(str(int(self.moveno.get()) + 1))

                    self.displayNode(c)
                    self.update_captures(c)
                else:
                    try:
                        self.cursor.previous(0)
                    except lk.SGFError:
                        showwarning(_('Error'), _('Error in SGF file'))
                        break

        if not done:
            if self.guessMode.get():
                self.guessFailure(right_pos, p)
                return 0

            # print 'play', x, y
            if self.modeVar.get() == 'blackwhite':
                self.modeVar.set('whiteblack')
            elif self.modeVar.get() == 'whiteblack':
                self.modeVar.set('blackwhite')

            s = ';' + nM + '[' + chr(x + ord('a')) + chr(y + ord('a')) + ']'

            try:
                self.cursor.add(s)
                c = self.cursor.currentNode()

                self.board.delMarks()
                self.board.delLabels()

                self.moveno.set(str(int(self.moveno.get()) + 1))

                self.displayNode(c)
                self.update_captures({nM: 1})
            except lk.SGFError:
                showwarning(_('Error'), _('SGF Error') + '(nextMove, 2)')

            self.currentFileChanged()

        self.markAll()

        return done

    def prev(self, markCurrent=1):
        """ Go back one move. """

        if not self.cursor.atStart:
            self.leaveNode()

            try:
                c = self.cursor.currentNode()
                if ('B' in c and c['B'][0]) or ('W' in c and c['W'][0]):
                    self.update_captures(c, undo=True)
                    self.board.undo()

                for t in ['AE', 'AW', 'AB']:
                    if t in c:
                        self.board.undo(len(c[t]), 0)

                c = self.cursor.previous(markCurrent)
                self.moveno.set(str(int(self.moveno.get()) - 1))

                self.board.delLabels()
                self.board.delMarks()

                self.markAll()
                self.modeVar.set('blackwhite' if self.board.currentColor == 'black' else 'whiteblack')
                self.displayLabels(c)
            except:
                pass

    def next(self, n=0, markCurrent=True):
        """Go to (n-th child of) next move."""

        if not self.cursor.atEnd:
            self.leaveNode()

            try:
                c = self.cursor.next(n, markCurrent)
            except lk.SGFError:
                return 0  # failure

            self.moveno.set(str(int(self.moveno.get()) + 1))

            self.board.delMarks()
            self.board.delLabels()

            self.displayNode(c)
            self.update_captures(c)

            self.markAll()
            self.modeVar.set('blackwhite' if self.board.currentColor == 'black' else 'whiteblack')

            return 1  # success

    def upVariation(self, event):
        if self.cursor.currentN.up:
            i = self.cursor.currentN.level
            self.prev(0)
            self.next(i - 1)

    def downVariation(self, event):
        if self.cursor.currentN.down:
            i = self.cursor.currentN.level
            self.prev(0)
            self.next(i + 1)

    def displayNode(self, c):
        """Display the stones played in the current node,
           and call displayLabels(). """

        if 'AB' in c and c['AB'][0]:
            self.board.AB([self.convCoord(p) for p in c['AB']])
            self.board.currentColor = 'black' if self.board.currentColor == 'white' else 'white'
        if 'AW' in c and c['AW'][0]:
            self.board.AW([self.convCoord(p) for p in c['AW']])
            self.board.currentColor = 'black' if self.board.currentColor == 'white' else 'white'
        if 'AE' in c and c['AE'][0]:
            self.board.AE([self.convCoord(p) for p in c['AE']])

        if 'B' in c and c['B'][0]:
            p = self.convCoord(c['B'][0])
            # print 'dN, play B', p
            if not p or not self.board.play(p, 'black'):
                self.board.undostack_append_pass()
        elif 'W' in c and c['W'][0]:
            p = self.convCoord(c['W'][0])
            if not p or not self.board.play(p, 'white'):
                self.board.undostack_append_pass()

        self.displayLabels(c)

    def displayLabels(self, c):
        """ Display the labels in the current node."""

        self.comments.delete('1.0', END)
        self.dataWindow.comments.configure(text_font=self.standardFont)
        if 'C' in c:
            comment_text = self.cursor.transcode('C', c).splitlines()
            if comment_text:
                if comment_text[0] == '@@monospace':
                    self.dataWindow.comments.configure(text_font=self.monospaceFont)

                self.comments.insert('1.0', '\n'.join(comment_text))

        for type in ['CR', 'MA', 'SQ', 'TR']:
            if type in c and c[type][0]:
                for p in c[type]:
                    self.board.placeLabel(self.convCoord(p), type)

        if 'LB' in c and c['LB'][0]:
            for p1 in c['LB']:
                p, text = split(p1, ':')
                self.board.placeLabel(self.convCoord(p), 'LB', text)

    def next10(self):
        for i in range(10):
            self.next(0, 0)
        self.cursor.seeCurrent()

    def prev10(self):
        for i in range(10):
            self.prev(0)
        self.cursor.seeCurrent()

    def end(self):
        """ Go to end of game. """
        if not self.cursor:
            return
        while not self.cursor.atEnd and self.next(0, 0):
            pass
        self.cursor.seeCurrent()

    def start(self, update=1):
        """ Go to beginning of game."""
        if not self.cursor:
            return
        if update:
            self.leaveNode()
        self.comments.delete('1.0', END)
        self.board.delMarks()
        self.board.delLabels()
        self.board.currentColor = 'black'
        self.modeVar.set('blackwhite')
        self.setup(self.cursor.currentGame)
        self.cursor.seeCurrent()

    def jumpToNode(self, moveno):
        try:
            ctr = 0
            while ctr < len(moveno):
                mn = moveno[ctr]
                if mn == 0:
                    break
                i = 1
                while i < mn:
                    if self.cursor.atEnd:
                        break
                    i += 1
                    self.next(0, 0)
                if not self.cursor.atEnd:
                    if ctr < len(moveno) - 1:
                        self.next(n=moveno[ctr + 1], markCurrent=False)
                        ctr += 2
                    else:
                        self.next(markCurrent=False)
                        break
                else:
                    break
        except:
            showwarning(_('Error'), _('SGF Error'))
        self.cursor.seeCurrent()

    def labelClick(self, event):
        x, y = self.board.getBoardCoord((event.x, event.y), 1)
        if x == -1 or y == -1:
            return
        pos = chr(x + ord('a')) + chr(y + ord('a'))

        t = self.options.labelType.get()

        # delete stones

        try:
            if t == 'DEL ST':
                if self.board.getStatus(x, y) == ' ':
                    return
                if 'AB' in self.cursor.currentNode() or 'AW' in self.cursor.currentNode() or 'AE' in self.cursor.currentNode():
                    removed = False
                    for key in ['AW', 'AB']:
                        if key in self.cursor.currentNode() and pos in self.cursor.currentNode()[key]:
                            ll = list(self.cursor.currentNode()[key])
                            ll.remove(pos)
                            self.cursor.currentNode()[key] = ll
                            removed = True
                            if not self.cursor.currentNode()[key]:
                                del self.cursor.currentNode()[key]
                    if not removed:
                        self.cursor.currentN.add_property_value('AE', (pos, ))
                    self.board.remove((x, y), removed)
                    self.board.currentColor = self.modeVar.get()[:5]
                else:
                    s = ';AE[' + pos + ']'
                    self.cursor.add(s)
                    c = self.cursor.currentNode()
                    self.board.delMarks()
                    self.board.delLabels()
                    self.moveno.set(str(int(self.moveno.get()) + 1))
                    self.displayNode(c)

                return

            # labels

            # check if there is a label at current position (and delete it, if so)

            cn = self.cursor.currentNode()
            for tt in ['TR', 'SQ', 'CR', 'MA']:
                if tt in cn and pos in cn[tt]:
                    pr = list(cn[tt])
                    pr.remove(pos)
                    if pr:
                        cn[tt] = pr
                    else:
                        del cn[tt]
                    self.board.placeLabel((x, y), tt)
                    return

            if 'LB' in cn:
                for item in cn['LB']:
                    if split(item, ':')[0] == pos:
                        pr = list(cn['LB'])
                        pr.remove(item)
                        if pr:
                            cn['LB'] = pr
                        else:
                            del cn['LB']
                        self.board.placeLabel((x, y), 'LB', '')
                        return

            def place_first_unused(cn, labels):
                if 'LB' in cn:
                    for item in cn['LB']:
                        p, t = split(item, ':')
                        try:
                            labels.remove(t)
                        except ValueError:
                            pass
                    text = labels[0] if labels else '?'
                    cn.add_property_value('LB', [pos+':'+text, ])
                else:
                    text = labels[0]
                    cn['LB'] = [pos+':'+text]
                self.board.placeLabel((x,y), 'LB', text)

            if t == '12n': # place 'number' label
                place_first_unused(cn, [str(i) for i in range(1, 400)])
            elif t == 'ABC':
                place_first_unused(cn, list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
            elif t == 'abc':
                place_first_unused(cn, list('abcdefghijklmnopqrstuvwxyz'))
            else:
                text = ''
                if cn.has_key(t):
                    cn.add_property_value(t, (pos, ))
                else:
                    cn[t] = [pos]
                self.board.placeLabel((x,y), t, text)

        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error') + '(def labelClick())')

        self.currentFileChanged()

    def delVar(self):
        try:
            n = self.cursor.currentN
            self.prev()
            self.cursor.delVariation(n)

            self.board.delMarks()
            self.markAll()

            self.cursor.updateTree()
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error') + '(delVar)')
        self.currentFileChanged()

    def newGame(self):
        """Add a new game tree to the current collection."""
        self.leaveNode()
        self.comments.delete('1.0', END)
        self.currentFileChanged()

        p = self.cursor.currentNode().pathToNode()
        self.cursor.currentN = self.cursor.root
        self.cursor.add(';GM[1]FF[4]SZ[19]AP[Kombilo]')
        self.cursor.currentN.previous = None
        self.dataWindow.gamelist.insert(END, '[%d]' % (self.cursor.root.numChildren - 1))

        if self.dataWindow.gamelist.list.curselection():
            index = int(self.dataWindow.gamelist.list.curselection()[0])
            self.dataWindow.gamelist.list.select_clear(index)
        self.dataWindow.gamelist.list.select_set(END)
        self.dataWindow.gamelist.list.see(END)
        self.dataWindow.updateGameInfo(self.cursor)

        self.changeCurrentGame(None, self.cursor.root.numChildren - 1, p)

    def delGame(self):
        """Add currently selected game from collection."""

        if not self.dataWindow.gamelist.list.curselection():  # should actually never happen!
            return

        self.comments.delete('1.0', END)
        self.currentFileChanged()
        index = int(self.dataWindow.gamelist.list.curselection()[0])

        n = self.cursor.root.next
        for i in range(index):
            n = n.down

        try:
            self.cursor.delVariation(n)
        except:
            pass

        if n.up:
            n.up.down = n.down
        else:
            self.cursor.root.next = n.down

        if n.down:
            n.down.up = n.up

        self.cursor.root.numChildren -= 1

        self.dataWindow.gamelist.delete(index)

        d = self.filelist[self.currentFileNum][4]

        if index in d:
            del d[index]
        new_d = {}
        for i in d:
            if type(i) != type(0):
                continue                 # because of 'currentgame'
            if i > index:
                new_d[i - 1] = d[i]
            else:
                new_d[i] = d[i]

        self.filelist[self.currentFileNum][4] = new_d

        if index == self.cursor.root.numChildren and index != 0:
            index -= 1

        self.cursor.currentGame = -1  # for changeCurrentGame

        if self.cursor.root.numChildren == 0:
            self.newGame()
            return

        self.changeCurrentGame(None, index, None, 1)

        for i in range(index, self.cursor.root.numChildren):

            s = '[%d]' % i
            t = self.dataWindow.gamelist.list.get(i)
            l = split(t, ']')
            l[0] = s
            self.dataWindow.gamelist.delete(i)
            self.dataWindow.gamelist.insert(i, join(l, ''))

        self.dataWindow.gamelist.list.select_set(index)
        self.dataWindow.gamelist.list.see(index)
        self.dataWindow.updateGameInfo(self.cursor)

    def currentFileChanged(self, removeMark=0):
        """This method is called, when the current file is changed (then it puts a * before the file name
        of the current SGF file), resp. when the file is saved (then the * is removed). """

        index = self.currentFileNum

        s = self.dataWindow.filelist.list.get(index)

        if removeMark:
            if s[0:2] != '* ':
                return
            self.dataWindow.filelist.delete(index)
            self.dataWindow.filelist.insert(index, s[2:])
            self.dataWindow.filelist.list.select_set(index)
        else:
            if s[0] == '*':
                return
            self.dataWindow.filelist.delete(index)
            self.dataWindow.filelist.insert(index, '* ' + s)
            self.dataWindow.filelist.list.select_set(index)

    def newFile(self, cursor=None):
        sgf = cursor.output() if cursor else '(;GM[1]FF[4]SZ[19]AP[Kombilo])' # TODO boardsize
        c = EnhancedCursor(sgf, self.comments, self.dataWindow.SGFtreeC, self)

        if self.dataWindow.filelist.list.curselection():
            index = int(self.dataWindow.filelist.list.curselection()[0])
            self.dataWindow.filelist.list.select_clear(index)

        self.filelist.insert(0, [_('New'), '', (), c, {}])
        self.currentFileNum += 1
        self.dataWindow.filelist.insert(0, _('New'))
        self.changeCurrentFile(None, 0)

    def openFile(self, path=None, filename=None, do_not_change_sgfpath=False, encoding=''):
        """ Read an SGF file given by filename (if None, ask for a filename). """

        if not path:
            path = '.'

        if not filename:
            r = tkFileDialog.askopenfilename(filetypes=[(_('SGF files'), '*.sgf'), (_('All files'), '*')], initialdir=self.sgfpath)
            if r:
                path, filename = os.path.split(r)
            else:
                return
        if filename:
            try:
                f = open(os.path.join(path, filename))
                s = f.read()
                f.close()
            except IOError:
                showwarning(_('Open file'), _('Cannot open this file\n'))
                return 0
            else:
                if not s:
                    return 0
                if not do_not_change_sgfpath:
                    self.sgfpath = path

                try:
                    c = EnhancedCursor(s, self.comments, self.dataWindow.SGFtreeC, self)

                except lk.SGFError:
                    showwarning(_('Parsing Error'), _('Error in SGF file!'))
                    return 0

                self.dataWindow.filelist.insert(0, filename)
                self.filelist.insert(0, [filename, os.path.join(path, filename), (), c, {}])
                self.currentFileNum += 1
                self.board.clear()
                self.board.delLabels()
                self.board.delMarks()

                self.gameName.set('')

                self.board.state('normal', self.nextMove)
                self.master.update_idletasks()

                self.changeCurrentFile(None, 0)

    def delFile(self):
        if not self.dataWindow.filelist.list.curselection():  # should actually never happen!
            return

        index = int(self.dataWindow.filelist.list.curselection()[0])

        s = self.dataWindow.filelist.list.get(index)

        if self.options.confirmDelete.get() and s[0:2] == '* ':
            if not askokcancel(_('Confirm deletion'), _('There are unsaved changes. Discard them?')):
                return

        del self.filelist[index]

        self.dataWindow.filelist.list.select_clear(index)
        self.dataWindow.filelist.delete(index)

        if index == len(self.filelist):
            index -= 1

        if index == -1:                    # file list is empty now, so create a new game
            self.currentFileNum = -2
            self.newFile()
            return 1

        self.currentFileNum = -1
        self.changeCurrentFile(None, index)

        return 1

    def modeChange(self):
        self.board.currentColor = self.modeVar.get()[:5]

    def leaveNode(self):
        """This method should be called before leaving the current node in the
        SGF file. It will take care of saving the changes (currently that
        means: changes to the comments) to the SGF file."""

        if not self.cursor:
            return

        s = strip(self.comments.get('1.0', END))
        changed = False

        try:
            d = self.cursor.currentNode()
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error') + '(leaveNode())')
            return

        if 'C' in d:
            if strip(d['C'][0]) != s:
                d['C'] = [s]
                changed = True
        else:
            if s:
                d['C'] = [s]
                changed = True

        if changed:
            self.currentFileChanged()

    def changeCurrentGame(self, event, index=-1, p=None, no_leavenode=0):

        if index == -1:
            index = self.dataWindow.gamelist.list.nearest(event.y)

        if index == -1:
            return

        if not event:
            if not self.dataWindow.gamelist.list.curselection():
                self.dataWindow.gamelist.list.select_set(index)
                self.dataWindow.gamelist.list.see(index)
            elif index != int(self.dataWindow.gamelist.list.curselection()[0]):
                self.dataWindow.gamelist.list.select_clear(self.dataWindow.gamelist.list.curselection())
                self.dataWindow.gamelist.list.select_set(index)
                self.dataWindow.gamelist.list.see(index)

        if 0 <= index <= self.cursor.root.numChildren and index != self.cursor.currentGame:
            filelistIndex = self.currentFileNum
            if self.cursor.currentGame != -1:           # cf. self.changeCurrentFile
                self.filelist[filelistIndex][4][self.cursor.currentGame] = p or self.cursor.currentNode().pathToNode()
                                                                         # cf. self.newGame
            if not no_leavenode:
                self.leaveNode()
                self.comments.delete('1.0', END)
            self.setup(index)
            if index in self.filelist[filelistIndex][4]:
                for i in self.filelist[filelistIndex][4][index]:
                    self.next(i, 0)
                self.cursor.seeCurrent()

        self.dataWindow.updateGameInfo(self.cursor)

    def changeCurrentFile(self, event, index=-1):

        if index == -1:
            index = self.dataWindow.filelist.list.nearest(event.y)

        if index == -1:
            return

        if not event:
            if not self.dataWindow.filelist.list.curselection():
                self.dataWindow.filelist.list.select_set(index)
                self.dataWindow.filelist.list.see(index)
            elif index != int(self.dataWindow.filelist.list.curselection()[0]):
                self.filelist[int(self.dataWindow.filelist.list.curselection()[0])][4]['currentGame'] = self.cursor.currentGame
                self.dataWindow.filelist.list.select_clear(self.dataWindow.filelist.list.curselection())
                self.dataWindow.filelist.list.select_set(index)
                self.dataWindow.filelist.list.see(index)

        if 0 <= index < len(self.filelist):

            if self.currentFileNum != -1:      # cf. self.delFile
                self.filelist[self.currentFileNum][4]['currentGame'] = self.cursor.currentGame
                self.filelist[self.currentFileNum][4][self.cursor.currentGame] = self.cursor.currentNode().pathToNode()

            self.currentFileNum = index
            self.currentFile = self.filelist[index][0]
            self.leaveNode()
            self.comments.delete('1.0', END)
            self.cursor = self.filelist[index][3]

            self.cursor.updateGamelist()
            self.cursor.currentGame = -1  # to get around 'index != self.cursor.currentGame' test in self.changeCurrentGame
            if 'currentGame' in self.filelist[index][4]:
                self.changeCurrentGame(None, self.filelist[index][4]['currentGame'], None, 1)
            else:
                self.changeCurrentGame(None, 0, None, 1)

    def saveSGFfile(self):
        if not self.cursor or not self.dataWindow.filelist.list.curselection():
            return
        index = int(self.dataWindow.filelist.list.curselection()[0])

        filename = self.filelist[index][1]
        if not filename:
            self.saveasSGFfile()
            return

        self.leaveNode()

        try:
            sgf_out = self.cursor.output()
            file = open(filename, 'w')
            file.write(sgf_out)
            file.close()
        except IOError:
            showwarning(_('Error'), _('I/O Error'))
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error') + '(saveSGFfile)')
        else:
            self.currentFileChanged(1)

    def saveasSGFfile(self):
        if not self.cursor or not self.dataWindow.filelist.list.curselection():
            return

        self.leaveNode()

        f = tkFileDialog.asksaveasfilename(filetypes=[(_('SGF files'), '*.sgf'), (_('All files'), '*')],
                                           initialdir=self.sgfpath, defaultextension='.sgf')

        if not f:
            return
        try:
            sgf_out = self.cursor.output()
            file = open(f, 'w')
            file.write(sgf_out)
            file.close()
        except IOError:
            showwarning(_('I/O Error'), _('Could not write to file ') + f)
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error') + '(saveasSGFfile)')

        else:
            self.sgfpath, self.currentFile = os.path.split(f)
            self.gameName.set(self.currentFile[:15])

            index = int(self.dataWindow.filelist.list.curselection()[0])
            self.filelist[index][0] = self.currentFile
            self.filelist[index][1] = f
            self.dataWindow.filelist.delete(index)
            self.dataWindow.filelist.insert(index, self.currentFile)
            self.dataWindow.filelist.list.select_set(index)

        self.master.focus()

    def exportSGF(self):
        self.leaveNode()
        try:
            t = self.cursor.exportGame()
            TextEditor(t, self.sgfpath, self.monospaceFont)
        except lk.SGFError:
            showwarning(_('Error'), _('SGF Error'))

    def quit(self):
        """ Exit the program. """

        for i in range(len(self.filelist)):
            s = self.dataWindow.filelist.list.get(i)
            if self.options.confirmDelete.get() and s[0:2] == '* ':
                if not askokcancel(_('Confirm deletion'), _('There are unsaved changes. Discard them?')):
                    return
                else:
                    break

        try:
            c = self.config
            c['main']['version'] = 'kombilo%s' % KOMBILO_VERSION
            c['main']['sgfpath'] = self.sgfpath
            self.saveOptions(c['options'])
            c.filename = os.path.join(get_configfile_directory(), 'kombilo.cfg')
            c.write()
        except IOError:
            showwarning(_('I/O Error'), _('Could not write kombilo.cfg.'))

        self.master.destroy()

    def saveOptions(self, d):
        """ Save options to the dictionary d. """
        self.options.windowGeom.set(self.master.geometry())
        self.options.dataWindowGeometry.set(self.dataWindow.get_geometry())
        self.options.sashPos.set(self.mainframe.sash_coord(0)[0])

        self.options.saveToDisk(d)

    def loadOptions(self, d):
        """ Load options from dictionary d. """
        self.options.loadFromDisk(d)

    def get_config_obj(self):
        defaultfile = pkg_resources.resource_stream(__name__, 'default.cfg')
        c = ConfigObj(infile=defaultfile, encoding='utf8', default_encoding='utf8')
        defaultfile.close()

        config_path = os.path.join(get_configfile_directory(), 'kombilo.cfg')
        if os.path.exists(config_path):
            configfile = open(config_path)
            c.merge(ConfigObj(infile=configfile, encoding='utf8', default_encoding='utf8'))
            configfile.close()
        return c

    def edit_options(self):
        self.saveOptions(self.config['options'])
        oe = OptionEditor(self.config)
        self.loadOptions(self.config['options'])
        self.initFonts()
        self.board.resize()

    def helpDocumentation(self):
        try:
            webbrowser.open('http://dl.u-go.net/kombilo/doc/', new=1)
        except:
            showwarning(_('Error'), _('Failed to open the web browser.\nYou can find the documentation at') + ' http://dl.u-go.net/kombilo/doc/')

    def helpAbout(self):
        """ Display the 'About ...' window with some basic information. """

        t = _('v.py - written by Ulrich Goertz (ug@geometry.de)') + '\n\n'
        t = t + _('v.py is a program to display go game records in SGF format.') + '\n'
        t = t + _('It comes together with the go database program Kombilo.') + '\n'

        t = t + _('v.py is free software; for more information see the documentation.') + '\n\n'

        window = Toplevel()
        window.title(_('About v.py ...'))

        text = Text(window, height=15, width=60, relief=FLAT, wrap=WORD)
        text.insert(1.0, t)

        text.config(state=DISABLED)
        text.pack()

        b = Button(window, text=_("OK"), command=window.destroy)
        b.pack(side=RIGHT)

        window.update_idletasks()

        window.focus()
        window.grab_set()
        window.wait_window()

    def helpLicense(self):
        """ Display the GNU General Public License. """
        try:
            t = 'v.py\n (C) Ulrich Goertz (ug@geometry.de), 2001-2012.\n'
            t = t + '------------------------------------------------------------------------\n\n'
            t = t + pkg_resources.resource_string(__name__, 'license.rst')
        except IOError:
            t = _('v.py was written by') + ' Ulrich Goertz (ug@geometry.de).\n'
            t += _('It is open source software, published under the MIT License.')
            t += _('See the documentation for more information. ')
            t += _('This program is distributed WITHOUT ANY WARRANTY!') + '\n\n'
        self.textWindow(t, 'v.py license')

    def textWindow(self, t, title='', grab=1):
        """ Open a window and display the text in the string t.
            The window has the title title, and grabs the focus if grab==1. """

        window = Toplevel()
        window.title(title)
        text = ScrolledText(window, height=25, width=80, relief=FLAT, wrap=WORD)
        text.insert(1.0, t)

        text.config(state=DISABLED)
        text.pack()

        b = Button(window, text=_("OK"), command=window.destroy)
        b.pack(side=RIGHT)

        window.update_idletasks()
        if grab:
            window.focus()
            window.grab_set()
            window.wait_window()

    def gameinfoOK(self):
        keylist = ['PB', 'BR', 'PW', 'WR', 'EV', 'RE', 'DT', 'KM']
        for key in keylist:
            value = self.gameinfoVars[key].get()
            if type(value) == type(u''):
                try:
                    value = value.encode('utf-8', 'ignore')
                except:
                    pass
            self.gameinfoDict[key] = [value]

        value = strip(self.gameinfoGCText.get('1.0', END))
        if type(value) == type(u''):
            try:
                value = value.encode('utf-8', 'ignore')
            except:
                pass
        self.gameinfoDict['GC'] = [value]
        # print self.gameinfoDict

        for key in keylist + ['GC']:
            if not strip(self.gameinfoDict[key][0]):
                del self.gameinfoDict[key]

        s = self.gameinfoOthersText.get('1.0', END)
        try:
            s = s.encode('utf-8', 'ignore')
        except:
            pass
        try:
            # print "d =", s
            cc = Cursor(('(;' + s + ')'), 1)
            d = cc.getRootNode(0)
            # print 'd.keys'
            # print d.keys()
            for k in d.keys():
                self.gameinfoDict[k] = d[k]

            for k in self.gameinfoDict.keys():
                if (not k in keylist + ['GC']) and (not k in d.keys()):
                    del self.gameinfoDict[k]

        except:
            showwarning(_('SGF Error'), _("Parse error in 'Other SGF tags'"))
        else:
            if not self.returnChanges:
                self.currentFileChanged()
            self.gameinfoWindow.destroy()
        self.update_window_title()

    def gameinfoCancel(self):
        self.gameinfoDict = None
        self.gameinfoWindow.destroy()

    def gameinfo(self, data=None):
        """ Open window with the game info of the current game.

        self.gameinfoDict is a dictionary with the SGF tags of the root node of the corresponding game, in utf-8.
        """

        if not data and not self.cursor:
            return

        if not data:
            try:
                self.gameinfoDict = self.cursor.getRootNode(self.cursor.currentGame)
            except:
                showwarning(_('Error'), _('SGF Error') + '(gameinfo)')
                return
            self.returnChanges = 0
        else:
            self.gameinfoDict = data
            self.returnChanges = 1

        window = Toplevel()
        window.transient(self.master)
        window.protocol('WM_DELETE_WINDOW', self.gameinfoCancel)
        self.gameinfoWindow = window
        window.title(_('Game Info'))

        keylist = ['GC', 'PB', 'BR', 'PW', 'WR', 'EV', 'RE', 'DT', 'KM']

        if 'GC' in self.gameinfoDict and self.options.removeCarriageReturn.get():
            self.gameinfoDict['GC'][0] = replace(self.gameinfoDict['GC'][0], '\r', '')

        self.gameinfoVars = {}
        for key in keylist:
            self.gameinfoVars[key] = StringVar()
            if not (key in self.gameinfoDict and self.gameinfoDict[key]):
                self.gameinfoVars[key].set('')
            else:
                self.gameinfoVars[key].set(self.gameinfoDict[key][0])

        self.gameinfoVars['others'] = StringVar()
        oth = ''
        for key in self.gameinfoDict.keys():
            if key not in keylist:
                oth += key + '[' + join([lk.SGFescape(s.encode('utf-8')) for s in self.gameinfoDict[key]], '][') + ']\n'
        self.gameinfoVars['others'].set(oth)

        f = Frame(window)
        f.pack(side=TOP, anchor=W)
        Label(f, text='White:', justify=LEFT).grid(row=0, column=0, sticky=W)
        Entry(f, width=30, textvariable=self.gameinfoVars['PW']).grid(row=0, column=1)
        Entry(f, width=5, textvariable=self.gameinfoVars['WR']).grid(row=0, column=2)

        Label(f, text='Black:', justify=LEFT).grid(row=1, column=0, sticky=W)
        Entry(f, width=30, textvariable=self.gameinfoVars['PB']).grid(row=1, column=1)
        Entry(f, width=5, textvariable=self.gameinfoVars['BR']).grid(row=1, column=2)

        i = 2
        for key, text in [('EV', 'Event'), ('RE', 'Result'), ('DT', 'Date'),
                          ('KM', 'Komi')]:
            Label(f, text=text + ':').grid(row=i, column=0, sticky=W)
            Entry(f, width=35, textvariable=self.gameinfoVars[key]).grid(row=i, column=1, columnspan=2, sticky=W + E)
            i += 1

        Label(window, text=_('Game Comment: ')).pack(anchor=W)
        self.gameinfoGCText = ScrolledText(window, height=5, width=40, relief=SUNKEN, wrap=WORD)
        self.gameinfoGCText.pack(expand=YES, fill=BOTH)
        self.gameinfoGCText.insert(END, self.gameinfoVars['GC'].get())

        Label(window, text=_('Other SGF tags: ')).pack(anchor=W)
        self.gameinfoOthersText = ScrolledText(window, height=5, width=40, relief=FLAT, wrap=WORD)
        self.gameinfoOthersText.pack(expand=YES, fill=BOTH)
        self.gameinfoOthersText.insert(END, self.gameinfoVars['others'].get())

        Button(window, text=_('Cancel'), command=self.gameinfoCancel).pack(side=RIGHT)
        Button(window, text=_("OK"), command=self.gameinfoOK).pack(side=RIGHT)

        window.update_idletasks()
        window.focus()
        window.grab_set()
        window.wait_window()

        if self.returnChanges:
            return self.gameinfoDict
        elif not self.gameinfoDict is None:
            self.cursor.updateRootNode(self.gameinfoDict, self.cursor.currentGame)
            d = self.gameinfoDict
            s = '[%d] %s - %s' % (self.cursor.currentGame, self.cursor.transcode('PW', d), self.cursor.transcode('PB', d))
            if 'RE' in d:
                s += ' (%s)' % self.cursor.transcode('RE', d)

            self.dataWindow.gamelist.delete(self.cursor.currentGame)
            self.dataWindow.gamelist.insert(self.cursor.currentGame, s)
            self.dataWindow.gamelist.list.select_set(self.cursor.currentGame)
            self.dataWindow.updateGameInfo(self.cursor)

    def toggleCoordinates(self):
        if self.options.showCoordinates.get():
            self.board.coordinates = 1
            self.board.resize()
        else:
            self.board.coordinates = 0
            self.board.resize()

    def initFonts(self):
        self.monospaceFont = tkFont.Font(
                family=self.options.monospaceFont.get(),
                size=self.options.monospaceFontSize.get(),
                weight=self.options.monospaceFontWeight.get())
        self.standardFont = tkFont.Font(
                family=self.options.standardFont.get(),
                size=self.options.standardFontSize.get(),
                weight=self.options.standardFontWeight.get())
        self.labelFont = tkFont.Font(
                family=self.options.labelFont.get(),
                size=self.options.labelFontSize.get(),
                weight=self.options.labelFontWeight.get())
        self.smallFont = tkFont.Font(
                family=self.options.smallFont.get(),
                size=self.options.smallFontSize.get(),
                weight=self.options.smallFontWeight.get())
        self.boldFont = tkFont.Font(
                family=self.options.standardFont.get(),
                size=self.options.standardFontSize.get(),
                weight='bold')
        defaultfont = tkFont.nametofont('TkDefaultFont')
        defaultfont.configure(size=self.options.standardFontSize.get())


    def initMenus(self):

        menu = Menu(self.master)
        self.master.config(menu=menu)

        # -------------- FILE -------------------
        self.filemenu = Menu(menu)
        menu.add_cascade(get_addmenu_options(label=_('_File'), menu=self.filemenu))
        self.filemenu.add_command(get_addmenu_options(label=_('_New SGF'), command=self.newFile))
        self.filemenu.add_command(get_addmenu_options(label=_('_Open SGF'), command=self.openFile))
        self.filemenu.add_command(get_addmenu_options(label=_('_Save SGF'), command=self.saveSGFfile))
        self.filemenu.add_command(get_addmenu_options(label=_('Save SGF _as'), command=self.saveasSGFfile))
        self.filemenu.add_command(label=_('Export SGF source'), command=self.exportSGF)

        self.filemenu.add_separator()
        self.filemenu.add_command(get_addmenu_options(label=_('E_xit'), command=self.quit))

        # --------------- EDIT ------------------
        self.editmenu = Menu(menu)
        menu.add_cascade(get_addmenu_options(label=_('_Edit'), menu=self.editmenu))
        self.editmenu.add_command(get_addmenu_options(label=_('Mirror _vertically'), command=lambda self=self, flip=flip_mirror1: self.mirrorSGF(flip)))
        self.editmenu.add_command(get_addmenu_options(label=_('Mirror _diagonally'), command=lambda self=self, flip=flip_mirror2: self.mirrorSGF(flip)))
        self.editmenu.add_command(get_addmenu_options(label=_('_Rotate'), command=lambda self=self, flip=flip_rotate: self.mirrorSGF(flip)))

        ctrlclickmenu = Menu(self.editmenu)
        self.editmenu.add_cascade(label=_('Ctrl-Click behavior'), menu=ctrlclickmenu)
        for text, value in [(_('_Delete stone'), 'DEL ST', ), (_('_Triangle label'), 'TR', ), (_('_Square label'), 'SQ', ), (_('_Upper case letter'), 'ABC', ),
                            (_('_Lower case letter'), 'abc', ), (_('_Number label'), '12n', ), ]:
            ctrlclickmenu.add_radiobutton(get_addmenu_options(label=text, variable=self.options.labelType, value=value))

        # -------------- PRACTICE ------------------

        self.practicemenu = Menu(menu)
        menu.add_cascade(get_addmenu_options(label=_('_Practice'), menu=self.practicemenu))
        self.practicemenu.add_checkbutton(get_addmenu_options(label=_('_Guess mode'), variable=self.guessMode, command=self.dataWindow.toggleGuessMode))

        # -------------- OPTIONS -------------------
        self.optionsmenu = Menu(menu)
        menu.add_cascade(get_addmenu_options(label=_('_Options'), menu=self.optionsmenu))

        self.optionsmenu.add_checkbutton(get_addmenu_options(label=_('Show _next move'), variable=self.options.showNextMoveVar, command=self.showNextMove))
        self.optionsmenu.add_checkbutton(get_addmenu_options(label=_('Show _last move'), variable=self.options.showCurrMoveVar, command=self.showNextMove))
        self.optionsmenu.add_checkbutton(label=_('Show coordinates'), variable=self.options.showCoordinates, command=self.toggleCoordinates)
        self.optionsmenu.add_checkbutton(label=_('Ask before discarding unsaved changes'), variable=self.options.confirmDelete)

        theme_menu = Menu(self.optionsmenu)
        for th in self.style.theme_names():
            theme_menu.add_radiobutton(label=th, variable=self.options.theme, value=th, command=lambda: self.style.theme_use(self.options.theme.get()))
        self.optionsmenu.add_cascade(get_addmenu_options(label=_('_Theme'), menu=theme_menu))

        lang_menu = Menu(self.optionsmenu)
        languages = [('en', 'English'), ('de', 'Deutsch'), ]
        for code, lang in languages:
            lang_menu.add_radiobutton(label=lang, variable=self.options.language, value=code, command=lambda: self.switch_language(self.options.language.get(), show_warning=True))
        self.optionsmenu.add_cascade(get_addmenu_options(label=_('_Language'), menu=lang_menu))

        self.optionsmenu.add_command(get_addmenu_options(label=_('_Edit advanced options'), command=self.edit_options))

        # -------------- HELP -------------------
        self.helpmenu = Menu(menu, name=_('help'))
        menu.add_cascade(get_addmenu_options(label=_('_Help'), menu=self.helpmenu))

        self.helpmenu.add_command(get_addmenu_options(label=_('_About ...'), command=self.helpAbout))

        self.helpmenu.add_command(get_addmenu_options(label=_('License'), command=self.helpLicense))
        self.helpmenu.add_command(get_addmenu_options(label=_('Documentation'), command=self.helpDocumentation))

        self.mainMenu = menu

    def initButtons(self, navFrame, labelFrame):
        # The buttons
        self.modeVar = StringVar()
        self.modeVar.set('blackwhite')
        self.board.currentColor = 'black'

        self.BWbutton = Radiobutton(navFrame, text='BW', indicatoron=0, bg='#999999',
                                    variable=self.modeVar, value='blackwhite', command=self.modeChange)
        self.WBbutton = Radiobutton(navFrame, text='WB', indicatoron=0, bg='#999999',
                                    variable=self.modeVar, value='whiteblack', command=self.modeChange)
        self.Bbutton = Radiobutton(navFrame, text='B', indicatoron=0, bg='#999999',
                                   variable=self.modeVar, value='black', command=self.modeChange)
        self.Wbutton = Radiobutton(navFrame, text='W', indicatoron=0, bg='#999999',
                                   variable=self.modeVar, value='white', command=self.modeChange)

        self.nextButton = Button(navFrame, text='->', command=self.next)
        self.boardFrame.bind('<Right>', lambda e, s=self.nextButton: s.invoke())
        self.prevButton = Button(navFrame, text='<-', command=self.prev)
        self.boardFrame.bind('<Left>', lambda e, s=self.prevButton: s.invoke())
        self.next10Button = Button(navFrame, text='-> 10', command=self.next10)
        self.boardFrame.bind('<Down>', lambda e, s=self.next10Button: s.invoke())
        self.prev10Button = Button(navFrame, text='<- 10', command=self.prev10)
        self.boardFrame.bind('<Up>', lambda e, s=self.prev10Button: s.invoke())
        self.startButton = Button(navFrame, text='|<-', command=self.start)
        self.boardFrame.bind('<Home>', lambda e, s=self.startButton: s.invoke())
        self.endButton = Button(navFrame, text='->|', command=self.end)
        self.boardFrame.bind('<End>', lambda e, s=self.endButton: s.invoke())

        self.boardFrame.bind('<Prior>', self.upVariation)
        self.boardFrame.bind('<Next>', self.downVariation)

        self.passButton = Button(navFrame, text=_('Pass'), command=self.passFct)

        self.gameinfoButton = Button(navFrame, text=_('Info'), command=self.gameinfo, underline=0)
        self.boardFrame.bind('<Control-i>', lambda e, s=self.gameinfoButton: s.invoke())

        lab = Label(navFrame, text=_('Ctrl-Click:'))

        self.removeStoneButton = Radiobutton(navFrame, text='DEL ST', indicatoron=0, variable=self.options.labelType, value='DEL ST')
        self.triangleButton = Radiobutton(navFrame, text='TR', indicatoron=0, variable=self.options.labelType, value='TR')
        self.squareButton = Radiobutton(navFrame, text='SQ', indicatoron=0, variable=self.options.labelType, value='SQ')
        self.letterUButton = Radiobutton(navFrame, text='ABC', indicatoron=0, variable=self.options.labelType, value='ABC')
        self.letterLButton = Radiobutton(navFrame, text='abc', indicatoron=0, variable=self.options.labelType, value='abc')
        self.numberButton = Radiobutton(navFrame, text='123', indicatoron=0, variable=self.options.labelType, value='12n')
        self.delButton = Button(navFrame, text='DEL', command=lambda self=self: self.delVar())
        self.guessModeButton = Checkbutton(navFrame, text=_('Guess mode'), indicatoron=0,
                                           variable=self.guessMode, command=self.dataWindow.toggleGuessMode)

        ca0 = Separator(navFrame, orient='vertical')
        ca1 = Separator(navFrame, orient='vertical')
        ca2 = Separator(navFrame, orient='vertical')

        # try to load icons for navigation buttons and grid the buttons

        self.tkImages = []
        for i, (button, filename, options) in enumerate([
                                 (self.BWbutton, 'bw', {}),
                                 (self.WBbutton, 'wb', {}),
                                 (self.Bbutton, 'b', {}),
                                 (self.Wbutton, 'w', {}),
                                 (self.prevButton, 'actions-media-playback-back', {}),
                                 (self.nextButton, 'actions-media-playback-start', {}),
                                 (self.prev10Button, 'actions-media-seek-backward', {}),
                                 (self.next10Button, 'actions-media-seek-forward', {}),
                                 (self.startButton, 'actions-media-skip-backward', {}),
                                 (self.endButton, 'actions-media-skip-forward', {}),
                                 (self.passButton, 'actions-media-playback-pause', {}),
                                 (self.gameinfoButton, 'actions-edit-find', {}),
                                 (ca0, None, {'padx': 10}),
                                 (lab, None, {}),
                                 (self.removeStoneButton, 'status-dialog-error', {}),
                                 (self.triangleButton, 'tr', {}),
                                 (self.squareButton, 'sq', {}),
                                 (self.letterUButton, 'abc-u', {}),
                                 (self.letterLButton, 'abc-l', {}),
                                 (self.numberButton, '123', {}),
                                 (ca1, None, {'padx': 10}),
                                 (self.delButton, 'actions-process-stop', {}),
                                 (ca2, None, {'padx': 10}),
                                 (self.guessModeButton, 'apps-help-browser', {}), ]):
            if filename:
                load_icon(button, filename, self.tkImages, buttonsize=self.options.scaling.get())
            button.grid(row=0, column=i, **options)

        self.currentFile = ''

        self.boardFrame.focus()

        self.moveno = StringVar()
        self.movenoLabel = Label(labelFrame, height=1, width=5, relief=SUNKEN, justify=RIGHT, textvariable=self.moveno, font=self.smallFont)
        self.gameName = StringVar()
        self.gameNameLabel = Label(labelFrame, height=1, width=20, relief=SUNKEN, justify=LEFT, textvariable=self.gameName, font=self.smallFont)

        self.capVar = StringVar()
        self.capLabel = Label(labelFrame, height=1, width=15, relief=SUNKEN, justify=LEFT, textvariable=self.capVar, font=self.smallFont)

        # pack everything

        self.gameNameLabel.pack(expand=NO, fill=X, side=LEFT, padx=5)
        self.movenoLabel.pack(expand=NO, fill=X, side=LEFT, padx=5)
        self.capLabel.pack(expand=NO, fill=X, side=LEFT, padx=5)

    def balloonHelp(self):
        ToolTip(self.prevButton, _('Back one move'))
        ToolTip(self.nextButton, _('Forward one move'))
        ToolTip(self.prev10Button, _('Back 10 moves'))
        ToolTip(self.next10Button, _('Forward 10 moves'))
        ToolTip(self.startButton, _('Start of game/Clear board'))
        ToolTip(self.endButton, _('End of game'))
        ToolTip(self.passButton, _('Pass'))
        ToolTip(self.gameinfoButton, _('Edit game info'))

        ToolTip(self.BWbutton, _('Play black/white stones'))
        ToolTip(self.WBbutton, _('Play white/black stones'))
        ToolTip(self.Bbutton, _('Place black stones'))
        ToolTip(self.Wbutton, _('Place white stones'))

        ToolTip(self.capLabel, _('Number of captured stones'))
        ToolTip(self.movenoLabel, _('Number of current move'))
        ToolTip(self.gameNameLabel, _('Current SGF file'))

        ToolTip(self.dataWindow.filelistB1, _('Create new SGF file'))
        ToolTip(self.dataWindow.filelistB2, _('Open SGF file'))
        ToolTip(self.dataWindow.filelistB3, _('Delete SGF file from list'))
        ToolTip(self.dataWindow.filelistB4, _('Split collection into single files'))
        ToolTip(self.dataWindow.gamelistB1, _('Create new game'))
        ToolTip(self.dataWindow.gamelistB2, _('Delete game'))

        ToolTip(self.removeStoneButton, _('Ctrl-click deletes stone'))
        ToolTip(self.triangleButton, _('Ctrl-click places/deletes triangle label'))
        ToolTip(self.squareButton, _('Ctrl-click places/deletes square label'))
        ToolTip(self.letterUButton, _('Ctrl-click places/deletes uppercase label'))
        ToolTip(self.letterLButton, _('Ctrl-click places/deletes lowercase label'))
        ToolTip(self.numberButton, _('Ctrl-click places/deletes number label'))
        ToolTip(self.delButton, _('Delete this and all following nodes'))
        ToolTip(self.guessModeButton, _('Enter/leave guess mode'))

    def evalOptions(self):
        """
        Do things that depend on reading the options file.
        """

        self.dataWindow.comments.configure(text_font=self.standardFont)
        if self.options.showCoordinates.get():
            self.board.coordinates = 1
            self.board.resize()
        if self.options.windowGeom.get():
            self.master.geometry(self.options.windowGeom.get())
        if self.options.dataWindowGeometry.get():
            self.dataWindow.set_geometry(self.options.dataWindowGeometry.get())
        self.mainframe.update_idletasks()
        try:
            self.mainframe.sash_place(0, int(self.options.sashPos.get()), 1)
            self.mainframe.update_idletasks()
        except:
            pass

    def init_key_bindings(self):
        self.master.bind('<Control-q>', lambda e, self=self: self.quit())

    def switch_language(self, lang, show_warning=False):
        try:
            resource = os.path.join('lang', lang, 'LC_MESSAGES', 'kombilo.mo')

            translation = gettext.GNUTranslations(pkg_resources.resource_stream(__name__, resource))
            translation.install(unicode=True)
        except:
            if show_warning:
                showwarning(_('Warning'), _('The language files could not be found.'))
        else:
            if show_warning:
                showwarning(_('Note'), _('You have to restart the program to make the change become effective.'))

    def __init__(self, master, BoardClass=Board, DataWindowClass=DataWindow):
        """ Initialize the GUI, some variables, etc. """

        self.options = BunchTkVar()
        self.sgfpath = os.curdir

        try:
            self.config = self.get_config_obj()
            if self.config['main']['version'].strip() == 'kombilo%s' % KOMBILO_VERSION:
                # otherwise this is an old .cfg file which should be ignored

                if 'sgfpath' in self.config['main']:
                    self.sgfpath = self.config['main']['sgfpath']
                self.loadOptions(self.config['options'])
        except:
            showwarning(_('Error'), _('Neither kombilo.cfg nor default.cfg were found.'))
            sys.exit()

        if not os.path.exists(get_configfile_directory()):
            try:
                os.makedirs(get_configfile_directory())
            except IOError:
                showwarning(
                        _('Error'),
                        _('Unable to create directory %s.') % get_configfile_directory())
                sys.exit()

        sys.stderr = open(os.path.join(get_configfile_directory(), 'kombilo.err'), 'a')

        self.guessMode = IntVar()

        self.style = Style()
        self.style.theme_use(self.options.theme.get())

        if self.options.language.get():
            self.switch_language(self.options.language.get())

        if self.options.scaling.get() == -1:
            # Application is opened for the first time, so we adjust button size
            # (stored in self.options.scaling) and some font sizes in case the
            # screen resolution is (probably) very high.
            varlist = [
                    (self.options.scaling, 22, 32),
                    (self.options.standardFontSize, 9, 10),
                    (self.options.smallFontSize, 8, 9),
                    (self.options.labelFontSize, 5, 7),
                    (self.options.monospaceFontSize, 10, 12),
                    ]

            if master.winfo_screenwidth() > 2200:
                for variable, dummy, size in varlist:
                    variable.set(size)
            else:
                for variable, size, dummy in varlist:
                    variable.set(size)

        # The main window

        if BoardClass == Board:  # not invoked by Kombilo
            if sys.platform.startswith('win') and self.options.maximize_viewer.get():
                try:
                    master.state('zoomed')
                except:
                    pass

        self.master = master

        navFrame = Frame(self.master)
        navFrame.pack(side=TOP, pady=3)
        self.mainframe = PanedWindow(self.master, sashrelief=SUNKEN, sashwidth=2, sashpad=2, orient='horizontal')  # note that PanedWindow is Tkinter, not ttk
        self.mainframe.pack(expand=YES, fill=BOTH)
        dw_frame = Frame(self.mainframe)
        self.mainframe.add(dw_frame, minsize=1, )
        self.frame = Frame(self.mainframe)
        self.mainframe.add(self.frame, minsize=250)

        self.boardFrame = Frame(self.frame, takefocus=1)
        labelFrame = Frame(self.frame)

        self.boardFrame.pack(side=TOP, expand=YES, fill=BOTH, padx=5)
        labelFrame.pack(side=TOP)

        self.initFonts()

        # The board

        try:
            self.boardImg = PILImageTk.PhotoImage(PILImage.open(pkg_resources.resource_stream(__name__, 'icons/board.png')))
        except (TclError, IOError, AttributeError):
            self.boardImg = None

        self.blackStones = [
                PILImage.open(
                    pkg_resources.resource_stream(
                        __name__,
                        'icons/black.png')).convert('RGBA'),
                    ]
        self.whiteStones = [
                PILImage.open(
                    pkg_resources.resource_stream(
                        __name__, 'icons/white%d.png' % i)).convert('RGBA')
                    for i in range(16)
                    ]

        self.board = BoardClass(self.boardFrame, 19, (30, 25), 1, self.labelFont, 1, None, self.boardImg, self.blackStones, self.whiteStones, True)
        self.board.shadedStoneVar = self.options.shadedStoneVar
        self.board.fuzzy = self.options.fuzzy

        self.board.pack(expand=YES, fill=BOTH)
        # self.board.pack_propagate(0)
        self.board.update_idletasks()


        # the data window

        self.dataWindow = DataWindowClass(self, dw_frame)

        self.comments = self.dataWindow.comments
        self.cursor = EnhancedCursor('(;GM[1]FF[4]SZ[19]AP[Kombilo])', self.comments, self.dataWindow.SGFtreeC, self)
        self.dataWindow.updateGameInfo(self.cursor)
        self.evalOptions()
        self.dataWindow.window.update_idletasks()

        self.initButtons(navFrame, labelFrame)
        self.init_key_bindings()
        self.initMenus()

        self.master.deiconify()

        self.filelist = []
        self.currentFileNum = -2
        self.newFile()

        self.board.state('normal', self.nextMove)
        self.board.bind('<Control-1>', self.labelClick)
        self.board.bind('<Shift-3>', self.gotoMove)

        def _mouse_wheel(event, self=self):
            if event.delta < 0:
                for i in range((-event.delta) // 120):
                    self.next()
            elif event.delta > 0:
                for i in range(event.delta // 120):
                    self.prev()
            return 'break'
        self.boardFrame.bind('<MouseWheel>', _mouse_wheel)
        self.board.bind('<Button-5>', lambda e: self.next())
        self.board.bind('<Button-4>', lambda e: self.prev())

        self.moveno.set(0)
        self.capB, self.capW = 0, 0

        self.balloonHelp()

# ---------------------------------------------------------------------------------------

def run():

    import __builtin__
    if not '_' in __builtin__.__dict__:
        __builtin__.__dict__['_'] = lambda s: s

    root = Tk()
    root.withdraw()
    root.option_add("*Font", "TkDefaultFont")

    try:
        if os.path.exists(os.path.join(get_configfile_directory(), 'kombilo.app')):
            root.option_readfile(os.path.join(get_configfile_directory(), 'kombilo.app'))
    except TclError:
        showwarning(_('Error'), _('Error reading kombilo.app file.'))

    app = Viewer(root)

    root.protocol('WM_DELETE_WINDOW', app.quit)
    root.title('v.py')

    app.boardFrame.focus_force()
    root.tkraise()

    if len(sys.argv) > 1:              # load sgf file given as first argument
        app.openFile(os.path.split(sys.argv[1])[0], os.path.split(sys.argv[1])[1])
        app.changeCurrentFile(None, 1)
        app.delFile()

    if len(sys.argv) > 2:              # jump to move given as second argument
        try:
            for i in range(int(sys.argv[2])):
                app.next()
        except:
            pass

    root.mainloop()

if __name__ == '__main__':
    run()

