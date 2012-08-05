/*! \file algos.h
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
 *
 *
 *
 * <h2>Basic information</h2>
 *
 *
 * <h3>Coordinate system</h3>
 *
 * We use the following coordinate system (given here for board size 19x19):
 *
 * <pre>
 * (0,0) ---------------------- (18,0)
 *   |                             |
 *   |                             |
 *   |                             |
 *   |                             |
 *   |                             |
 *   |                             |
 *   |                             |
 *   |                             |
 * (0,18) --------------------- (18,18)
 * </pre>
 *
 * This corresponds nicely to the system used by SGF ((0,0) = aa, (18,18) = ss).
 *
 * <h3>Board symmetries</h3>
 *
 * There are 8 symmetries of the square, and hence of the go board. We
 * enumerate them as follows (to simplify notation, we give the maps for
 * boardsize 19). A point with coordinates (x,y) is mapped to
 *
 * 0. (x,y)<br>
 * 1. (18-x, y)<br>
 * 2. (x, 18-y)<br>
 * 3. (18-x, 18-y)<br>
 * 4. (y, x)<br>
 * 5. (18-y, x)<br>
 * 6. (y, 18-x)<br>
 * 7. (18-y, 18-x)<br>
 *
 * So for instance the symmetry 0 is the identity map, and symmetry 1 is
 * reflection with respect to the vertical axis.
 *
 * Furthermore, given a position, there is the color swap which exchanges black
 * and white stones.
 *
 * The corresponding PatternList is a list of all reflections, rotations etc.
 * of the pattern, in other words the set of images of the patterns under
 * symmetries of the board.
 *
 * <h3>Continuations</h3>
 * 
 * When doing a pattern search, we want to keep track of possible
 * continuations. Of course, for images of the original pattern under a
 * symmetry, any continuation has to be "re-mapped" to the original pattern.
 * Furthermore, when showing continuations, symmetry needs to be taken into
 * account, for instance in
 *
 * <pre>
 * +--------
 * |........
 * |........
 * |.....a..
 * |...X....
 * |........
 * |..b.....
 * |........
 * |........
 * </pre>
 *
 * the positions a and b are equivalent, and only one of them should be shown
 * as a possible continuation.  To keep track of all this, we use, for each
 * pattern in the pattern list, a dictionary Symmetries such that if a
 * continuation is played in the pattern at the point (i,j), then 
 * <tt>Symmetries[color, i, j] == (c,x,y)</tt> which means that the result should
 * be shown at (x,y) in the original pattern with color \c c. ('color' is the
 * color (black/white) of the continuation.)
 *
 */


#ifndef _ALGOS_H_
#define _ALGOS_H_

#include <vector>
#include <stack>
#include <fstream>
#include <stdint.h>
#include <sqlite3.h>
#include "boost/unordered_map.hpp"

#include "abstractboard.h"
#include "sgfparser.h"
#include "pattern.h"



class GameList;
class SearchOptions;


/*! A base class for all algorithms which defines the methods each algorithm class has to provide. */
class Algorithm {
  public:
    Algorithm(int bsize);
    virtual ~Algorithm();

    virtual void initialize_process();                    ///< Called by GameList::start_processing
    virtual void newgame_process(int game_id);            ///< Called when a new game is about to be GameList::process'ed
    virtual void AB_process(int x, int y);                ///< Called during processing, for each \c AB SGF tag
    virtual void AW_process(int x, int y);                ///< Called during processing, for each \c AW SGF tag
    virtual void AE_process(int x, int y, char removed);  ///< Called during processing, for each \c AE SGF tag
    virtual void endOfNode_process();                     ///< Called during processing, after fully processing a node (which might contain several \c AB, \c AW tags)
    virtual void move_process(Move m);                    ///< Called during processing, for each move (\c B, \c W tags)
    virtual void pass_process();                          ///< Called during processing, for each pass
    virtual void branchpoint_process();                   ///< Called during processing, for each node where a variation starts
    virtual void endOfVariation_process();                ///< Called during processing, when reaching the end of variation ("jump back to most recent branchpoint")
    virtual void endgame_process(bool commit=true);       ///< Called during processing, when the end of the game is reached
    virtual void finalize_process();                      ///< Called by GameList::finalize_processing

    virtual SnapshotVector get_data();                    ///< Extract the relevant data from file at Kombilo startup.

    virtual int search(PatternList& patternList, GameList& gl, SearchOptions& options); ///< pattern search

    int gid;          ///< store the game id during processing
    int boardsize;    ///< board size
};


// --------------------------------------------------------------------------------------------------

/// This algorithm computes the symmetrized Dyer signature of each game.
class Algo_signature : public Algorithm {
  public:
    Algo_signature(int bsize, SnapshotVector DATA);
    ~Algo_signature();
    void initialize_process();
    void newgame_process(int game_id);
    void AB_process(int x, int y);
    void AW_process(int x, int y);
    void AE_process(int x, int y, char removed);
    void endOfNode_process();
    void move_process(Move m);
    void pass_process();
    void branchpoint_process();
    void endOfVariation_process();
    void endgame_process(bool commit=true);
    void finalize_process();

    int counter;
    char* signature;
    char* get_current_signature();
    std::vector<int> search_signature(char* sig);

    SnapshotVector get_data();
    boost::unordered_multimap<string, int> data;
  private:
    bool main_variation;
};


/*! The basic idea of this algorithm is to compare a given pattern with the
 * final position of the game in order to find all positions on the board where
 * the given pattern could possibly occur. "Final position" has to be
 * understood in the right sense. More precisely, when creating the
 * corresponding database, we record, for each point on the board, whether at
 * some time during the game, a black stone or a white stone is placed there.
 * Of course, with captures and under the stones play, it can happen that at a
 * certain point there is a black as well as a white stone at some time.
 *
 * The output of the finalpos algorithm is a list of candidates which have then
 * to be checked using another algorithm (see AlgoMovelist).
 *
 * This comparison against the "final position" of course gives us information
 * only from those points in the search pattern which are non-empty. Hence to
 * reduce the time needed for these comparisons, we use the smallest rectangle
 * inside the original pattern which contains all of its stones, i.e. we cut
 * off the exterior rows/columns which are empty. 
 */

class Algo_finalpos : public Algorithm {
  public:
    Algo_finalpos(int bsize, SnapshotVector DATA);
    ~Algo_finalpos();
    void initialize_process();
    void newgame_process(int game_id);
    void AB_process(int x, int y);
    void AW_process(int x, int y);
    void AE_process(int x, int y, char removed);
    void endOfNode_process();
    void move_process(Move m);
    void pass_process();
    void branchpoint_process();
    void endOfVariation_process();
    void endgame_process(bool commit=true);
    void finalize_process();
    hashtype get_current_fphash();
    hashtype get_fphash(int index);

    char* fp;
    int fpIndex;

    SnapshotVector get_data();
    std::vector<pair<int, char* > > data;

    int search(PatternList& patternList, GameList& gl, SearchOptions& options);
};


// -------------------------------------------------------------------------------------------------------


// in x-coord:
const int ENDOFNODE = 128;
const int BRANCHPOINT = 64;
const int ENDOFVARIATION = 32;

// in y-coord
const int REMOVE = 128;
const int BLACK = 64;
const int WHITE = 32;


class MovelistCand {
  public:
    int orientation;
    Pattern* p;
    char* dicts;
    ExtendedMoveNumber dictsF;
    bool dictsFound;
    ExtendedMoveNumber dictsFI;
    bool node_changes_relevant_region;
    bool dictsFoundInitial;
    bool dictsDR;
    int dictsNO;
    std::vector<MoveNC> contList;
    int contListIndex;
    p_cc Xinterv;
    p_cc Yinterv;
    char mx;
    char my;

    MovelistCand(Pattern* P, int ORIENTATION, char* DICTS, int NO, char X, char Y);
    ~MovelistCand();
    char dictsget(char x, char y);
    void dictsset(char x, char y, char d);
    bool in_relevant_region(char x, char y);
    char contlistgetX(int i);
    char contlistgetY(int i);
    char contlistgetCO(int i);
};

class VecMC : public std::vector<MovelistCand* > {
  public:
    VecMC();
    ~VecMC();
    VecMC* deepcopy(ExtendedMoveNumber& COUNTER, int CANDSSIZE);
    ExtendedMoveNumber counter;
    int candssize;
};




/*!
 *
 * This algorithm takes a candidate for a hit (as provided by AlgoFinalpos or
 * AlgoHash), i.e. a position on the board where a certain pattern could
 * possibly match, and then plays through the game in order to decide whether
 * this is really a hit. Of course, in practice, we take a list of all
 * candidates for a given game, so that we have to play through the game only
 * once. Furthermore, instead of using the SGF file, we use a "move list" where
 * all the moves and captures are stored - by avoiding to compute whether any
 * stones are captured with some move (and which ones) we save a lot of time. 
 * This move list is generated during processing when the database is built.
 */
class Algo_movelist : public Algorithm {
  public:
    Algo_movelist(int bsize, SnapshotVector DATA);
    ~Algo_movelist();
    void initialize_process();
    void newgame_process(int game_id);
    void AB_process(int x, int y);
    void AW_process(int x, int y);
    void AE_process(int x, int y, char removed);
    void endOfNode_process();
    void move_process(Move m);
    void pass_process();
    void branchpoint_process();
    void endOfVariation_process();
    void endgame_process(bool commit=true);
    void finalize_process();
    int search(PatternList& patternList, GameList& gl, SearchOptions& options);

    std::vector<char> movelist;
    char* fpC;
    std::map<int, char* > data1;
    std::map<int, char* > data2;
    std::map<int, int> data1l;
    SnapshotVector get_data();
};


// --------------------------------------------------------------------------------------------------------



class HashhitF { // hashing hit for full board search
  public:
    int gameid;
    char orientation;
    MoveNC* cont;
    ExtendedMoveNumber* emn;

    HashhitF();
    HashhitF(int GAMEID, char ORIENTATION, ExtendedMoveNumber& EMN, MoveNC* CONT);
    HashhitF(int GAMEID, char ORIENTATION, char* blob);
    HashhitF(const HashhitF& HHF);
    ~HashhitF();
    HashhitF& operator=(const HashhitF& HHF);

    char* export_blob();
};

typedef vector<HashhitF* >* vpsip;

class HashhitCS { // hashing hit for corner/side pattern search
  public:
    int gameid;
    int position;
    bool cs;
    HashhitCS(int GAMEID, int POSITION, bool CS);
    bool operator==(const HashhitCS& hhc);
};

class HashVarInfo {
  public:
    hashtype chc;
    std::vector<std::pair<hashtype, ExtendedMoveNumber> > * lfc;
    ExtendedMoveNumber* moveNumber;
    int numStones;

    HashVarInfo(hashtype CHC, std::vector<std::pair<hashtype, ExtendedMoveNumber> > * LFC, ExtendedMoveNumber* MOVENUMBER, int NUMSTONES);
};

/// Hashing for full board patterns
class Algo_hash_full : public Algorithm {
  /*! Basic notes:
   *
   * For searches, <tt>data</tt> is used. It maps hashCodes to positions in the
   * file <tt>os_data</tt>. At the specified position of the file, all game ids
   * etc. where a position with this hashCode occurs are listed.
   *
   * During processing, a multimap <tt>data_p</tt> is used which maps hashCodes
   * to single hits. This data is written to os_data (together with the data
   * previously available, if any) in <tt>get_data</tt>.
   */

  public:
    Algo_hash_full(int bsize, SnapshotVector DATA, const string OS_DATA_NAME, int MAXNUMSTONES = 50);
    ~Algo_hash_full();
    void initialize_process();
    void newgame_process(int game_id);
    void AB_process(int x, int y);
    void AW_process(int x, int y);
    void AE_process(int x, int y, char removed);
    void endOfNode_process();
    void move_process(Move m);
    void pass_process();
    void branchpoint_process();
    void endOfVariation_process();
    void endgame_process(bool commit=true);
    void finalize_process();
    int search(PatternList& patternList, GameList& gl, SearchOptions& options);

    void process_lfc(int x, int y, char color);
    hashtype compute_hashkey(Pattern& pattern);
    int maxNumStones;
    int numStones;

    vector<pair<hashtype, int> > data;
    boost::unordered_multimap<hashtype, HashhitF> data_p;
    SnapshotVector get_data();
    fstream os_data;
    
  private:
    hashtype currentHashCode;
    ExtendedMoveNumber* moveNumber;
    std::vector<std::pair<hashtype, ExtendedMoveNumber> > *lfc; // hash code + move number, still *l*ooking *f*or *c*ontinuation
    std::stack<HashVarInfo>* branchpoints;
    boost::unordered_multimap<hashtype, HashhitF> hash_vector;
    void get_HHF(int ptr, vpsip results, int orientation);
};


// --------------------------------------------------------------------------------------------


class HashInstance {
  // When processing sgf games, Algo_hash maintains a list of HashInstance's -
  // those are regions on the board for which hash codes are put into the
  // database

  public:
    HashInstance(char X, char Y, char SIZEX, char SIZEY, int BOARDSIZE);
    ~HashInstance();
    bool inRelevantRegion(char X, char Y);

    char xx; // position on the board
    char yy;
    int pos;
    int boardsize;
    char sizeX; // size of the pattern
    char sizeY;
    bool changed;

    void initialize();
    void finalize();
    void addB(char x, char y);
    void removeB(char x, char y);
    void addW(char x, char y);
    void removeW(char x, char y);
    void bppush();
    void bppop();
    std::pair<hashtype,int> cHC();  // returns min(currentHashCode) and corresp. index
    hashtype* currentHashCode; // array of 8 hashtype values (to automatically symmetrize hash codes)
    std::stack<std::pair<hashtype*,int> >* branchpoints;
    int numStones;
};

/// Base class for hashing for general type patterns (currently works only for corner patterns).
class Algo_hash : public Algorithm {
  // This class should not be used by the "end-user" (see Algo_hash_corner and
  // Algo_hash_sides instead)

  public:
    Algo_hash(int bsize, SnapshotVector DATA, string OS_DATA_NAME, int MAXNUMSTONES);
    virtual ~Algo_hash();
    virtual void initialize_process();
    virtual void newgame_process(int game_id);
    virtual void AB_process(int x, int y);
    virtual void AW_process(int x, int y);
    virtual void AE_process(int x, int y, char removed);
    virtual void endOfNode_process();
    virtual void move_process(Move m);
    virtual void pass_process();
    virtual void branchpoint_process();
    virtual void endOfVariation_process();
    virtual void endgame_process(bool commit=true);
    virtual void finalize_process();

    /// Do a pattern search for the Pattern specified by patternList, in the GameList gl.
    /// 
    /// This computes the hashCode for the given pattern, looks it up in the database,
    /// and turns all records found there into Candidate entries which can be used by Algo_movelist::search
    /// If more than one corner lies inside the pattern, the hashCode for the corner which contains most stones
    /// is used.
    virtual int search(PatternList& patternList, GameList& gl, SearchOptions& options);

    friend class GameList;
    friend class Algo_hash_full;
    friend class HashInstance;
    
  protected:

    int maxNumStones;
    SnapshotVector get_data(); //< Used to read data from disk into \c data
    
    /// takes a pointer to os_data, a vector results, and a bool cs (==colorSwitch)
    /// and adds the hits from the database to the results vector:
    virtual void get_HHCS(int ptr, vector<HashhitCS* >* results, bool cs);

    virtual std::pair<hashtype,std::vector<int> >  compute_hashkey(PatternList& pl, int CS);
    static const hashtype hashCodes[];
    std::vector<HashInstance>* hi;
    std::vector<std::pair<hashtype, int> > hash_vector;

    vector<pair<hashtype, int> > data;
    boost::unordered_multimap<hashtype, pair<int,int> > data_p;
    fstream os_data;
};

/// Hashing for corner patterns
class Algo_hash_corner : public Algo_hash {
  public:
    Algo_hash_corner(int bsize, SnapshotVector DATA, string OS_DATA_NAME, int SIZE=7, int MAXNUMSTONES = 20);

    /// Given a PatternList and a choice of colorSwitch (true/false), compute the hashCodes that we
    /// have to look for in the db.
    ///
    /// The method returns a vector of pairs, consisting of a hashCode (for one of the corners covered by the pattern)
    /// and a vector of possible flips which should be used to produce a Candidate.
    std::pair<hashtype,std::vector<int> >  compute_hashkey(PatternList& pl, int CS);

    /// size of the region used for hashing (the region is a square with side-length \c size, located at a corner of the board)
    int size;
};


// ---------------------------------------------------------------------------------------------------------------


typedef Algorithm* algo_p;


#endif

