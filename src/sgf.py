# file: sgf.py

##   This file is part of Kombilo, a go database program
##   It contains classes that help handlng sgf files.

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

'''
The sgf module provides functionality for handling SGF files.
'''

import libkombilo as lk

# ------- MISC TOOLS ------------------------------------------------------------


def flip_mirror1(pos):

    if not pos:
        return ''

    x = ord(pos[0]) - ord('a')
    y = ord(pos[1]) - ord('a')
    x = 18 - x
    return chr(x + ord('a')) + chr(y + ord('a'))


def flip_mirror2(pos):

    if not pos:
        return ''

    x = ord(pos[0]) - ord('a')
    y = ord(pos[1]) - ord('a')
    help = 18 - y
    y = 18 - x
    x = help
    return chr(x + ord('a')) + chr(y + ord('a'))


def flip_rotate(pos):

    if not pos:
        return ''

    x = ord(pos[0]) - ord('a')
    y = ord(pos[1]) - ord('a')
    help = 18 - x
    x = y
    y = help
    return chr(x + ord('a')) + chr(y + ord('a'))


class Cursor(lk.Cursor):

    '''The Cursor class takes SGF data (as a string) and provides methods to
    traverse the game and to retrieve the information for each node stored in
    the SGF file.

    To create a Cursor instance, call Cursor with the following arguments:

    * sgf: The SGF data as a string.
    * sloppy (optional, default is False): If this is True, then the parser
      tries to ignore deviations from the SGF format.
    * encoding (optional, default is 'utf-8'): **This option is currently not
      used.** Later, the parser will decode the file with the specified
      encoding.
    '''

    def __init__(self, sgf, sloppy=False, encoding='utf8'):
        try:
            lk.Cursor.__init__(self, sgf, 1)  # TODO: later, use encoding when parsing the sgf file, and immediately recode to utf-8.
        except:
            raise lk.SGFError()
        # self.encoding = encoding

    def currentNode(self):
        '''Get an instance of class :py:class:`Node` for the node the cursor
        currently points to.'''
        return Node(self.currentN)

    def game(self, n, update=None):
        # Add dummy update argument for call from kombiloNG, sgf_tree
        lk.Cursor.game(self, n)

    def add(self, st, update=None):
        lk.Cursor.add(self, st)

    def next(self, n=0, markCurrent=None):
        '''Go to n-th child of current node. Default for n is 0, so if there
        are no variations, you can traverse the game by repeatedly calling
        ``next()``.
        '''
        return Node(lk.Cursor.next(self, n))

    def previous(self):
        '''Go to the previous node.
        '''
        return Node(lk.Cursor.previous(self))

    def getRootNode(self, n):
        '''Get the first node of the ``n``-th node of this SGF game collection.
        Typically, SGF files contain only a single game; ``getRootNode(0)``
        will give you its root node.
        '''
        return Node(lk.Cursor.getRootNode(self, n))

    def updateRootNode(self, data, n=0):
        '''Update the root node of the ``n``-th game in this collection.

        ``data`` is a dictionary which maps SGF properties like PB, PW, ... to their values.
        '''
        if n >= self.root.numChildren:
            raise lk.SGFError('Game not found')

        nn = self.root.next
        for i in range(n):
            nn = nn.down

        nn.SGFstring = self.rootNodeToString(data)
        nn.parsed = 0
        nn.parseNode()

    def rootNodeToString(self, node):

        result = [';']
        keylist = ['GM', 'FF', 'SZ', 'PW', 'WR', 'PB', 'BR',
                   'EV', 'RO', 'DT', 'PC', 'KM', 'RE', 'US', 'GC']
        for key in keylist:  # first append the above fields, if present, in the given order
            if key in node:
                result.append(key)
                result.append('[' + lk.SGFescape(node[key][0].encode('utf-8')) + ']\n')

        l = 0
        for key in node.keys():  # now check for remaining fields
            if not key in keylist:
                result.append(key)
                l += len(key)
                for item in node[key]:
                    result.append('[' + lk.SGFescape(item.encode('utf-8')) + ']\n')
                    l += len(item) + 2
                    if l > 72:
                        result.append('\n')
                        l = 0

        return ''.join(result)

    def noChildren(self):
        '''Returns the number of children of the current node, i.e. the number
        of variations starting here.
        '''
        return self.currentN.numChildren

    def exportGame(self, gameNumber=None):
        '''
        Return a string with the game attached to self in SGF format (with character encoding utf-8!).
        Depending on gameNumber:

        - if None: only the currently "active" game in the collection is written (as specified by self.currentGame)
        - if an integer: the game specified by gameNumber is written
        - it a tuple of integer: the games for this tuple are written
        - if == 'ALL': all games are written
        '''

        if type(gameNumber) == type(0):
            gameNumber = (gameNumber, )
        elif gameNumber is None:
            gameNumber = (self.currentGame, )
        elif gameNumber == 'ALL':
            gameNumber = range(self.root.numChildren)

        t = ''
        g = 0
        n = self.root.next
        while g < self.root.numChildren:
            if g in gameNumber:
                t += '(' + self.outputVar(n) + ')'
            g += 1
            n = n.down

        # t = t.replace('\r', '')
        return t


class Node(object):
    '''The Node class represents a single node in a game. This class is a
    wrapper for lk.Node class. It has dictionary style access to sgf property
    values.

    This class does not inherit from ``lk.Node``. To construct a Node, pass an
    lk.Node instance to ``__init__``. It is stored as ``self.n``.

    You can check whether a Node ``node`` has an SGF property and retrieve its
    value like this: ``if 'B' in node: print node['B']``. Similarly, using
    ``node['B'] = ('pp', )`` and ``del node['B']`` you can set values and
    delete properties from ``node``.
    '''

    def __init__(self, node):
        try:
            self.n = node.n
        except:
            self.n = node  # a lk.Node instance

    def __getattr__(self, attr):
        '''Retrieve 'unknown' attributes from self.n.'''

        try:
            return self.n.__getattribute__(attr)
        except:
            raise AttributeError

    def get_move_number(self):
        '''Returns the move number where the node sits inside the game. This is
        a list of non-negative integers. The entries with even indices mean "go
        right by this amount in the game tree"; the entries at odd places mean
        "go down as many steps as indicated, i.e. pass to the corresponding
        sibling".
        '''
        return self.n.get_move_number()

    def __contains__(self, item):
        return True if self.n.gpv(item) else False

    def has_key(self, key):
        return self.__contains__(key)

    def __getitem__(self, ID):
        # print 'get', ID
        try:
            return [x.decode('utf-8') for x in self.n.gpv(ID)]
        except:
            raise KeyError

    def __setitem__(self, ID, value):
        # print 'set', ID, value
        self.n.set_property_value(ID, [(x.encode('utf-8') if type(x) == type(u'') else x)  for x in value])

    def __delitem__(self, item):
        # print 'del', item
        self.n.del_property_value(item)

    def remove(self, ID, item):
        '''Remove ``item`` from the list ``self.n[ID]``.
        '''
        ll = list(self.n[ID])
        ll.remove(item.encode('utf-8') if type(item) == type(u'') else item)
        self.n[ID] = ll

    def add_property_value(self, ID, item):
        '''Add ``item`` to the list ``self[ID]``.
        '''
        self.n.add_property_value(ID, [(x.encode('utf-8') if type(x) == type(u'') else x) for x in item])

    def pathToNode(self):
        '''
        Returns 'path' to the specified node in the following format:
        ``[0,1,0,2,0]`` means: from rootNode, go
        * to next move (0-th variation), then (
        * to first variation, then
        * to next move (0-th var.), then
        * to second variation,
        * then to next move.

        In other words, a cursor c pointing to rootNode can be moved to n by
        ``for i in n.pathToNode(): c.next(i)``.
        '''

        l = []
        n = self

        while n.previous:
            l.append(n.level)
            n = n.previous

        l.reverse()
        return l
