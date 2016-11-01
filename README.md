Kombilo - a go database program
===============================

Kombilo is a go database program. Its main purpose is to search for games in
which a given pattern or position occurs. You can also search for other criteria
(like time period, players, events). This program does not come with any game
records, but you can import games in SGF format.

See http://dl.u-go.net/kombilo/doc/ for documentation.


Notes on the win branches (v0.8win etc.)
========================================

These branches contain some additional files and modifications which are
required to build Kombilo an Windows (including a windows installer).

Files modified in this branch
-----------------------------

.gitignore
----------

Since we need to add the SWIG produced files to the repo in this branch.


Files added in this branch
--------------------------

Before building a new version, these files must be updated manually, if
necessary (e.g., by running SWIG, fetching more up-to-date sqlite sources, etc.)

For PyInstaller
---------------

Script to apply PyInstaller to: kombiloexe.py

Configuration file: kombilo.spec

Bundled Pmw files: Pmw.py, PmwBlt.py, PmwColor.py

I18n files: kombilo/lang/de/LC\_MESSAGES/kombilo.mo, kombilo/lang/en/LC\_MESSAGES/kombilo.mo


For InnoSetup
-------------

kombilo.iss


Appveyor files
--------------

appveyor.yml, appveyor/run\_with\_env.cmd

SWIG produced files
-------------------

kombilo/libkombilo.py
kombilo/libkombilo/libkombilo\_wrap.cxx

SQLite3 source files
--------------------

kombilo/libkombilo/sqlite3.c, kombilo/libkombilo/sqlite3.h

