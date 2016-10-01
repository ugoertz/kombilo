==============
Kombilo manual
==============

.. _install:

Installation
============


.. index::
  pair: Installation; Linux

.. _install-linux:

Linux
-----

The following instructions cover the installation of Kombilo under Ubuntu
Linux (current version, i.e. 11.10). If you use another flavor of Linux and
are somewhat familiar with it, you will easily adapt them.

.. _quick-start:

Quick start: installation on a Ubuntu system
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

With the following commands you can install Kombilo on a Ubuntu system.
Lines starting with a ``#`` are comments - no need to type them. These
instructions will create a subdirectory ``kombilo`` inside the current
directory.

There are three main steps to the installation: installing Python and the
Python packages, downloading the Kombilo files and extracting them, and
compiling the extension for the fast pattern search. See below for more
details on the different steps.

::

  # Install the packages that Kombilo depends on (and wget for the next step):
  sudo apt-get install python-tk python-imaging python-imaging-tk python-pmw
  sudo apt-get install python-configobj g++  libsqlite3-dev
  sudo apt-get install python-dev libboost-filesystem-dev libboost-system-dev 

  # download the Kombilo archive
  wget https://bitbucket.org/ugoertz/kombilo/downloads/kombilo-0.7.4.tar.gz

  # unpack the archive
  tar xfz kombilo-0.7.4.tar.gz kombilo

  # compile the C++ extension
  cd kombilo/lk
  python setup.py build_ext
  cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/

  # start the program
  cd ../src/
  ./kombilo.py


Now continue with the :ref:`getting-started` section of the tutorial.
After installing, you start the program by executing the ``kombilo.py``
script in the ``kombilo/src`` directory.


Basic dependencies
^^^^^^^^^^^^^^^^^^

The best Python version to run Kombilo on is **Python 2.7**. You might be able
to get it to work with 2.6, but this will need some more work (at least you need
to install pyttk separately). It is currently not compatible with Python 3.

Unless you are a Python specialist, the easiest way to install the packages
required for Kombilo is to install the following packages using the package
manager of your choice (``synaptic``, ``aptitude``, ``apt-get`` etc.)::

  python
  python-tk
  python-imaging
  python-imaging-tk
  python-pmw  
  python-configobj


If you *are* a Python specialist and want to retain finer control (and
place Kombilo in a virtualenv environment, say), it is enough to install
the ``python`` and ``python-tk`` packages, and then to use ``pip`` to
install the Python packages specified in the ``requirements.txt`` file.
In addition, in this case, you have to install the Python Mega-Widgets by
hand: download the tar.gz file from http://pmw.sourceforge.net/, unpack and
install using python setup.py install.


Downloading Kombilo
^^^^^^^^^^^^^^^^^^^

tar.gz files
............

Download the ``kombilo-0.7.4.tar.gz`` archive from the `Kombilo downloads
<https://bitbucket.org/ugoertz/kombilo/downloads>`_ site.

Unpack the archive somewhere by ::

  tar xfz kombilo-0.7.4.tar.gz kombilo

This will extract all the files into the kombilo subdirectory.


Mercurial repository
....................

You can also clone the Kombilo mercurial repository. See :ref:`development`
below for some details.



Libkombilo
^^^^^^^^^^

To compile the extension for the pattern search, make sure that the
following packages are installed::

  g++
  python-dev
  libboost-filesystem-dev
  libboost-system-dev
  libsqlite3-dev

Then, to compile the package, do the following::

  cd ~/go/lk
  python setup.py build_ext
  cp build/lib.*/_libkombilo.so ~/go/kombilo/


.. _development:

Development
^^^^^^^^^^^

If you want to work on Kombilo or Libkombilo yourself, you can clone the
mercurial repository::

  hg clone https://bitbucket.org/ugoertz/kombilo

Make sure (before ...) that you have mercurial installed, and also install
SWIG::

  sudo apt-get mercurial swig

Before you can compile the libkombilo extension, you need to run swig::

  cd kombilo/lk
  swig -c++ -python libkombilo.i 
  python setup.py build_ext
  cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/


Build the documentation
^^^^^^^^^^^^^^^^^^^^^^^

If you installed Kombilo from a ``tar.gz`` archive, then you can skip this
step. If you installed directly from its Mercurial repository, and want to
use the documentation offline (either directly or from the Kombilo Help
menu), then you need to build the documentation yourself. If you install it
from a tar.gz file, then you can skip this step.

Kombilo documentation
.....................

Install `Sphinx <http://sphinx.pocoo.org/>`_ either via ``pip install
sphinx``, or globally by ::

  sudo apt-get install python-sphinx

and in the ``doc/`` directory, run ::

  make html

to build the HTML documentation (to be found in ``doc/_build/html/``), or
 :: 

  make latexpdf

to build a pdf file. (For the latter, you need to have LaTeX installed on
your computer).


Libkombilo documentation
........................

Install `Doxygen <http://www.stack.nl/~dimitri/doxygen/>`_ by ::

  sudo apt-get install doxygen

and in the ``lk/doc/`` directory, run ::

  doxygen

Besides a lot of warnings, this will generate HTML and LaTeX files of the
documentation in ``lk/doc/build/``.


.. index::
  pair: Installation; Windows
.. _install-windows:

Windows
-------

Installer
^^^^^^^^^

The installer installs the Kombilo package together with all libraries etc.
which it depends on. Using it should allow you to ignore the whole Installation
section of this documentation.

If you would like to know the details, here is some further information:

Basically, the installer extracts an archive which contains the Python
interpreter, further packages that Kombilo depends on, and the Kombilo files
themselves to your hard disk. In this way, for one thing you do not have to
install all these packages yourself, and furthermore Kombilo will not interfere
with different versions of these packages that you might have in use.

**Main kombilo directory:** The Kombilo files all go into the installation
directory that you can specify during installation; typically ``c:\Program
Files\kombilo07`` or something similar

**Source code:** The Kombilo source code is included as a zip archive in the
main Kombilo directory.

**Microsoft DLLs:** Python, and hence the Kombilo installer, relies on a couple
of DLLs (shared libraries) that are part of Microsoft's Visual C++ compiler
package. The installer includes a self-extracting archive which may be freely
distributed; if you do not yet have them, the DLLs will be installed on your
system, in an appropriate folder.

**Configuration/log files:** The individual configuration file ``kombilo.cfg``,
and (if necessary) the error log file ``kombilo.err`` will be written to
a directory inside the *APPDATA* directory (something like
``c:\Users\yourusername\AppData\Roaming\kombilo\07\``).

**Uninstall:** The installer creates an *uninstall* menu entry in the Kombilo
menu inside your start menu (unless you disable the start menu entry
altogether). The uninstaller will remove all files that Kombilo created inside
the main kombilo directory, as well as the start menu entry and possibly the
desktop icon. It cannot (and should not) remove the DLLs. Neither will it remove
the configuration files (see above). This allows you to uninstall kombilo,
install a new version, and continue to use your old configuration. Instead of
using the menu entry, you can also directly invoke the exe file (its file name
starts with ``unins``) directly.


Installation from scratch
^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to build Kombilo from source yourself, here are some notes. The
*libkombilo* extension has to be compiled with a C++ compiler. You could
(probably, and probably easier) use Microsoft Visual C++, but I used the open
source `MinGW <http://www.mingw.org/>`_ compiler.  To use MinGW, some
preparations have to be made:

In ``\Python27\Lib\distutils\``, create a file ``distutils.cfg`` with the
following content::

  [build]
  compiler = mingw32

Furthermore, there is a problem with the Python distutils core: it passes the
``-mno-cygwin`` option to MinGW, but this option is not recognized. One way
around this is to remove the ``-mno-cygwin`` from lines 322, 323, 324, 325 and
326 of ``\Python27\Lib\distutils\cygwinccompiler``.

Install `sqlite3 <http://www.sqlite.org/>`_ (and `create a libsqlite3.a file
<http://stackoverflow.com/a/1862394>`_ for MinGW) and the `Boost
library <http://www.boost.org/>`_ (only the header files are needed for
libkombilo; there is no need to compile the boost library).

After that, you should be able to run ``python setup.py build_ext`` in the
``lk`` subdirectory inside your Kombilo directory.

After installing Python and the packages (configobj, PIL, Pmw) that Kombilo
depends on, you should now be able to run ``python kombilo.py``.

To create a stand-alone exe file, you can use `py2exe
<http://www.py2exe.org/>`_. To distribute the whole thing as
a one-file-installer, I use `InnoSetup <http://www.jrsoftware.org/isinfo.php>`_.
See also the ``deploy_win`` method in the fabric file ``fabfile.py`` in the main
Kombilo directory.


.. index::
  pair: Installation; Mac OS X
.. _install-macosx:

Mac OS X
--------

Kombilo runs on Macs, and since Mac OS X is a Unix variant, most of the notes in
the :ref:`install-linux` section apply to Mac OS X, as well. However, under some
circumstances there appear to be some problems, depending on the versions of the
packages that Kombilo depends on.  Simon Cozens reported that on a Mac (with Mac
OS X 10.6) with `Homebrew <http://mxcl.github.com/homebrew/>`_ he could run
Kombilo after ::

  sudo easy_install configobj setuptools pyttk pip
  brew install PIL boost
  sudo pip install pil

then installing `Pmw <http://pmw.sourceforge.net/>`_ from source and building
the libkombilo extension via ``python setup.py build_ext`` as described in the
:ref:`install-linux` section.

On the other hand, sometimes the Python Imaging Library PIL seems to cause
problems (installing it via Homebrew seems to be the best way). In fact, it is
used only for the nicer stone pictures, so it is not too bad to not use it, and
I made this the default for Macs. Change the :ref:`corresponding option
<use-pil>` if you do want to use it. (Thanks to R. Berenguel for his help with
figuring this out.)

If you have Python 2.6, you need to install the ``pyttk`` package to run
Kombilo. In Python 2.7, which is the preferred Python version for Kombilo, this
package is already included in Python.

See also the :ref:`Only one mouse button <onlyonemousebutton>` option.


Setting up the SGF databases
----------------------------

Before you can start working with Kombilo, you need to add your SGF files.
For Kombilo, a database is just a directory with SGF files in it.
Select ``Edit DB list`` in the ``Database`` menu. A new window will open.

.. image:: images/editdblist.jpg

Add databases
^^^^^^^^^^^^^

In the lower section *Processing options* you can select which kind of
files you want to add, whether to recursively add all subdirectories,
whether to accept duplicates, and whether to store variations in the
database for pattern search. You can also select whether all games (or
none) of the database should be considered as pro games, or whether this
should be decided by the rank specified in the files.

If you prefer, you can specifiy a folder where the Kombilo files should be
stored. If you do not name a folder here, the files will be stored in the
folder containing your SGF files.

Finally, you can choose which algorithms you want to use with your
databases. (You can also :ref:`disable the hashing algorithms
<search-options>` for each pattern search, but you can only use then if you
selected the corresponding option before processing the games.)

The hashing algorithms speed up searches for full board and corner
positions respectively, on the other hand the procesing takes slightly
longer, more disk space is consumed, and Kombilo uses more memory when
running.


.. index::
  pair: Messages; Processing
.. _processing-messages:

Messages during processing
..........................

In the lower text area, Kombilo will output messages about the processed games.

* **Duplicates**: Games which are duplicates to games already in the database
  are named. Being a duplicate is tested with the method chosen in the options.
  In every case, the Dyer signature (position of moves 20, 31, 40, 51, 60, 71)
  is compared. With strict duplicate checking, in addition the final position is
  compared. See :ref:`Find duplicates <find-duplicates>`.
* **SGF Error**: If there was an SGF error, Kombilo issues a warning. It tries
  to do its best to recover, and will insert as much of the game as it
  understands into the database anyway.
* **Unacceptable board size**: Currently, Kombilo processes only 19x19 games.
* **not inserted**: For games which are not inserted into the database, this
  message is appended to the error message. Otherwise, the game is inserted.


File sizes
..........

| **No Hashing**: roughly 170 MB for about 70,000 games (GoGoD winter 2011)
| **Hashing for full board positions**: roughly 270 MB
| **Hashing for full board and corner positions**: roughly 365 MB

After adjusting the options, if necessary, select ``Add DB`` in order to
add some SGF files.

The optimal size (i.e. number of SGF files) of the databases depends mostly
on the amount of memory in your computer.  I recommend a size of at least
1,000 - 2,000 SGF files per database; that should be fine on almost every
system.  If you have a lot of memory, you can experiment with larger
databases to increase performance. For databases with ten thousands of
games, the "finalizing" will take quite some time (a few minutes for the
70,000 GoGoD games on my laptop), so please be patient.

Kombilo will create several database files: ``kombilo.db``, ``kombilo.da``,
and if you use the hashing algorithms, also ``kombilo.db1`` and
``kombilo.db2``.


Toggle normal/disabled
^^^^^^^^^^^^^^^^^^^^^^

If you want to temporarily exclude a database from some searches, select it
and use this button to set its status to 'disabled'.  It will then be
marked as 'DISABLED' in the database list.  Its games will not show up
anymore in the game list, and will not be found by any search.
Nevertheless, Kombilo's database files written during the processing are
still available, and if you toggle the status back to 'normal', you can use
that database again without processing it again.


Remove a database
^^^^^^^^^^^^^^^^^

If you want to remove a database from Kombilo's list completely, select it
and press this button. The database files Kombilo has written will then be
deleted. Of yourse, the SGF files themselves will not be deleted (Kombilo
will actually never change them.) If you want to add this database again
later, it will have to be processed again.


Reprocess a database
^^^^^^^^^^^^^^^^^^^^

If you made any changes to the SGF files in one of the database directories
(or added/deleted SGF files in there), you should reprocess the database,
so that the pattern search really uses the information corresponding to the
current version of the SGF files.

Since version 0.7.1, reprocessing keeps all the tags on your database. This
is usually the desired behavior. If you prefer to have all tags deleted,
instead of reprocessing, remove the databases and then add them again.


Save messages
^^^^^^^^^^^^^

If there are errors in the SGF files, or if Kombilo finds duplicates, a
message is issued. The 'save messages' button allows you to save these
messages into a file, such that you can look at them later again in order
to correct the errors. (After correcting any errors, you should reprocess
the corresponding databases.)


Further notes
^^^^^^^^^^^^^

With Ctrl-click and Shift-click you *can select several databases* in the
list simultaneously. The "Toggle normal/disabled", "Remove" and "Reprocess"
buttons will then apply to all the selected databases.

Currently it is not possible to add single games to a database, or to
delete single games.


Searching
=========

There are two main ways to search in your database: by patterns occurring
in the games (:ref:`pattern-search`), and by properties written out in the
SGF file (such as the players, the result, the date, the event where the
game was played etc.).  We call the latter type of search a
:ref:`game-info-search`.

Furthermore, you can search for tags - either games that were automatically
tagged by Kombilo (e.g. handicap games), or for games that you tagged
yourself - (:ref:`tag-search`), and for the Dyer signature of a game
(:ref:`signature-search`). This is typically used less often, but may be
useful to quickly find a game whose Kifu you have in printed form.


.. _pattern-searcH:

Pattern search
--------------

Enter the pattern you want to search for by "putting down" the black and
white stones on the board, and select the size of the pattern (the
"relevant region" for the search) by clicking with the right mouse button
and dragging.

.. index::
  pair: Pattern search; Search options

.. _search-options:

Search options
^^^^^^^^^^^^^^

fixed color
  If this is set, the pattern is searched only as it is given on the board.
  Otherwise, the pattern with black and white exchanged is also considered.
  In the list of results given at the end of each line in the game list,
  hits where the colors are exchanged are marked by a minus sign following
  the move number.

next move
  Specify whether black or white should move next in the search region.

fixed anchor
  Do not "move" the pattern along the side or within the center of the
  board.

Search in variations
  Usually, Kombilo searches for the pattern in all variations in the game.
  If you switch this off, only the first ("main") variation will be
  considered.

move limit
  Find only occurrences before the given move number. The maximum value 250
  means: find all occurrences.

algorithms
  Choose whether Kombilo should use hashing algorithms for full board
  patterns and/or for corner patterns. (If you want to use them, you have
  to choose them when creating the database from your SGF files.)


.. index::
  pair: Pattern search; Wildcards

.. _wildcards:

Wildcards
^^^^^^^^^

You can put down a wildcard by shift-clicking. A green dot means that this
spot may either be empty, or contain a black stone, or contain a white
stone. A black dot means that the spot may be empty or contain a black
stone, and analogously for a white dot. You can go from empty to green,
black, white, etc. by shift-clicking several times.

.. index::
  pair: Pattern search; Move sequence

Move sequences
^^^^^^^^^^^^^^

You can search for move sequences, i.e., specify that some stones of the
pattern have to be played in a certain order. To do so, first create the
final pattern of the sequence. Then put numbers as labels on those stones
that constitute the sequence that must have been played to arrive at this
pattern. You can leave stones unnumbered - this means that they have to be
present in the results before the move sequence starts.

.. warning::

  Currently there is no good way of dealing with captures, i.e., if a stone
  of your sequence captures other stones, you cannot search for the
  sequence with the current mechanism. This is only a problem of the user
  interface; a mechanism of telling Kombilo about the captured stones is
  currently missing (and will hopefully be added some time).

Further notes
^^^^^^^^^^^^^

.. warning:: Passes in the game

  In the unlikely case that one of the players passed in the middle of the
  game (but see file 1998-04-21a in the GoGoD database), the handling of
  continuations is not consistent between the different algorithms.


.. _game-info-search:

Game info search
----------------

In the game info search tab, you can search for properties of the game
which are written out in the SGF file.

For all text search fields (except for *Event*, *Anywhere*, *SQL*), Kombilo
returns all games where the corresponding game info starts with the given
string; i.e., if you search for *Cho* as player, you will get games by *Cho
Chikun* as well as *Cho U* (and all other Cho's).

For the *Event* and *Anywhere* fields, all games are returned where the
given text occurs anywhere in the event field or in the whole SGF file,
respectively.

You can in addition use the percent sign ``%`` as a wildcard yourself,
e.g.: if you search for *%Hideki* as the player, you will get all games of
*Matsuoka Hideki* as well as those of *Komatsu Hideki* etc.


Player
  matches black player and white player names.

from, to
  Specify dates in the form ``YYYY`` or ``YYYY-MM`` or ``YYYY-MM-DD``. If
  you want to search for a date in a different form, you need to use the
  *Anywhere* or the *SQL* search field.

SQL
  This is passed directly to the database as the ``WHERE`` clause of an SQL
  statement. Examples::

    not PW like 'Cho%'
    DATE < 1900-00-00 or DATE >= 2000-00-00

  The column names of the SQL table are ::

    PB (player black)
    PW (player white)
    RE (result)
    EV (event)
    DT (the date as given in the sgf file)
    date (the date in the form YYYY-MM,DD)
    filename
    sgf (the full SFG source).

  In SQL statements, you have to take care of *escaping* characters yourself;
  inparticular, single quotes occurring inside the search string must be
  doubled::

    PB = 'Yi Ch''ang-ho'


.. _tag-search:

Tag search
----------

The tags in the tag list have an *abbreviation* which is written in square
brackets on the left hand side of the entry. You can search for tags using
these abbreviations, and combining them using the logical operators
``and``, ``or``, ``not``, and parentheses. So for example:

* **H** searches for all handicap games.

* **S and C** searches for all games you have previously opened, and for
  which a reference to a commentary is available.

* **A and B and not C** searches for all games which carry the tags A and
  B, but not the tag C (assuming that you created these tags before; see
  below).

Just enter the search expression into the entry field below the tag list
and press enter, or click the looking glass button right of this field.


.. _signature-search:

Signature search
----------------

In order to check for duplicates in the database, Kombilo computes a
modified `Dyer signature
<http://www.andromeda.com/people/ddyer/go/signature-spec.html>`_ of every
game in the database. The signature of a game is given by the coordinates
(in SGF format) of the moves 20, 40, 60, 31, 51, 71. This almost always
characterizes a game uniquely.

In order to detect games which differ only by a symmetry of the board,
Kombilo uses a symmetrized Dyer signature: the Dyer signatures
for the game and for all rotations/reflections of the game
are computed, and then the smallest of these (with respect to
the lexicographic order) is stored.

You can also search for the signature. This might be useful
to see if a certain game is in the database if you have
the game record in some (foreign-language) book, say, and cannot read the
player's names.

Select *signature search* from the database menu, and a window will
pop up, where you can enter the coordinates of the corresponding
moves. If you click on an intersection on the board,
the corresponding coordinates will be entered in the
currently active text entry below, and the next entry will be made 
active. So you can enter the signature simply by clicking on
the places where moves 20, 40, ... were played. You can also omit
some of them (in most cases, two or three of the moves will
be enough to characterize a game uniquely).

You can print the signature of a game to the log tab by selecting it in the
game list and pressing *s*.


.. _export-search-results:

Export search results
---------------------

If you want to save some information on a pattern search, you
can use the 'Export search results' function in the Database menu.  This
will open a new window with a very simple text editor.  It will contain the
search pattern, the search pattern with the continuations, some statistical
information on the search, and the number of hits in each database.

You can edit the information and in the end save the text to a 
file. I would be interested in hearing your opinion if other
or additional information should be given, or if the information
should be presented in another format.

Before the text editor opens, you will be asked if you want "ASCII" or
"Wiki" style output.  Usually you will choose 'ASCII', which produces plain
text.  If you want to use the output for Sensei's Library, choose 'Wiki'
instead.  You can also choose if all continuations, or if only ten of them
should be displayed.

The text editor has a button which lets you include the complete
current game list (names of players, etc.).



The game list
=============

The game list shows the current list of games. Depending on your
configuration, it shows the *white
player*, the *black player*, the *result*, the *date*. In the options menu,
you can choose to include (or exclude) the *file name* as the first item,
and the *date* as the last item.

After a pattern search, the game list shows a list of hits for each game:
the move number when the pattern occurred; the continuation (if any); a
minus sign if the pattern occurred with black/white exchanged.

Entries with different color (or background color) reflect tags set on
games. This behavior can be configured in kombilo.cfg.


Statistics
----------

The statistics tab shows information about the continuations in the most
recent pattern search. For each of the 12 most common continuation, a bar
indicates the frequency. The black/white parts of the bar indicate the
number of times that black/white played in the pattern region immediately
after the pattern was completed. The dark gray/light gray parts indicate
the number of times that black/white played in the pattern region after a
tenuki.


Date profile
------------

The bar diagram shows the distribution of games in the current list in
comparison to all games in the database, by date. The height of the bars
indicate the proportion of games in current list versus games in complete
database. *The height of the bars does not contain absolute information*,
i.e. even if there are only very few games in the current list, the highest
bar will have full height. Absolute information is printed above the bars
(number of games in current list in this time period/number of games in
complete database in this time period).

Computing the date profile is pretty slow (much slower than a pattern
search), so you should keep this tab open only as long as you are really
interested in the results.

Tags
----

You can tag games in order to find them more easily and to carry through
more complicated searches.
The *Tags* tab lists all existing tags. The following ones are built into
Kombilo and are set (semi-)automatically:

* Handicap game; set automatically for all handicap games.

* Professional (a game where at least one professional player plays). You
  can choose during processing whether and in which way Kombilo should set
  this tag.

* Reference to commentary available; set automatically for all games for
  which a reference to a game comment in the literature is available. You
  can configure which books/journals should be considered here by editing
  the file ``kombilo.cfg`` accordingly.

* Seen: set automatically for all games which you opened in the SGF viewer.

If you select a game in the game list, the tags which it carries are
highlighted in the tag list. On the other hand, you can specify how tagged
games should be marked in the game list (text color/background color).

Creating new tags/deleting tags
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To create a new tag, add its abbreviation (which must not yet be taken)
followed by a space and the description of the tag, like this::

  N My new tag

and click the button showing a plus sign.

To delete a tag from the tag list (and hence to remove it from all games),
enter its abbreviation and click the button showing a minus sign.


Setting/removing tags on games
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: images/tag_buttons.jpg
  :align: right


To specify the tags of a **single game**, select the game in the game list.
The tags which it currently carries are highlighted. You can now
select/deselect tags in the tag list by clicking them (use Control-click to
select multiple entries). To set the chosen combination of tags on the
selected games, click the second button from the left in the tags toolbar.

To add a tag to **all games currently in game list**, enter its
abbreviation into the text entry field, and click the third button from the
left. To remove a tag from all games currently in the game list, enter its
abbreviation into the text entry field and click the fourth button from the
left (depicting a broom).

For instance, you could create a tag ``A Large Avalanche Joseki``, do a
pattern search for the large avalanche joseki, and tag all games in the
resulting game list with the tag ``A``. The you can easily search for all
these games, also in combination with other tags, and you can search for
all games where the large avalanche does not occur, by searching for ``not
A`` - and again, this can be combined with searching for other tags.


.. _import-export-tags:

Importing/exporting tabs
^^^^^^^^^^^^^^^^^^^^^^^^

You can export the tags in your current database, and import them later to
a (different) database. (Use the corresponding menu items in the Database
menu.) The games are identified by the Dyer signature and
some additional hash code, so the imported tags will be set precisely on
the games *with the same moves* as the games that carried the tags when
exporting.

In version 0.7, you can/should use this to transfer your tags when updating
your database by reprocess. Since version 0.7.1, reprocess does this for
you automatically.


GoTo field
----------

Use this field (in the game info search tab) to jump to a game in the game
list quickly by entering a few letters of the current sort criterion (see
the options/game list menu). E.g., if you sort the games by date, entering
``1990`` will bring you to the games from 1999; if you sort the games by
white player, entering ``Cho`` will bring you to the games with white
player Cho.


Log
---

In this tab, Kombilo prints out some information about its actions (timing
of searches etc.).


.. index:: Duplicates, Find duplicates

.. _find-duplicates:

Find duplicates
---------------

Use ``Find duplicates`` in the ``Database`` menu to produce a list of
duplicates in the database (or rather, in all the databases that are currently
active). The list will be presented in a new window and can be saved as a text
file. The duplicate check will be strict (i.e., the Dyer signature and the final
position will be compared) or non-strict (only the Dyer signatures will be
compared) depending on the setting of the corresponding processing option. This
option can be changed in the ``Edit DB list`` window or in the
``Options-Advanced`` menu.

The SGF editor
==============

Most of the SGF editor handling should be self-explanatory, so this section
is rather brief.

.. warning::

  By default, Kombilo does not ask for a confirmation before discarding
  unsaved changes, or before deleting a game. You can change this in the
  options menu, or in the ``kombilo.cfg`` configuration file.

Guess mode
----------

Activating the *guess next move* button (depicting a question mark) in the
SGF edit toolbar in the data window starts Kombilo's guess mode. That means
that clicks on the board will be interpreted as guesses - if it coincides
with the next move in the current SGF file, that move is played; otherwise
no stone is placed on the board. For obvious reasons, the *show next move*
option will be disabled as long as the guess mode is active..

When you switch to the 'guess next move' mode, a small frame appears next
to the game tree, which gives you some feedback on your guesses. If your
guess is right, it displays a green square (and the move is played on the 
board).

If the guess is wrong, it displays a red rectangle; the rectangle is
roughly centered at the position of the next move, and the closer your
guess was, the smaller is that rectangle. Furthermore the number of correct
guesses and the number of all guesses, as well as the success percentage
are given.

If you just can't find the next move, you can always use the
'Next move' button above the board to move forward in the game.


Export current position/SGF
---------------------------

Similarly to the  :ref:`export-search-results` function, you can "Export
current position" (in the database menu): this will open a text editor with
the current position.  Again, you can choose "ASCII" or "Wiki" type. In
addition, Kombilo can put the next moves (up to 9 moves) on the board,
marked by the numbers 1 to 9.

Finally, you can also export the SGF source of the current game (see the
File menu), in a text editor.

Miscellaneous remarks
---------------------

With the **rotate/flip SGF file** menu items (in the Edit menu), you can
rotate and flip the game; th SGF file is changed so as to describe the game
with the new orientation. This is useful if you want to change a game
record to obey the usual convention that the first move is in the upper
right corner.

With the **split collection** button (depicting scissors) right to the list
of files, you can split one SGF file containing several games into a
collection of files, one for each game.

With *Copy current SGF files to folder* in the Database menu you can copy
the SGF files corresponding to the games currently in the game list to some
folder (e.g. in order to use them with a different program).

**@@monospace in SGF comments**. If you put the string ``@@monospace`` as
the first line of a comment of an SGF node, Kombilo will display the
comment in a fixed width font. This is useful whenever you want to output
tabular data in a node (see the :py:mod:`sgftree` script).

.. index::
  single: Game info; edit

In the **Game info** edit window, in the *Other SGF tags* entry field you
must enter correct SGF code, i.e. special signs such as ``]`` and ``\``
must be escaped by a preceding ``\``.



Key and mouse bindings
======================

Global key bindings
-------------------

* ``Control-r`` reset game list
* ``Control-s`` select statistics tab
* ``Control-o`` select options tab
* ``Control-g`` select game info search tab
* ``Control-d`` select date profile tab
* ``Control-t`` select tags tab
* ``Control-p`` start pattern search
* ``Control-b`` go back to previous search
* ``Control-e`` print information about previous search pattern to log tab

If the :ref:`search-history-as-tab <search-history-as-tab>` option is 1,
then there is also

* ``Control-h`` select search history tab

Board key bindings
------------------

* ``Left``/``right``: back/forward 1 move
* ``Up``/``down``: back/forward 10 moves
* ``Home``/``end``: to start/end of game
* ``PgUp``/``PgDown``: navigate variations
* ``Control-i``: open game info

Game list key bindings
----------------------

* ``Up``/``down``/``PgUp``/``PgDown``: move in game list
* ``Home``/``End``: scroll to left/right
* ``Return``: open selected game in viewer
* ``Control-a``: print Dyer signature of selected game to log tab

Mouse bindings
--------------

* Use Left-click to put stones on the board.
* With Right-click and drag, you select the search-relevant region.
* Use Shift + Left-click you can put (change/remove) :ref:`wildcards` on the board.
* With Shift + Right-clicking on a stone, you can go to the point in the SGF
  file, where this stone was played.
* The mouse wheel lets you scroll the game list, or scroll through the current
  game, depending on where the mouse pointer is located.
* The next button triggers a pattern search, the back button goes back to the
  previous search. (This does not work on Windows.)



Configuring Kombilo
===================

The most common options can be changed in the *Options* menu. Furthermore,
you can configure Kombilo by :ref:`editing the file kombilo.cfg
<kombilocfg>` (when Kombilo is not running). Finally, the appearance can be
modified by creating/changing the file ``kombilo.app`` accordingly.

Window layout
-------------

You can change the width of the three columns of the main window, as well
as the height of the entried in the left hand column by dragging the
"sashed" between them to the left/right (or up/down, resp.). Move your
mouse pointer slowly over the region between the columns; it should change
its look when you are over the sash.

See also the :ref:`maximize window <maximize-window>` option.


.. index::
  pair: Options; Menu

.. _options-menu:

Options in the Options menu
---------------------------

**Fuzzy stone placement**
Place the stones on the main board slightly off the exact point, in a
random direction, to make the position look more natural. (Well, some
people might think that it is just ugly, so you can switch it off here).


**Shaded stone mouse pointer**
(Don't) Show the current position of the mouse pointer on 
the board and the color of the next stone to be played
by a shaded stone.


**Show next move**
In case a SGF file has been loaded, show the position of the
next move with a circle.

**Show last move**
This marks the most recent move with a small circle. Thanks to Bernd Schmidt
who provideda a patch for this. (The SGF file is not changed.)

**Show Coordinates**
Show coordinates around the board.

.. _option-discarding-changes:

**Ask before discarding unsaved changes**
If this option is enabled, Kombilo will ask for confirmation before
discarding unsaved changes in an SGF file (i.e. before deleting the
game from the game list, and before exiting Kombilo).

**Jump to match**
This controls the behaviour of the SGF viewer when you open
a game from the game lis tafter a pattern search.
If this option is checked, the viewer will jump directly to the position
where the pattern you searched for was found in that game.


**Smart fixed color**
If this option is enabled, the 'fixed color' option will be automatically
enabled when you select the whole board as search-relevant region, and
disabled when you select a smaller region. (You can nevertheless change
that after selecting the region and before starting the search.) This is
useful because if 'fixed color' is not used, Kombilo regards a position and
the same position with swapped colors as equivalent; in the case of whole
board searches that can lead to counter-intuitive results when you look at
the continuations (e.g. place a black resp.  white stone on the upper left
resp. upper right hoshi, do a whole board search without 'fixed color', and
look at the continuations).

.. _themes:

Themes
^^^^^^

Kombilo offers you to change its look according to one of a number of themes.
Which themes are available depends on your operating system. Just try them out.
The effects will be visible immediately.

The 'Game list' submenu
^^^^^^^^^^^^^^^^^^^^^^^

**Sorting the game list**
First of all, in the 'Game list' submenu of the Options menu, you can
choose how to sort the game list: by name of white or black player, date or
filename.

You can reverse the whole game list by selecting the *Reverse
order* option. So if you would like to sort the whole list by date, with
the most current games at the top, you could disable 'Sort per database',
choose 'Sort by date', and select 'Reverse order'.

**Show date/show filename**
Depending on where your SGF files come from, it might be interesting to
include the filename in the game list (as was done automatically in
previous Kombilo versions), or to omit it. Similarly, it might be
interesting to include the date (if it cannot be read off from the file
name, say, or to omit it). These two options allow you to control this.
Changing either of these options will reset the game list.


Advanced
^^^^^^^^

.. _open-game-in-external-viewer:

**Open game in external SGF viewer**
By default, by double-clicking on a game in a game list, the game is opened
in Kombilo's main window. (You can open the game in an external viewer, by
shift-clicking, though). If this option is active, double-clicking opens
the game in an external viewer (v.py or an alternative SGF viewer). In that
case, shift-clicking opens the game in the Kombilo main window.

**Alternative SGF viewer**
If you want to use your customary SGF viewer/editor instead of the viewer
coming with Kombilo, enter the command to start it and the command line
options that tell it to open a certain sgf file here (put an %f where the
filename should be).  (If your viewer supports it, you can also put an %n
where the move number the viewer should jump to directly should be put.)

If your viewer supports jumping directly to a certain move in a game, you
can use %n as a placeholder for the move number of the first hit.
Similarly, if your viewer supports SGF collection, you can use %g as a
placeholder for the number of the concerning game in the given SGF file.

Under Windows, the file name is put in quotes. This is necessary if the
path contains spaces. If you don't want the quotes (or want to set them
yourself), you can use %F instead.


.. _maximize-window:

**Maximize window** (*Windows only*)
If this is active, Kombilo will try to maximize its main window on startup. This
option will become effective when you start Kombilo the next time (not
immediately).



.. index::
  single: Options; kombilo.cfg
.. _kombilocfg:

The kombilo.cfg configuration file
----------------------------------

All configurable options can be changed by editing the file ``kombilo.cfg``
in the kombilo folder. This file is a plain text file which you can edit
yourself. *You should not edit this file while Kombilo is running.* It is
created when Kombilo is started for the first time.

.. note:: Location of the ``kombilo.cfg`` file

  Depending on your platform, the kombilo.cfg file will be stored in the
  following place:

  *Linux/Mac OS*: ``~/.kombilo/07/``, where ``~`` is your home directory; on
  Linux, this is typically ``/home/yourusername/``.

  *Windows*: In the folder ``kombilo\07\`` inside the *APPDATA* folder;
  typically *APPDATA* is something like
  ``\Users\yourusername\AppData\Roaming\``.

  If you want to use several instances of the same Kombilo version at the same
  time, you can also place the kombilo.cfg file inside the main Kombilo
  directory. If there is a kombilo.cfg present there, it will be preferred. Note
  that in this case you need write permissions for this folder.

Lines starting with a ``#`` are comments. Most options are explained by
comments in this file.

In addition to the options, you can also define how tagged games should be
displayed (background/foreground color) in the game list, and which
references to commentaries in the literature should be displayed in the
game list.


.. _search-history-as-tab:

**search_history_as_tab** (new in 0.7.1)
Set this to 1 in order to put the search history frame as a tab in the
right hand column. If the option is 0, then the search history will be
displayed as the bottom pane of the left hand column. The current default
for this option is 0, in version 0.8 the default will become 1.


.. _use-pil:

**use_PIL** (new in 0.7.1)
Set this to 0 in order to disable the use of the Python Imaging Library
(PIL). If 1, then PIL will be used. If ``use_PIL = auto``, then PIL will
not be used on Mac OS, but will be used on other systems. This is the
default setting, because PIL causes problems on Mac OS X. The only
consequence is that without PIL, you will not get the "3D" stones, but just
black/white circles as stones. (So if you prefer the flat stones, you could
just set this option to 0.)


**Uppercase labels**
If you want to use the 'Export search results' function to
produce output for Sensei's Library, it is useful to use
lowercase labels for the continuations, since only lowercase
letters are automatically understood by Sensei's Library. 
If you do not want to do that, and find that uppercase
labels look better, you can use this option.


.. _onlyonemousebutton:

**Only one mouse button**
Some Mac OS X users have a mouse with only one button. Using this option, 
they can mark the search-relevant region with Alt + (left) mouse button
instead of the right mouse button.
Set it to ::

  onlyOneMouseButton = <M2-Button-1>;<M2-B1-Motion>


**Number of previous searches remembered**
As we have seen, with the 'back' button you can jump back to the previous
search. This option controls the number of previous searches that are remembered.
The default is 30, and if your machine has only a small amount of memory,
you probably should not set it much higher, or Kombilo might run out of
memory and crash.  On the other hand, if you have lots of memory, it might
be convenient to set it to a higher number, or even to 0, which means 'no
limit': all searches are remembered, as long as there is enough memory.


Per-user configuration file
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If in the *main* section, the ``kombilo.cfg`` file contains a configdir
entry, like ::

  configdir = ~

then this will be taken as a directory, and the ``kombilo.cfg`` file will
be read from the ``.kombilo`` subdirectory of the configdir. In the
configdir string, the tilde ``~`` will be replaced with the user's home
directory (Linux). In this case, settings in the individual config file
will overwrite those in the global file.


kombilo.app
-----------

You can change some 'global properties' like background color, type
and size of the font used in the game list and in the text windows
etc. by creating a file 'kombilo.app' in the main Kombilo
directory. This is a plain text file; if you change it, please
make sure to save the new version as plain text (ASCII), too.

Here is an example which shows the format of the file::

  *font:                  Helvetica 10
  *background:            grey88
  *foreground:            black
  *activeBackground:      grey77
  *activeForeground:      black
  *selectBackground:      grey77
  *selectForeground:      black
  *Listbox.background:    white
  *Text.background:       white
  *Entry.background:      white
  *Canvas.background:     grey88
  *Label.background:      grey88

.. note::

  **Changed in version 0.7.1:** Before Version 0.7.1, the kombilo.app file was
  present by default. Before you create it, check whether you can obtain a look
  which is to your taste by :ref:`choosing a *theme* <themes>` in the options
  menu.


Miscellaneous
-------------

The files containing the board image and the black and white stones are
``icons/board.jpg``, ``icons/black.gif`` and ``icons/white.gif``.


.. index::
  single: Contributing
  single: Reporting bugs
  single: Bug reports

.. _contributing:


Troubleshooting
===============

In case of errors, Kombilo writes some information to the file ``kombilo.err``
which is in the same directory as your :ref:`kombilo.cfg <kombilocfg>` file.

If you encounter problems, feel free to :ref:`contact me <report-bugs>`.

Contributing
============

Kombilo intentionally is an open-source project. It has profited much from
the contributions of its users in the past, and all your feedback and
contributions are very much appreciated.

Development is concentrated on the `Kombilo project page
<https://www.bitbucket.org/ugoertz/kombilo/>`_ on `BitBucket
<https://www.bitbucket.org>`_.


Tell me how you like Kombilo
----------------------------

Any kind of feedback is appreciated. Tell me which parts of Kombilo you
like, and which ones need improvement. Did you use the Kombilo engine in
your own scripts? I would be glad to learn about your results.

.. _report-bugs:

Ask questions, report bugs
--------------------------

If you have any problems, feel free to ask! Either by email at
``ug@geometry.de``, or via the `issue tracker
<https://bitbucket.org/ugoertz/kombilo/issues?status=new&status=open>`_.


Ideas
-----

I have lots of ideas of new features I would like to implement, and I also
would like to learn your ideas and priorities!


Development
-----------

If you have time to delve into Kombilo development, check out the mercurial
repository::

  hg clone https://bitbucket.org/ugoertz/kombilo

Feel free to fork the project and do send me pull requests for improvements
or fixes you made.

Documentation
-------------

I try to maintain a reasonably complete documentation, but there surely are
gaps and probably some inaccuracies. Please notify me, if you think that
something is not explained well.


Windows/Mac OS X
----------------

I would love to add better support for Windows and/or Mac OS X users,
however I do not have access to computers running either of these operating
systems, right now. If you make progress on this, please tell me. I am also
willing to discuss problems based on my experience with the previous
Kombilo version for which I made a Windows installer.





Miscellaneous notes
===================

References to commentaries
--------------------------

Kombilo has built in a list of references to game commentaries in the
english go literature. The games are referenced by the Dyer signature (a
signature assigned to the game which encodes the positions of move 20, 40,
60, 31, 51, 71, and which in practice characterizes a game uniquely); in
particular Kombilo does not contain the game records. If Kombilo recognizes
a game for which it has a reference, the corresponding line in the game
list is highlighted by a light green background (by default - you can
change this by editing the ``kombilo.cfg`` file), and a line which gives
the actual reference is appended to the game info which is shown when that
line in the game list is selected. (This is printed in blue, to show that
it is not part of the game info proper, but was added by Kombilo.)

.. image:: images/references.jpg

Currently, the list contains around 2000 references; in particular all
issues of Go World, and most English books with game commentaries that I
know of.

The references are stored in the file ``references`` in the ``data`` folder
inside the main Kombilo directory. This is just a text file which you could
edit yourself. The format should be self-explanatory. You can also download
the `current version
<https://bitbucket.org/ugoertz/kombilo/raw/tip/src/data/references>`_ of
this file from the Kombilo source code repository and save it as the
``references`` file.

If you want only references to sources which you own to be shown, you can
define exclude or include rules in the file ``kombilo.cfg``.

Of course, additions to the list of references are very welcome. 
I think it would make sense to add references to other journals, like the
American Go Journal, the British Go Journal, the Deutsche Go-Zeitung, 
the Revue Francaise de Go, etc.

.. index:: Command line arguments

Command line arguments
----------------------

Kombilo.py
^^^^^^^^^^

You can give file names of SGF files as command line arguments, and Kombilo
will open these files upon startup. The file names should be given with the
complete path. If blanks occur in the path or in the file name, it has to
be put inside quotation marks.

v.py
^^^^

The ``v.py`` SGF viewer accepts one SGF file name as the first argument,
and optionally a move number as the second argument. The file will be
opened at the specified move number.

.. _encodings:

Encodings
---------

Kombilo can use SGF files with non-ASCII characters such as umlauts (äöü),
accents (éèê), asian language characters, etc, **but currently it can only
handle UTF-8-encoded files**. Of course, in addition the appropriate fonts
to display these characters must be installed on your computer.


.. _requirements-on-SGF-files:

Requirements on SGF files
-------------------------


There are a few requirements on the SGF files that are used in the 
databases. They will be satisfied by ordinary game records, but 
might not be satisfied by "strange" SGF files.

First of all, the filename of an SGF file always has to end in '.sgf'.

In addition, at the very beginning an initial position can be set up. This 
is what happens in handicap games, for example. So handicap stones are treated
correctly. It is also possible to set up an initial position consisting
of black and white stones, like a go problem. On the other hand, "during the 
game", i.e. after the first black or white move has been played, no stones may 
be added or removed except for the ordinary alternating black/white moves (and 
except for captures, of course). In particular, all stones in the initial
position have to be set up in the same node of the SGF file. Unfortunately,
in a few handicap games of the Go Teaching Ladder, this is not the case;
you will have to edit these files manually if you want to use them with Kombilo.

Empty nodes are skipped. When the usual 'black play' - 'white play' -
'black play' ... order is broken, Kombilo will stop processing the game in
question at that point.  This is another problem with games of the Go
Teaching Ladder: in some of them, after a variation forked off a
black/white move is not shown with the usual B/W tag, but with a AB/AW tag
(which should be used to set up stones like handicap stones). Kombilo will
process these games only until the first variation.

SGF collections: Kombilo's SGF editor can handle SGF files with several
games in them, and so can the search engine. Nevertheless it is not a good
idea to use games in that form, for performance reasons. It is better to
split the collections, and then feed them into Kombilo. The problem with
collections is that whenever the SGF file has to be read (for game info
searches or to display the game info), the whole collection has to be read
from disk, and has to be parsed.


The viewer does accept most SGF features, I think. In particular it handles 
variations (the navigation has to be done by clicking on the concerning
points on the board), and adding/removal of stones during the game. It 
displays labels, but it does not properly display text labels with more 
than one letter/digit.

It ignores some of the new SGF tags like "good for black", "bad for white", 
... .

Kombilo ignores everything before the first '(;'. In particular, it will 
accept files with am email header and an SGF file after that. Be aware,
though, that the header will be lost when you change the game info
of that game: whenever Kombilo writes an SGF file, it will only write
the game (resp. the game collection) itself.

.. index::
  Game records; Where to find

.. _find-game-records:

Where to find game records
--------------------------

Here are some sources of game records:

* `GoGoD encyclopedia <http://gogodonline.co.uk/>`_ has more than
  70,000 games.
* `Go4go <http://www.go4go.net/v2/>`_ has more than 28,000 games.
* `Games of strong players on KGS <http://www.u-go.net/gamerecords/>`_
* `List of links to SGF collections on u-go.net <http://u-go.net/links/gamerecords/>`_
* `List of links to SGF collections on Sensei's library
  <http://senseis.xmp.net/?GoDatabases>`_

