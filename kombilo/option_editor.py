#!/usr/bin/python
# File: option_editor.py

##   Copyright (C) 2001-  Ulrich Goertz (ug@geometry.de)

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
from configobj import ConfigObj
from Tkinter import (
        Toplevel, Frame,
        IntVar, BooleanVar, StringVar,
        Button, Checkbutton, Label, Entry, Text, )
from ttk import Combobox
from Pmw import ScrolledFrame

class OptionEditor(object):
    # Parses default.cfg configuration file and sets up a window where those
    # properties markes as "editable" can be altered. See the remarks in
    # default.cfg for the format.

    def __init__(self, configobj):
        self.window = Toplevel()
        # self.window.option_add("*Background", "white")
        self.window.protocol('WM_DELETE_WINDOW', self.cancel)

        f0 = Frame(self.window)
        f0.pack(side='top', anchor='w', expand=False, fill='x')
        t = _('Note that most changes become effective only after restarting the program.')
        text = Text(f0, height=len(t)//80+1, width=80, wrap='word')
        text.insert(1.0, _(t))
        text.config(state='disabled')
        text.pack(side='left', expand=True, fill='x')
        Button(f0, text=_('Save'), command=self.save, bg='lightgreen').pack(side='right', anchor='e')
        Button(f0, text=_('Cancel'), command=self.cancel, bg='orange').pack(side='right', anchor='e')

        self.configobj = configobj
        self.variables = {}  # will store the Tkinter variables containing the values
        special_values = ['# -----', '# section', '# label', '# editable', '# values', ]

        sf = ScrolledFrame(
                self.window,
                usehullsize=1, hull_height=500)
        sf.pack(side='top', anchor='w', expand=True, fill='both')
        f = sf.interior()
        ctr = -1

        for prop in configobj['options']:
            comments = configobj['options'].comments[prop]

            # new "section"?
            sec = self.retrieve('# section:', comments)
            if sec:
                ctr += 1
                Label(f, text=_(sec), justify='left', bg='#eeeeee', font=('Helvetica', 14, 'bold')
                        ).grid(row=ctr, column=0, columnspan=3, sticky='we', pady=10)

            if '# editable' in comments:
                ctr += 1

                label = self.retrieve('# label:', comments) or prop
                label = label.strip()
                values = self.retrieve('# values:', comments)
                if values:
                    values = values.split(', ')
                else:
                    values = []
                help_text = ' '.join(x[1:].strip() for x in comments if not any(
                    x.startswith(v) for v in special_values)).strip()

                if 'BOOLEAN' in values:
                    self.variables[prop] = BooleanVar()
                else:
                    self.variables[prop] = StringVar()

                if '--' in values and configobj['options'][prop] == '':
                    self.variables[prop].set('--')
                else:
                    self.variables[prop].set(configobj['options'][prop])

                if 'BOOLEAN' in values:
                    Checkbutton(
                            f, text=_(label), indicatoron=1, variable=self.variables[prop]
                            ).grid(row=ctr, column=1, sticky='nw', pady=5)
                elif values and not 'INT' in values:
                    Label(f, text=_(label), justify='left').grid(row=ctr, column=0, sticky='nw', pady=5)
                    Combobox(
                            f, justify='left', textvariable=self.variables[prop], values=values,
                            ).grid(row=ctr, column=1, sticky='nw', pady=5)
                else:
                    Label(f, text=_(label), justify='left').grid(row=ctr, column=0, sticky='nw', pady=5)
                    Entry(f, width=20, textvariable=self.variables[prop]
                            ).grid(row=ctr, column=1, sticky='nw', pady=5)
                if help_text:
                    ht = _(help_text)
                    text = Text(f, height=len(ht)//60+1, width=60, borderwidth=0, wrap='word')
                    text.insert(1.0, _(help_text))
                    text.config(state='disabled')
                    text.grid(row=ctr, column=2, sticky='nsew', pady=5)

        self.window.update_idletasks()

        self.window.focus()
        self.window.grab_set()
        self.window.wait_window()

    def cancel(self):
        self.window.destroy()

    def save(self):
        for prop in self.configobj['options']:
            comments = self.configobj['options'].comments[prop]
            if '# editable' in comments:
                # validate:
                values = self.retrieve('# values:', comments)
                if values:
                    values = values.split(', ')
                else:
                    values = []
                if 'INT' in values:
                    try:
                        self.configobj['options'][prop] = int(self.variables[prop].get())
                    except ValueError:
                        pass
                elif 'BOOLEAN' in values:
                    self.configobj['options'][prop] = self.variables[prop].get()
                elif not values:
                    self.configobj['options'][prop] = self.variables[prop].get()
                else:
                    if '--' in values and self.variables[prop].get() == '--':
                        self.configobj['options'][prop] = ''
                    elif self.variables[prop].get() in values:
                        self.configobj['options'][prop] = self.variables[prop].get()
        self.window.destroy()

    def retrieve(self, s, comments):
        return ''.join(x[len(s):].strip() for x in comments if x.startswith(s))

