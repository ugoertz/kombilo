#!/usr/bin/env python

# File: vsl/vl.py

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


from Tkinter import *


class VirtualScrollbar(Scrollbar):

    def __init__(self, parent, offset, current_in_list, total_in_list, *args, **kwargs):
        self.offset = offset  # a "pointer", i.e. a list whose first and only entry contains the offset
        self.current_in_list = current_in_list
        self.total_in_list = total_in_list
        Scrollbar.__init__(self, parent, *args, **kwargs)

    def set(self, *args):
        # print 'Scrollbar.set', self.current_in_list, self.total_in_list
        if self.total_in_list == 0:
            return
        cil = min(self.current_in_list, self.total_in_list)
        multiplier = cil * 1.0 / self.total_in_list
        alpha = float(args[0]) * multiplier + self.offset[0]
        beta = float(args[1]) * multiplier + self.offset[0]
        # print args, multiplier, alpha, beta, str(alpha), str(beta)
        Scrollbar.set(self, str(alpha), str(beta))


class VirtualListbox(Listbox):
    def __init__(self, parent, offset, current_in_list, total_in_list, get_data, *args, **kwargs):
        '''
        get_data is a function; get_data(i) will be displayed as the i-th line of the list
        get_data_ic, if specified (in kwargs), is a function which returns a dict to be plugged into itemconfig; this can be used to change color of background color of a line.
        '''

        if not 'activestyle' in kwargs:
            kwargs['activestyle'] = 'none'
        if 'get_data_ic' in kwargs:
            self.get_data_ic = kwargs['get_data_ic']
            del kwargs['get_data_ic']
        else:
            self.get_data_ic = None
        Listbox.__init__(self, parent, *args, **kwargs)
        self.current = (0, current_in_list)
        self.total_in_list = total_in_list
        self.current_in_list = current_in_list
        self.get_data = get_data
        self.offset = offset
        self.insert_interval()

    def insert_interval(self, interval=None):
        interval = interval or self.current
        for i in xrange(*interval):
            d = self.get_data(i)
            self.insert(END, self.get_data(i))
            if d and self.get_data_ic:
                ic = self.get_data_ic(i)
                if ic:
                    try:
                        self.itemconfig(i - interval[0], **ic)
                    except TclError:
                        pass

    def virt_select_set_see(self, index):
        '''
        index should refer to the "whole" list (not just to the current interval).
        '''

        if not self.current[0] <= index < self.current[1]:
            cil = self.current_in_list
            new_start = max(0, int(index) - cil / 2)
            new_current = (new_start, new_start + cil)
            self.delete(0, END)
            self.insert_interval(new_current)
            self.offset[0] = new_current[0] * 1.0 / self.total_in_list
            self.current = new_current
        i = int(index) - self.current[0]
        Listbox.select_set(self, i)
        Listbox.see(self, i)

    def adjust_scrollbar_offset(self, beta_til):
        if self.total_in_list == 0:
            return
        cil = min(self.current_in_list, self.total_in_list)
        if self.current[0] > 0 and (beta_til - self.current[0]) < cil / 6:
            new_start = max(0, int(beta_til - cil // 2))
            new_current = (new_start, new_start + cil)
            self.delete(0, END)
            self.insert_interval(new_current)
            self.offset[0] = new_current[0] * 1.0 / self.total_in_list
            # print '1 -------------------------------------------------', self.current, new_current, self.offset[0]
        elif self.current[1] < self.total_in_list and (self.current[1] - beta_til) < cil / 6:
            new_end = min(int(beta_til + cil // 2), self.total_in_list)
            new_current = (new_end - cil, new_end)
            self.delete(0, END)
            self.insert_interval(new_current)
            self.offset[0] = new_current[0] * 1.0 / self.total_in_list
            # print '2 -------------------------------------------------', self.current, new_current, self.offset[0]
        else:
            return
        change = new_current[0] - self.current[0]
        self.current = new_current
        return change

    def yview(self, *args):
        if self.total_in_list == 0:
            return
        cil = min(self.current_in_list, self.total_in_list)
        if len(args) > 0 and args[0] == 'moveto':
            # print "LISTBOX YVIEW", args
            beta_til = float(args[1]) * self.total_in_list
            self.adjust_scrollbar_offset(beta_til)
            moveto = str((beta_til - self.current[0]) * 1.0 / cil)
            return Listbox.yview(self, 'moveto', moveto)
        else:  # e.g. if args[0] == 'scroll'
            # print 'yview else', args
            index = int(self.curselection()[0]) if self.curselection() else None
            Listbox.yview(self, *args)
            nearest0 = self.nearest(0)
            change = self.adjust_scrollbar_offset(self.nearest(0) + self.current[0])
            if change:
                self.select_clear(0, END)
                if index and 0 <= index - change < cil:
                    self.select_set(index - change)
                return Listbox.yview(self, 'moveto', str((nearest0 - change) * 1.0 / cil))


class VScrolledList(Frame):
    """ A 'virtual' listbox with dynamic vertical and horizontal scrollbars. """

    def __init__(self, parent, current_in_list, total_in_list, get_data, **kw):
        Frame.__init__(self, parent)
        self.offset = [0]  # shared "pointer" of listbox and sbar_vert
        self.current_in_list = current_in_list
        self.total_in_list = total_in_list

        self.sbar_vert = VirtualScrollbar(self, self.offset, current_in_list, total_in_list)
        self.sbar_hor = Scrollbar(self)  # was sbar1
        self.checking = 0

        defaults = {'height': 12, 'width': 40, 'relief': SUNKEN, 'selectmode': SINGLE, 'takefocus': 1, 'exportselection': 0}
        if kw:
            defaults.update(kw)

        self.listbox = VirtualListbox(self, self.offset, current_in_list, total_in_list, get_data, **defaults)
        self.sbar_vert.config(command=self.listbox.yview)
        self.sbar_hor.config(command=self.listbox.xview, orient='horizontal')
        self.listbox.config(xscrollcommand=self.sbar_hor.set, yscrollcommand=self.sbar_vert.set)
        self.listbox.grid(row=0, column=0, sticky=NSEW)
        self.sbar_vert.grid(row=0, column=1, sticky=NSEW)
        self.sbar_hor.grid(row=1, column=0, sticky=NSEW)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.focus_force()

        self.onSelectionChange = None

        self.listbox.bind('<Up>', self.up)
        self.listbox.bind('<Down>', self.down)
        self.listbox.bind('<Prior>', self.pgup)
        self.listbox.bind('<Next>', self.pgdown)

        self.unbind('<Configure>')
        self.bind('<Configure>', self.checkScrollbars)

        self.sbar_vert.grid_forget()
        self.sbar_hor.grid_forget()

    def get_index(self, i):
        return i + self.listbox.current[0]

    def reset(self):
        self.sbar_vert.current_in_list = self.current_in_list
        self.sbar_vert.total_in_list = self.total_in_list
        self.listbox.current = (0, self.current_in_list)
        self.listbox.total_in_list = self.total_in_list
        self.listbox.current_in_list = self.current_in_list
        self.listbox.delete(0, END)
        self.offset[0] = 0
        self.listbox.insert_interval()

    def upd(self):
        # print 'upd', self.listbox.curselection(), self.listbox.index('active'), self.listbox.index('anchor'), self.listbox.current, self.sbar_vert.get()
        savepos = self.sbar_vert.get()
        sel = self.listbox.curselection()
        self.listbox.delete(0, END)
        self.listbox.insert_interval()
        for s in sel:
            self.listbox.select_set(s)
        self.listbox.yview('moveto', savepos[0])

    def checkScrollbars(self, event=None):
        if self.listbox.yview() != (0.0, 1.0):
            self.sbar_vert.grid(row=0, column=1, sticky=NSEW)
        else:
            self.sbar_vert.grid_forget()
        if self.listbox.xview() != (0.0, 1.0):
            self.sbar_hor.grid(row=1, column=0, sticky=NSEW)
        else:
            self.sbar_hor.grid_forget()
        self.after(500, self.checkScrollbars)

    def up(self, event):
        if not self.listbox.curselection() or len(self.listbox.curselection()) > 1:
            return
        index = int(self.listbox.curselection()[0])
        if index != 0:
            self.listbox.select_clear(index)
            self.listbox.select_set(index - 1)
            self.listbox.see(index - 1)
            if self.onSelectionChange:
                self.onSelectionChange(None, self.get_index(index - 1))
        return 'break'

    def down(self, event):
        if not self.listbox.curselection() or len(self.listbox.curselection()) > 1:
            return
        index = int(self.listbox.curselection()[0])
        if index != self.listbox.size() - 1:
            self.listbox.see(index + 1)
            self.listbox.select_clear(index)
            self.listbox.select_set(index + 1)
            if self.onSelectionChange:
                self.onSelectionChange(None, self.get_index(index + 1))
        return 'break'

    def pgup(self, event):
        # print 'pgup'
        if not self.listbox.curselection() or len(self.listbox.curselection()) > 1:
            return
        index = int(self.listbox.curselection()[0])
        if index >= 10:
            self.listbox.select_clear(index)
            self.listbox.select_set(index - 10)
            self.listbox.see(index - 10)
            if self.onSelectionChange:
                self.onSelectionChange(None, self.get_index(index - 10))
        elif self.listbox.size():
            self.listbox.see(0)
            self.listbox.select_clear(index)
            self.listbox.select_set(0)
            if self.onSelectionChange:
                self.onSelectionChange(None, 0)
        return 'break'

    def pgdown(self, event):
        # print 'pgdn'
        if not self.listbox.curselection() or len(self.listbox.curselection()) > 1:
            return
        index = int(self.listbox.curselection()[0])
        if index <= self.listbox.size() - 10:
            self.listbox.select_clear(index)
            self.listbox.select_set(index + 10)
            self.listbox.see(index + 10)
            if self.onSelectionChange:
                self.onSelectionChange(None, self.get_index(index + 10))
        elif self.listbox.size():
            self.listbox.select_clear(index)
            self.listbox.select_set(self.listbox.size() - 1)
            self.listbox.see(END)
            if self.onSelectionChange:
                self.onSelectionChange(None, self.get_index(self.listbox.size() - 1))
        return 'break'


if __name__ == '__main__':

    def get_data(i):
        # print i
        return str(i) + ', ' + str(2 * i) + ', ' + str(i ** 10)

    root = Tk()

    vslb = VScrolledList(root, 2000, 100000, get_data)
    vslb.pack(expand=Y, fill=BOTH)
    mainloop()
