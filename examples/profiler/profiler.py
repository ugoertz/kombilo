#!/usr/bin/env python

# File: examples/profiler/profiler.py

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
This scripts performs a number of pattern searches and writes a HTML file with
information about the results and the time used for the searches. This makes it
easy to compare Kombilo performance with different search parameters. Invoking
the script for different versions of the underlying libkombilo library, you can
also experiment with changes to the search algorithms, or compare new
algorithms to the existing ones.

**Usage:**

Invoke the script as ::

  ./profiler.py s1

where ``s1`` is a subdirectory containing the following files.

Mandatory files::

  kombilo1.d* # kombilo database files  
  hgsummary # a text file whose first line should contain information about the
            # revision (inside the hg source code repository) of libkombilo
            # used in this instance; to get started, just put the date (or
            # anything) as the first line of a text file.
  jquery.js # The `JQuery <http://jquery.com>`_ javascript library which is
            # used in the HTML file produced by the script. Obtain a current
            # version from the `JQuery <http://jquery.com>`_ web site.

Optional files::

  libkombilo.py, _libkombilo.so # the files providing the libkombilo library
                                # If you do not put them in the subdirectory,
                                # they are taken from the ``src/`` directory of
                                # your Kombilo installation.


Of course, you could easily to change the script to read the database from a
different path or to use more than one database.
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
<title>Kombilo profiler %(basepath)s</title>
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
<h1>Kombilo profiler %(basepath)s</h1>

<p>libkombilo revision: %(revision)s</p>
<p>machine: %(machine)s</p>
<p>%(numofgames)d games in database</p>
<p>Loading time: %(loading).2f seconds.</p>
<p style="margin-top:20px; margin-bottom: 20px;">Memory usage after loading db: %(memory)s<br>
Peak memory usage: %(memory_peak)s</p>

<table style="margin-top:50px; padding:8px;">
<thead>
<tr><td>ID</td><td><div id="patternhead" style="cursor:pointer; color:blue;">Pattern</div></td><td>search time</td><td>Number of games</td><td>Result</td></tr>
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
    try:
        f = open('/proc/self/status')
        data['memory'] = [ x for x in f.readlines() if x.startswith('VmHWM') ][0].split(':')[1].strip()
        f.close()
    except: pass

    patterns = [ 
        ('p1_fb_nohash', '''
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
                ''', { 'ptype': FULLBOARD_PATTERN, 'contsinpattern': 'X'}, lk.SearchOptions(), lk.ALGO_FINALPOS|lk.ALGO_MOVELIST ),
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
                ''', { 'ptype': FULLBOARD_PATTERN, 'contsinpattern': 'X'}, lk.SearchOptions(), None ),
        ('p2_c', '''
                . . . . . . . . . . 
                . . . . . . . . . . 
                . . . . X . . . . . 
                , . . . . . X . O . 
                . . . . . . . . . . 
                . . . . . . . O . . 
                . . . . . . . . . . 
                . . . . . . . . . . 
                . . . . . . . . . . 
                , . . . . . , . . . 
                ''', { 'ptype': CORNER_NE_PATTERN, 'sizeX': 10 }, lk.SearchOptions(), None ),
        ('p2_c_nohash', '''
                . . . . . . . . . . 
                . . . . . . . . . . 
                . . . . X . . . . . 
                , . . . . . X . O . 
                . . . . . . . . . . 
                . . . . . . . O . . 
                . . . . . . . . . . 
                . . . . . . . . . . 
                . . . . . . . . . . 
                , . . . . . , . . . 
                ''', { 'ptype': CORNER_NE_PATTERN, 'sizeX': 10 }, lk.SearchOptions(), lk.ALGO_FINALPOS|lk.ALGO_MOVELIST ),
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
                ''', { 'ptype': CORNER_NE_PATTERN, 'sizeX': 9 }, lk.SearchOptions(), None ),
        ('p3_c_nohash', '''
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
                ''', { 'ptype': CORNER_NE_PATTERN, 'sizeX': 9 }, lk.SearchOptions(), lk.ALGO_FINALPOS|lk.ALGO_MOVELIST ),
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
        ]

    data['content'] = ''
    for id, iPos, kwargs, so, algos in patterns:
        # check whether png exists and create it if not
        p = Pattern(iPos, **kwargs)
        if algos: so.algos = algos
        dummy, searchtime = timer(K.patternSearch, p, so)
        if K.gamelist.noOfGames():
            data['content'] += '<tr><td>%s</td><td><div class="pattern" style="font-size:80%%;"><pre>%s</pre></div></td><td>%.3f</td><td>%d</td><td style="font-size:70%%;">%s<br>%s</td></tr>' % (id, iPos, searchtime, K.gamelist.noOfGames(), K.gamelist.get_data(0), K.gamelist.get_data(K.gamelist.noOfGames()-1))
        else:
            data['content'] += '<tr><td>%s</td><td><div class="pattern" style="font-size:80%%;"><pre>%s</pre></div></td><td>%.3f</td><td>%d</td><td style="font-size:70%%;">%s<br>%s</td></tr>' % (id, iPos, searchtime, 0, '-', '-')
        K.gamelist.reset()
    try:
        f = open('/proc/self/status')
        data['memory_peak'] = [ x for x in f.readlines() if x.startswith('VmHWM') ][0].split(':')[1].strip()
        f.close()
    except:
        data['memory_peak'] = '?'


    out = open(os.path.join(basepath, 'output.html'), 'w')
    out.write(HTML_TEMPLATE % data)
    out.close()

