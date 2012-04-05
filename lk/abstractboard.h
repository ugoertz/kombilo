/*! \file abstractboard.h
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


#ifndef _ABSTRACTBOARD_H_
#define _ABSTRACTBOARD_H_

#include <vector>
#include <utility>
#include <stack>
#include <iostream>

class BoardError {
 public:
  BoardError();
};

typedef std::pair<int,int> p_cc;


const char AB = 'x';
const char AW = 'y';
const char AEB = 'z'; // remove a black stone
const char AEW = 'Z'; // remove a white stone



class MoveNC {
  public:
    char x;
    char y;
    char color;

    MoveNC();
    MoveNC(char X, char Y, char COLOR);
    MoveNC(const MoveNC& MNC);
    bool operator==(const MoveNC& mnc) const;
};

class Move : public MoveNC {
  public:
    Move();
    Move(char xx, char yy, char cc);
    Move(char xx, char yy, char cc, std::vector<p_cc > cap);
    Move(const Move& m);
    ~Move();
    Move& operator=(const Move& m);

    std::vector<p_cc >* captures;
};


/// This class implements an "abstract" go board where you can play stones.
/// The \c play method checks whether the move is legal, and computes the
/// captures which it makes.
class abstractBoard {
  public:
    int boardsize;
    std::vector<Move> undostack;

    abstractBoard(int bs = 19) throw(BoardError);
    abstractBoard(const abstractBoard& ab);
    ~abstractBoard();
    abstractBoard& operator=(const abstractBoard& ab);

    void clear(); ///< Clear the board and the undostack
    int play(int x, int y, const char* color) throw(BoardError);
    ///< play a move of specified color (a string starting with \c b, \c B, \c w or \c W) at given position (x, y between 0 and boardsize-1)
    void undo(int n=1); ///< undo \c n moves
    void remove(int x, int y, bool removeFromUndostack);
    char getStatus(int x, int y);
    void setStatus(int x, int y, char val);

    /// \name Convenience methods to handle the undostack
    /// The undostack contains information about all moves played (and in particular the captures
    /// made with each of those moves.
    /**@{*/
    int len_cap_last() throw(BoardError);
    void undostack_append_pass();
    p_cc undostack_top_pos();
    char undostack_top_color();
    std::vector<p_cc > undostack_top_captures();
    void undostack_push(Move& m);
    void undostack_pop();
    /**@}*/

    // abstractBoard& copy(const abstractBoard& ab);

  private:
    char* status;
    int* neighbors(int x, int y);
    std::vector<p_cc >* legal(int x, int y, char color);
    std::vector<p_cc >* hasNoLibExcP(int x1, int y1, int exc=-1);
    char invert(char);
};

#endif

