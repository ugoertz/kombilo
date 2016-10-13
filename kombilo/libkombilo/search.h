/*! \file search.h
 * part of libkombilo, http://www.u-go.net/kombilo/
 *
 *  Copyright (c) 2006-12 Ulrich Goertz <ug@geometry.de>
 *
 *  Permission is hereby granted, free of charge, to any person obtaining a copy of 
 *  this software and associated documentation files (the "Software"), to deal in 
 *  the Software without restriction, including without limitation the rights to 
 *  use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
 *  of the Software, and to permit persons to whom the Software is furnished to do 
 *  so, subject to the following conditions:
 *  
 *  The above copyright notice and this permission notice shall be included in all 
 *  copies or substantial portions of the Software.
 *  
 *  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
 *  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
 *  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
 *  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
 *  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
 *  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
 *  SOFTWARE.
 */



/*! \mainpage
 *
 * The libkombilo documentation, created by doxygen from the documentation in the source code files.
 */


#ifndef _SEARCH_H_
#define _SEARCH_H_

#include <vector>
#include <utility>
#include <stack>
#include <fstream>
#include <stdint.h>
#include <sqlite3.h>
#include "boost/unordered_map.hpp"

#include "abstractboard.h"
#include "sgfparser.h"
#include "algos.h"

/*! You create an instance of this class by using the default constructor
 * ProcessOptions() which will set reasonable default values. You can then change
 * these values manually, if you want. Here are the relevant options
 * 
 * \li \c rootNodeTags This is a string containing a comma-separated list of the SGF tags which
 * should be extracted from the files to the database. The default value is
 * <tt>BR,CA,DT,EV,HA,KM,PB,PC,PW,RE,RO,RU,SZ,US,WR</tt>. 
 * \li \c sgfInDB Determines whether the complete sgf file will be stored in
 * the database. (Default: true.) 
 * \li \c algos  This option determines which algorithms will be available for pattern
 * searches. It has the form of a bitmask. A minimal setting (processing is very
 * fast, searching not so fast) is ALGO_FINALPOS | ALGO_MOVELIST . Usually you
 * will want to use ALGO_FINALPOS | ALGO_MOVELIST | ALGO_HASH_FULL |
 * ALGO_HASH_CORNER, which is the default value - this enables all the algorithms
 * which are currently available.
 * \li \c processVariations A boolean which says whether variations in games
 * should be 'processed' (and hence will be available for pattern searches), or
 * should be ignored. (This default value can be overridden in
 * \c start_processing in order to enable variations for part of the
 * database.) Default: true. 
 * \li \c algo_hash_full_maxNumStones Used to fine-tune the ALGO_HASH_FULL
 * algorithm. Positions with more than algo_hash_full_maxNumStones will not be
 * stored in the hashing table. A reasonable value seems to be something around
 * 50 (the default value). For positions with more stones, the ALGO_FINALPOS
 * algorithm is usually sufficiently fast anyway. 
 * \li \c algo_hash_corner_maxNumStones Same for ALGO_HASH_CORNER. Default: 20. 
 * \li \c professional_tag Determines whether/which games should be tagged as 
 * pro games. 0 = do not tag any games (default); 1 = tag all games; 2 = use
 * for players with 1p to 9p ranks in the \c BR, \c WR SGF tags.
 */

class ProcessOptions {
  public:
    bool processVariations;
    bool sgfInDB;
    std::string rootNodeTags; ///< a comma-separated list of those SGF tags which should be written to the database
    int algos;           ///< algorithms to be used
    int algo_hash_full_maxNumStones;
    int algo_hash_corner_maxNumStones;
    int professional_tag;               ///< whether to use "P" tag (0 = don't use; 1 = always use; 2 = use for players with 1p to 9p ranks)

    std::string asString();
    void validate();
    std::vector<std::string>* SGFTagsAsStrings();

    ProcessOptions(); ///< sets default values which can be overwritten individually
    ProcessOptions(std::string s);
};

class SearchOptions {
  public:
    int fixedColor;
    int nextMove; // 0 undetermined, 1 = next move must be black, 2 = next move must be white
    int moveLimit;
    bool trustHashFull;
    bool searchInVariations;
    int algos;

    SearchOptions();
    SearchOptions(int FIXEDCOLOR, int NEXTMOVE=0, int MOVELIMIT=10000);
    SearchOptions(SnapshotVector& snv);
    void to_snv(SnapshotVector& snv);
};

class GameListEntry {
  public:
    int id; // id within the concerning database
    std::string gameInfoStr;
    char winner;
    int date;
    std::vector<Hit* > * hits; // used for hits
    std::vector<Candidate* > * candidates; // used for candidates

    GameListEntry(int ID, char WINNER, std::string GAMEINFOSTR, int DATE);
    ~GameListEntry();

    void hits_from_snv(SnapshotVector& snv);
};

class VarInfo {
  public:
    Node* n;
    abstractBoard* b;
    int i;

    VarInfo(Node* N, abstractBoard* B, int I);
    VarInfo(const VarInfo& v);
    ~VarInfo();
};

/// \name process flags
///  (used to determine the behavior for individual games - in contrast to
/// options which apply to the whole GameList and are given in ProcessOptions)
/// Combine via bitwise OR.
/**@{*/ 
const int CHECK_FOR_DUPLICATES = 1; ///< check for duplicates using the signature
const int CHECK_FOR_DUPLICATES_STRICT = 2; ///< check for duplicates using the final position (if ALGO_FINAPOS is available)
const int OMIT_DUPLICATES = 4; ///< Omit games recognized as duplicates from the database.
const int OMIT_GAMES_WITH_SGF_ERRORS = 8; 
/**@}*/ 

/// \name process return values
/// 0:   SGF error occurred when parsing the "tree structure" (i.e. before parsing the individual nodes)
///      database was not changed
/// n>0: n games were processed, use process_results to access the individual results 
/**@{*/ 
const int UNACCEPTABLE_BOARDSIZE = 1; // (database not changed) 
const int SGF_ERROR = 2;
    ///< SGF error occurred when playing through the game 
    ///< (and the rest of the concerning variation was not used).
    ///< Depending on OMIT_GAMES_WITH_SGF_ERRORS, everything before this node (and other variations, 
    ///< if any) was inserted, or the database was not changed.
const int IS_DUPLICATE = 4;
const int NOT_INSERTED_INTO_DB = 8;
const int INDEX_OUT_OF_RANGE = 16;
/**@}*/ 




/*!
 * \brief The GameList class is the main interface to the libkombilo functionality.
 *
 * The GameList class is the most important class in libkombilo. We start with
 * a rough description of the basic functionality.  A GameList instance is the
 * main interface to operate on a collection of SGF files, and to do all kinds
 * of searches: pattern search, search for game information (such as players,
 * result, etc.), and others. To construct a GameList, you pass it a file name
 * which will be used to contain the main database, and possibly further
 * options. To add SGF files to the database, you need to GameList::process
 * them. Doing a search produces a list of games satisfying the given search
 * criteria, which we refer to the list of games "currently in the list".
 * Unless you GameList::reset the list, every search is applied only to the
 * games currently in the list. In other words, subsequent searches are
 * automatically AND-combined.
 */

class GameList {
  public:
    char* dbname;
    std::string orderby;
    std::string format1;
    std::string format2;
    int numColumns;
    int processVariations;

    int boardsize;
    std::vector<algo_p> algo_ps;
    std::vector<GameListEntry* > * all;
    std::vector<std::pair<int,int> > * currentList; // pair<int,int>: (database id, position within all )
                                                    // (usually sorted w.r.t. second component)
    std::vector<std::pair<int,int> > * oldList;
    int current;
    sqlite3* db;
    char* labels;
    vector<Continuation* > continuations;
    int num_hits;
    int num_switched;
    int Bwins;
    int BwinsAll; ///< number of B wins in all games of the gamelist (independent of currentList)
    int Wwins;
    int WwinsAll; ///< number of B wins in all games of the gamelist (independent of currentList)
    Pattern* mrs_pattern; ///< most recent search pattern
    SearchOptions* searchOptions;
    vector<int> dates_all; ///< a vector which counts, for each month between January 1600 and December 2020, the number of games in the all list
    vector<int> dates_all_per_year; ///< a vector which counts, for each year between 1600 and 2020, the number of games in the all list
    vector<int> dates_current; ///< a vector which counts, for each month between January 1600 and December 2020, the number of games in the current list
    // ----------------------------------------------------------------------------
    // the following methods provide the user interface

    // ------- constructor --------------------------------------------------------
    GameList(
        const char* DBNAME, 
        /*!< A file name, such as /home/ug/go/kombilo1.db. This file will
         * contain the sqlite3 database with information about all games in the
         * database.
         *
         * <b>Further data will be stored in files where the file name is varied
         * by exchanging the final letter of the specified DBNAME, e.g.
         * /home/ug/go/kombilo1.da, /home/ug/go/kombilo1.dd.</b>
         *
         * \bug Possibly problems might arise if the file name contains spaces.
         */
        std::string ORDERBY="",
        /*!< ORDERBY is a string which determines how the entries of the game
         * list are ordered; its value can be any column name of the games
         * database, for instance "PW" or "PB" (sort by name of black or white
         * player), or "DT" or "date".
         *
         * If orderby is the empty string, or equal to "ID", the list is sorted
         * by ID, i.e. in the order in which the games were inserted into the
         * database. This is the fastest option, so it pays off to insert all
         * your games into the database in the order you usually want to work
         * with.
         * 
         * You can use several sort criteria by giving a comma-separated list
         * of column names, e.g. "PW,PB,DATE". The ID will always be the final
         * sort criterion which determines the order in case all other values
         * are equal.
         *
         * You can sort the items in descending order by adding "desc" to the
         * corresponding criterion, for instance you could write "DATE DESC,
         * PW, PB". (In fact, the specified string is simply appended to all
         * sql select commands, so one could in theory imagine doing more fancy
         * things in this way.)
         */
        std::string FORMAT="",
        ///< This string controls the look of entries in the GameList (e.g. when retrieved using currentEntryAsString). 

        /*!< The FORMAT string is a template for the game information string
         * stored for the entries of the game list. It contains place holders
         * of the form [[column name]] , where 'column name', obviously, is the name of a
         * column of the database.
         * 
         * Currently, the columns in the database are
         * 
         * \li \c id  the ID within the database (a positive integer)
         * \li \c path, \c filename  path and file name of the corresponding sgf file
         * \li \c filename.   the file name without the suffix '.sgf' or '.mgt'
         * \li \c pos   the position of the game inside the sgf file (=0 unless
         * the sgf file is a collection of several games
         * \li \c date  date in format YYYY-MM-DD; see below
         * \li \c BR, \c CA, \c DT, \c EV, \c HA, \c KM, \c PB, \c PC, \c PW,
         * \c RE, \c RO, \c RU, \c SZ, \c US, \c WR SGF properties from the
         * root node of the game. The most important ones are PW, PB (white,
         * black player), RE (result), DT (date). Only tags specified via
         * ProcessOptions <b>at creation time</b> of the database can be used.
         * \li \c winner  not a database column, but available as a shortcut
         * for the first letter of the re column, if this first letter is B
         * (black win), W (white win) or J (jigo). Otherwise winner will be set
         * equal to '-'
         * 
         * The column names are case-sensitive. You must not use [[ at other
         * places than indicating column names as described above. If the
         * format string is empty, the example given below will be used.
         * 
         * \b Example:
         * 
         * [[PW]] - [[PB]] ([[WINNER]]), [[DT]],
         * 
         * With this format string, a typical entry in the game list would be
         * 
         * <tt>Cho Chikun - O Rissei (W), 2005-04-20,21,</tt>
         * 
         * If the database contains hits from a pattern search, then
         * currentEntriesAsStrings() returns the concatenation of the game info
         * string as above and the list of hits.  
         *
         * The difference between <tt>DT</tt> and <tt>date</tt>
         *
         * \c DT is the date as given in the SGF file, \c date is always in
         * format YYYY-MM-DD Upon processing the SGF file, the program tries to
         * extract \c date from the \c DT entry. For instance the entry in the
         * sgf file might be "Published on 1960-01-01", in which case date will
         * be "1960-01-01".  It usually makes more sense to sort the list by \c
         * date, but maybe you want to use \c DT in the format string. 
         */
        ProcessOptions* p_options=0, ///<  p_options will be copied by GameList, so the caller has to free the pointer; <b>only used for newly built GameList</b>
        int BOARDSIZE=19, ///< The board size. Note that the board size is fixed for all games in the GameList. If you need different board sizes, you have to work with several instances of GameList.
        int cache=100 ///< Cache size for the sqlite3 database. Usually does not have a big impact.
          ) throw(DBError);
    ~GameList();


    /*!  \name Processing SGF files
     * To "set up" the processing, you call \c GameList::start_processing();
     * (or GameList::start_processing(0) to disable processing of variations).
     * Then, for each game you want to add to the database, call
     * <tt>GameList::process(sgf, path, fn, DBTREE, flags);</tt>
     * Finally, to write everything to the database, call \c finalize_processing.
     */
    /**@{*/ 
    /*!
     * \c sgf, \c path and \c fn are strings (that is <tt>char*</tt>'s) which
     * contain the content of the SGF file to be processed, the path where the
     * file lives and the file name. (You can pass empty strings as path and fn
     * if you do not want to store this information in the database.) \c DBTREE
     * is a string which is stored in the database and can be accessed via a
     * <tt>gisearch</tt> - this can be used to organize your database in a tree
     * structure.
     *
     * You can use the following \c flags to determine the behavior for the game to be processed:
     * \li \c CHECK_FOR_DUPLICATES
     * \li \c CHECK_FOR_DUPLICATES_STRICT
     * \li \c OMIT_DUPLICATES 
     * \li \c OMIT_GAMES_WITH_SGF_ERRORS
     *
     * Combine the flags using bitwise \c OR.
     * 
     * <b>Return value</b>
     *
     * \li 0: An SGF error occurred when parsing the "tree structure" (i.e.
     * before parsing the individual nodes), database was not changed.
     * \li a positive integer \c n: \c n games were processed. Use \c
     * process_results to access the individual results  
     */
    int process(const char* sgf, const char* path, const char* fn, std::vector<GameList* > glists, const char* DBTREE = 0, int flags=0) throw(SGFError,DBError);

    /*! For the processed games (0 <= i < n), use \c process_results(i). Its
     * return value is a combination of the following flags:
     *
     * \li \c UNACCEPTABLE_BOARDSIZE (database not changed) 
     * \li \c SGF_ERROR  An SGF error occurred when playing through the game
     * (and the rest of the concerning variation was not used). Depending on \c
     * OMIT_GAMES_WITH_SGF_ERRORS, everything before this node (and other
     * variations, if any) was inserted, or the database was not changed. 
     * \li \c IS_DUPLICATE 
     * \li \c NOT_INSERTED_INTO_DB
     * \li \c INDEX_OUT_OF_RANGE 
     */
    int process_results(unsigned int i=0); // result for i-th processed game in most recently processed SGF collection

    void start_processing(int PROCESSVARIATIONS=-1) throw(DBError);
    void finalize_processing() throw(DBError);
    /**@}*/ 


    /// \name Pattern search
    /**@{*/ 
    void search(Pattern& pattern, SearchOptions* options = 0) throw(DBError);
    char lookupLabel(char x, char y);
    void setLabel(char x, char y, char label);
    Continuation lookupContinuation(char x, char y);
    int numHits(); ///< Number of hits in most recent pattern search
    /**@}*/ 

    /// \name Signature search
    /**@{*/ 
    void sigsearch(char* sig) throw(DBError);
    vector<int> sigsearchNC(char* sig) throw(DBError); // sig search in all; do not change currentList
    std::string getSignature(int i) throw(DBError);
    /**@}*/ 

    /// \name game info search
    /**@{*/
    void gisearch(const char* sql, int complete=0) throw(DBError);
    ///< Search for given sql query. The string sql is inserted into the following query:
    ///< select id from GAMES where %s " order by id;" % sql
    ///< (putting the gamelist in the right order is dealt with separately)
    ///< If complete==1, then sql is passed as an sql query without any changes (i.e. you must put in the "select ..." stuff in yourself).
    
    vector<int>* gisearchNC(const char* sql, int complete=0) throw(DBError);
    ///< Execute the given sql query (inserted in select id from GAMES where %s " order by id;" % sql
    ///< without changing the GameList.
    ///< Returns a vector of int's containing all indices (in currentList) of games that match the query.
    ///< If complete==1, then sql is passed as an sql query without any changes (i.e. you must put in the "select ..." stuff in yourself).
    /**@}*/

    /*! \name Tagging games
     *
     * It is be possible to have (default and user-defined) categories (or
     * tags). Default categories correspond to properties which can be detected
     * automatically when the game is processed; for instance whether it is a
     * handicap game, or whether the players are professionals (i.e. have a 'p'
     * in their rank). User-defined tags are arbitrary (identified by an
     * integer \c handle); the user interface will have to provide a suitable
     * way for assigning such tags. 
     */
    /**@{*/
    void tagsearch(int tag) throw(DBError); ///< Search for all games tagged with the given tag.

    /*! The \c tagsearchSQL method allows specifying SQL which will simply be inserted
     * into the following \c SELECT statement:
     * <tt>select GAMES.id from GAMES where %(query)s order by GAMES.id</tt>
     * Typically, you will build \c query as an AND/OR/NOT combination of snippets like
     * <tt>exists(select * from game_tags where game_id=games.id and tag_id=%(t)s)</tt>
     * with one or more \c tag_id's.
     */
    void tagsearchSQL(char* query) throw(DBError);
    void setTag(int tag, int start=0, int end=0) throw(DBError);
    ///< Tag all games in range <tt>start <= i < end</tt>. (Details below.)

    ///< Setting \c end to \c 0 means: tag only the game with index \c start.
    ///< \c start and \c end refer to indices in currentList, i.e. in the list of games "currently in view".

    void setTagID(int tag, int i) throw(DBError); ///< Tag the game with \c ID equal to \c i with tag \c tag.

    /*! If \c tag is 0, return \c vector with all tags attached to game \c i.
     * If tag is not 0, return vector with single element \c tag, or empty
     * vector, depending on whether \c tag is attached to game \c i.
     *
     * Here \c i refers to the row ID of the game in the sqlite database.
     */
    vector<int> getTagsID(int i, int tag=0) throw(DBError);

    void deleteTag(int tag, int i = -1) throw(DBError); ///< Remove \c tag from game with \c ID \c i, or from all games in the list (if \c i is -1, the default!).


    /*! If \c tag is 0, return \c vector with all tags attached to \c i-th game
     * of \c currentList.  If tag is not 0, return vector with single element
     * \c tag, or empty vector, depending on whether \c tag is attached to game
     * \c i.
     *
     * Here \c i refers to the index of the game in the list of games
     * "currently in the game list".
     */
    std::vector<int> getTags(unsigned int i, int tag=0) throw(DBError); // note the order of arguments!
    /**@}*/


    void export_tags(string tag_db_name, vector<int> which_tags);
    void import_tags(string tag_db_name);


    /// \name snapshot, restore
    /**@{*/
    int snapshot() throw(DBError);
    void restore(int handle, bool del=false) throw(DBError);
    void delete_snapshot(int handle) throw(DBError);
    void delete_all_snapshots() throw(DBError);
    /**@}*/

    // ------- misc ---------------------------------------------------------------
    void reset(); ///< Reset gane list so that all games in the database are in currentList.
    void resetFormat(std::string ORDERBY="", std::string FORMAT=""); ///< Change sort criterion and format string
    int size(); ///< Number of games in currentList
    int size_all(); ///< Number of games in all
    std::string resultsStr(GameListEntry* gle);

    /// Retrieve information about games in currentList
    /**@{*/
    std::string currentEntryAsString(int i);
    std::vector<std::string> currentEntriesAsStrings(int start=0, int end=0);
    std::string getSGF(int i) throw(DBError);
    std::string getCurrentProperty(int i, std::string tag) throw (DBError);
    /**@}*/


    /// \name List of all players
    /**@{*/
    int plSize();
    std::string plEntry(int i);
    /**@}*/


    friend class Algo_finalpos;
    friend class Algo_movelist;
    friend class Algo_hash_full;
    friend class Algo_hash;
    friend class Algo_hash_corner;
    friend int gis_callback(void *gl, int argc, char **argv, char **azColName);
    friend int gis_callbackNC(void *pair_gl_CL, int argc, char **argv, char **azColName);

  private:
    void createGamesDB() throw(DBError);
    void readDB() throw(DBError);
    void addAlgos(bool NEW);
    int posDT; // used when parsing the DT, SZ, BR, WR, HA fields during processing
    int posSZ;
    int posBR;
    int posWR;
    int posHA;
    int SGFtagsSize;
    ProcessOptions* p_op;
    std::vector<std::string>* SGFtags;
    std::string sql_ins_rnp; // sql string to insert root node properties
    std::vector<std::string> pl; // list of all players
    void readPlayersList() throw(DBError);
    std::vector<std::vector<int> >* duplicates;
    std::vector<int> process_results_vector;

    int startO();
    int start();
    int next();
    int start_sorted();
    int end_sorted();
    void update_dates_current();
    int get_current_index(int id, int* start); // returns the index in oldList of the game with game id "id" 
                                               // (if available, otherwise returns -1),
                                               // use this between start_sorted and end_sorted
    int get_current_index_CL(int id, int start=0); // returns the index in currentList of the game with game id "id" 
                                                   // (if available, otherwise returns -1), requires currentList to
                                                   // be sorted wrt first component (see duplicates())
    char getCurrentWinner();
    int getCurrentDate();
    std::vector<Candidate* > *getCurrentCandidateList();
    void makeCurrentCandidate(std::vector<Candidate* > *candidates);
    void makeCurrentHit(std::vector<Hit* > *hits);
    void makeIndexCandidate(int index, std::vector<Candidate* > *candidates);
    void makeIndexHit(int index, std::vector<Hit* > *hits, vector<int>* CL = 0);
    ///< Used inside the search methods to mark a game (referenced by an index referring to the previous currentList) as a hit.
    ///< If CL is != 0, the index is not appended to currentList, but to CL instead (hits are ignored in that case)
    ///< This is used in search methods as gisearchNC which do not change the currentList
    
    void setCurrentFromIndex(int index);
    void readNumOfWins() throw(DBError);
};

// ------- duplicates ---------------------------------------------------------
/*! To find duplicates, pass a list of GameList instances (by specifying the
 * file names of their .db files in a vector of strings) to this method. You
 * can also specify whether the duplicate checks should be strict, and whether
 * duplicates within the individual GameList instances should also be found, or
 * whether only duplicates "spanning" at least two dbs should be found.
 *
 * The function returns a map<string, vector<int> > whose keys are game
 * signatures, and for each signature, a list of duplicates with this
 * signature. This list is in the form db_id1, game_id1, db_id2, game_id2, ...;
 * here db_id is the place within the glists vector which was passed to
 * find_duplicates, and game_id is the id within the gamelist db_id.
 */
std::map<std::string, std::vector<int> >  find_duplicates(std::vector<string> glists, bool strict=false, bool dupl_within_db=false) throw(DBError);



const int HANDI_TAG = 1;
const int PROFESSIONAL_TAG = 2;

#endif

