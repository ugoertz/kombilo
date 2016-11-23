# file: utilities.py

##   This file is part of Kombilo, a go database program
##   It contains classes that help handlng sgf files.

##   Copyright (C) 2001- Ulrich Goertz (ug@geometry.de)

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

def bb(x):
    '''Always returns bytestring; encode to UTF8 if x is not a bytestring.'''
    if type(x) == type(u''):
        x = x.encode('utf8')
    # assert type(x) == type(b'')
    return x

def uu(x):
    '''Always returns unicode; decode from UTF8 if x is not unicode itself.'''
    if type(x) == type(b''):
        x = x.decode('utf8')
    # assert type(x) == type(u'')
    return x

