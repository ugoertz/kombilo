#!/usr/bin/env python

# file: sgftree.py

##   This file is part of Kombilo, a go database program

##   Copyright (C) 2001-12 Ulrich Goertz (u@g0ertz.de)

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
  initialposition # the initial position; see below for examples
  depth # the highest move number that is considered
  min_number_of_hits # variations with less hits are not considered
  max_number_of_branches # if there are more continuations,
                         # only those with the most hits are considered

Further options::

  gisearch # a query text for a game info search to be carried out
           # before the pattern searches
  comment_head # text that should be prepended to every comment

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

from configobj import ConfigObj

from kombiloNG import *

if __name__ == '__main__':
    K = KEngine()
    with open(sys.argv[1]) as configfile:
        c = ConfigObj(infile=configfile)

        K.gamelist.populateDBlist(c['databases'])
        K.loadDBs()

        print K.gamelist.noOfGames(), 'games in database.'

        OUTPUT = c['options']['output']
        SGF = c['options']['initialposition']
        DEPTH = int(c['options']['depth'])
        MIN_NUMBER_OF_HITS = int(c['options']['min_number_of_hits'])
        MAX_NUMBER_OF_BRANCHES = int(c['options']['max_number_of_branches'])
        GISEARCH = c['options'].get('gisearch', '')
        COMMENT_HEAD = c['options'].get('comment_head', '@@monospace')

        searchOptions = lk.SearchOptions()
        if 'searchoptions' in c:
            searchOptions.fixedColor = int(c['searchoptions'].get('fixedColor',0))
            searchOptions.nextMove = int(c['searchoptions'].get('nextMove',0))
            searchOptions.searchInVariations = int(c['searchoptions'].get('searchInVariations',1))
            searchOptions.moveLimit = int(c['searchoptions'].get('moveLimit',1000))


    c = Cursor(SGF)

    # plist is a list of pairs consisting of a node and some information (label,
    # number of B, W hits of this node) which will eventually inserted into the
    # comments of the parent node during the search, new nodes (arising as
    # continuations) will be added to plist (as long as the criteria such as DEPTH
    # ... are met)
    plist = [ (c.currentNode(), None) ] 

    counter = 0

    while plist:
        counter += 1
        if counter % 100 == 0:
            print 'Done %d searches so far, %d nodes in current plist.' % (counter, len(plist))

        (node, info), plist = plist[0], plist[1:]
        K.gamelist.reset()
        if GISEARCH: K.gameinfoSearch(GISEARCH) # TODO could optimize by using snapshot/restore

        pattern = node.exportPattern()
        # print pattern.printPattern()
        K.patternSearch(pattern, searchOptions)

        # add comment with statistics information to previous node
        if node.previous:
            pr = Node(node.previous)
            if not 'C' in pr: pr['C'] = ['@@monospace\nLB    |  #  | First played | Last played | \n']
            comment_text= '%s (%s)  %5d  %s      %s\n' % (info[0], 'B' if 'B' in node else 'W', info[1] if 'B' in node else info[2],
                                                          K.gamelist.getProperty(0, GL_DATE), K.gamelist.getProperty(-1, GL_DATE))

            pr['C'] = [ pr['C'][0] + comment_text, ]

        if len(node.pathToNode()) > DEPTH: continue
        
        for cont in K.continuations[:MAX_NUMBER_OF_BRANCHES]:
            if cont[3] < MIN_NUMBER_OF_HITS and cont[7] < MIN_NUMBER_OF_HITS: continue

            # put label for (cont[1], cont[2]) into node
            pos = chr(cont[1]+97)+chr(cont[2]+97) # SGF coordinates
            node.add_property_value('LB', [ pos + ':' + cont[11] ])

            # create children of node for each continuation (with MIN number of hits)

            def addNode(color):
                s = ';%s[%s]' % (color, pos, )
                c.game(0)
                path = node.pathToNode()
                for i in path: c.next(i)
                c.add(s)
                plist.append((c.currentNode(), (cont[11], cont[3], cont[7])))

            if cont[3] >= MIN_NUMBER_OF_HITS: addNode('B') # black move here?
            if cont[7] >= MIN_NUMBER_OF_HITS: addNode('W')  # white move here?

    outfile = open(OUTPUT, 'w')
    outfile.write(c.output())
    outfile.close()


