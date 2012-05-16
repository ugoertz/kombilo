/*! \file pattern.h
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


#ifndef _PATTERN_H_
#define _PATTERN_H_

#include <vector>
#include <stack>
#include <fstream>
#include <stdint.h>
#include <sqlite3.h>
#include "boost/unordered_map.hpp"

#include "abstractboard.h"
#include "sgfparser.h"


typedef char* char_p;
typedef int64_t hashtype;
#if (defined(__BORLANDC__) || defined(_MSC_VER))
const hashtype NOT_HASHABLE = 9223372036854775807i64;
#else
const hashtype NOT_HASHABLE = 9223372036854775807LL;  // == (1 << 63) -1; in fact, (1<<64)-1 shoul be OK, too.
#endif

const char NO_CONT = 255;

const int CORNER_NW_PATTERN = 0;
const int CORNER_NE_PATTERN = 1;
const int CORNER_SW_PATTERN = 2;
const int CORNER_SE_PATTERN = 3;
const int SIDE_N_PATTERN = 4;
const int SIDE_W_PATTERN = 5;
const int SIDE_E_PATTERN = 6;
const int SIDE_S_PATTERN = 7;
const int CENTER_PATTERN = 8;
const int FULLBOARD_PATTERN = 9;

const int ALGO_FINALPOS = 1;
const int ALGO_MOVELIST = 2;
const int ALGO_HASH_FULL = 4;
const int ALGO_HASH_CORNER = 8;
// const int ALGO_INTERVALS = 16;
const int ALGO_HASH_CENTER = 32;
const int ALGO_HASH_SIDE = 64;

const int algo_finalpos = 1;
const int algo_movelist = 2;
const int algo_hash_full = 3;
const int algo_hash_corner = 4;
const int algo_intervals = 5;
const int algo_hash_center = 6;
const int algo_hash_side = 7;

/// \name date profile constants
/**@{*/
const int DATE_PROFILE_START = 1600;
const int DATE_PROFILE_END = 2020;
/**@}*/

char* flipped_sig(int f, char* sig, int boardsize);
char* symmetrize(char* sig, int boardsize);

class SnapshotVector : public std::vector<unsigned char> {
  public:
    SnapshotVector();
    SnapshotVector(char* c, int size);

    void pb_int(int d);
    void pb_hashtype(hashtype d);
    void pb_int64(int64_t d);
    void pb_charp(const char* c, int size);
    void pb_char(char c);
    void pb_string(std::string s);
    void pb_intp(int* p, int size);

    int retrieve_int();
    hashtype retrieve_hashtype();
    int64_t retrieve_int64();
    int* retrieve_intp();
    char retrieve_char();
    char* retrieve_charp();
    std::string retrieve_string();

    char* to_charp();

  private:
    SnapshotVector::iterator current;
};


class PatternError {
  public:
    PatternError();
};

class DBError {
  public:
    DBError();
};

class Symmetries {
  public:
    char* dataX;
    char* dataY;
    char* dataCS;
    char sizeX;
    char sizeY;
    Symmetries(char sX=0, char sY=0);
    ~Symmetries();
    Symmetries(const Symmetries& s);
    Symmetries& operator=(const Symmetries& s);
    void set(char i, char j, char k, char l, char cs) throw(PatternError);
    char getX(char i, char j) throw(PatternError);
    char getY(char i, char j) throw(PatternError);
    char getCS(char i, char j) throw(PatternError);
    char has_key(char i, char j) throw(PatternError);
};

/*! A pattern, say 
 * 
 * <pre>
 * XXOo
 * ..Xx
 * ..O*
 * </pre>
 * 
 * is given by
 * \li \c sizeX = 4 (the size along the horizontal axis),
 * \li \c sizeY = 3 (the size along the vertical axis),
 * \li \c a string initialPos = "XXOo..Xx..O*" of length <tt>sizeX*sizeY</tt> which contains the "content" of the pattern.
 *
 * Here we use the following notation for search patterns:
 * 
 * \li \c . must be empty
 * \li \c X  must have a black stone
 * \li \c O  must have a white stone
 * \li \c x  must be black or empty
 * \li \c o  must be white or empty
 * \li \c *  can be arbitrary
 *
 * We use an analogous coordinate system as for the board, so a point with
 * coordinates (i,j) is stored at position (i + j*sizeX) in the string.
 *
 * The area of the board where we want to search for the given pattern (or, in
 * other words, the set of permissible translations) is described by the
 * parameters \c left, \c right, \c top, \c bottom where the rectangle with
 * corners (left,top) and (right,bottom) is the set of possible positions for
 * the upper left point of the pattern.
 *
 * For instance, if all entries are 0, then the upper left corner is the only
 * place where we would look for the pattern.
 *
 * Instead of specifying \c left, \c right, \c top, \c bottom, in most cases
 * one can just give the "pattern type", see the constants FULLBOARD_PATTERN,
 * CENTER_PATTERN, etc.
 *
 * <h4>Possibly a list of continuations</h4>



 *
 *
 *
 */

class Pattern {
  public:
    int left; // left, right, top, bottom "==" anchors
    int right;
    int bottom;
    int top;
    int boardsize;

    int sizeX;
    int sizeY;

    int flip;                  // used for elements of a patternList
    int colorSwitch;           // dito
    char* initialPos;
    char* finalPos;
    char* contLabels;
    std::vector<MoveNC> contList;

    // Pattern constructors
    //
    // the char* contLabels, if != 0, should have the same size as the pattern, and should 
    // contain pre-fixed label (which should be re-used when presenting the search results)
    // Positions without a given label should contain '.'
    //
    // Note: the char*'s iPos and CONTLABELS will NOT be free'ed by the Pattern class.

    Pattern();
    Pattern(int le, int ri, int to, int bo, int BOARDSIZE, int sX, int sY, const char* iPos, const std::vector<MoveNC>& CONTLIST, const char* CONTLABELS = 0) throw(PatternError);
    Pattern(int le, int ri, int to, int bo, int BOARDSIZE, int sX, int sY, const char* iPos) throw(PatternError);
    Pattern(int type, int BOARDSIZE, int sX, int sY, const char* iPos, const std::vector<MoveNC>& CONTLIST, const char* CONTLABELS = 0);
    Pattern(int type, int BOARDSIZE, int sX, int sY, const char* iPos, const char* CONTLABELS = 0);
    Pattern(const Pattern& p);
    Pattern(SnapshotVector& snv);
    ~Pattern();
    Pattern& operator=(const Pattern& p);
    Pattern& copy(const Pattern& p);

    char getInitial(int i, int j);
    char getFinal(int i, int j);

    char BW2XO(char c);
    int operator==(const Pattern& p);
    std::string printPattern();
    void to_snv(SnapshotVector& snv);

    static int flipsX(int i, int x, int y, int XX, int YY);
    static int flipsY(int i, int x, int y, int XX, int YY);
    static int PatternInvFlip(int i);
    static int compose_flips(int i, int j); // returns index of flip "first j, then i"
};

class GameList;

class Continuation {
  public:
    int x; ///< x coordinate of corresp. label on board
    int y; ///< y coordinate of corresp. label on board
    int B ; ///< number of all black continuations
    int W ; ///< number of all white continuations
    int tB; ///< number of black tenuki plays
    int tW; ///< number of white tenuki plays
    int wB; ///< black wins (where next play is B)
    int lB; ///< black losses (where next play is B)
    int wW; ///< black wins (where next play is W)
    int lW; ///< black losses (where next play is W)
    vector<int> dates_B;
    vector<int> dates_W;

    char label;

    GameList* gamelist;

    Continuation(GameList* gl); ///< initializes all member variables with 0
    Continuation(const Continuation& c);
    Continuation& operator=(const Continuation& c);
    void add(const Continuation c); ///< Add values for B, W, tB, tW, wB, lB, wW, lW of c to values of this
    int earliest(); ///< earliest date when this was played
    int earliest_B(); ///< earliest date when this was played by B
    int earliest_W(); ///< earliest date when this was played by W
    int latest(); ///< latest date when this was played
    int latest_B();
    int latest_W();
    float average_date(); ///< average date when this was played
    float average_date_B();
    float average_date_W();
    int became_popular(); ///< date when this move became popular
    int became_popular_B();
    int became_popular_W();
    int became_unpopular(); ///< date when this move became unpopular
    int became_unpopular_B();
    int became_unpopular_W();
    // TODO weighted average

    /// All dates are given by year (in the interval between DATE_PROFILE_START
    /// and DATE_PROFILE_END).
    int total();

    friend class GameList;

  private:
    void from_snv(SnapshotVector& snv);
    void to_snv(SnapshotVector& snv);
};

class PatternList {
  public:
    Pattern pattern;
    int fixedColor;                      ///< search for pattern with exchanged colors as well?
    int nextMove;                        ///< 1: next must be black, 2: next must be white, 0: no restriction
    std::vector<Pattern> data;
    std::vector<Symmetries> symmetries;
    vector<Continuation* > continuations;
    int* flipTable;
    int special; ///< == -1, unless there exists a symmetry which yields the color-switched pattern

    PatternList(Pattern& p, int fColor, int nMove, GameList* gl) throw (PatternError);
    ~PatternList();

    void patternList();
    Pattern get(int i);
    int size();

    friend class GameList;
    friend class Algo_movelist;
    friend class Algo_hash_full;
  
  private:
    char* updateContinuations(int orientation, int x, int y, char co, bool tenuki, char winner, int date);
    char* sortContinuations(); // and give them names to be used as labels
    char invertColor(char co);
};

class Candidate {
  public:
    char x;
    char y;
    char orientation; // == index in corresp patternList

    Candidate(char X, char Y, char ORIENTATION);
};

class Hit {
  public:
    ExtendedMoveNumber* pos;
    char* label; // this does not really contain the label, but rather the position of the continuation move
    Hit(ExtendedMoveNumber* POS, char* LABEL);
    Hit(SnapshotVector& snv); // takes a SnapshotVector and reads information produced by Hit::to_snv()
    ~Hit();
    static bool cmp_pts(Hit* a, Hit* b);
    void to_snv(SnapshotVector& snv);
};




#endif

