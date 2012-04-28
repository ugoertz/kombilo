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


'''
The kombiloNG module provides much of the Kombilo functionality without the
Graphical User Interface. You can use it to do pattern searches etc. in your
Python scripts.
'''


import time
import os
import sys
import cPickle
from copy import copy, deepcopy
from string import split, find, join, strip, replace, digits, maketrans, translate, lower
from collections import defaultdict
import glob
import re
from array import *
from configobj import ConfigObj

import libkombilo as lk
from abstractboard import abstractBoard
import sgf

KOMBILO_VERSION = '0.7'

REFERENCED_TAG = 3
SEEN_TAG = 4

# -------------- TOOLS --------------------------------------------------

def getDateOfFile(filename):

    try:
        t = time.localtime(os.stat(filename)[8])
        return time.strftime("%d %b %Y %H:%M", t)
    except:
        return ''



def getFilename(s):
    if s[-1] == '.': return s[:-1]         # no extension
    elif s[-2:] == '.m': return s + 'gt'   # extension '.mgt'
    else: return s + '.sgf'                # extension '.sgf'


def symmetrizeSig(s):
    """Given a signature s, compute the 'rotated'/'mirrored' signatures,
    and return the first, w.r.t. lexicographic order, of all these.
    Games which differ only by a symmetry of the board will thus have the
    same symmetrized signature.
    """

    l = []
    oa = ord('a')
    for i in range(6): l.append((ord(s[2*i])-oa, ord(s[2*i+1])-oa))

    m = []
    for f in Pattern.flips:
        k1 = [ f(x[0], x[1]) for x in l] 
        k2 = []
        for i in range(6):
            k2.append('?' if s[2*i] == '?' else chr(k1[i][0]+oa))
            k2.append('?' if s[2*i+1] == '?' else chr(k1[i][1]+oa))
        m.append(join(k2, ''))

    m.sort()
    return m[0]


# ------ PATTERN ----------------------------------------------------------------

from libkombilo import CORNER_NW_PATTERN, CORNER_NE_PATTERN, CORNER_SW_PATTERN, CORNER_SE_PATTERN, SIDE_N_PATTERN, SIDE_W_PATTERN, SIDE_E_PATTERN, SIDE_S_PATTERN, CENTER_PATTERN, FULLBOARD_PATTERN


class Pattern(lk.Pattern):
    '''
    A pattern, i.e., a configuration of black and white stones (and empty
    spots, and possibly wildcards) on a portion of the go board.

    To create a pattern, pass the following arguments to Pattern:

    * p: The pattern as a string (``...XXO..X``). Blanks and line breaks will be
      ignored. Commas (to mark hoshis) will be replaces by periods.
    * ptype (optional): one of ::
  
        CORNER_NW_PATTERN, CORNER_NE_PATTERN, CORNER_SW_PATTERN, CORNER_SE_PATTERN
        # fixed in specified corner

        SIDE_N_PATTERN, SIDE_W_PATTERN, SIDE_E_PATTERN, SIDE_S_PATTERN
        # slides along specified side

        CENTER_PATTERN
        # movable in center

        FULLBOARD_PATTERN.
    * sizeX, sizeY: the size (horizontal/vertical) of the pattern (not needed,
      if ptype is ``FULLBOARD_PATTERN``).
    * anchors (optional): A tuple (right, left, top, bottom) which describe the
      rectangle containing all permissible positions for the top left corner of
      the pattern.

    One of ptype and anchors must be present. If ptype is given, then anchors
    will be ignored.

    * contlist (optional): A list of continuations, in *SGF format*, e.g.
      ``;B[qq];W[de];B[gf]``,
    * topleft (optional): a pair of coordinates, specifying the top left corner
      of the pattern, needed for translating contlist into coordinates relative
      to the pattern
    * contsinpattern (optional; used only if contlist is not given): ``X``
      (black) or ``O`` (white). If given, the labels 1, 2, 3, ... in the pattern
      are extracted and handled as continuations, with 1 played by the
      specified color. 
    * contLabels (optional): A string of same size as p, with labels that
      should be used for labelling continuations.

    .. warning:: Continuation and captures

      With the :py:class:`Pattern` class it is not currently possible to deal
      with captures made by one of the moves of the continuation list. While
      the libkombilo library allows to do this, I have yet to think of a good
      interface to access this functionality.
    '''

    def __init__(self, p, **kwargs):
        iPos = p.replace(' ','').replace(',','.').replace('\n','').replace('\r','')
        boardsize = kwargs.get('boardsize', 19)
        sX = kwargs.get('sizeX', 0)
        sY = kwargs.get('sizeY', 0)

        if 'ptype' in kwargs and kwargs['ptype'] == FULLBOARD_PATTERN:
            sX, sY = boardsize, boardsize
        if sY == 0: sY = len(iPos)/sX # determine vertical size from horizontal size and total size of pattern
        # for i in range(sY): print iPos[i*sX:(i+1)*sX]

        contlist = lk.vectorMNC()
        if 'contlist' in kwargs and kwargs['contlist']: # FIXME does not work correctly if there are captures!
            XX, YY = kwargs.get('topleft', (0,0))

            c = Cursor('(%s)' % kwargs['contlist']) 
            while 1:
                n = c.currentNode()
                if 'B' in n:
                    contlist.push_back(lk.MoveNC(ord(n['B'][0][0])-97-XX, ord(n['B'][0][1])-97-YY, 'X'))
                if 'W' in n:
                    contlist.push_back(lk.MoveNC(ord(n['W'][0][0])-97-XX, ord(n['W'][0][1])-97-YY, 'O'))
                if c.atEnd: break
                c.next()
        elif 'contsinpattern' in kwargs:
            color = kwargs['contsinpattern']
            for counter in range(1,10):
                i = iPos.find(str(counter))
                if i == -1: break
                # print i%sX, i/sX, color
                contlist.push_back(lk.MoveNC(i%sX, i/sX, color))
                iPos = iPos.replace(str(counter), '.')
                color = 'X' if color == 'O' else 'O'

        contlabels = kwargs.get('contlabels', '.'*len(iPos))

        if 'ptype' in kwargs:
            lk.Pattern.__init__(self, kwargs['ptype'], boardsize, sX, sY, iPos, contlist, contlabels)
        else:
            lk.Pattern.__init__(self, *(kwargs['anchors'] + (boardsize, sX, sY, iPos, contlist, contlabels)))


    def getInitialPosAsList(self, hoshi = False, boundary = False, ):
        '''
        Export current pattern as list of lists, like [ ['.', 'X', '.'], ['O', '.', '.'] ]

        If boundary==True, a boundary of spaces, '-', '|', '+'s is added.
        If hoshi==True, hoshi points are marked with ','. (Of course, this is only applicable for fullboard or corner patterns, or patterns with fixed anchor.)
        '''

        plist = [ list(self.initialPos[i*self.sizeX: (i+1)*self.sizeX]) for i in range(self.sizeY)  ]

        if hoshi and self.left == self.right and self.top == self.bottom:
            if self.boardsize == 19:
                hoshilist = [ (3,3), (3,9), (3,15), (9,3), (9,9), (9,15), (15,3), (15,9), (15,15) ]
            elif self.boardsize == 13:
                hoshilist = [ (3,3), (3,6), (3,9), (6,3), (6,6), (6,9), (9,3), (9,6), (9,9) ]
            elif self.boardsize == 9:
                hoshilist = [ (2,2), (2,4), (2,6), (4,2), (4,4), (4,6), (6,2), (6,4), (6,6) ]
            else:
                hoshilist = []

            for h1, h2 in hoshilist:
                if 0 <= h1 - self.left < self.sizeX  and 0 <= h2 - self.top < self.sizeY and plist[h2 - self.top][h1 - self.left] == '.':
                    plist[h2 - self.top][h1 - self.left] = ','

        if boundary:
            TOP = '-' if self.top == self.bottom == 0 else ' '
            TOPLEFT = '+' if self.top == self.bottom == self.left == self.right == 0 else ' '
            LEFT = '|' if self.left == self.right == 0 else ' '
            BOTTOM = '-' if self.top == self.bottom == self.boardsize - self.sizeY else ' '
            RIGHT = '|' if self.left == self.right == self.boardsize - self.sizeX else ' '
            TOPRIGHT = '+' if self.top == self.bottom == 0 and self.left == self.right == self.boardsize - self.sizeX else ' '
            BOTTOMLEFT = '+' if self.top == self.bottom == self.boardsize - self.sizeY and self.left == self.right == 0 else ' '
            BOTTOMRIGHT = '+' if self.top==self.bottom==self.boardsize-self.sizeY and self.left==self.right==self.boardsize-self.sizeX else ' '
            plist = [ [ TOPLEFT ] + [ TOP ]*self.sizeX + [ TOPRIGHT ] ] + [ [ LEFT ] + x + [ RIGHT ] for x in plist  ] + [ [ BOTTOMLEFT ] + [ BOTTOM ]*(self.sizeX) + [ BOTTOMRIGHT ] ]
            
        return plist


# ------ CURSOR -----------------------------------------------------------------

class Cursor(sgf.Cursor):
    '''A Cursor which is used to traverse an SGF file. See the documentation of
    the :py:mod:`sgf` module for further details.'''

    def __init__(self, *args, **kwargs):
        sgf.Cursor.__init__(self, *args, **kwargs)

    def currentNode(self):
        return Node(self.currentN)


class Node(sgf.Node):
    '''A Node of an SGF file. Also see the documentation of the :py:mod:`sgf`
    module.
    '''

    def __init__(self, *args, **kwargs):
        sgf.Node.__init__(self, *args, **kwargs)

    def exportPattern(self, boardsize=19):
        '''Return a full board pattern with the position at this node.
        '''
        b = abstractBoard(boardsize=boardsize)
        path = [] # compare pathToNode; redo this here since we also need to find corresponding starting node
        n = self

        while n.previous:
            path.append(n.level)
            n = n.previous

        path.reverse()

        def play(n, b):
            for s in ['AB', 'AW', 'B', 'W']:
                if s in n:
                    for p in n[s]:
                        b.play((ord(p[0])-97, ord(p[1])-97), s[-1])

        play(Node(n), b)
        for i in path:
            n = n.next
            for j in range(i): n = n.down
            play(Node(n), b)

        p = ''.join([ {'B':'X', 'W':'O', ' ':'.'}[b.getStatus(x,y)] for y in range(boardsize) for x in range(boardsize) ])
        return Pattern(p, ptype=FULLBOARD_PATTERN)


# ------ GAMELIST ---------------------------------------------------------------

class lkGameList(lk.GameList):

    def __init__(self, *args):
        if len(args) == 1:
            lk.GameList.__init__(self, args[0], '', '[[filename.]],,,[[id]],,,[[PB]],,,[[PW]],,,[[winner]],,,signaturexxx,,,[[date]]', lk.ProcessOptions(), 19, 50000)
        else:
            lk.GameList.__init__(self, *args)



    def getCurrent(self, index):
        return self.currentEntryAsString(index).split(',,,')


    def __getitem__(self, index):
        return self.all[index].gameInfoStr.split(',,,')

    def find_by_ID(self, ID):
        return [i for i, item in enumerate(self.all) if item.id == ID][0]


# compare def loadDBs()
GL_FILENAME = 0
GL_NAMELISTINDEX = 1
GL_PB = 2
GL_PW = 3
GL_RESULT = 4
GL_SIGNATURE = 5
GL_DATE = 6


class GameList(object):
    '''A Kombilo list of games. The list can consist of several Kombilo
    databases. You do not construct instances of this class yourself. Rather,
    every :py:class:`KEngine` instance ``K`` has a unique instance
    ``K.gamelist`` of :py:class:`GameList`.

    As in Kombilo, the GameList maintains a list of games that are "currently
    visible" (think of all games matching some pattern). All search methods and
    many other methods work with this "current list".
    '''

    def __init__(self):
        self.DBlist = []      # list of dicts

        self.Bwins, self.Wwins, self.Owins = 0, 0, 0   # others: Jigo, Void, Left unfinished, ? (Unknown)

        self.references = {}
        self.gameIndex = []
        self.showFilename = 1
        self.showDate = 0
        self.customTags = { '1': ('H', 'Handicap game', ), '2': ('P', 'Professional game', ), str(REFERENCED_TAG): ('C', 'Reference to commentary available', ), str(SEEN_TAG): ('S', 'Seen', ),  }

    def populateDBlist(self, d):
        '''Add the databases specified in the dictionary ``d`` to this
        GameList. ``d`` must have the following format:

        For each key ``k``, ``d[k]`` is a list of three entries. The first
        entry is the ``sgfpath``, i.e. the path where the SGF files of this
        database are stored. The second entry is the path where the Kombilo
        database files are stored, and the third entry is the name of these
        database files, without the extension.

        The keys are assumed to be strings. If``k`` ends with 'disabled', then
        the disabled flag will be set for the corresponding database.

        After adding the databases in this way, you must call
        :py:meth:`KEngine.loadDBs` to load the database files.
        '''
        for db in d:
            line = d[db]
            if db.endswith('disabled'):
                self.DBlist.append({'sgfpath':line[0], 'name':(line[1], line[2]), 'data':[], 'disabled': 1})
            else:
                self.DBlist.append({'sgfpath':line[0], 'name':(line[1], line[2]), 'data': None, 'disabled': 0})


    def printSignature(self, index):
        '''Return the symmetrized Dyer signature of the game at ``index`` in
        the current list of games.
        '''
        if index == -1: return ''
        DBindex, index = self.getIndex(index)
        if DBindex == -1: return ''
        return self.DBlist[DBindex]['data'].getSignature(index)


    def addTag(self, tag, index):
        '''Set tag on game at position index in the current list.
        '''
        DBindex, index = self.getIndex(index)
        if DBindex == -1: return
        self.DBlist[DBindex]['data'].setTag(tag, index, index+1)


    def getTags(self, index):
        '''Get all tags of the game at position index in the current list.
        '''
        DBindex, index = self.getIndex(index)
        if DBindex == -1: return
        return self.DBlist[DBindex]['data'].getTags(index)

    def exportTags(self, filename, which_tags = []):
        '''Export all tags in all non-disabled databases into the file
        specified by ``filename``.

        If which_tags is specified, then it has to be a list of positive
        integers, and only the tags in the list are exported.
        '''
        for db in self.DBlist:
            if db['disabled']: continue
            db['data'].export_tags(filename, which_tags)

    def importTags(self, filename):
        '''The file given by filename should be a file to which previously tags
        have been exported using :py:meth:`exportTags`.

        This method imports all the tags into the current databases. The games
        are identified by the Dyer signature together with a hash value of
        their final position. So unless there are duplicates in the database,
        this should put the tags on those games where they were before
        exporting. In case of duplicates, all duplicates will receive the
        corresponding tags.
        '''
        for db in self.DBlist:
            if db['disabled']: continue
            db['data'].import_tags(filename)


    def getProperty(self, index, prop):
        '''Return a property of the game at position ``index`` in the current
        list of games. Here ``prop`` should be one of the following constants:

        * ``GL_FILENAME`` - the filename
        * ``GL_PB`` - the black player
        * ``GL_PW`` - the white player
        * ``GL_RESULT`` - the result
        * ``GL_SIGNATURE`` - the symmetrized Dyer signature
        * ``GL_DATE`` - the date.
        '''
        DBindex, game = self.getIndex(index)
        if DBindex == -1: return
        ID, pos = self.DBlist[DBindex]['data'].currentList[game]
        return self.DBlist[DBindex]['data'][pos][prop]

    def getSGF(self, index):
        '''Return the SGF source of the game at position ``index`` in the current
        list of games.
        '''
        DBindex, game = self.getIndex(index)
        if DBindex == -1: return
        return self.DBlist[DBindex]['data'].getSGF(game)


    def sortCrit(self, index, c):
        dbIndex, j = self.getIndex(index)
        return self.DBlist[dbIndex]['data'].getCurrent(j)[c] 

    def getIndex(self, i):
        """ Returns dbIndex, j, such that self.DBlist[dbIndex]['current'][j] corresponds to the
        i-th entry of the current list of games. """

        return self.gameIndex[i][-2:] if (i < len(self.gameIndex)) else (-1, -1, )


    def get_data(self, i, showTags=True):
        ''' Return entry in line i of current list of games (as it appears in
        the Kombilo game list window).
        '''

        db, game = self.getIndex(i)
        if db == -1: return
        ID, pos = self.DBlist[db]['data'].currentList[game]
        d = self.DBlist[db]['data'][pos]
        # print ID, pos, d
        res = self.DBlist[db]['data'].resultsStr(self.DBlist[db]['data'].all[pos])
        li = []
        
        if showTags:
            taglist = self.DBlist[db]['data'].getTagsID(ID,0)
            if taglist:
                li.append('['+''.join([ ('%s' % self.customTags[str(x)][0]) for x in taglist if str(x) in self.customTags ]) + '] ')
        
        if self.showFilename:
            endFilename = find(d[GL_FILENAME], '[')
            if endFilename == -1: endFilename = len(d[GL_FILENAME])
        
            if d[GL_FILENAME][endFilename-1] == '.':
                filename = d[GL_FILENAME][:endFilename-1] + d[GL_FILENAME][endFilename:]
            elif d[GL_FILENAME][endFilename-2:endFilename] == '.m':
                filename = d[GL_FILENAME][:endFilename-2] + d[GL_FILENAME][endFilename:]
            else: filename = d[GL_FILENAME]
        
            li.append(filename + ': ')

        li.append(d[GL_PW] + ' - ' + d[GL_PB] + ' (' + d[GL_RESULT] + '), ')
        if self.showDate: li.append(d[GL_DATE]+', ')
        li.append(res)
        return ''.join(li)


    def reset(self):
        """ Reset the list, s.t. it includes all the games from self.data. """
        
        for db in self.DBlist:
            if db['disabled']: continue
            db['data'].reset()
        self.Bwins, self.Wwins, self.Owins = 0, 0, 0
        self.update()

        
    def update(self, sortcrit = GL_DATE, sortReverse = False, ):
        self.gameIndex = []
        self.Bwins, self.Wwins = 0, 0

        for i, db in enumerate(self.DBlist):
            if db['disabled']:
                continue
            self.Bwins += db['data'].Bwins
            self.Wwins += db['data'].Wwins
            self.gameIndex.extend([ ( db['data'].getCurrent(x)[sortcrit], i, x) for x in xrange(db['data'].size()) ])

        self.gameIndex.sort()
        if sortReverse: self.gameIndex.reverse()
        # assert len(self.gameIndex) == sum([ db['data'].size() for db in self.DBlist if not db['disabled'] ])
        # assert len(self.gameIndex) == self.noOfGames()


    def noOfGames(self):
        '''Return the number of games in the current list of games.
        '''
        return sum([ db['data'].size() for db in self.DBlist if not db['disabled'] ])

    def noOfHits(self):
        '''Return the number of hits for the last pattern search.
        '''
        return sum([ db['data'].num_hits for db in self.DBlist if not db['disabled'] ])

    def noOfSwitched(self):
        '''Return the number of hits where the colors are reversed for the last
        pattern search.
        '''
        return sum([ db['data'].num_switched for db in self.DBlist if not db['disabled'] ])


    def listOfCurrentSGFFiles(self):
        '''Return a list of file names for all SGF files of games in the
        current list of games.
        '''
        l = []
        for db in self.DBlist:
            if db['disabled']: continue
            for i in xrange(db['data'].size()):
                l.append(os.path.join(db['sgfpath'], getFilename(db['data'].getCurrent(i)[GL_FILENAME])))
        return l  


    def printGameInfo(self, index):
        '''Return a pair whose first entry is a string containing the game info
        for the game at index. The second entry is a string giving the
        reference to commentaries in the literature, if available.
        '''

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
            f = open(filename)
            sgf = f.read()
            c = Cursor(sgf, 1)

            f.close()
            node = c.getRootNode(gameNumber)
        except:
            return

        t = node['PW'][0] if node.has_key('PW') else ' ?'
        t += (' ' + node['WR'][0]) if node.has_key('WR') else ''
        t += ' - '

        t += node['PB'][0] if node.has_key('PB') else ' ?'
        t += (' ' + node['BR'][0]) if node.has_key('BR') else ''

        if node.has_key('RE'): t = t + ', ' + node['RE'][0]
        if node.has_key('KM'): t = t + ' (Komi ' + node['KM'][0] + ')'
        if node.has_key('HA'): t = t + ' (Hcp ' + node['HA'][0] + ')'

        t = t + '\n'

        if node.has_key('EV'): t = t + node['EV'][0] + ', '
        if node.has_key('RO'): t = t + node['RO'][0] + ', '
        if node.has_key('DT'): t = t + node['DT'][0] + '\n'

        if node.has_key('GC'):
            gc = node['GC'][0]
            gc = replace(gc, '\n\r', ' ')
            gc = replace(gc, '\r\n', ' ')
            gc = replace(gc, '\r', ' ')
            gc = replace(gc, '\n', ' ')
            
            t = t + gc

        signature = self.DBlist[DBindex]['data'].getSignature(index)
        t2 = ('Commentary in ' + ', '.join(self.references[signature])) if signature in self.references else ''

        return t, t2
        



class KEngine(object):
    '''
    This is the class which you use to use the Kombilo search functionality.

    After instantiating it, you need to tell the gamelist which databases you
    want to use, e.g. using :py:meth:`GameList.populateDBlist`, and then call
    :py:meth:`loadDBs`. Afterwards you can use :py:meth:`patternSearch`, for
    instance.

    See the Kombilo documentation on further information how to get started.

    **Further notes.**

    After a pattern search, the continuations are assembled into the list
    ``self.continuations``, whose entries are lists [ total number of hits,
    x-coordinate in currentSearchPattern, y-coordinate in currentSearchPattern,
    number of black continuations, number of black wins after black play here,
    number of black losses after black play here, number of black plays here
    after tenuki, number of white continuations, number of black wins after
    white play here, number of black losses after white play here, number of
    white plays here after tenuki, label used on the board at this point ]
    '''


    def __init__(self):
        self.gamelist = GameList()
        self.currentSearchPattern = None



    def patternSearch(self, CSP, SO=None, CL = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789', FL = {}, progBar=None):
        '''Start a pattern search on the current game list.
        
        * CSP must be an instance of :py:class:`Pattern` - it is the pattern
          that is searched for.
        * You can specify search options as `SO` - this must be an instance of
          ``lk.SearchOptions`` (see below).
        * ``CL``, ``FL``, ``progBar`` are used with the Kombilo GUI.

        **Search options.** 
        Create an instance of ``lk.SearchOptions`` by ::
        
          so = lk.SearchOptions

        You can then set particular options on ``so``, e.g.::

          so.fixedColor = 1
          so.searchInVariations = false

        Available options:

        * fixedColor, values: 0 = also search for pattern with colors reversed;
          1 = fix colors as given in pattern; default value is 0
        * nextMove, values: 0 either player moves next, 1 = next move must be
          black, 2 = next move must be white; default value is 0
        * moveLimit, positive integer; pattern must occur at this move in the
          game or earlier; default value is 10000
        * trustHashFull, boolean, values: true = do not use ALGO_MOVELIST to
          confirm a hit given by ALGO_HASH_FULL, false = use ALGO_MOVELIST to
          confirm it; default value is false
        * searchInVariations, boolean; default value is true
        * algos, an integer which specifies which algorithms should be used; in
          practice, use one of the following::

            lk.ALGO_FINALPOS | lk.ALGO_MOVELIST
            lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL
            lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_FULL | lk.ALGO_HASH_CORNER

          The default is to use all available algorithms.
        '''
        self.currentSearchPattern = CSP
        self.searchOptions = SO if SO else lk.SearchOptions(0, 0, 10000)
        # self.searchOptions.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST # | lk.ALGO_HASH_CORNER | lk.ALGO_HASH_FULL
        # self.searchOptions.trustHashFull = True
        self.contLabels = CL
        self.fixedLabels = FL

        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0 
        self.continuations = []
        if progBar:
            progBar.configure(value=5)
            progBar.update()
        done = 0

        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            gl = db['data']
            # print self.searchOptions.algos
            gl.search(self.currentSearchPattern, self.searchOptions)

            done += db['data'].all.size()
            if progBar:
                if self.gamelist.noOfGames():
                    progBar.configure(value= min(99, int(done*100.0/self.gamelist.noOfGames())))
                else:
                    progBar.configure(value=1)
                progBar.update()

            self.lookUpContinuations(gl)

        self.setLabels()
        self.gamelist.update()



    def lookUpContinuations(self, gl):
        self.noMatches += gl.num_hits
        self.noSwitched += gl.num_switched
        self.Bwins += gl.Bwins
        self.Wwins += gl.Wwins

        for y in range(self.currentSearchPattern.sizeY):
            for x in range(self.currentSearchPattern.sizeX):
                if gl.lookupLabel(x,y) != '.':
                    for c in self.continuations:
                        if c[1] == x and c[2] == y: # exists
                            ll = c
                            break
                    else:
                        ll = [ 0, x, y, 0, 0, 0, 0, 0, 0, 0, 0, '?' ]
                        self.continuations.append(ll)
                    cont = gl.lookupContinuation(x,y)
                    ll[0] += cont.B + cont.W
                    for i, val in enumerate([ cont.B, cont.wB, cont.lB, cont.tB, cont.W, cont.wW, cont.lW, cont.tW ]):
                        ll[i+3] += val


    def setLabels(self):
        self.continuations.sort()
        self.continuations.reverse()
        # print self.continuations
        i = 0
        for c in self.continuations:
            x, y = c[1:3]
            if (x,y) in self.fixedLabels: lab = self.fixedLabels[(x,y)]
            elif i < len(self.contLabels):
                lab = self.contLabels[i]
                i += 1
            else: lab = '?'
            c[-1] = lab.encode('utf-8') if type(lab) == type(u'') else lab
            for db in self.gamelist.DBlist:
                if db['disabled']: continue
                db['data'].setLabel(x, y, c[-1])


    def gameinfoSearch(self, query):
        '''Do a game info search on the current list of games.

        * ``query`` provides the query as part of an SQL clause which can be
          used as an SQL WHERE clause. Examples::

            date >= '2000-03-00'
            PB = 'Cho Chikun'
            PB like 'Cho%'
            PW like 'Go Seigen' and not PB like 'Hashimoto%'

          After the ``like`` operator, you can use the percent sign ``%`` as a
          wildcard to mach arbitrary text.

          The columns in the database are ::

            PB (player black)
            PW (player white)
            RE (result)
            EV (event)
            DT (the date as given in the sgf file)
            date (the date in the form YYYY-MM,DD)
            filename
            sgf (the full SFG source).
        '''
        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            db['data'].gisearch(query)

        self.gamelist.update()


    def gameinfoSearchNC(self, query):
        '''Returns the number of games matching the given query (see
        :py:meth:`gameinfoSearch` for the format of the query) **without
        changing the list of current games**.
        '''
        count = 0
        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            count += db['data'].gisearchNC(query).size()

        return count


    def dateProfileRelative(self):
        '''Return the ratios of games in the current list versus games in the
        whole database, for each of the date intervals specified in
        :py:meth:`dateProfile`.
        '''
        d = self.dateProfile()
        return [ (x, y, self.dateProfileWholeDB[i][1]) for i, (x, y) in enumerate(d) ]


    def dateProfile(self, intervals = None):
        '''Return the absolute numbers of games in the given date intervals
        among the games in the current list of games.

        Default value for ``intervals`` is ::

          [ (0, 1900), (1900, 1950), (1950, 1975), (1975, 1985), (1985, 1992),
          (1992, 1997), (1997, 2002), (2002, 2006), (2006, 2009), (2009, 2013),
          ]
        '''
        if intervals is None:
            intervals = [ (0, 1900), (1900, 1950), (1950, 1975), (1975, 1985),
                    (1985, 1992), (1992, 1997), (1997, 2002), (2002, 2006),
                    (2006, 2009), (2009, 2013),  ]

        return [ (i, self.gameinfoSearchNC("date >= '%d-00-00' and date < '%d-00-00'" % i)) for i in intervals ]



    def signatureSearch(self, sig):
        '''Do a signature search for the Dyer signature ``sig``.
        '''
        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0 
        noGames = self.gamelist.noOfGames()

        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            gl = db['data']
            gl.sigsearch(sig)
            self.noMatches += gl.num_hits
            self.noSwitched += gl.num_switched
            self.Bwins += gl.Bwins
            self.Wwins += gl.Wwins
                    
        self.gamelist.update()


    def tagSearch(self, tag):
        '''
        Do a tag search on the current game list.

        tag can be an expression like ``H and (X or not M)``, where H, X, M are
        abbreviations for tags (i.e. keys in self.gamelist.customTags). In the
        simplest example, tag == ``H``, i.e. we just search for all games tagged
        with ``H``.
        '''

        if not self.gamelist.noOfGames(): return
        query = tag.replace('(', ' ( ').replace(')', ' ) ').split()
        if not query: return
        for i, q in enumerate(query):
            if not q in ['and', 'or', 'not', '(', ')']:
                for t in self.gamelist.customTags:
                    if self.gamelist.customTags[t][0] == q: break # find the integer handle corresponding to the given abbreviation
                else:
                    self.logger.insert('end', 'Invalid query.\n')
                    return
                query[i] = 'exists(select * from game_tags where game_id=games.id and tag_id=%s)' % t

        for db in self.gamelist.DBlist:
            if db['disabled']: continue
            db['data'].tagsearchSQL(' '.join(query))
        self.gamelist.update()

        



    def patternSearchDetails(self, exportMode='ascii', showAllCont=False):
        '''Returns a string with information on the most recent pattern search.
        '''

        t = []
        if self.currentSearchPattern: 
            p = self.currentSearchPattern
            plist = p.getInitialPosAsList(boundary=True, hoshi = True)
            
            l1 = [ ' '.join(x).strip() for x in plist ]

            N = 400 if showAllCont else 10
            for cont in self.continuations[:N]:
                x, y = cont[1]+1, cont[2]+1
                if plist[y][x] in ['.', ',']: plist[y][x] = cont[11] # plist[y] is the y-th *line* of the pattern, i.e. consists of the points with coordinates (0, y), ..., (boardsize-1, y).
            l2 = [ ' '.join(x).strip() for x in plist ]
        
            s1 = '$$B Search Pattern\n$$' + join(l1, '\n$$') + '\n' if exportMode=='wiki' else join(l1, '\n') 
            s2 = '$$B Continuations\n$$' + join(l2, '\n$$') + '\n' if exportMode=='wiki' else join(l2, '\n')

            if exportMode=='wiki': t.append('!')
            t.append('Search results\n\n')
            if not exportMode=='wiki': t.append('Pattern:\n')

            t.append(s1)

            if not exportMode=='wiki': t.append('\n\nContinuations:\n')
            else: t.append('\n\n')
        
            t.append(s2)
            t.append('\n')

            if self.continuations:
                if exportMode=='wiki': t.append('%%%%\n!')
                else: t.append('\n')

                t.append('Statistics:\n')

                Bperc = self.Bwins * 100.0 / self.noMatches
                Wperc = self.Wwins * 100.0 / self.noMatches

                t.append('%d matches (%d/%d), B: %1.1f%%, W: %1.1f%%' % (self.noMatches, self.noMatches-self.noSwitched, self.noSwitched, Bperc, Wperc))

                if exportMode=='wiki': t.append(' %%%\n')
                t.append('\n')

                for cont in self.continuations[:N]:
                    if cont[3]: # black continuations
                        t.append('B%s:    %d (%d), ' % (cont[11], cont[3], cont[3]-cont[6]))
                        t.append('B %1.1f%% - W %1.1f%%' % (cont[4]*100.0/cont[3], cont[5]*100.0/cont[3]))
                        if exportMode=='wiki': t.append(' %%%')
                        t.append('\n')
                    if cont[7]: # white continuations
                        t.append('W%s:    %d (%d), ' % (cont[11], cont[7], cont[7]-cont[10]))
                        t.append('B %1.1f%% - W %1.1f%%' % (cont[8]*100.0/cont[7], cont[9]*100.0/cont[7]))
                        if exportMode=='wiki': t.append(' %%%')
                        t.append('\n')

                t.append('\n')
                if exportMode=='wiki': t.append('!')

                t.append('Hits per database\n')
                for db in self.gamelist.DBlist:
                    if db['disabled']: continue
                    t.append(db['sgfpath'] + ': ' + `db['data'].size()` + ' games (of ' + `db['data'].all.size()` + ')')
                    if exportMode=='wiki': t.append(' %%%')
                    t.append('\n')

        return ''.join(t)


    def copyCurrentGamesToFolder(self, dir):
        '''Copy all SGF files belonging to games in the current list to the
        folder given as ``dir``.
        '''
        l = self.gamelist.listOfCurrentSGFFiles()
        for f in l:
            inf = open(f)
            s = inf.read()
            inf.close()

            outfile = os.path.join(dir, os.path.split(f)[-1])
            if os.path.exists(outfile): continue
            out = open(outfile, 'w')
            out.write(s)
            out.close()



    def parseReferencesFile(self, datafile, options = None):
        '''Parse a file with references to commentaries in the literature. See
        the file ``src/data/references`` for the file format.

        The method builds up ``self.gamelist.references``, a dictionary which
        for each Dyer signature has a list of all references for the
        corresponding game.
        '''

        include = [] # if no items are explicitly included, we take that as "include everything that's not excluded"
        exclude = []
        if options:
            def parse_list(d):
                result = []
                for item in d:
                    if not d[item]:
                        result.append(item)
                    else:
                        try: # is this a range of integers? (e.g., translate '4-6' to [ item 4, item 5, item 6 ])
                            ll = d[item].split('-')
                            assert len(ll) == 2
                            result.extend([ '%s %d' % (item, i) for i in range(int(ll[0]), int(ll[1]))])
                        except:
                            result.append(item + ' ' + d[item].strip())
                return result

            exclude = parse_list(options['exclude']) if 'exclude' in options else []
            include = parse_list(options['include']) if 'include' in options else []

        self.gamelist.references = defaultdict(list)
        try:
            with open(datafile) as ref_file:
                c = ConfigObj(infile=ref_file)
                if 'boardsize' in c:
                    boardsize = int(c['boardsize'])
                    del c['boardsize']
                else:
                    boardsize = 19
                for k in c:
                    if k in exclude: continue
                    if include and not k in include: continue
                    for sig in c[k]['data']:
                        symmsig = lk.symmetrize(sig, boardsize)
                        self.gamelist.references[symmsig].append(c[k]['title'])
        except: pass


    def loadDBs(self, progBar = None, showwarning = None):
        '''Load the database files for all databases that were added to the
        gamelist.
        '''

        DBlistIndex = 0
        for i in range(len(self.gamelist.DBlist)):
            if progBar: progBar.update()
            db = self.gamelist.DBlist[DBlistIndex]
            if db['disabled']:
                db['data'] = None
            else:
                try:
                    db['data'] = lkGameList(os.path.join(db['name'][0], db['name'][1]+'.db'))
                except: 
                    if showwarning: showwarning('IOError', 'Could not open database %s/%s.' % db['name'])
                    del self.gamelist.DBlist[DBlistIndex]
                    continue
            DBlistIndex += 1  # May differ from loop counter if databases which cannot be opened are omitted.
        self.gamelist.reset()
        self.dateProfileWholeDB = self.dateProfile()

    # ---------- database administration (processing etc.)

    def find_duplicates(self, strict=True, dupl_within_db=True):
        return lk.find_duplicates([os.path.join(db['name'][0], db['name'][1]+'.db') for db in self.gamelist.DBlist if not db['disabled']],
                                  strict, dupl_within_db)

    def addDB(self, dbp, datap=('', '#'), recursive=True, filenames = '*.sgf', acceptDupl=True, strictDuplCheck=True,
              tagAsPro=0, processVariations = 1, algos = None,
              messages=None, progBar=None, showwarning=None, index=None):
        '''
        Call this method to newly add a database of SGF files.

        Parameters:

        * dbp: the path where the sgf files are to be found.
        * datap:
          the path where the database files will be stored. Leaving the default
          value means: store database at dbp, with base filename 'kombilo'.
          Instead, you can specify a pair (path, filename). Then
          path/filenameN.d? will be the locations of the database files.  Every
          Kombilo database consists of several files; they will have names with
          ? equal to a, b, ...  N is a natural number chosen to make the file
          name unique.
        * recursive: specifies whether subdirectories should be included recursively
        * messages: a 'message text window' which receives status messages
        * progBar: a progress bar
        * showwarning: a method which display warnings (like Tkinter showwarning)
        '''

        if recursive:
            os.path.walk(dbp, self.addOneDB,
                         (filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar, showwarning, datap, index))
        else:
            self.addOneDB((filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar, showwarning, datap, index),
                          dbp, None)
    
        

    def addOneDB(self, arguments, dbpath, dummy):        # dummys needed for os.path.walk

        filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar, showwarning, datap, index = arguments
        # print 'addOneDB', datap, dbpath

        if datap == ('', '#'): datap = (dbpath, 'kombilo')

        if os.path.isfile(os.path.join(datap[0], datap[1] + '.db')): # if file exists, append a counter
            i = 1
            while os.path.isfile(os.path.join(datap[0], datap[1] + '%d.db' % i)): i += 1
            datapath = (datap[0], datap[1]+'%d' % i)
        else:
            datapath = datap

        if os.path.isfile(os.path.join(datapath[0], datapath[1]+'.db')):
            if showwarning: showwarning('Error', 'A kombilo database already exists at %s. Please remove it first, or reprocess that database.' % os.path.join(datapath[0], datapath[1]))
            return

        try:
            gl = self.process(dbpath, datapath, filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar)
        except:
            if showwarning: showwarning('Error', 'A fatal error occured when processing ' + dbpath + '. Are the directories for the database files writable?')
            return

        if gl == None:
            if messages: messages.insert('end', 'Directory %s contains no sgf files.\n' % dbpath)
            return
        # open the lkGameList:
        if index is None:
            self.gamelist.DBlist.append({'name': datapath, 'sgfpath':dbpath, 'data': gl, 'disabled': 0})
        else:
            self.gamelist.DBlist[index:index] = [{'name':datapath, 'sgfpath':dbpath, 'data': gl, 'disabled': 0}]
        self.currentSearchPattern = None
        self.gamelist.update()
        if messages: messages.insert('end', 'Added ' + dbpath + '.\n')
        return gl != None


    def process(self, dbpath, datap, filenames='*.sgf', acceptDupl = True, strictDuplCheck=True, tagAsPro = 0,
                processVariations = 1, algos = None, messages = None, progBar = None, deleteDBfiles = False):
        if progBar:
            progBar.configure(value=0)
            progBar.update()
        if messages:
            messages.insert('end', 'Processing ' + dbpath + '.\n')
            messages.update()
        if filenames == '*.sgf':
            filelist = glob.glob(os.path.join(dbpath,'*.sgf'))
        elif filenames == '*.sgf, *.mgt':
            filelist = glob.glob(os.path.join(dbpath,'*.sgf')) + glob.glob(os.path.join(dbpath, '*.mgt'))
        else:
            filelist = glob.glob(os.path.join(dbpath,'*'))
        if len(filelist) == 0: return
        filelist.sort()

        gls = lk.vectorGL()
        for db in self.gamelist.DBlist:
            if not db['disabled']: # for disabled db's, db['data'] is None
                gls.push_back(db['data'])

        pop = lk.ProcessOptions()
        pop.rootNodeTags = 'PW,PB,RE,DT,EV'
        pop.sgfInDB = True
        pop.professional_tag = tagAsPro
        pop.processVariations = processVariations
        pop.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST
        if algos: pop.algos |= algos
        if deleteDBfiles and os.path.exists(os.path.join(datap[0], datap[1]+'.db')):
            if messages:
                messages.insert('end', 'Delete old database files.')
                messages.update()
            for ext in [ 'db', 'da', 'db1', 'db2', ]:
                try:
                    os.remove(os.path.join(datap[0], datap[1]+'.%s' % ext))
                except:
                    if messages:
                        messages.insert('end', 'Unable to delete database file %s.' % os.path.join(datap[0], datap[1]+'.%s' % ext))
                        messages.update()

        gl = lkGameList(os.path.join(datap[0], datap[1]+'.db'), 'DATE', '[[filename.]],,,[[id]],,,[[PB]],,,[[PW]],,,[[winner]],,,signaturexxx,,,[[date]],,,', pop, 19, 5000)
        # TODO boardsize

        gl.start_processing()
        for counter, filename in enumerate(filelist):
            if progBar and counter%100 == 0:
                progBar.configure(value=counter*100.0/len(filelist))
                progBar.update()
            try:
                file = open(filename)
                sgf = file.read()
                file.close()
            except:
                if messages:
                    messages.insert('end', 'Unable to read file %s' % filename)
                    messages.update()
                continue

            path, fn = os.path.split(filename)
            pops = lk.CHECK_FOR_DUPLICATES
            if not acceptDupl:
                pops |= lk.OMIT_DUPLICATES
            if strictDuplCheck: pops |= lk.CHECK_FOR_DUPLICATES_STRICT

            try:
                if gl.process(sgf, path, fn, gls, '', pops):
                    pres = gl.process_results()
                    if messages:
                        if pres & lk.IS_DUPLICATE:
                            messages.insert('end', 'Duplicate ... %s\n' % filename)
                            messages.update()
                        if pres & lk.SGF_ERROR:
                            messages.insert('end', 'SGF error, file %s, %d\n' % (filename, pres))
                            messages.update()
                        if pres & lk.UNACCEPTABLE_BOARDSIZE:
                            messages.insert('end', 'Unacceptable board size error, file %s, %d\n' % (filename, pres))
                            messages.update()
                        if pres & lk.NOT_INSERTED_INTO_DB:
                            messages.insert('end', 'not inserted\n')
                            messages.update()
                elif messages:
                    messages.insert('end', 'SGF error, file %s, not inserted.\n' % filename)
                    messages.update()
            except:
                if messages:
                    messages.insert('end', 'SGF error, file %s. Not inserted.\n' % filename)
                    messages.update()
            
        messages.insert('end', 'Finalizing ... (this will take some time)\n')
        messages.update()
        gl.finalize_processing()

        for ref in self.gamelist.references:
            for gid in gl.sigsearchNC(ref):
                # print gid, ref, self.gamelist.references[ref],
                gl.setTagID(REFERENCED_TAG, gid)
        if progBar: progBar.stop()

        return gl


    # ---------- misc tools

    def getFilename(self, no):
        dbindex, index = self.gamelist.getIndex(no)
        if dbindex == -1: return
        ID, pos = self.gamelist.DBlist[dbindex]['data'].currentList[index]
        
        moveno = (0, )
        s = self.gamelist.DBlist[dbindex]['data'].resultsStr(self.gamelist.DBlist[dbindex]['data'].all[pos])
        if s:
            i = 0
            while s[i] in digits + '-': i += 1
            if i: moveno = tuple([ int(x) for x in s[:i].split('-') ])

        # print 's', s
        # print 'moveno', moveno

        f1 = strip(os.path.join(self.gamelist.DBlist[dbindex]['sgfpath'], self.gamelist.DBlist[dbindex]['data'].getCurrent(index)[GL_FILENAME]))
        if find(f1, '[') != -1:
            f1, f2 = split(f1, '[')
            gameNumber = int(strip(f2)[:-1])
        else: gameNumber = 0
                
        filename = getFilename(f1)        

        return filename, gameNumber, moveno

