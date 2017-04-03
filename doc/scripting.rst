:tocdepth: 2

============================================
Using the Kombilo engine in your own scripts
============================================

This document describes how to use the Kombilo database from your own
Python scripts, enabling you to do all kinds of data mining on your SGF
databases.

Getting started
===============

It is easiest to create some databases using Kombilo, and then just use the
database files ``kombilo.d*`` (or first copy them somewhere).

Then, a pattern search can be done in a few lines::

    # set up the KEngine, load the database files
    K = KEngine()
    K.gamelist.DBlist.append({ 'sgfpath': '.', 'name':('.', 'kombilo1'), 
                               'data': None, 'disabled': 0})
    K.loadDBs()

    # let us check whether this worked
    print K.gamelist.noOfGames(), 'games in database.'

    # define a search pattern
    p = Pattern('''
                .......
                .......
                ...X...
                ....X..
                ...OX..
                ...OO..
                .......
                ''', ptype=CORNER_NE_PATTERN, sizeX=7, sizeY=7)

    # start pattern search
    K.patternSearch(p)

    # print some information
    print K.patternSearchDetails()

For a slightly extended example, see :py:mod:`basic_pattern_search`.
Instead of appending items to ``K.gamelist.DBlist`` manually as above, you
can also use the py:meth:`GameList.populateDBs` method, see e.g.
:py:mod:`sgftree`.

The scripts in the examples directory
=====================================

basic_pattern_search.py
-----------------------

.. automodule:: basic_pattern_search


sgftree
-------

.. automodule:: sgftree



profiler
--------

.. automodule:: profiler



test_pattern_search
-------------------

In this directory there are a couple of scripts which I used to test the
pattern search for consistency. You can use them as starting points for
your own scripts.

Also see the tests in the ``kombilo/tests`` subdirectory.

various_tests.py
^^^^^^^^^^^^^^^^

.. automodule:: various_tests


API
===

The kombiloNG module
--------------------

.. automodule:: kombilo.kombiloNG
  :members:

The sgf module
--------------

.. automodule:: kombilo.sgf
  :members:



Libkombilo constants
--------------------

Pattern types::

  CORNER_NW_PATTERN
  CORNER_NE_PATTERN
  CORNER_SW_PATTERN
  CORNER_SE_PATTERN

  SIDE_N_PATTERN
  SIDE_W_PATTERN
  SIDE_E_PATTERN
  SIDE_S_PATTERN
  
  CENTER_PATTERN
  
  FULLBOARD_PATTERN


Algorithms::

  ALGO_FINALPOS
  ALGO_MOVELIST
  ALGO_HASH_CORNER
  ALGO_HASH_FULL

Libkombilo
==========

To study the underlying C++ library in detail, look at the `Libkombilo
documentation <http://dl.u-go.net/libkombilo/doc/>`_. A good starting point
is the ``cpptest.cpp`` program in ``lk/examples``.

