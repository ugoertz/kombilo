#! /usr/bin/env python
# File: kombiloNG.py

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
from string import split, find, join, strip, digits
from collections import defaultdict
from copy import copy
import glob
from array import *
from configobj import ConfigObj

import libkombilo as lk
from abstractboard import abstractBoard
import sgf

import __builtin__
if not '_' in __builtin__.__dict__:
    # print 'kombiloNG ignores translations'
    _ = lambda s: s

KOMBILO_VERSION = '0.8'

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
    if s[-1] == '.':
        return s[:-1]        # no extension
    elif s[-2:] == '.m':
        return s + 'gt'      # extension '.mgt'
    else:
        return s + '.sgf'    # extension '.sgf'


class dummyMessages:
    def insert(self, *args):
        pass
    def update(self):
        pass


def translateRE(s):
    '''
    Try to provide accurate translation of REsult string in an SGF file.
    See also the notes of Andries Brouwer at
    http://homepages.cwi.nl/~aeb/go/misc/sgfnotes.html
    '''

    if s in ['0', 'J', 'Jigo', 'Draw']:
        return _('Jigo')

    if s in ['Void', ]:
        return _('No result')

    if s in ['?', 'Unknown', ]:
        return _('Result unknown')

    if s in ['Both lost', ]:
        return _('Both lost')

    if s in ['Unfinished', 'Left unfinished', 'U', 'UF', ]:
        return _('Unfinished')

    for reason in ['Time', 'Forfeit', 'Resign']:
        if s[1:].startswith('+' + reason):
            return _(s[0]) + '+' + _(reason) + (_(s[len(reason)+2:]) if s[len(reason)+2:] else '')
        if s[1:].startswith('+' + reason[0]):
            return _(s[0]) + '+' + _(reason) + (_(s[3:]) if s[3:] else '')

    if s.startswith('B+') or s.startswith('W+'):
        # print(s, ' --- ', _(s[0]) + s[1:])
        return _(s[0]) + s[1:]

    # print('unable to translate RE')
    return s

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
        iPos = p.replace(' ', '').replace(',', '.').replace('\n', '').replace('\r', '')
        boardsize = kwargs.get('boardsize', 19)
        sX = kwargs.get('sizeX', 0)
        sY = kwargs.get('sizeY', 0)

        if 'ptype' in kwargs and kwargs['ptype'] == FULLBOARD_PATTERN:
            sX, sY = boardsize, boardsize
        if sY == 0:
            sY = len(iPos) // sX  # determine vertical size from horizontal size and total size of pattern
        # for i in range(sY): print iPos[i*sX:(i+1)*sX]

        contlist = lk.vectorMNC()
        if 'contlist' in kwargs and kwargs['contlist']:  # FIXME does not work correctly if there are captures!
            XX, YY = kwargs.get('topleft', (0, 0))

            c = Cursor('(%s)' % kwargs['contlist'])
            while 1:
                n = c.currentNode()
                if 'B' in n:
                    contlist.push_back(lk.MoveNC(ord(n['B'][0][0]) - 97 - XX, ord(n['B'][0][1]) - 97 - YY, 'X'))
                if 'W' in n:
                    contlist.push_back(lk.MoveNC(ord(n['W'][0][0]) - 97 - XX, ord(n['W'][0][1]) - 97 - YY, 'O'))
                if c.atEnd:
                    break
                c.next()
        elif 'contsinpattern' in kwargs:
            color = kwargs['contsinpattern']
            for counter in range(1, 10):
                i = iPos.find(str(counter))
                if i == -1:
                    break
                # print i%sX, i/sX, color
                contlist.push_back(lk.MoveNC(i % sX, i // sX, color))
                iPos = iPos.replace(str(counter), '.')
                color = 'X' if color == 'O' else 'O'

        contlabels = kwargs.get('contlabels', '.' * len(iPos))

        if 'ptype' in kwargs:
            lk.Pattern.__init__(self, kwargs['ptype'], boardsize, sX, sY, iPos, contlist, contlabels)
        else:
            lk.Pattern.__init__(self, *(kwargs['anchors'] + (boardsize, sX, sY, iPos, contlist, contlabels)))

    def getInitialPosAsList(self, hoshi=False, boundary=False, ):
        '''
        Export current pattern as list of lists, like [ ['.', 'X', '.'], ['O', '.', '.'] ]

        If boundary==True, a boundary of spaces, '-', '|', '+'s is added.
        If hoshi==True, hoshi points are marked with ','. (Of course, this is only applicable for fullboard or corner patterns, or patterns with fixed anchor.)
        '''

        plist = [list(self.initialPos[i * self.sizeX: (i + 1) * self.sizeX]) for i in range(self.sizeY)]

        if hoshi and self.left == self.right and self.top == self.bottom:
            if self.boardsize == 19:
                hoshilist = [(3, 3), (3, 9), (3, 15), (9, 3), (9, 9), (9, 15), (15, 3), (15, 9), (15, 15)]
            elif self.boardsize == 13:
                hoshilist = [(3, 3), (3, 6), (3, 9), (6, 3), (6, 6), (6, 9), (9, 3), (9, 6), (9, 9)]
            elif self.boardsize == 9:
                hoshilist = [(2, 2), (2, 4), (2, 6), (4, 2), (4, 4), (4, 6), (6, 2), (6, 4), (6, 6)]
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
            BOTTOMRIGHT = '+' if self.top == self.bottom == self.boardsize - self.sizeY and self.left == self.right == self.boardsize - self.sizeX else ' '
            plist = [[TOPLEFT] + [TOP] * self.sizeX + [TOPRIGHT]] + [[LEFT] + x + [RIGHT] for x in plist] + [[BOTTOMLEFT] + [BOTTOM] * self.sizeX + [BOTTOMRIGHT]]

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


# ------ GAMELIST ---------------------------------------------------------------


class lkGameList(lk.GameList):

    def __init__(self, *args):
        try:
            args = [(x.encode('utf8') if type(x)==type(u'') else x) for x in args]
        except:
            pass
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
        self.customTags = {'1': ('H', 'Handicap game', ),
                           '2': ('P', 'Professional game', ),
                           str(REFERENCED_TAG): ('C', 'Reference to commentary available', ),
                           str(SEEN_TAG): ('S', 'Seen', ), }

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
                self.DBlist.append({'sgfpath': line[0], 'name': (line[1], line[2]), 'data': [], 'disabled': 1})
            else:
                self.DBlist.append({'sgfpath': line[0], 'name': (line[1], line[2]), 'data': None, 'disabled': 0})

    def printSignature(self, index):
        '''Return the symmetrized Dyer signature of the game at ``index`` in
        the current list of games.
        '''
        if index == -1:
            return ''
        DBindex, index = self.getIndex(index)
        if DBindex == -1:
            return ''
        return self.DBlist[DBindex]['data'].getSignature(index)

    def addTag(self, tag, index):
        '''Set tag on game at position index in the current list.
        '''
        DBindex, index = self.getIndex(index)
        if DBindex == -1:
            return
        self.DBlist[DBindex]['data'].setTag(tag, index, index + 1)

    def getTags(self, index):
        '''Get all tags of the game at position index in the current list.
        '''
        DBindex, index = self.getIndex(index)
        if DBindex == -1:
            return
        return self.DBlist[DBindex]['data'].getTags(index)

    def exportTags(self, filename, which_tags=[]):
        '''Export all tags in all non-disabled databases into the file
        specified by ``filename``.

        If which_tags is specified, then it has to be a list of positive
        integers, and only the tags in the list are exported.
        '''
        for db in self.DBlist:
            if db['disabled']:
                continue
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
            if db['disabled']:
                continue
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
        if DBindex == -1:
            return
        ID, pos = self.DBlist[DBindex]['data'].currentList[game]
        return self.DBlist[DBindex]['data'][pos][prop]

    def getSGF(self, index):
        '''Return the SGF source of the game at position ``index`` in the current
        list of games.
        '''
        DBindex, game = self.getIndex(index)
        if DBindex == -1:
            return
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
        if db == -1:
            return
        ID, pos = self.DBlist[db]['data'].currentList[game]
        d = self.DBlist[db]['data'][pos]
        # print ID, pos, d
        res = self.DBlist[db]['data'].resultsStr(self.DBlist[db]['data'].all[pos])
        li = []

        if showTags:
            taglist = self.DBlist[db]['data'].getTagsID(ID, 0)
            if taglist:
                li.append('[' + ''.join([('%s' % self.customTags[str(x)][0]) for x in taglist if str(x) in self.customTags]) + '] ')

        if self.showFilename:
            endFilename = find(d[GL_FILENAME], '[')
            if endFilename == -1:
                endFilename = len(d[GL_FILENAME])

            if d[GL_FILENAME][endFilename - 1] == '.':
                filename = d[GL_FILENAME][:endFilename - 1] + d[GL_FILENAME][endFilename:]
            elif d[GL_FILENAME][endFilename - 2:endFilename] == '.m':
                filename = d[GL_FILENAME][:endFilename - 2] + d[GL_FILENAME][endFilename:]
            else:
                filename = d[GL_FILENAME]

            li.append(filename + ': ')

        li.append(d[GL_PW] + ' - ' + d[GL_PB] + ' (' + _(d[GL_RESULT]).encode('utf8') + '), ')
        if self.showDate:
            li.append(d[GL_DATE] + ', ')
        li.append(res)
        return ''.join(li)

    def reset(self):
        """ Reset the list, s.t. it includes all the games from self.data. """

        for db in self.DBlist:
            if db['disabled']:
                continue
            db['data'].reset()
        self.Bwins, self.Wwins, self.Owins = 0, 0, 0
        self.update()

    def update_winning_percentages(self):
        self.Bwins, self.Wwins = 0, 0

        for i, db in enumerate(self.DBlist):
            if db['disabled']:
                continue
            self.Bwins += db['data'].Bwins
            self.Wwins += db['data'].Wwins

    def update(self, sortcrit=GL_DATE, sortReverse=False, ):
        self.gameIndex = []
        self.update_winning_percentages()

        for i, db in enumerate(self.DBlist):
            if db['disabled']:
                continue
            self.gameIndex.extend([(db['data'].getCurrent(x)[sortcrit], i, x) for x in xrange(db['data'].size())])

        self.gameIndex.sort()
        if sortReverse:
            self.gameIndex.reverse()
        # assert len(self.gameIndex) == sum([ db['data'].size() for db in self.DBlist if not db['disabled'] ])
        # assert len(self.gameIndex) == self.noOfGames()

    def noOfGames(self):
        '''Return the number of games in the current list of games.
        '''
        return sum([db['data'].size() for db in self.DBlist if not db['disabled']])

    def noOfHits(self):
        '''Return the number of hits for the last pattern search.
        '''
        return sum([db['data'].num_hits for db in self.DBlist if not db['disabled']])

    def noOfSwitched(self):
        '''Return the number of hits where the colors are reversed for the last
        pattern search.
        '''
        return sum([db['data'].num_switched for db in self.DBlist if not db['disabled']])

    def listOfCurrentSGFFiles(self):
        '''Return a list of file names for all SGF files of games in the
        current list of games.
        '''
        l = []
        for db in self.DBlist:
            if db['disabled']:
                continue
            for i in xrange(db['data'].size()):
                l.append(os.path.join(db['sgfpath'], getFilename(db['data'].getCurrent(i)[GL_FILENAME])))
        return l

    def printGameInfo(self, index):
        '''Return a pair whose first entry is a string containing the game info
        for the game at index. The second entry is a string giving the
        reference to commentaries in the literature, if available.
        '''

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
            f = open(filename)
            sgf = f.read()
            c = Cursor(sgf, 1)

            f.close()
            node = c.getRootNode(gameNumber)
        except:
            return

        t = node['PW'][0] if 'PW' in node else ' ?'
        t += (' ' + node['WR'][0]) if 'WR' in node else ''
        t += ' - '

        t += node['PB'][0] if 'PB' in node else ' ?'
        t += (' ' + node['BR'][0]) if 'BR' in node else ''

        if 'RE' in node:
            t = t + ', ' + translateRE(node['RE'][0])
        if 'KM' in node:
            t = t + ' (' + _('Komi') + ' ' + node['KM'][0] + ')'
        if 'HA' in node:
            t = t + ' (' + _('Hcp') + ' ' + node['HA'][0] + ')'

        t += '\n'
        t += ', '.join([node[prop][0] for prop in ['EV', 'RO', 'DT'] if prop in node]) + '\n'

        if 'GC' in node:
            t += node['GC'][0].replace('\n\r', ' ').replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ')

        signature = self.DBlist[DBindex]['data'].getSignature(index)
        t2 = (_('Commentary in ') + ', '.join(self.references[signature])) if signature in self.references else ''

        return t, t2

    def dates_relative(self, fr=0, to=0, chunk_size=1):
        result = []
        to = to or (lk.DATE_PROFILE_END - lk.DATE_PROFILE_START) * 12
        fr = max(0, fr)
        to = min(to, (lk.DATE_PROFILE_END - lk.DATE_PROFILE_START) * 12)

        l = (to - fr) // chunk_size

        for i in range(l):
            current = sum([db['data'].dates_current[j + fr] for j in range(i * chunk_size, (i + 1) * chunk_size) for db in self.DBlist if not db['disabled']])
            d_all = sum([db['data'].dates_all[j + fr] for j in range(i * chunk_size, (i + 1) * chunk_size) for db in self.DBlist if not db['disabled']])
            result.append(current * 1.0 / d_all if d_all else 0)
        return result


cont_sort_criteria = {'total': lambda c1, c2: c2.total() - c1.total(),
                      'earliest': lambda c1, c2: c1.earliest() - c2.earliest(),
                      'latest': lambda c1, c2: c2.latest() - c1.latest(),
                      'average': lambda c1, c2: c1.average_date() - c2.average_date(),
                      'became popular': lambda c1, c2: (c1.became_popular() if c1.became_popular() != -1 else 10000) - (c2.became_popular() if c2.became_popular() != -1 else 10000),
                      'became unpopular': lambda c1, c2: c2.became_unpopular() - c1.became_unpopular(),
                     }


def _get_date(d):
    return '%d' % d


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
    ``self.continuations``, whose entries are instances of lk.Continuation,
    storing total number of hits, position in currentSearchPattern, number of
    black continuations, number of black wins after black play here, number of
    black losses after black play here, number of black plays here after tenuki,
    number of white continuations, number of black wins after white play here,
    number of black losses after white play here, number of white plays here
    after tenuki, label used on the board at this point.
    '''

    def __init__(self):
        self.gamelist = GameList()
        self.currentSearchPattern = None

    def patternSearch(self, CSP, SO=None, CL='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz123456789', FL={}, progBar=None, sort_criterion=None, update_gamelist=True):
        '''Start a pattern search on the current game list.

        * CSP must be an instance of :py:class:`Pattern` - it is the pattern
          that is searched for.
        * You can specify search options as `SO` - this must be an instance of
          ``lk.SearchOptions`` (see below).
        * ``CL``, ``FL``, ``progBar`` are used with the Kombilo GUI.
        * sort_criterion will be used for sorting the continuations:

          * total: by number of occurrences
          * earliest: by earliest occurrence (earliest first)
          * latest: by latest occurrence (latest date first)
          * average: by average date of occurrence (earliest date first)
          * became popular: by weighted average which tries to measure when the move became popular (earliest date first)
          * became unpopular: by weighted average which tries to measure when the move became unpopular (latest date first)

        **Search options.**
        Create an instance of ``lk.SearchOptions`` by ::

          so = lk.SearchOptions

        You can then set particular options on ``so``, e.g.::

          so.fixedColor = 1
          so.searchInVariations = False

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
            if db['disabled']:
                continue
            gl = db['data']
            # print self.searchOptions.algos
            gl.search(self.currentSearchPattern, self.searchOptions)

            done += db['data'].all.size()
            if progBar:
                if self.gamelist.noOfGames():
                    progBar.configure(value=min(99, int(done * 100.0 / self.gamelist.noOfGames())))
                else:
                    progBar.configure(value=1)
                progBar.update()

            self.lookUpContinuations(gl)

        self.set_labels(sort_criterion)
        if update_gamelist:
            self.gamelist.update()

    def sgf_tree(self, cursor, current_game, options, searchOptions, messages=None, progBar=None, ):
        # plist is a list of pairs consisting of a node and some information (label,
        # number of B, W hits of this node) which will eventually be inserted into the
        # comments of the parent node during the search, new nodes (arising as
        # continuations) will be added to plist (as long as the criteria such as DEPTH
        # ... are met)

        messages = messages or dummyMessages()

        # compute column widths for table of continuations in output
        column_widths = [len(s) for s in [_('Label'), '   #  ', _('First played'), _('Last played')]]
        head_str = '%%%ds |   #    | %%%ds | %%%ds |\n'  % (max(5, len(_('Label'))), max(7, len(_('First played'))), max(7, len(_('Last played'))))
        head_str = head_str % (_('Label'), _('First played'), _('Last played'))
        body_str = '%%%ds (%%s) | %%6d | %%%ds | %%%ds |\n'  % (max(5, len(_('Label'))) - 4, max(7, len(_('First played'))), max(7, len(_('Last played'))))

        # create snapshot for initial situation:
        DBlist = [db for db in self.gamelist.DBlist if not db['disabled']]
        snapshot_ids = [(i, db['data'].snapshot()) for i, db in enumerate(DBlist)]
        all_snapshot_ids = copy(snapshot_ids)
        messages.insert('end', _('Start building SGF tree.\n'))
        messages.insert('end', _('%d games before searching for initial pattern.\n') % self.gamelist.noOfGames())

        path_to_initial_node = cursor.currentNode().pathToNode()
        plist = [(cursor.currentNode(), snapshot_ids)]

        counter = 0

        while plist:
            counter += 1
            if counter % 50 == 0:
                messages.insert('end', _('Done {0} searches so far, {1} nodes pending.\n').format(counter, len(plist)))
                if progBar:
                    progBar.update()

            (node, snapshot_ids_parent, ), plist = plist[0], plist[1:]

            # restore snapshots ...
            for i, sid in snapshot_ids_parent:
                DBlist[i]['data'].restore(sid)

            pattern = self.get_pattern_from_node(node, anchors=tuple(int(x) for x in options['anchors']), boardsize=options.as_int('boardsize'), selection=options['selection'])
            # FIXME (in get_pattern_from_node): wildcards?! move sequences?!
            self.patternSearch(pattern, searchOptions, update_gamelist=False)
            self.gamelist.update_winning_percentages()
            noOfG = self.gamelist.noOfGames()
            if noOfG:
                Bperc = self.gamelist.Bwins * 100.0 / noOfG
                Wperc = self.gamelist.Wwins * 100.0 / noOfG
            else:
                Bperc, Wperc = 0, 0
            comment_text = options['comment_head'] + '\n' + _('{0} games (B: {1:1.1f}%, W: {2:1.1f}%)').format(noOfG, Bperc, Wperc)
            if not 'C' in node:
                node['C'] = [comment_text]
            else:
                node['C'] = [node['C'][0] + '\n\n' + comment_text, ]

            if len(node.pathToNode()) - len(path_to_initial_node) >= options.as_int('depth'):
                continue

            if options.as_bool('reset_game_list'):
                snapshot_ids_parent = snapshot_ids
            else:
                snapshot_ids_parent = [(i, db['data'].snapshot()) for i, db in enumerate(DBlist)]
                all_snapshot_ids.extend(snapshot_ids_parent)
            # split continuations up according to B/W
            continuations = []
            for cont in self.continuations:
                cB = lk.Continuation(cont.gamelist)
                cB.add(cont)
                cB.W = 0
                cW = lk.Continuation(cont.gamelist)
                cW.add(cont)
                cW.B = 0
                for sep_cont in [cB, cW]:
                    sep_cont.x, sep_cont.y, sep_cont.label = cont.x, cont.y, cont.label
                    continuations.append(sep_cont)
            continuations.sort(cont_sort_criteria[options['sort_criterion']])

            # assign new labels to reflect new order
            new_labels = {}
            label_ctr = 0
            label_str = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            for cont in continuations:
                try:
                    cont.label = new_labels[cont.label]
                except KeyError:
                    new_labels[cont.label] = label_str[label_ctr] if label_ctr < len(label_str) else '?'
                    cont.label = new_labels[cont.label]
                    label_ctr += 1

            ctr = 0
            comment_text = ''
            for cont in continuations:
                if ctr > options.as_int('max_number_of_branches'):
                    break
                if cont.B < max(1, options.as_int('min_number_of_hits')) and cont.W < max(1, options.as_int('min_number_of_hits')):
                    continue
                ctr += 1

                comment_text += body_str % (cont.label, 'B' if cont.B else 'W', cont.B or cont.W, _get_date(cont.earliest()), _get_date(cont.latest()))

                # put label for (cont.x, cont.y) into node
                pos = chr(cont.x + options['selection'][0][0] + 97) + chr(cont.y + options['selection'][0][1] + 97)  # SGF coordinates
                for item in node['LB']:
                    if item.split(':')[1] == cont.label:  # label already present
                        break
                else:
                    node.add_property_value('LB', [pos + ':' + cont.label])

                # append child node to SGF
                s = ';%s[%s]' % ('B' if cont.B else 'W', pos, )
                cursor.game(current_game, update=0)
                path = node.pathToNode()
                for i in path:
                    cursor.next(i, markCurrent=False)
                cursor.add(s, update=False)
                plist.append((cursor.currentNode(),         # store the node
                            snapshot_ids_parent,          # store snapshots
                            ))

            if comment_text:
                comment_text = head_str + comment_text
            node['C'] = [node['C'][0] + '\n\n' + comment_text, ]

        messages.insert('end', _('Total: %d pattern searches\n') % counter)
        messages.insert('end', _('Cleaning up ...\n'))
        for i, sid in snapshot_ids:
            DBlist[i]['data'].restore(sid)
        self.gamelist.update()
        for i, id in all_snapshot_ids:
            DBlist[i]['data'].delete_snapshot(id)

        return cursor

    def get_pattern_from_node(self, node, boardsize=19, **kwargs):
        '''Return a full board pattern with the position at ``node``.
        \**kwargs are passed on to :py:meth:`Pattern.__init__`.
        '''
        b = abstractBoard(boardsize=boardsize)
        kwargs['sizeX'] = kwargs['selection'][1][0] - kwargs['selection'][0][0] + 1
        kwargs['sizeY'] = kwargs['selection'][1][1] - kwargs['selection'][0][1] + 1

        path = []  # compare pathToNode; redo this here since we also need to find corresponding starting node
        while node.previous:
            path.append(node.level)
            node = node.previous
        path.reverse()

        def play(n, b):
            for s in ['AB', 'AW', 'B', 'W']:
                if s in n:
                    for p in n[s]:
                        #print('play %s %s%s' % (s, p[0], p[1]))
                        b.play((ord(p[0]) - 97, ord(p[1]) - 97), s[-1])

        play(Node(node), b)
        for i in path:
            node = node.next
            for j in range(i):
                node = node.down
            play(Node(node), b)

        p = self.pattern_string_from_board(b, kwargs['selection'])[1]
        if not kwargs:
            kwargs['ptype'] = FULLBOARD_PATTERN
        #print p
        #print kwargs
        return Pattern(p, **kwargs)

    def pattern_string_from_board(self, board, sel, cursor=None):
        try:
            board.wildcards
            board_has_wildcards = True
        except AttributeError:
            board_has_wildcards = False

        dp = ''
        d = ''
        contdict = []

        for i in range(sel[0][1], sel[1][1] + 1):
            for j in range(sel[0][0], sel[1][0] + 1):
                if board_has_wildcards and (j, i) in board.wildcards:
                    dp += board.wildcards[(j, i)][1]
                    d += board.wildcards[(j, i)][1]
                elif board.getStatus(j, i) == ' ':
                    dp += '.' if (not i in [3, 9, 15] or not j in [3, 9, 15]) else ','  # TODO board size
                    d += '.'
                else:
                    inContdict = False
                    if cursor and 'LB' in cursor.currentNode():
                        # check whether position (j,i) is labelled by a number
                        # (in which case we will not in the initial pattern, but in the contlist)

                        pos = chr(j + 97) + chr(i + 97)
                        labels = cursor.currentNode()['LB']
                        for l in labels:
                            p, mark = l.split(':')
                            if pos == p:
                                try:  # will fail if int(mark) does not work
                                    contdict.append((int(mark), '%s[%s]' % (board.getStatus(j, i),  pos, )))
                                    dp += mark
                                    d += '.'
                                    inContdict = True
                                    break
                                except ValueError:
                                    pass
                    if not inContdict:
                        dp += {'B': 'X', 'W': 'O'}[board.getStatus(j, i)]
                        d += {'B': 'X', 'W': 'O'}[board.getStatus(j, i)]

        contdict.sort()
        contlist = ';' + ';'.join([x[1] for x in contdict]) if contdict else None
        # print 'contlist', contlist
        #print d
        return dp, d, contlist

    def lookUpContinuations(self, gl):
        self.noMatches += gl.num_hits
        self.noSwitched += gl.num_switched
        self.Bwins += gl.Bwins
        self.Wwins += gl.Wwins

        for y in range(self.currentSearchPattern.sizeY):
            for x in range(self.currentSearchPattern.sizeX):
                if gl.lookupLabel(x, y) != '.':
                    for c in self.continuations:
                        if c.x == x and c.y == y:  # exists
                            ll = c
                            break
                    else:
                        ll = lk.Continuation(gl)
                        ll.x = x
                        ll.y = y
                        ll.label == '?'
                        self.continuations.append(ll)
                    ll.add(gl.lookupContinuation(x, y))


    def set_labels(self, sort_criterion=None):
        self.continuations.sort(cmp=cont_sort_criteria[sort_criterion or 'total'])
        # print self.continuations
        i = 0
        for c in self.continuations:
            x, y = c.x, c.y
            if (x, y) in self.fixedLabels:
                lab = self.fixedLabels[(x, y)]
            elif i < len(self.contLabels):
                lab = self.contLabels[i]
                i += 1
            else:
                lab = '?'
            c.label = lab.encode('utf-8') if type(lab) == type(u'') else lab
            for db in self.gamelist.DBlist:
                if db['disabled']:
                    continue
                db['data'].setLabel(x, y, c.label)

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
            date (the date in the form YYYY-MM-DD)
            filename
            sgf (the full SFG source).
        '''
        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
            db['data'].gisearch(query)

        self.gamelist.update()

    def gameinfoSearchNC(self, query):
        '''Returns the number of games matching the given query (see
        :py:meth:`gameinfoSearch` for the format of the query) **without
        changing the list of current games**.
        '''
        count = 0
        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
            count += db['data'].gisearchNC(query).size()

        return count

    def dateProfileRelative(self):
        '''Return the ratios of games in the current list versus games in the
        whole database, for each of the date intervals specified in
        :py:meth:`dateProfile`.
        '''
        d = self.dateProfile()
        return [(x, y, self.dateProfileWholeDB[i][1]) for i, (x, y) in enumerate(d)]

    def dateProfile(self, intervals=None):
        '''Return the absolute numbers of games in the given date intervals
        among the games in the current list of games.

        Default value for ``intervals`` is ::

          [ (0, 1900), (1900, 1950), (1950, 1975), (1975, 1985), (1985, 1992),
          (1992, 1997), (1997, 2002), (2002, 2006), (2006, 2009), (2009, 2013),
          ]
        '''
        if intervals is None:
            intervals = [(0, 1900), (1900, 1950), (1950, 1975), (1975, 1985),
                    (1985, 1992), (1992, 1997), (1997, 2002), (2002, 2006),
                    (2006, 2009), (2009, 2013), ]

        return [(i, self.gameinfoSearchNC("date >= '%d-00-00' and date < '%d-00-00'" % i)) for i in intervals]

    def signatureSearch(self, sig):
        '''Do a signature search for the Dyer signature ``sig``.
        '''
        self.noMatches, self.noSwitched, self.Bwins, self.Wwins = 0, 0, 0, 0

        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
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

        if not self.gamelist.noOfGames():
            return
        query = tag.replace('(', ' ( ').replace(')', ' ) ').split()
        if not query:
            return
        for i, q in enumerate(query):
            if not q in ['and', 'or', 'not', '(', ')']:
                for t in self.gamelist.customTags:
                    if self.gamelist.customTags[t][0] == q:
                        break  # find the integer handle corresponding to the given abbreviation
                else:
                    self.logger.insert('end', 'Invalid query.\n')
                    return
                query[i] = 'exists(select * from game_tags where game_id=games.id and tag_id=%s)' % t

        for db in self.gamelist.DBlist:
            if db['disabled']:
                continue
            db['data'].tagsearchSQL(' '.join(query))
        self.gamelist.update()

    def patternSearchDetails(self, exportMode='ascii', showAllCont=False):
        '''Returns a string with information on the most recent pattern search.
        '''

        t = []
        if self.currentSearchPattern:
            p = self.currentSearchPattern
            plist = p.getInitialPosAsList(boundary=True, hoshi=True)

            l1 = [' '.join(x).strip() for x in plist]

            N = 400 if showAllCont else 10
            for cont in self.continuations[:N]:
                x, y = cont.x + 1, cont.y + 1
                if plist[y][x] in ['.', ',']:
                    plist[y][x] = cont.label  # plist[y] is the y-th *line* of the pattern, i.e. consists of the points with coordinates (0, y), ..., (boardsize-1, y).
            l2 = [' '.join(x).strip() for x in plist]

            s1 = '$$B ' + _('Search Pattern') + '\n$$' + join(l1, '\n$$') + '\n' if exportMode == 'wiki' else join(l1, '\n')
            s2 = '$$B ' + _('Continuations') + '\n$$' + join(l2, '\n$$') + '\n' if exportMode == 'wiki' else join(l2, '\n')

            if exportMode == 'wiki':
                t.append('!')
            t.append(_('Search results') + '\n\n')
            if not exportMode == 'wiki':
                t.append(_('Pattern:') + '\n')

            t.append(s1)

            if not exportMode == 'wiki':
                t.append('\n\n' + _('Continuations') + ':\n')
            else:
                t.append('\n\n')

            t.append(s2)
            t.append('\n')

            if self.continuations:
                if exportMode == 'wiki':
                    t.append('%%%%\n!')
                else:
                    t.append('\n')

                t.append(_('Statistics') + ':\n')

                Bperc = self.Bwins * 100.0 / self.noMatches
                Wperc = self.Wwins * 100.0 / self.noMatches

                t.append(_('{0} matches ({1}/{2}), B: {3:1.1f}%, W: {4:1.1f}%').format(self.noMatches, self.noMatches - self.noSwitched, self.noSwitched, Bperc, Wperc))

                if exportMode == 'wiki':
                    t.append(' %%%\n')
                t.append('\n')

                for cont in self.continuations[:N]:
                    if cont.B:  # black continuations
                        t.append(_('B') + '%s:    %d (%d), ' % (cont.label, cont.B, cont.B - cont.tB))
                        t.append((_('B') + ' %1.1f%% - ' + _('W') + ' %1.1f%%') % (cont.wB * 100.0 / cont.B, cont.lB * 100.0 / cont.B))
                        if exportMode == 'wiki':
                            t.append(' %%%')
                        t.append('\n')
                    if cont.W:  # white continuations
                        t.append(_('W') + '%s:    %d (%d), ' % (cont.label, cont.W, cont.W - cont.tW))
                        t.append((_('B') + ' %1.1f%% - ' + _('W') + ' %1.1f%%') % (cont.wW * 100.0 / cont.W, cont.lW * 100.0 / cont.W))
                        if exportMode == 'wiki':
                            t.append(' %%%')
                        t.append('\n')

                t.append('\n')
                if exportMode == 'wiki':
                    t.append('!')

                # give some date profile information
                column_widths = [len(s) for s in [_('Label'), '   #  ', _('First played'), _('Last played')]]
                head_str = '%%%ds |   #    | %%%ds | %%%ds |\n'  % (max(5, len(_('Label'))), max(7, len(_('First played'))), max(7, len(_('Last played'))))
                head_str = head_str % (_('Label'), _('First played'), _('Last played'))
                body_str = '%%%ds (%%s) | %%6d | %%%ds | %%%ds |\n'  % (max(5, len(_('Label'))) - 4, max(7, len(_('First played'))), max(7, len(_('Last played'))))
                comment_text = ''
                for cont in self.continuations[:N]:
                    comment_text += body_str % (cont.label, 'B' if cont.B else 'W', cont.B or cont.W, _get_date(cont.earliest()), _get_date(cont.latest()))
                if comment_text:
                    comment_text = head_str + comment_text
                t.append(comment_text)
                t.append('\n')
                if exportMode == 'wiki':
                    t.append('!')

                t.append(_('Hits per database\n'))
                for db in self.gamelist.DBlist:
                    if db['disabled']:
                        continue
                    t.append(_('{0}: {1} games (of {2})').format(db['sgfpath'], db['data'].size(), db['data'].all.size()))
                    if exportMode == 'wiki':
                        t.append(' %%%')
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
            if os.path.exists(outfile):
                continue
            out = open(outfile, 'w')
            out.write(s)
            out.close()

    def parseReferencesFile(self, datafile, options=None):
        '''Parse a file with references to commentaries in the literature. See
        the file ``src/data/references`` for the file format.

        The method builds up ``self.gamelist.references``, a dictionary which
        for each Dyer signature has a list of all references for the
        corresponding game.

        datafile is expected to be a "file-like object" (like an opened file) with a .read() method.
        '''

        include = []  # if no items are explicitly included, we take that as "include everything that's not excluded"
        exclude = []
        if options:
            def parse_list(d):
                result = []
                for item in d:
                    if not d[item]:
                        result.append(item)
                    else:
                        try:  # is this a range of integers? (e.g., translate '4-6' to [ item 4, item 5, item 6 ])
                            ll = d[item].split('-')
                            assert len(ll) == 2
                            result.extend(['%s %d' % (item, i) for i in range(int(ll[0]), int(ll[1]))])
                        except:
                            result.append(item + ' ' + d[item].strip())
                return result

            exclude = parse_list(options['exclude']) if 'exclude' in options else []
            include = parse_list(options['include']) if 'include' in options else []

        self.gamelist.references = defaultdict(list)
        try:
            c = ConfigObj(infile=datafile, encoding='utf8', default_encoding='utf8')
            if 'boardsize' in c:
                boardsize = int(c['boardsize'])
                del c['boardsize']
            else:
                boardsize = 19
            for k in c:
                if k in exclude:
                    continue
                if include and not k in include:
                    continue
                for sig in c[k]['data']:
                    symmsig = lk.symmetrize(sig, boardsize)
                    self.gamelist.references[symmsig].append(c[k]['title'])
        except:
            pass

    def loadDBs(self, progBar=None, showwarning=None):
        '''Load the database files for all databases that were added to the
        gamelist.
        '''

        DBlistIndex = 0
        for i in range(len(self.gamelist.DBlist)):
            if progBar:
                progBar.update()
            db = self.gamelist.DBlist[DBlistIndex]
            if db['disabled']:
                db['data'] = None
            else:
                try:
                    if not os.path.exists(os.path.join(db['name'][0], db['name'][1] + '.db')):
                        raise IOError
                    db['data'] = lkGameList(os.path.join(db['name'][0], db['name'][1] + '.db'))
                except:
                    if progBar:
                        progBar.stop()
                    if showwarning:
                        showwarning(_('I/O Error'), _('Could not open database {0}/{1}.').format(*db['name']))
                    del self.gamelist.DBlist[DBlistIndex]
                    continue
            DBlistIndex += 1  # May differ from loop counter if databases which cannot be opened are omitted.
        self.gamelist.reset()
        self.dateProfileWholeDB = self.dateProfile()

    # ---------- database administration (processing etc.)

    def find_duplicates(self, strict=True, dupl_within_db=True):
        return lk.find_duplicates([os.path.join(db['name'][0], db['name'][1]+'.db').encode('utf8') for db in self.gamelist.DBlist if not db['disabled']],
                                  strict, dupl_within_db)


    def addDB(self, dbp, datap=('', '#'), recursive=True, filenames='*.sgf', acceptDupl=True, strictDuplCheck=True,
              tagAsPro=0, processVariations=True, algos=None,
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

        arguments = (filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar, showwarning, datap, index)
        if recursive:
            for dirpath, dirnames, files in os.walk(dbp):
                self.addOneDB(arguments, dirpath)
        else:
            self.addOneDB(arguments, dbp)

    def addOneDB(self, arguments, dbpath):

        filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar, showwarning, datap, index = arguments
        # print 'addOneDB', datap, dbpath
        messages = messages or dummyMessages()

        if datap == ('', '#'):
            datap = (dbpath, 'kombilo')

        def db_file_exists(d):
            return (os.path.isfile(os.path.join(d[0], d[1] + '.da')) or
                    os.path.isfile(os.path.join(d[0], d[1] + '.db')) or
                    os.path.isfile(os.path.join(d[0], d[1] + '.db1')) or
                    os.path.isfile(os.path.join(d[0], d[1] + '.db2')))

        if db_file_exists(datap):
            # if file exists, append a counter
            i = 1
            while db_file_exists((datap[0], datap[1] + '%d' % i)):
                i += 1
            datapath = (datap[0], datap[1]+'%d' % i)
        else:
            datapath = datap

        try:
            gl = self.process(dbpath, datapath, filenames, acceptDupl, strictDuplCheck, tagAsPro, processVariations, algos, messages, progBar)
        except:
            if showwarning:
                showwarning(_('Error'), _('A fatal error occurred when processing %s. Are the directories for the database files writable?') % dbpath)
            return

        if gl == None:
            messages.insert('end', _('Directory %s contains no sgf files.\n') % dbpath)
            return
        # open the lkGameList:
        if index is None:
            self.gamelist.DBlist.append({'name': datapath, 'sgfpath': dbpath, 'data': gl, 'disabled': 0})
        else:
            self.gamelist.DBlist[index:index] = [{'name':datapath, 'sgfpath':dbpath, 'data': gl, 'disabled': 0}]
        self.currentSearchPattern = None
        self.gamelist.update()
        messages.insert('end', _('Added %s.') % dbpath + '\n')
        return gl != None

    def process(self, dbpath, datap, filenames='*.sgf', acceptDupl=True, strictDuplCheck=True, tagAsPro=0,
                processVariations=True, algos=None, messages=None, progBar=None, deleteDBfiles=False):
        messages = messages or dummyMessages()
        if progBar:
            progBar.configure(value=0)
            progBar.update()
        messages.insert('end', _('Processing %s.') % dbpath + '\n')
        messages.update()
        if filenames == '*.sgf':
            filelist = glob.glob(os.path.join(dbpath, '*.sgf'))
        elif filenames == '*.sgf, *.mgt':
            filelist = glob.glob(os.path.join(dbpath, '*.sgf')) + glob.glob(os.path.join(dbpath, '*.mgt'))
        else:
            filelist = glob.glob(os.path.join(dbpath, '*'))
        if len(filelist) == 0:
            return
        filelist.sort()

        gls = lk.vectorGL()
        for db in self.gamelist.DBlist:
            if not db['disabled']:  # for disabled db's, db['data'] is None
                gls.push_back(db['data'])

        pop = lk.ProcessOptions()
        pop.rootNodeTags = 'PW,PB,RE,DT,EV'
        pop.sgfInDB = True
        pop.professional_tag = tagAsPro
        pop.processVariations = processVariations
        pop.algos = lk.ALGO_FINALPOS | lk.ALGO_MOVELIST
        if algos:
            pop.algos |= algos
        if deleteDBfiles and os.path.exists(os.path.join(datap[0], datap[1] + '.db')):
            messages.insert('end', _('Delete old database files.'))
            messages.update()
            for ext in ['db', 'da', 'db1', 'db2', ]:
                try:
                    os.remove(os.path.join(datap[0], datap[1] + '.%s' % ext))
                except:
                    messages.insert('end', _('Unable to delete database file %s.') % os.path.join(datap[0], datap[1] + '.%s' % ext))
                    messages.update()

        gl = lkGameList(os.path.join(datap[0], datap[1] + '.db'), 'DATE', '[[filename.]],,,[[id]],,,[[PB]],,,[[PW]],,,[[winner]],,,signaturexxx,,,[[date]],,,', pop, 19, 5000)
        # TODO boardsize

        gl.start_processing()
        for counter, filename in enumerate(filelist):
            if progBar and counter % 100 == 0:
                progBar.configure(value=counter * 100.0 / len(filelist))
                progBar.update()
            try:
                file = open(filename)
                sgf = file.read()
                file.close()
            except:
                messages.insert('end', _('Unable to read file %s') % filename)
                messages.update()
                continue

            path, fn = os.path.split(filename)
            pops = lk.CHECK_FOR_DUPLICATES
            if not acceptDupl:
                pops |= lk.OMIT_DUPLICATES
            if strictDuplCheck:
                pops |= lk.CHECK_FOR_DUPLICATES_STRICT

            try:
                if gl.process(sgf, path, fn, gls, '', pops):
                    pres = gl.process_results()
                    if pres & lk.IS_DUPLICATE:
                        messages.insert('end', _('Duplicate ... %s\n') % filename)
                        messages.update()
                    if pres & lk.SGF_ERROR:
                        messages.insert('end', _('SGF error, file {0}, {1}\n').format(filename, pres))
                        messages.update()
                    if pres & lk.UNACCEPTABLE_BOARDSIZE:
                        messages.insert('end', _('Unacceptable board size error, file {0}, {1}\n').format(filename, pres))
                        messages.update()
                    if pres & lk.NOT_INSERTED_INTO_DB:
                        messages.insert('end', _('not inserted\n'))
                        messages.update()
                else:
                    messages.insert('end', _('SGF error, file %s, not inserted.') % filename + '\n')
                    messages.update()
            except:
                messages.insert('end', _('SGF error, file %s, not inserted.') % filename + '\n')
                messages.update()

        messages.insert('end', _('Finalizing ... (this will take some time)\n'))
        messages.update()
        gl.finalize_processing()

        for ref in self.gamelist.references:
            for gid in gl.sigsearchNC(ref):
                # print gid, ref, self.gamelist.references[ref],
                gl.setTagID(REFERENCED_TAG, gid)
        if progBar:
            progBar.stop()

        return gl

    # ---------- misc tools

    def getFilename(self, no):
        dbindex, index = self.gamelist.getIndex(no)
        if dbindex == -1:
            return
        ID, pos = self.gamelist.DBlist[dbindex]['data'].currentList[index]

        moveno = (0, )
        s = self.gamelist.DBlist[dbindex]['data'].resultsStr(self.gamelist.DBlist[dbindex]['data'].all[pos])
        if s:
            i = 0
            while s[i] in digits + '-':
                i += 1
            if i:
                moveno = tuple([int(x) for x in s[:i].split('-')])

        # print 's', s
        # print 'moveno', moveno

        f1 = strip(os.path.join(self.gamelist.DBlist[dbindex]['sgfpath'], self.gamelist.DBlist[dbindex]['data'].getCurrent(index)[GL_FILENAME]))
        if find(f1, '[') != -1:
            f1, f2 = split(f1, '[')
            gameNumber = int(strip(f2)[:-1])
        else:
            gameNumber = 0

        filename = getFilename(f1)

        return filename, gameNumber, moveno
