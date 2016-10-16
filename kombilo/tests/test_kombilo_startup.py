#!/usr/bin/env python

# File: examples/test_patternsearch/final_position.py

##   Copyright (C) 2001-16 Ulrich Goertz (ug@geometry.de)

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

'''
Test whether kombilo.py starts up.
'''


from __future__ import absolute_import

from Tkinter import Tk

from kombilo.kombilo import App

def test_kombilo_startup():
    import __builtin__
    if not '_' in __builtin__.__dict__:
        __builtin__.__dict__['_'] = lambda s: s

    root = Tk()
    root.withdraw()

    app = App(root)

    root.protocol('WM_DELETE_WINDOW', app.quit)
    root.title('Kombilo')

    app.boardFrame.focus_force()
    root.destroy()

