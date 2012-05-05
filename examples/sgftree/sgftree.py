#!/usr/bin/env python

# file: sgftree.py

##   This file is part of Kombilo, a go database program

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
This script takes an initial position, searches for it in the given database,
and then searches for all continuations, then for all continuations in the
newly found results etc. In this way, a tree of positions is computed, and in
the end everything is written into an SGF file, with some information about the
search results at each step.

Before starting the script, you need to write a configuration file. In the
``[databases]`` section, information about the databases to be used should be
given, in the ``[options]`` section some options must be set.

Mandatory options are ::

  output # name of the output file

Further options::

  initialposition # the initial position; see below for examples, default: empty board
  boardsize # board size, default: 19,
  anchors # the rectangle within which the top left corner of the search pattern
          # may move, default: (0, 0, 0, 0),
  selection # the region on the board which is used as the search pattern,
            # default: ((0, 0), (18, 18)),

  depth # the highest move number that is considered, default: 10
  min_number_of_hits # variations with less hits are not considered (black/white
                     # continuations are considered separately) default: 10
  max_number_of_branches # if there are more continuations,
                         # only those with the most hits are considered, default: 20

  gisearch # a query text for a game info search to be carried out
           # before the pattern searches, default: no game info search
  reset_game_list # should each search start from the initial game list, or from
                  # the list resulting from the search for the parent node?
                  # (This determines whether for some node all games featuring
                  # this position should be seen, or only those where it arose
                  # by the same sequence of moves as in the SGF file),
                  # default: False
  comment_head # text that should be prepended to every comment,
               # default: @@monospace

The default value for ``comment_head`` is ``@@monospace`` which causes Kombilo
to display the comment in a fixed width font. This is useful for output in
tabular form.

In the ``[searchoptions]`` section, you can pass search options to Kombilo;
possible choices are ::

  fixedColor, nextMove, searchInVariations, moveLimit

Example config file (starting from the empty board)::

  [databases]
  d0 = /home/ug/go/gogod10W, /home/ug/go/gogod10W, kombilo1
  d1 = /home/ug/go/go4go, /home/ug/go/go4go, kombilo1
  d2 = /home/ug/go/go4goN, /home/ug/go/go4goN, kombilo1
  [options]
  output = out1.sgf
  # start with empty board:
  initialposition = '(;)'
  depth = 15
  min_number_of_hits = 20
  max_number_of_branches = 20
  [searchoptions]
  fixedColor = 1


Example config file (starting with opposing san ren sei)::

  [databases]
  d0 = /home/ug/go/gogod11W, /home/ug/go/gogod11W, kombilo3
  [options]
  output = out2.sgf
  initialposition = '(;AB[pd][pp][pj]AW[dd][dp][dj])'
  depth = 15
  min_number_of_hits = 5
  max_number_of_branches = 20
  [searchoptions]
  fixedColor = 1
'''


import sys
sys.path.append('../../src')
from copy import copy

from configobj import ConfigObj
from kombiloNG import KEngine, lk, Cursor

def _(s):
    return s

class Messages:

    def insert(self, pos, s):
        print s


if __name__ == '__main__':
    messages = Messages()
    K = KEngine()

    co = ConfigObj({'options': {'min_number_of_hits': 10, 'max_number_of_branches': 20, 'depth': 10,
                                'gisearch': '', 'initialposition': '(;)',
                                'comment_head': '@@monospace', 'reset_game_list': False,
                                'sort_criterion': 'total',
                                'boardsize': 19, 'anchors': (0, 0, 0, 0),
                                'selection': ((0, 0), (18, 18)),
                                },
                    'searchoptions': {'fixedColor': 1, 'nextMove': 0, 'searchInVariations': 1,
                                      'moveLimit': 1000,
                                      },
                   })

    with open(sys.argv[1]) as configfile:
        co.merge(ConfigObj(infile=configfile))

    K.gamelist.populateDBlist(co['databases'])
    K.loadDBs()
    messages.insert('end', _('%d games in database.') % K.gamelist.noOfGames())

    searchOptions = lk.SearchOptions()
    if 'searchoptions' in co:
        so = co['searchoptions']
        for attr in ['fixedColor', 'nextMove', 'searchInVariations', 'moveLimit', ]:
            setattr(searchOptions, attr, so.as_int(attr))

    current_game = 0  # game number within the SGF collection
    cursor = Cursor(co['options']['initialposition'])  # add results to this Cursor

    # put game list in specified "initial state"
    K.gamelist.reset()
    if co['options']['gisearch']:
        self.gameinfoSearch(options['gisearch'])

    K.sgf_tree(cursor, current_game, co['options'], searchOptions, messages)

    outfile = open(co['options']['output'], 'w')
    outfile.write(cursor.output())
    outfile.close()
