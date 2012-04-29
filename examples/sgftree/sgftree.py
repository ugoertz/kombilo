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
from kombiloNG import *

def _(s):
    return s

class Messages:

    def insert(self, s):
        print s


def _get_date(d):
    return '%d-%d' % (d // 12, d % 12 + 1)

if __name__ == '__main__':
    messages = Messages()
    K = KEngine()

    co = ConfigObj({'options': {'min_number_of_hits': 10, 'max_number_of_branches': 20, 'depth': 10, 'gisearch': '', 'initialposition': '(;)',
                                'comment_head': '@@monospace', 'reset_game_list': False,
                                'boardsize': 19, 'sizex': 19, 'sizey': 19, 'anchors': (0, 0, 0, 0), },
                    'searchoptions': {'fixedColor': 1, 'nextMove': 0, 'searchInVariations': 1, 'moveLimit': 1000, },
                   })

    with open(sys.argv[1]) as configfile:
        co.merge(ConfigObj(infile=configfile))
    options = co['options']

    K.gamelist.populateDBlist(co['databases'])
    K.loadDBs()
    messages.insert(_('%d games in database.') % K.gamelist.noOfGames())

    searchOptions = lk.SearchOptions()
    if 'searchoptions' in co:
        so = co['searchoptions']
        for attr in ['fixedColor', 'nextMove', 'searchInVariations', 'moveLimit', ]:
            setattr(searchOptions, attr, so.as_int(attr))

    current_game = 0  # game number within the SGF collection

    # create snapshot for initial situation:
    K.gamelist.reset()
    DBlist = [db for db in K.gamelist.DBlist if not db['disabled']]
    if options['gisearch']:
        K.gameinfoSearch(options['gisearch'])
    snapshot_ids = [(i, db['data'].snapshot()) for i, db in enumerate(DBlist)]
    all_snapshot_ids = copy(snapshot_ids)
    messages.insert(_('%d games before searching for initial pattern.') % K.gamelist.noOfGames())

    c = Cursor(options['initialposition']) # add results to this Cursor

    # plist is a list of pairs consisting of a node and some information (label,
    # number of B, W hits of this node) which will eventually be inserted into the
    # comments of the parent node during the search, new nodes (arising as
    # continuations) will be added to plist (as long as the criteria such as DEPTH
    # ... are met)
    plist = [(c.currentNode(), snapshot_ids)]

    counter = 0

    while plist:
        counter += 1
        if counter % 100 == 0:
            messages.insert(_('Done %d searches so far, %d nodes pending.') % (counter, len(plist)))

        (node, snapshot_ids_parent, ), plist = plist[0], plist[1:]

        # restore snapshots ...
        for i, sid in snapshot_ids_parent:
            DBlist[i]['data'].restore(sid)

        pattern = node.exportPattern(sizeX=options.as_int('sizex'), sizeY=options.as_int('sizey'), anchors=tuple(int(x) for x in options['anchors']), boardsize=options.as_int('boardsize'))
        K.patternSearch(pattern, searchOptions)
        if options.as_bool('reset_game_list'):
            snapshot_ids_parent = snapshot_ids
        else:
            snapshot_ids_parent = [(i, db['data'].snapshot()) for i, db in enumerate(DBlist)]
            all_snapshot_ids.extend(snapshot_ids_parent)

        if len(node.pathToNode()) > options.as_int('depth'):
            continue

        # split continuations up according to B/W
        continuations = []
        for cont in K.continuations:
            cB = lk.Continuation()
            cB.add(cont)
            cB.W = 0
            cW = lk.Continuation()
            cW.add(cont)
            cW.B = 0
            for sep_cont in [cB, cW]:
                sep_cont.x, sep_cont.y, sep_cont.label = cont.x, cont.y, cont.label
                continuations.append(sep_cont)
        continuations.sort(cmp=lambda c1, c2: c2.total() - c1.total())

        ctr = 0
        for cont in continuations:
            if ctr > options.as_int('max_number_of_branches'):
                break
            if cont.B < max(1, options.as_int('min_number_of_hits')) and cont.W < max(1, options.as_int('min_number_of_hits')):
                continue
            ctr += 1

            if not 'C' in node:
                node['C'] = [options['comment_head'] + '\n' + _('Label') + ' |  #  | ' + _('First played') + ' | ' + _('Last played') + ' | \n']

            comment_text= '%s (%s)  %5d  %s      %s\n' % (cont.label, 'B' if cont.B else 'W', cont.B or cont.W, _get_date(cont.earliest), _get_date(cont.latest))
            # FIXME column sizes, in particular in case of translations
            node['C'] = [node['C'][0] + comment_text, ]

            # put label for (cont.x, cont.y) into node
            pos = chr(cont.x + 97) + chr(cont.y + 97)  # SGF coordinates
            for item in node['LB']:
                if item.split(':')[1] == cont.label:  # label already present
                    break
            else:
                node.add_property_value('LB', [pos + ':' + cont.label])

            # append child node to SGF
            s = ';%s[%s]' % ('B' if cont.B else 'W', pos, )
            c.game(current_game)
            path = node.pathToNode()
            for i in path:
                c.next(i)
            c.add(s)
            plist.append((c.currentNode(),                # store the node
                            snapshot_ids_parent,          # store snapshots
                         ))

    outfile = open(options['output'], 'w')
    outfile.write(c.output())
    outfile.close()

    messages.insert(_('Cleaning up ...'))
    for i, id in all_snapshot_ids:
        DBlist[i]['data'].delete_snapshot(id)
