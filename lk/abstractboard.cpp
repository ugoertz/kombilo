/*! \file abstractboard.cpp
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


#include <stdio.h>
#include <iostream>
#include "abstractboard.h"
using std::stack;
using std::vector;
using namespace std;

BoardError::BoardError() {}

MoveNC::MoveNC() {
  x = -1;
  y = -1;
  color = ' ';
}

MoveNC::MoveNC(const MoveNC& MNC) {
  x = MNC.x;
  y = MNC.y;
  color = MNC.color;
}

// coordinates used here: top left = (0,0) - bottom right = (boardsize-1,boardsize-1)
MoveNC::MoveNC(char X, char Y, char COLOR) {
  x = X;
  y = Y;
  color = COLOR;
}

bool MoveNC::operator==(const MoveNC& mnc) const {
  if (x == mnc.x && y == mnc.y && color == mnc.color) return true;
  else return false;
}


Move::Move() : MoveNC() {
  captures = 0;
}

Move::Move(char xx, char yy, char cc) : MoveNC(xx, yy, cc) {
  captures = 0;
}

Move::Move(char xx, char yy, char cc, vector<p_cc > cap) : MoveNC(xx, yy, cc) {
  captures = new vector<p_cc >(cap);
}

Move::Move(const Move& m) : MoveNC(m.x, m.y, m.color) {
  if (m.captures) {
    captures = new vector<p_cc>;
    vector<p_cc>::iterator it;
    for(it = m.captures->begin(); it != m.captures->end(); it++) 
      captures->push_back(*it);
  }
  else captures = 0;
}

Move::~Move() {
  if (captures) delete captures;
}

Move& Move::operator=(const Move& m) {
  if (this != &m) {
    x = m.x;
    y = m.y;
    color = m.color;
    if (captures) delete captures;
    if (m.captures) {
      captures = new vector<p_cc>;
      vector<p_cc>::iterator it;
      for(it = m.captures->begin(); it != m.captures->end(); it++) 
        captures->push_back(*it);
    }
    else captures = 0;
  }
  return *this;
}

abstractBoard::abstractBoard(int bs) throw(BoardError) {
  boardsize = bs;
  if (boardsize < 1) throw BoardError();
  status = new char[boardsize*boardsize+1];
  for (int i = 0; i < boardsize*boardsize; i++)
      status[i] = ' ';
  status[boardsize*boardsize] = 0;
}

abstractBoard::abstractBoard(const abstractBoard& ab) {
  boardsize = ab.boardsize;
  status = new char[boardsize*boardsize+1];
  for (int i = 0; i < boardsize*boardsize; i++)
      status[i] = ab.status[i];
  status[boardsize*boardsize] = 0;
  undostack = vector<Move>(ab.undostack);
}

abstractBoard& abstractBoard::operator=(const abstractBoard& ab) {
  if (this != &ab) {
    boardsize = ab.boardsize;
    delete [] status;
    status = new char[boardsize*boardsize+1];
    for (int i = 0; i < boardsize*boardsize; i++)
      status[i] = ab.status[i];
    status[boardsize*boardsize] = 0;
    undostack = vector<Move>(ab.undostack);
  }
  return *this;
}

abstractBoard::~abstractBoard() {
  delete [] status;
}

// abstractBoard& abstractBoard::copy(const abstractBoard& ab) {
//   printf("copy assignment operator\n");
//   if (this != &ab) {
//     delete status;
//     boardsize = ab.boardsize;
//     status = new char[boardsize*boardsize+1];
//     for (int i = 0; i < boardsize*boardsize; i++)
//       status[i] = ab.status[i];
//     status[boardsize*boardsize] = 0;
//     undostack = ab.undostack;
//   }
//   return *this;
// }

char abstractBoard::getStatus(int x, int y) {
  return status[boardsize*x + y];
}

void abstractBoard::setStatus(int x, int y, char val) {
  if (val=='b' || val=='B') status[boardsize*x + y] = 'B';
  else if (val=='w' || val=='W') status[boardsize*x + y] = 'W';
  else status[boardsize*x + y] = val;
}

int abstractBoard::len_cap_last() throw(BoardError) {
  return undostack_top_captures().size();
}


p_cc abstractBoard::undostack_top_pos() {
  Move m = undostack.back();
  return p_cc(m.x, m.y);
}

char abstractBoard::undostack_top_color() {
  Move m = undostack.back();
  return m.color;
}

vector<p_cc> abstractBoard::undostack_top_captures() {
  Move m = undostack.back();
  if (m.captures) return vector<p_cc>(*m.captures);
  else return vector<p_cc>();
}

void abstractBoard::undostack_pop() {
  undostack.pop_back();
}

void abstractBoard::undostack_push(Move& m) {
  undostack.push_back(m);
}

void abstractBoard::undostack_append_pass() {
  undostack.push_back(Move(19,19,'-'));
}

int* abstractBoard::neighbors(int x, int y) {
  int* result = new int[5];
  int resultIndex = 1;
  if (x-1 >= 0) result[resultIndex++]=(x-1) * boardsize + y;
  if (x+1 < boardsize) result[resultIndex++]=(x+1) * boardsize + y;
  if (y-1 >= 0) result[resultIndex++]=x * boardsize + y-1;
  if (y+1 < boardsize) result[resultIndex++]=x*boardsize + y+1;
  result[0] = resultIndex-1;
  return result;
}

void abstractBoard::clear() {
  for(int i=0; i<boardsize*boardsize; i++) status[i]=' ';
  undostack = vector<Move>();
}

int abstractBoard::play(int x, int y, const char* color) throw (BoardError) {
  // cout << "ab::play" << x << " " << y << endl;
  if (x<0 || x>=boardsize || y<0 || y>=boardsize) return 0;
  if (status[boardsize*x+y] != ' ') {
    // cout << "status" << x << " " << y << endl;
    return 0;
  }

  char co = color[0];
  if (co == 'b') co = 'B';
  if (co == 'w') co = 'W';
  vector<p_cc>* captures = legal(x, y, co);
  if (captures) {
    vector<p_cc>::iterator it;
    for(it=captures->begin(); it!=captures->end(); it++)
      status[boardsize*it->first + it->second] = ' '; // remove captured stones, if any
    Move m(x, y, co);
    if (captures->size()) m.captures = captures;
    else delete captures;
    undostack.push_back(m);
    return 1;
  }
  return 0;
}

vector<p_cc>* abstractBoard::legal(int x, int y, char color) {
  vector<p_cc>* c = new vector<p_cc>;
  int* nb = neighbors(x,y);
  for(int i=1; i<=nb[0]; i++) {
    int x1 = nb[i] / boardsize;
    int y1 = nb[i] % boardsize;
    if (status[boardsize*x1 + y1] == invert(color)) {
      vector<p_cc>* d = hasNoLibExcP(x1, y1, x*boardsize+y);
      vector<p_cc>::iterator it;
      for(it = d->begin(); it != d->end(); it++) c->push_back(*it);
      delete d;
    }
  }
  delete [] nb;
  setStatus(x,y,color);

  if (c->size()) {
    vector<p_cc>* captures = new vector<p_cc>();
    while (c->size()) {
      p_cc ctop = (*c)[0];
      bool contained = false;
      vector<p_cc>::iterator it;
      for(it = captures->begin(); it != captures->end(); it++) {
        if (ctop.first == it->first && ctop.second == it->second) {
          contained = true;
          break;
        }
      }
      if (!contained) captures->push_back(ctop);
      c->erase(c->begin());
    }
    delete c;
    return captures;
  }
  delete c;
  vector<p_cc>* d = hasNoLibExcP(x, y);
  if (d->size()) {
    delete d;
    status[boardsize*x + y] = ' ';
    return 0;
  }
  else {
    delete d;
    vector<p_cc>* ret = new vector<p_cc>();
    return ret;
  }
}

vector<p_cc>* abstractBoard::hasNoLibExcP(int x1, int y1, int exc) {
  vector<p_cc>* st = new vector<p_cc>;
  vector<p_cc>* newlyFound = new vector<p_cc>;
  newlyFound->push_back(p_cc(x1, y1));
  vector<p_cc>* n;
  int foundNew = 1;

  while (foundNew) {
    foundNew = 0;
    n = new vector<p_cc>;
    vector<p_cc>::iterator it1;
    for(it1=newlyFound->begin(); it1!=newlyFound->end(); it1++) {
      int x = it1->first;
      int y = it1->second;
      int* nbs = neighbors(x,y);
      for (int j=1; j <= nbs[0]; j++) {
        int yy1 = nbs[j];
        if (status[yy1] == ' ' && yy1 != exc) {
          delete [] nbs;
          delete st;
          delete newlyFound;
          delete n;
          return new vector<p_cc>;
        }
        else {
          if (status[yy1]==status[x*boardsize+y]) {
            p_cc yy(yy1/boardsize, yy1%boardsize);
            int foundNewHere = 1;
            vector<p_cc>::iterator it;
            for(it=n->begin(); it!=n->end(); it++) {
              if (it->first==yy.first && it->second==yy.second) {
                foundNewHere = 0;
                break;
              }
            }
            if (foundNewHere) {
              for(it = st->begin(); it!=st->end(); it++) {
                if (it->first==yy.first && it->second==yy.second) {
                  foundNewHere = 0;
                  break;
                }
              }
            }
            if (foundNewHere) {
              n->push_back(yy);
              foundNew = 1;
            }
          }
        }
      }
      delete [] nbs;
    }

    vector<p_cc>::iterator it;
    for(it=newlyFound->begin(); it!=newlyFound->end(); it++) {
      st->push_back(*it);
    }
    delete newlyFound;
    newlyFound = n;
  }
  delete n;
  return st;
}


void abstractBoard::undo(int n) {
  for(int i=0; i<n; i++) {
    if (undostack.size()) {
      Move tuple = undostack.back();
      int x = tuple.x;
      int y = tuple.y;

      undostack.pop_back();
      char color = tuple.color;
      vector<p_cc>* captures = tuple.captures;

      if (color == 'B' || color == 'W') {
        status[x*boardsize+y] = ' ';
        if (captures) {
          for(unsigned int i=0; i < captures->size(); i++) {
            p_cc t = (*captures)[i];
            setStatus(t.first, t.second, invert(color));
          }
        }
      }
      if (color == AB || color == AW) setStatus(x, y, ' ');
      if (color == AEB) setStatus(x, y, 'B'); 
      if (color == AEW) setStatus(x, y, 'W'); 
    }
  }
}

void abstractBoard::remove(int x, int y, bool removeFromUndostack) {
  if (removeFromUndostack) { // removing a stone which was placed by AB/AW in same SGF node
    char t = status[boardsize*x+y] == 'B' ? AB : AW;
    for(vector<Move>::reverse_iterator it = undostack.rbegin(); it != undostack.rend(); it++) {
      if (it->color == t && it->x == x && it->y == y) {
        // cout << "erase" << x << " " << y << endl;
        undostack.erase(it.base()-1);
        break;
      }
    }
  } else  undostack.push_back(Move(x, y, status[boardsize*x+y] == 'B' ? AEB : AEW));
  status[boardsize*x+y] = ' ';
}

char abstractBoard::invert(char color) {
  if (color == 'B' || color == 'b') return 'W';
  if (color == 'W' || color == 'w') return 'B';
  return ' ';
}

