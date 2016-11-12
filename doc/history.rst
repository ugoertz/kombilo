:tocdepth: 2

=================
History/Upgrading
=================


Upgrading
=========

When upgrading between major versions (e.g., 0.5 to 0.7), you always have
to newly process your databases. Since processing is pretty fast by now, it
should not hurt too much.

Between minor versions in the 0.7 branch, the database file format did not
change. You can copy your kombilo.cfg file (which contains, among many
options, the database locations) to the new directory, and thus keep your
databases, including all tags.



History/Change log
==================

0.8
---

0.8.3 (November 2016)
^^^^^^^^^^^^^^^^^^^^^

Several minor changes, mostly to ensure compatibility with Mac OS X.


0.8.2 (November 2016)
^^^^^^^^^^^^^^^^^^^^^

* Reduce memory usage at several points: pattern searches, search history, processing
* Improve user interface (thanks to D. Sigaty for several suggestions)
* Improve handling of collections distributed among many folders
* Add references to commentaries (Go World now complete; several books added)
* Several minor bug fixes


0.8.1 (October 2016)
^^^^^^^^^^^^^^^^^^^^

* Add Windows Installer
* Minor bug fixes

0.8 (October 2016)
^^^^^^^^^^^^^^^^^^

Major changes:

* :ref:`SGF tree function <sgf-tree>` in Kombilo: continue searching recursively
  for all continuations arising from some search pattern.
* Add framework to translate the application to other languages (plus German
  translation)
* Install Kombilo as a Python package via pip (so far, as a *source
  distribution* only, i.e., a C++ compiler is still required)
* Reintroduce :ref:`custom-menus` as in Kombilo 0.5.
* Improve date profile: more fine-grained information, several options
  configurable by user.
* Organize pattern search history as a tree.

The source code is now hosted in a `GitHub repository
<https://github.com/ugoertz/kombilo/>`_.



0.7
---

0.7.6 (October 2016)
^^^^^^^^^^^^^^^^^^^^

Some small bug fixes.

0.7.5 (October 2016)
^^^^^^^^^^^^^^^^^^^^

* Fix a few small bugs, most notably fix searching for the empty board (thanks
  to Bram Vandenbon for the bug report). Thanks also to Gilles Arcas and Claude
  Brisson for sending bug reports with fixes included.
* Switch code versioning system to Git, hosted in Github: `Kombilo
  <https://github.com/ugoertz/kombilo>`_
* Small changes to reflect updates in third-party packages (SWIG, jQuery).


0.7.4 (August 2012)
^^^^^^^^^^^^^^^^^^^

Fixed bug in search algorithm. Thanks to John Fairbairn for pointing it out.


0.7.3 (May 2012)
^^^^^^^^^^^^^^^^

* Add :ref:`Find duplicates <find-duplicates>` method.
* Fix ``goto move`` method (Shift + Right click).
* ``.sgf`` as default extension upon saving files.



0.7.2 (April 2012)
^^^^^^^^^^^^^^^^^^

Bug fixes. Added mouse wheel support, and - on Linux - support for back/next
mouse buttons. Option to always maximize window (Windows only). Updated
references to commentaries.

.. note:: Update from version 0.7 or 0.7.1 to 0.7.2:

  While reprocessing your databases is not necessary for Kombilo to be working
  correctly, it will greaty speed up the date profile computation, so it is
  advisable to do this.


0.7.1 (April 2012)
^^^^^^^^^^^^^^^^^^

Major changes:

* provide a Windows installer.

Selected minor fixes:

* Make reprocess export/import tags automatically.
* Optionally put search history as a tab in notebook in right column.
  Thanks to crux@lifein19x19 for the suggestion.
* Pass focus to boardFrame upon double click in game list. Thanks to
  crux@lifein19x19 for the suggestion.
* Update references to commentaries.
* optionally Kombilo avoids the use of Python Imaging Library (PIL). With this
  option, Kombilo can be made to work on Mac OS X. Thanks to
  RBerenguel@lifein19x19 for testing things on Mac OS.
* Fixed some issues regarding the handling of bad SGF files.


0.7 (March 2012)
^^^^^^^^^^^^^^^^

Version 0.7 brought lots of changes to Kombilo and Libkombilo, including

**Kombilo**

* Kombilo now makes use of the libkombilo C++ library; it can search in
  variations, and search for move sequences
* Tags for games
* Show *date profile* for current list of games
* Much better support for using Kombilo in your own Python scripts; several
  example scripts included
* Update the GUI: nicer icons, keyboard bindings, better handling of large game
  lists, etc.

**Libkombilo**

* Use multiple processor cores/processors, if available
* Allow tagging of games
* Change the data file format the search algorithms use to make startup and
  searching faster
* Many bug fixes and small improvements

Furthermore, there have been a number of changes to make the development process
easier and more pleasant, e.g.

* switch to `Mercurial <http://mercurial.selenic.com/>`_ as the versioning system
  for the source code, and host the project on `BitBucket
  <https://bitbucket.org/ugoertz/kombilo/>`_,
* use `Sphinx <http://sphinx.pocoo.org>`_ for producing the documentation
* use `Fabric <http://fabfil.org>`_ to make deployment easier


"0.6": Libkombilo (2006)
------------------------

There was no *Kombilo 0.6* release, but in 2006 I partially rewrote the pattern
matching algorithms, and isolated them from the graphical user interface. This
made it easy to include it as a library into other programs. Since version 3.0
(2007) it is included in `Drago <http://www.godrago.net>`_.

The libkombilo library can ...

* search for corner patterns, full board patterns, and patterns anywhere on the
  board, of course taking into account symmetries (rotation, mirroring), and
  -unless switched of- color reversal. 

* handle for any (square) board size. 

* search for continuations, i.e. you give an initial pattern (possibly
  empty), and then a sequence of moves which have to occur in every hit in the
  given order.

* search in games with variations, and find results within variations as well.
  




0.5 (2002-2004)
---------------

* Kombilo comes with a complete SGF editor: so you can add variations of
  your own, comment the game, add labels etc. The SGF editor can also
  handle collections, i.e. SGF files containing several games. The tree
  structure of the current game is shown in a separate window. You can
  rotate/mirror SGF files.

* Kombilo now comes with a built in list of references to commentaries
  of games in the English go literature. (NB: Kombilo does not come with
  the game records, but recognizes the games by the Dyer signature.) Those
  games in your database which Kombilo finds in its list are marked in the
  game list, and in the game info a reference to the journal/book which has
  the commentary is given. Currently the list contains around 1200
  references, and includes references to the game commentaries in 85 issues
  of Go World and in most English go books with game comentaries.

* The previous search patterns are now shown on small boards in a
  scrollable separate window. Thus you can switch back and forth between
  different search patterns much more easily. This also works much better
  now with different SGF files. In particular, you can load games from the
  game list directly to the Kombilo main board, and then search for
  patterns which arise in that game.

* You can sort the game list with respect to one of several criteria
  (besides the default, sort by filename, you can now also sort by date,
  white player or black player). You can also easily change the order of
  the databases.

* You can refine pattern searches by filtering who moves next in the
  search pattern. 


0.4 (2002)
----------

* Custom menus: menus which you can edit yourself. Upon selecting a menu
  entry, the following actions can be performed: search for a predefined
  pattern; search for predefined game information (player, event, ...);
  open the web browser with some html file.  Thus you could create a
  "Fuseki/Joseki pattern" menu, a "Players" or a "Titles" menu.

* Even faster SGF parser. (On my computer, Kogo's joseki dictionary now
  comes up immediately.)

* Better handling of large databases.

* First SGF editing features: you can now edit the game information, and
  the comments. (Make sure to have backups of important files ;-) )

* Optionally include the whole game list when exporting search results.

* Indicate color swap in the list of results

* Searches with lots of matches are considerably faster now.


0.3 (2002)
----------

* The search engine has been partially rewritten; in particular two
  subtle bugs have been fixed. The use of hash tables makes joseki
  and fuseki searches considerably faster.

* A faster SGF parser. With the new parser, Kogo's joseki dictionary,
  a huge file, can be read in in a few seconds, and thus can be
  conveniently used with Kombilo to study Joseki.

* Winning percentages for continuations; show how often some
  continuation is played after tenuki.

* Export function for search results (either as plain text, or in
  a format suitable for use in Sensei's Library) 


0.2 (2002)
----------


* More comfortable game info search (time period, players, event, ...)

* 'Back' button to return to the previous search.

* More convenient user interface. In particular, the two windows will fit
  on your screen (800x600 or bigger) without overlapping now.

* Display Black/White winning percentages. More detailed statistics on the
  continuations in a search pattern.

* Check for duplicates in the data base (with the Dyer signature), search
  games by signature.


0.1 (October 2001)
------------------

The first Kombilo version. It already had the basic pattern search
functionality (including the C++ extension), but was still rough around the
edges.
