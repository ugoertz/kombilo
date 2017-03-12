#!/usr/bin/env python

# File: examples/test_patternsearch/various_tests.py

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

from __future__ import print_function

'''
This script carries out a number of pattern searches, for various patterns and
with various parameters, and checks the results for consistency.

Usage: invoke as ::

  ./various_tests.py s1

where ``s1`` is a subdirectory which contains data as for the
:py:mod:`profiler` script, and to which the output html page is written.
'''

import sys
basepath = sys.argv[1]
sys.path.insert(0, basepath)
sys.path.append('../../src')
import time, os, os.path

import libkombilo as lk
from kombiloNG import *


def timer(f, *args, **kwargs):
    t = time.time()
    result = f(*args, **kwargs)
    return result, time.time()-t


HTML_TEMPLATE = '''
<html>
<head>
<title>Kombilo pattern search test, setup: %(basepath)s</title>
<link rel="stylesheet" href="../style.css" type="text/css" />
<style type="text/css">
.odd { background-color:#eeeeee; }
</style>
<script type="application/javascript" src="jquery.js"></script>

<script type="application/javascript">
$(function() {
    $('.pattern').hide(); 
    $('#patternhead').click(function() { $('.pattern').toggle(); });
    $('tr:nth-child(odd)').addClass('odd')
});
</script>
</head>
<body>
<div class="content">
<h1>Kombilo pattern search test, setup: %(basepath)s</h1>

<p>libkombilo revision: %(revision)s</p>
<p>machine: %(machine)s</p>
<p>%(numofgames)d games in database</p>
<p>Loading time: %(loading).2f seconds.</p>
<p style="margin-top:20px; margin-bottom: 20px;">Memory usage after loading db: %(memory)s<br>
Peak memory usage: %(memory_peak)s</p>

<table style="margin-top:50px; padding:8px;">
<thead>
<tr><td>ID</td><td><div id="patternhead" style="cursor:pointer; color:blue;">Pattern</div></td><td>Search results data</td></tr>
</thead>
<tbody>
%(content)s
</tbody>
</table>

</div></body>
</html>
'''

if __name__ == '__main__':
    data = { 'basepath': basepath,
             'memory': '?',
             'machine': '?',
           }

    try:
        f = open('/proc/cpuinfo')
        for l in f.readlines():
            if l.startswith('model name'):
                data['machine'] = l.split(':')[1].strip()
                break
        f.close()
    except: pass

    f = open(os.path.join(basepath, 'hgsummary'))
    data['revision'] = f.readlines()[0]
    f.close()

    K = KEngine()
    K.gamelist.DBlist.append({'sgfpath': '', 'name':(os.path.abspath(basepath), 'kombilo1'), 'data': None, 'disabled': 0})

    dummy, data['loading'] = timer(K.loadDBs)
    data['numofgames'] = K.gamelist.noOfGames()
    print(data['numofgames'], 'games')
    try:
        f = open('/proc/self/status')
        data['memory'] = [ x for x in f.readlines() if x.startswith('VmHWM') ][0].split(':')[1].strip()
        f.close()
    except: pass

    patterns = [ 
        ('p1_fb', '''
                ...................
                ...................
                ...................
                ...O...........X...
                ...................
                ...................
                ...................
                ...................
                ...................
                ...................
                ...................
                ...................
                ...................
                ...................
                ...................
                ...O...............
                .....1.........X...
                ...................
                ...................
                ''', { 'ptype': FULLBOARD_PATTERN, 'contsinpattern': 'X'}, lk.SearchOptions(), [ lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_CORNER  | lk.ALGO_HASH_FULL, lk.ALGO_FINALPOS | lk.ALGO_MOVELIST ] ),
        ('p2_c', '''
                . . . . . . . 
                . . . . . . . 
                . X . . . . . 
                . . . X . O . 
                . . . . X . . 
                . . . . O . . 
                . . . . . . . 
                ''', { 'ptype': CORNER_NE_PATTERN, 'sizeX': 7 }, lk.SearchOptions(), [ lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_CORNER  | lk.ALGO_HASH_FULL, lk.ALGO_FINALPOS | lk.ALGO_MOVELIST ] ),
        ('p3_c', '''
                . . . . . . . . . 
                . . . . X O O . . 
                X . . O X X O . . 
                . . . . . X O . . 
                . . . . X O O O . 
                . . . . . X X X . 
                . . . . . . . . . 
                . . . . . . . . . 
                . . . . . . . . . 
                . . . . . , . . . 
                ''', { 'ptype': CORNER_NE_PATTERN, 'sizeX': 9 }, lk.SearchOptions(), [ lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_CORNER  | lk.ALGO_HASH_FULL, lk.ALGO_FINALPOS | lk.ALGO_MOVELIST ] ),
        ('p4', '''
               ...
               .XO
               .OX
               ...
               ''', {'ptype': CENTER_PATTERN, 'sizeX': 3 }, lk.SearchOptions(), None ),
        ('p4a', '''
               .O
               OX
               ''', {'ptype': CENTER_PATTERN, 'sizeX': 2 }, lk.SearchOptions(), None ),
        ('p5', '''
               . . . . . . . . . 
               . . . . . . . . . 
               . . O . X X O X . 
               . . , . . O O X , 
               . . . O . . . . . 
               . . . . . . . . .
        ''', {'ptype': SIDE_N_PATTERN, 'sizeX': 9 }, lk.SearchOptions(), None ),
        ('p6','''
           .OOOOXX
           X.OXXOX
           OOOXOOO
           OXXXO.O
           XXX.XO.
           OO.XXXX
        ''', {'ptype': CORNER_SE_PATTERN, 'sizeX': 7, 'sizeY': 6, }, lk.SearchOptions(), None ),
        ]

    parameters = [ ('Number of games', K.gamelist.noOfGames, None), 
                   ('Number of hits', K.gamelist.noOfHits, None), 
                   ('Number of color switches', K.gamelist.noOfSwitched,
                         lambda x, y, p: x['Number of hits']-x['Number of color switches']==y if p.colorSwitch else x['Number of color switches']==y),
                   ('B wins', lambda: K.gamelist.Bwins, lambda x, y, p: x['W wins']==y if p.colorSwitch else x['B wins']==y), 
                   ('W wins', lambda: K.gamelist.Wwins, lambda x, y, p: x['B wins']==y if p.colorSwitch else x['W wins']==y),
                 ]

    data['content'] = ''
    for id, iPos, kwargs, so, algos in patterns:
        # TODO check whether png exists and create it if not
        p_orig = Pattern(iPos, **kwargs)
        pl = lk.PatternList(p_orig, 0, 0, K.gamelist.DBlist[0]['data'])
        data['content'] += '<tr><td>%s</td><td><div class="pattern" style="font-size:80%%;"><pre>%s</pre></div></td><td><table style="font-size:80%%;">' % (id, iPos)
        searchresults = { }
        for p_ctr in range(pl.size()):
            print('.', end='')
            p = pl.get(p_ctr)
            for alg in (algos or [ lk.ALGO_FINALPOS | lk.ALGO_MOVELIST | lk.ALGO_HASH_CORNER  | lk.ALGO_HASH_FULL ]):
                so.algos = alg
                dummy, searchtime = timer(K.patternSearch, p, so)
                data['content'] += '<tr><td>%.3f</td><td>Algos: %d</td>' % (searchtime, alg, )
                for key, fct, verify in parameters:
                    val = fct()
                    if not key in searchresults:
                        bgc = 'grey'
                        searchresults[key] = val
                    else:
                        if verify:
                            bgc = 'lightgreen' if verify(searchresults, val, p) else 'orange'
                        else:
                            bgc = 'lightgreen' if searchresults[key] == val else 'orange'
                    data['content'] += '<td><span style="background-color:%s;">%s: %d</span></td>' % (bgc, key, val)
                
                K.gamelist.reset()
        data['content'] += '</table></td></tr>'

    try:
        f = open('/proc/self/status')
        data['memory_peak'] = [ x for x in f.readlines() if x.startswith('VmHWM') ][0].split(':')[1].strip()
        f.close()
    except:
        data['memory_peak'] = '?'


    out = open(os.path.join(basepath, 'output.html'), 'w')
    out.write(HTML_TEMPLATE % data)
    out.close()

