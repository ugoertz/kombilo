// File: algos.cpp
// part of libkombilo, http://www.u-go.net/kombilo/

// Copyright (c) 2006-12 Ulrich Goertz <ug@geometry.de>

// Permission is hereby granted, free of charge, to any person obtaining a copy of
// this software and associated documentation files (the "Software"), to deal in
// the Software without restriction, including without limitation the rights to
// use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
// of the Software, and to permit persons to whom the Software is furnished to do
// so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

#include "sgfparser.h"
#include "abstractboard.h"
#include "pattern.h"
#include "algos.h"
#include "search.h"
#include "boost/unordered_map.hpp"
#include <stdio.h>
#include <string>
#include <cstring>
#include <iostream>
#include <fstream>

using std::min;
using std::max;
using std::string;
using std::vector;
using std::map;
using std::pair;
using std::make_pair;
using std::stack;
using std::ofstream;

#if defined(_MSC_VER)
#include <algorithm>
#else
#include <algorithm>
using std::sort;
#endif


DBError::DBError() {
}


// ------------------------------------------------------------------------------------------------


Algorithm::Algorithm(int bsize) {
  boardsize = bsize;
}

Algorithm::~Algorithm() {}

void Algorithm::initialize_process() {}
void Algorithm::newgame_process(int game_id) {}
void Algorithm::AB_process(int x, int y) {}
void Algorithm::AW_process(int x, int y) {}
void Algorithm::AE_process(int x, int y, char removed) {}
void Algorithm::endOfNode_process() {}
void Algorithm::move_process(Move m) {}
void Algorithm::pass_process() {}
void Algorithm::branchpoint_process() {}
void Algorithm::endOfVariation_process() {}
void Algorithm::endgame_process(bool commit) {}
void Algorithm::finalize_process() {}
SnapshotVector Algorithm::get_data() { return SnapshotVector(); }
int Algorithm::search(PatternList& patternList, GameList& gl, SearchOptions& options) {
  return -1;
}


// -----------------------------------------------------------------------------------------------


Algo_signature::Algo_signature(int bsize, SnapshotVector DATA) : Algorithm(bsize) {
  main_variation = true;

  // initialize data from DATA
  // data is boost::unordered_multimap<string = signature, int = gameid>

  if (!DATA.empty()) {
    int si = DATA.retrieve_int();
    // printf("read size %d\n", si);
    for(int i=0; i<si; i++) {
      // int size = DATA.retrieve_int();
      // if (size!=13) printf("ouch %d\n", size);
      // DATA.current -= 4;
      char* s = DATA.retrieve_charp();
      data.insert(pair<string,int>(string(s), DATA.retrieve_int()));
      delete [] s;
    }
  }
}

SnapshotVector Algo_signature::get_data() {
  SnapshotVector v;

  v.pb_int(data.size());
  // printf("push back size %d\n", data.size());
  for(boost::unordered_multimap<string,int>::iterator it = data.begin(); it != data.end(); it++) {
    if ((it->first)[12] != 0) printf("oops\n");
    v.pb_charp(it->first.c_str(), 13);
    v.pb_int(it->second);
    // printf("gameid %d\n", it->second);
  }
  // printf("v size %d\n", v.size());
  return v;
}


Algo_signature::~Algo_signature() {
}

void Algo_signature::initialize_process() {
}

void Algo_signature::newgame_process(int game_id) {
  main_variation = true;
  counter = 0;
  gid = game_id;
  signature = new char[13];
  for(int i=0; i<12; i++) signature[i] = '?';
  signature[12] = 0;
}

void Algo_signature::AB_process(int x, int y) {
}

void Algo_signature::AW_process(int x, int y) {
}

void Algo_signature::AE_process(int x, int y, char removed) {
}

void Algo_signature::endOfNode_process() {
}

void Algo_signature::move_process(Move m) {
  if (!main_variation) return;
  counter++;

  if (counter==20) {
    signature[0] = m.x + 97; // 97 == ord('a')
    signature[1] = m.y + 97;
  }
  if (counter==40) {
    signature[2] = m.x + 97;
    signature[3] = m.y + 97;
  }
  if (counter==60) {
    signature[4] = m.x + 97;
    signature[5] = m.y + 97;
  }
  if (counter==31) {
    signature[6] = m.x + 97;
    signature[7] = m.y + 97;
  }
  if (counter==51) {
    signature[8] = m.x + 97;
    signature[9] = m.y + 97;
  }
  if (counter==71) {
    signature[10] = m.x + 97;
    signature[11] = m.y + 97;
  }
}

void Algo_signature::pass_process() {
  if (main_variation) move_process(Move(19,19,'p'));
}

void Algo_signature::branchpoint_process() {
}

void Algo_signature::endOfVariation_process() {
  main_variation = false;
}

void Algo_signature::endgame_process(bool commit) {
  if (commit) {
    char* min_signature = symmetrize(signature, boardsize);
    data.insert(pair<string,int>(string(min_signature), gid));
    // for(int i=0; i<12; i++) printf("%c", min_signature[i]); printf("\n");
    delete [] min_signature;
  }
  delete [] signature;
}

void Algo_signature::finalize_process() {
}

char* Algo_signature::get_current_signature() {
  return symmetrize(signature, boardsize);
}

vector<int> Algo_signature::search_signature(char* sig) { // sig is expected to be a 0-terminated cstr;
                                                          // this is called only during process (but also for other gamelists in the glists
                                                          // argument to process, in order to check for duplicates).
  vector<int> result;
  pair<boost::unordered_multimap<string,int>::iterator, boost::unordered_multimap<string,int>::iterator> res = data.equal_range(string(sig));
  for (boost::unordered_multimap<string,int>::iterator it = res.first; it != res.second; it++)
    result.push_back((*it).second);
  return result;
}




// ----------------------------------------------------------------------------------------------------------------


Algo_finalpos::Algo_finalpos(int bsize, SnapshotVector DATA) : Algorithm(bsize) {
  fp = 0;
  fpIndex = -1;

  // data is a map<int = gameid, char* = char[100] containing the finalpos for gameid>

  if (!DATA.empty()) {
    unsigned int si = DATA.retrieve_int();
    for(size_t i=0; i<si; i++) {
      int game_id = DATA.retrieve_int();
      // printf("game id %d\n", game_id);
      char* s = DATA.retrieve_charp();
      data.push_back(pair<int, char*>(game_id, s));
    }
  }
}



SnapshotVector Algo_finalpos::get_data() {
  SnapshotVector v;
  v.pb_int(data.size());

  for(vector<pair<int, char*> >::iterator it = data.begin(); it != data.end(); it++) {
    v.pb_int(it->first);
    v.pb_charp(it->second, 100);
  }
  return v;
}

Algo_finalpos::~Algo_finalpos() {
  for(vector<pair<int, char* > >::iterator it = data.begin(); it != data.end(); it++) delete [] it->second;
}

void Algo_finalpos::initialize_process() {
  // printf("init Algo_finalpos\n");
}

void Algo_finalpos::newgame_process(int game_id) {
  gid = game_id;
  fp = new char[100]; // TODO boardsize?!
  for(int i=0; i<100; i++) fp[i] = 255;
}

void Algo_finalpos::AB_process(int x, int y) {
  fp[y/2 + 10*(x/2)] &= ~(1 << (2*(x%2 + 2*(y%2))));
}

void Algo_finalpos::AW_process(int x, int y) {
  fp[y/2 + 10*(x/2)] &= ~(1 << (2*(x%2 + 2*(y%2))+1));
}

void Algo_finalpos::AE_process(int x, int y, char removed) {
}

void Algo_finalpos::endOfNode_process() {
}

void Algo_finalpos::move_process(Move m) {
  if (m.color == 'B')
    fp[m.y/2 + 10*(m.x/2)] &= ~(1 << (2*(m.x%2 + 2*(m.y%2))));
  else if (m.color == 'W')
    fp[m.y/2 + 10*(m.x/2)] &= ~(1 << (2*(m.x%2 + 2*(m.y%2))+1));
}

void Algo_finalpos::pass_process() {
}

void Algo_finalpos::branchpoint_process() {
}

void Algo_finalpos::endOfVariation_process() {
}

void Algo_finalpos::endgame_process(bool commit) {
  if (commit) data.push_back(pair<int, char*>(gid, fp));
  else delete [] fp;
}

void Algo_finalpos::finalize_process() {
  sort(data.begin(), data.end());
}

unsigned long stringhash(int size, char *str) {
  // returns a simple hashcode of char[bs*bs]
  // cf http://www.ntecs.de/projects/guugelhupf/doc/html/x435.html, 7.2.4
  unsigned long hash = 0;
  for(int i=0; i<size; i++) hash = str[i] + (hash << 6) + (hash << 16) - hash;
  return hash;
}




hashtype Algo_finalpos::get_current_fphash() {
  return stringhash(100, fp); // TODO boardsize
}

hashtype Algo_finalpos::get_fphash(int index) {
  char* np = 0;
  vector<pair<int, char*> >::iterator it = lower_bound(data.begin(), data.end(), pair<int, char*>(index, np));
  return stringhash(100, it->second); // TODO boardsize;
}


int Algo_finalpos::search(PatternList& patternList, GameList& gl, SearchOptions& options) { // progress bar?!

  // Put the pattern into bitmap format, which is the format the final
  // positions are stored in in the database. This makes the comparisons
  // faster.

  int plS = patternList.size();
  char_p** allbits = new char_p*[plS];
  int** allbitlengths = new int*[plS];
  for(int N=0; N<plS; N++) {
    Pattern* pattern = &patternList.data[N];
    allbits[N] = new char_p[4];
    allbitlengths[N] = new int[4];

    for(int i=0; i<2; i++) {
      for(int j=0; j<2; j++) {
        int xBlocks = (pattern->sizeY+i+1)/2;
        int yBlocks = (pattern->sizeX+j+1)/2;
        char* nextBlock = new char[400];
        int nextBlockIndex = 0;
        nextBlock[nextBlockIndex++] = yBlocks;

        for(int k1=0; k1 < yBlocks; k1++) {
          char nlist[400];
          int nlistIndex = 0;

          for(int k2=0; k2 < xBlocks; k2++) {
            int n = 0;
            for(int x=0; x<2; x++) {
              for(int y=0; y<2; y++) {
                int indexX = k1 * 2 + y - j;
                int indexY = k2 * 2 + x - i;
                if (0 <= indexX && indexX < pattern->sizeX && 0 <= indexY && indexY < pattern->sizeY) {
                  if (pattern->getFinal(indexX,indexY)=='X')
                    n |= 1 << (2*(2*x+y));
                  else if (pattern->getFinal(indexX,indexY)=='O')
                    n |= 1 << (2*(2*x+y)+1);
                }
              }
            }
            nlist[nlistIndex++] = n;
          }

          int start = 0;
          int end = nlistIndex;

          while (start < end && !nlist[start]) start++;
          while (end > start && !nlist[end-1]) end--;

          nextBlock[nextBlockIndex++] = start;
          nextBlock[nextBlockIndex++] = end-start;
          for(int current=start; current < end; current++)
            nextBlock[nextBlockIndex++] = nlist[current];
        }
        char* nB = new char[nextBlockIndex];
        for(int ii=0; ii<nextBlockIndex; ii++) nB[ii] = nextBlock[ii];
        allbitlengths[N][2*i + j] = nextBlockIndex;
        allbits[N][2*i + j] = nB;
        delete [] nextBlock;
      }
    }
  }

  int num_of_games = gl.startO();

  #pragma omp parallel for
  for(int ctr=0; ctr < num_of_games; ctr++) {
    int index = gl.oldList->at(ctr).first;

    char start;
    char length;
    char x;
    char y;

    // if (!(counter++ % 1000)) printf("counter: %d, index: %d\n", counter, index);
    // if (progBar && !(counter % 100))
    //   progBar.redraw((progEnd-progStart)*counter/len(gl.current) + progStart);

    char* np = 0;
    vector<pair<int, char*> >::iterator it = lower_bound(data.begin(), data.end(), pair<int, char*>(index, np));
    if (it == data.end() || it->first != index) { // safety check - this should never happen
      // printf("skip\n");
      continue;
    }
    char* finalpos = it->second;
    // printf("index %d, %p\n", index, finalpos);
    vector<Candidate* > *matchList = new vector<Candidate* >;;

    for(int N=0; N<plS; N++) {
      Pattern* pattern = &patternList.data[N];
      for(int a0=pattern->left; a0 <= pattern->right; a0++) {
        for(int a1 = pattern->top; a1 <= pattern->bottom; a1++) {
          int matches = 1;

          int pIndex = 2*(a1%2) + (a0%2);
          char* pbits = allbits[N][pIndex];
          int pbIndex = 0;
          int fpIndex = a1/2 + (a0/2)*10;

          for(x=0; x < pbits[0]; x++) {
            start = pbits[++pbIndex];
            length = pbits[++pbIndex];
            fpIndex += start;
            for(y=0; y<length; y++) {
              pbIndex++;
              if (pbits[pbIndex] & finalpos[fpIndex]) {
                matches = 0;
                break;
              }
              fpIndex++;
            }
            if (!matches) break;
            fpIndex += 10 - start - length;
          }
          if (matches) {
            // printf("finalpos cand %d %d %d\n", a0, a1, N);
            matchList->push_back(new Candidate(a0,a1,N));
          }
        }
      }
    }

    if (matchList->size()) {
      GameListEntry* gle = gl.all->at(gl.oldList->at(ctr).second);
      if (gle->candidates) delete gle->candidates;
      gle->candidates = matchList;

      #pragma omp critical
      gl.currentList->push_back(gl.oldList->at(ctr));
    } else delete matchList;
  }
  {
    for(int N=0; N<plS; N++) {
      delete [] allbitlengths[N];
      for(int i=0; i<4; i++)
        if (allbits[N][i]) delete [] allbits[N][i];
      delete [] allbits[N];
    }
  }
  delete [] allbitlengths;
  delete [] allbits;
  return 0;
}



// ------------------------------------------------------------------------------------------------


Algo_movelist::Algo_movelist(int bsize, SnapshotVector DATA) : Algorithm(bsize) {
  // data1 is a map<int = gameid, char* = movelist>, where the length of movelist is given by data1l[gameid]
  // data2 is a map<int = gameid, char* "finalpos-captures">, where the char* has length 50

  if (!DATA.empty()) {
    int si = DATA.retrieve_int();
    for(int i=0; i<si; i++) {
      int game_id = DATA.retrieve_int();
      data1l.insert(pair<int, int>(game_id, DATA.retrieve_int()));
      data1.insert(pair<int, char*>(game_id, DATA.retrieve_charp()));
      data2.insert(pair<int, char*>(game_id, DATA.retrieve_charp()));
    }
  }
}

SnapshotVector Algo_movelist::get_data() {
  SnapshotVector v;

  v.pb_int(data1l.size());
  for(map<int, int>::iterator it = data1l.begin(); it != data1l.end(); it++) {
    int game_id = it->first;
    v.pb_int(game_id);
    v.pb_int(it->second);
    v.pb_charp(data1[game_id], it->second);
    v.pb_charp(data2[game_id], 50);
  }
  return v;
}

Algo_movelist::~Algo_movelist() {
  for(map<int, char* >::iterator it = data1.begin(); it != data1.end(); it++) {
    delete [] it->second;
  }
  for(map<int, char* >::iterator it = data2.begin(); it != data2.end(); it++) {
    delete [] it->second;
  }
}

void Algo_movelist::initialize_process() {
  // printf("init Algo_movelist\n");
}

void Algo_movelist::newgame_process(int game_id) {
  gid = game_id;
  movelist = vector<char>();

  fpC = new char[50];
  for(int i=0; i<50; i++) fpC[i] = 0;
}

void Algo_movelist::AB_process(int x, int y) {
  movelist.push_back((char)x);
  movelist.push_back((char)(y | BLACK));
}


void Algo_movelist::AW_process(int x, int y) {
  movelist.push_back((char)x);
  movelist.push_back((char)(y | WHITE));
}


void Algo_movelist::AE_process(int x, int y, char removed) {
  movelist.push_back((char)x);
  if (removed == 'B') movelist.push_back((char)(y | REMOVE | BLACK));
  else if (removed == 'W') movelist.push_back((char)(y | REMOVE | WHITE));
  else movelist.push_back((char)(y | REMOVE)); // BUGFIX by Claude Brisson, taking care of empty AE tags
}

void Algo_movelist::endOfNode_process() {
  if (movelist.size()>1) {
    if (movelist[movelist.size()-2] & (ENDOFNODE | BRANCHPOINT | ENDOFVARIATION)) {
      movelist.push_back(ENDOFNODE);
      movelist.push_back(0);
    } else {
      movelist[movelist.size()-2] |= ENDOFNODE;
    }
  } else {
    movelist.push_back(ENDOFNODE);
    movelist.push_back(0);
  }
}

void Algo_movelist::move_process(Move m) {
  if (!movelist.size()) {
    movelist.push_back(ENDOFNODE);
    movelist.push_back(0);
  }
  movelist.push_back(m.x);
  if (m.color=='B') movelist.push_back(m.y | BLACK);
  else movelist.push_back(m.y | WHITE);

  if (m.captures) {
    vector<p_cc>::iterator it;
    for(it = m.captures->begin(); it != m.captures->end(); it++) {
      int xx = it->first;
      int yy = it->second;

      movelist.push_back(xx);
      if (m.color=='B') movelist.push_back(yy | REMOVE | WHITE);
      else movelist.push_back(yy | REMOVE | BLACK);
      fpC[yy/4 + 5*(xx/2)] |= 1 << (xx%2 + 2*(yy%4));
    }
  }
}

void Algo_movelist::pass_process() {
  movelist.push_back(19);
  movelist.push_back(19);
}

void Algo_movelist::branchpoint_process() {
  movelist.push_back(BRANCHPOINT);
  movelist.push_back(0);
}

void Algo_movelist::endOfVariation_process() {
  movelist.push_back(ENDOFVARIATION);
  movelist.push_back(0);
}

void Algo_movelist::endgame_process(bool commit)  {
  if (commit) {
    char* ml = new char[movelist.size()];
    int mlIndex = 0;
    for(vector<char>::iterator it = movelist.begin(); it != movelist.end(); it++) {
      ml[mlIndex++] = *it;
    }
    data1.insert(pair<int, char*>(gid, ml));  // move list
    data1l.insert(pair<int, int>(gid, mlIndex)); // length of move list
    data2.insert(pair<int, char*>(gid, fpC)); // captures in final pos
  } else delete [] fpC;
}

void Algo_movelist::finalize_process() {
}



MovelistCand::MovelistCand(Pattern* P, int ORIENTATION, char* DICTS, int NO, char X, char Y) {
  orientation = ORIENTATION;
  p = P;
  mx = X;
  my = Y;
  Xinterv = make_pair(mx, mx+p->sizeX);
  Yinterv = make_pair(my, my+p->sizeY);
  // if (p->contList.size()) {
    // printf("new mlc %d %d %d %d, %d %d %d\n", X, Y, ORIENTATION, NO, p->contList[0].x, p->contList[0].y, p->contList[0].color);
  // }

  dicts = DICTS;
  dictsNO = NO;
  contListIndex = 0;
  dictsFound = false;
  dictsFoundInitial = false;
  dictsDR = false;
  contList = p->contList;
  node_changes_relevant_region = false;
}

MovelistCand::~MovelistCand() {
  delete [] dicts;
}

char MovelistCand::dictsget(char x, char y) {
  return dicts[x-mx + p->sizeX*(y-my)];
}

char MovelistCand::contlistgetX(int i = -1) {
  return contList[i == -1 ? contListIndex : i].x + mx;
}

char MovelistCand::contlistgetY(int i = -1) {
  return contList[i == -1 ? contListIndex : i].y + my;
}

char MovelistCand::contlistgetCO(int i = -1) {
  return contList[i == -1 ? contListIndex : i].color;
}

void MovelistCand::dictsset(char x, char y, char d) {
  dicts[x-mx + p->sizeX*(y-my)] = d;
}

bool MovelistCand::in_relevant_region(char x, char y) {
  return (Xinterv.first <= x && x < Xinterv.second && Yinterv.first <= y && y < Yinterv.second);
}


VecMC::VecMC() : vector<MovelistCand* >() {
  candssize = 0;
}

VecMC::~VecMC() {
  for(VecMC::iterator it = begin(); it != end(); it++) {
    if (*it) delete *it;
    *it = 0;
  }
}

VecMC* VecMC::deepcopy(ExtendedMoveNumber& COUNTER, int CANDSSIZE) {
  VecMC* result = new VecMC;
  result->candssize = CANDSSIZE;
  result->counter = COUNTER;
  for(VecMC::iterator it = begin(); it != end(); it++) {
    MovelistCand* mlc = 0;
    if (*it) {
      char* DICTS = new char[(*it)->p->sizeX * (*it)->p->sizeY];
      for (int i=0; i < (*it)->p->sizeX * (*it)->p->sizeY; i++) DICTS[i] = (*it)->dicts[i];
      mlc = new MovelistCand((*it)->p, (*it)->orientation, DICTS, (*it)->dictsNO, (*it)->mx, (*it)->my);
      mlc->contListIndex = (*it)->contListIndex;
      mlc->dictsFound = (*it)->dictsFound;
      mlc->dictsF = (*it)->dictsF;
      mlc->dictsFoundInitial = (*it)->dictsFoundInitial;
      mlc->dictsFI = (*it)->dictsFI;
      mlc->dictsDR = (*it)->dictsDR;
    }
    result->push_back(mlc);
  }
  return result;
}

int Algo_movelist::search(PatternList& patternList, GameList& gl, SearchOptions& options) {
  // printf("Enter Algo_movelist::search\n");
  int numOfHits = 0;
  int self_numOfSwitched = 0;
  int Bwins = 0;
  int Wwins = 0;

  int movelimit = options.moveLimit;

  int num_of_games = gl.startO();
  // printf("num of games: %d", num_of_games);

  #pragma omp parallel for
  for(int ctr = 0; ctr < num_of_games; ctr++) {
    // printf("ctr: %d", ctr);

    int index = gl.oldList->at(ctr).first;
    vector<Hit* > * result = new vector<Hit* >;
    int numOfSwitched = 0;
    stack<VecMC* > branchpoints;

    char* movel = data1[index];
    int movelistIndex = 0;
    int endMovelist = data1l[index];

    char* fpC = data2[index];

    vector<Candidate* > *currentMatchList = gl.all->at(gl.oldList->at(ctr).second)->candidates;
    int candssize = currentMatchList->size();
    VecMC* cands = new VecMC;
    cands->reserve(currentMatchList->size());

    for(int mCounter=0; mCounter<(int)currentMatchList->size(); mCounter++) {
      Candidate* m = (*currentMatchList)[mCounter];
      int dNO = 0;
      Pattern* p = &patternList.data[m->orientation];
      char* d = new char[p->sizeX * p->sizeY];
      for(int i=0; i<p->sizeX; i++) {
        for(int j=0; j<p->sizeY; j++) {
          char p_ij = p->getInitial(i,j);
          if (p_ij != '.') d[i+p->sizeX*j] = p_ij;
          else d[i+p->sizeX*j] = 0;
          if (p_ij == 'X' || p_ij == 'O') dNO++;
        }
      }
      cands->push_back(new MovelistCand(p, m->orientation, d, dNO, m->x, m->y));
    }
    // printf("candssize %d\n", cands->size());

    ExtendedMoveNumber counter(0);

    while (movelistIndex < endMovelist) {
      if (counter.total_move_num() == movelimit+1) {
        for(vector<MovelistCand* >::iterator it = cands->begin(); it != cands->end(); it++) {
          if (*it == 0) continue;
          if (!(*it)->dictsFound) {
            delete *it;
            *it = 0;
            candssize--;
          }
        }
      }
      // printf(".");
      if (options.searchInVariations && movel[movelistIndex] & BRANCHPOINT) {
        // printf("branchpoint\n");
        branchpoints.push(cands->deepcopy(counter, candssize));
        movelistIndex += 2;
        continue;
      }
      if (options.searchInVariations && movel[movelistIndex] & ENDOFVARIATION) {
        // printf("endofvariation\n");
        if (!patternList.nextMove) { // deal with hits w/o continuation
          for(vector<MovelistCand* >::iterator it = cands->begin(); it != cands->end(); it++) {
            if (*it == 0) continue;
            if ((*it)->dictsFound) {
              if ((*it)->p->colorSwitch) {
                numOfSwitched++;
                char* rstr = new char[3];
                rstr[0] = NO_CONT;
                rstr[1] = 0;
                rstr[2] = 1;
                result->push_back(new Hit(new ExtendedMoveNumber((*it)->dictsF), rstr));
              } else {
                char* rstr = new char[3];
                rstr[0] = NO_CONT;
                rstr[1] = 0;
                rstr[2] = 0;
                result->push_back(new Hit(new ExtendedMoveNumber((*it)->dictsF), rstr));
              }
            }
          }
        }

        delete cands;
        cands = branchpoints.top();
        counter = cands->counter;
        candssize = cands->candssize;
        counter.down();
        branchpoints.pop();
        movelistIndex += 2;
        continue;
      }

      char x = movel[movelistIndex] & 31;
      char y = movel[movelistIndex+1] & 31;

      char co = '?';
      // char invco = 'X';
      char lower_invco = 'x';

      if (!(movel[movelistIndex+1] & REMOVE) && (movel[movelistIndex+1] & (BLACK | WHITE))) {
        if (movel[movelistIndex+1] & BLACK) {
          co = 'X';
          // invco = 'O';
          lower_invco = 'o';
        } else {
          co = 'O';
          lower_invco = 'x';
        }
        // printf("mv %d %d %c\n", x, y, co);

        for(vector<MovelistCand* >::iterator it = cands->begin(); it != cands->end(); it++) {
          if (*it == 0) continue;
          if ((*it)->in_relevant_region(x,y)) {
            (*it)->node_changes_relevant_region = true;
            // printf("\nnextmove %d\n", counter.total_move_num());
            // if (it == cands->begin()) {
              // Candidate* m = (*currentMatchList)[0]; // refers to FIRST candidate
              // Pattern* p = &patternList.data[m->orientation];
              // for(int i=0; i<p->sizeX; i++) {
                // for(int j=0; j<p->sizeY; j++) {
                  // if ( (*it)->dicts[i+p->sizeX*j] == 0) printf("$");
                  // else printf("%c", (*it)->dicts[i+p->sizeX*j]);
                // }
                // printf("\n");
              // }
              // printf("\n");
              // printf("dictsNO %d\n", (*it)->dictsNO);
            // }
            // printf("loop 1\n %c", (*it)->dictsget(x,y));
            if ((*it)->dictsFound) { // found, so now we have found the continuation
              // printf("found cont\n");
              char* label;

              # pragma omp critical
              {
                label = patternList.updateContinuations(
                    (*it)->orientation, // pattern in question
                    x-(*it)->mx, y-(*it)->my, // pos of continuation
                    co, // color of continuation
                    (counter.total_move_num()-(*it)->dictsF.total_move_num())>2, // tenuki?
                    gl.all->at(gl.oldList->at(ctr).second)->winner,
                    gl.all->at(gl.oldList->at(ctr).second)->date
                    );
              }

              if (label) { // otherwise no hit because continuation has wrong color (i.e. nextMove set)
                numOfSwitched += label[2];
                result->push_back(new Hit(new ExtendedMoveNumber((*it)->dictsF), label));
              }

              delete *it;
              *it = 0;
              candssize--;
              continue;
            } else if ((*it)->dictsFoundInitial) { // foundInitial, so now look for contList
              if (x == (*it)->contlistgetX() && y == (*it)->contlistgetY() && co == (*it)->contlistgetCO()) {
                (*it)->contListIndex++;
                // printf("x %d, y %d, (*it)->contListIndex %d\n", x, y, (*it)->contListIndex);
                if ((*it)->contListIndex == (int)(*it)->contList.size()) {
                  (*it)->dictsF = counter;
                  (*it)->dictsFound = true;
                }
              } else {
                if ((*it)->dictsDR) { // don't restore
                  delete *it;
                  *it = 0;
                  candssize--;
                  continue;
                } else {
                  (*it)->contListIndex = 0;
                  (*it)->dictsFoundInitial = false;
                }
              }
            }

            if (!(*it)->dictsget(x,y)) { // this move occupies a spot which should be empty
              if (!(fpC[y/4 + 5*(x/2)] & (1 << (x%2 + 2*(y%4))))) {
                if (!(*it)->contListIndex) {
                  delete *it;
                  *it = 0;
                  candssize--;
                  continue;
                } else {
                  (*it)->dictsDR = true;
                  // printf("DR1\n");
                }
              } else {
                (*it)->dictsset(x,y,'.');
                (*it)->dictsNO++; // printf("++ A\n");
              }
            } else if ((*it)->dictsget(x,y) == lower_invco) {
              // this move occupies a wildcard spot of the wrong color
              if (!(fpC[y/4 + 5*(x/2)] & (1 << (x%2 + 2*(y%4))))) {
                if (!(*it)->contListIndex) {
                  delete *it;
                  *it = 0;
                  candssize--;
                  continue;
                } else (*it)->dictsDR = true;
              } else (*it)->dictsNO++; // printf("++ B\n");
            } else if ((*it)->dictsget(x,y) == co) {
              // this move gives us the stone we are looking for
              (*it)->dictsset(x,y,0);
              (*it)->dictsNO--; // printf("-- A\n");
            }
          }
        }
      }
      else if (movel[movelistIndex+1] & REMOVE) {
        if (movel[movelistIndex+1] & BLACK) {
          co = 'X';
          // invco = 'O';
          lower_invco = 'o';
        } else if (movel[movelistIndex+1] & WHITE) {
          co = 'O';
          // invco = 'X';
          lower_invco = 'x';
        }

        for(vector<MovelistCand* >::iterator it = cands->begin(); it != cands->end(); it++) {
          // printf("loop 2\n");
          if (*it == 0) continue;
          if ((*it)->in_relevant_region(x,y)) {
            (*it)->node_changes_relevant_region = true;
            if (!(*it)->dictsFound) { // not found yet
              if ((*it)->dictsFoundInitial) { // foundInitial
                int ii = (*it)->contListIndex;
                while (ii < (int)(*it)->contList.size() && (*it)->contlistgetCO(ii) == '-' &&
                    (x != (*it)->contlistgetX(ii) || y != (*it)->contlistgetY(ii)))
                  ii++;
                if (ii < (int)(*it)->contList.size() && (*it)->contlistgetCO(ii) == '-') {
                  MoveNC help = (*it)->contList[ii];
                  (*it)->contList[ii] = (*it)->contList[(*it)->contListIndex];
                  (*it)->contList[(*it)->contListIndex] = help;

                  (*it)->contListIndex++;
                } else {
                  if ((*it)->dictsDR) {
                    delete *it;
                    *it = 0;
                    candssize--;
                    continue;
                  } else {
                    (*it)->contListIndex = 0;
                    (*it)->dictsFoundInitial = false;
                  }
                }
              }
              if (!(*it)->dictsget(x,y)) {
                // the stone at this position was what we needed,
                // since it was captured, we are once again looking for it:
                (*it)->dictsset(x,y,co);
                (*it)->dictsNO++; // printf("++ C\n");
              }
              else if ((*it)->dictsget(x,y) == lower_invco) {
                (*it)->dictsNO--; // printf("-- B\n");
              }
              else if ((*it)->dictsget(x,y) == '.') {
                // we are looking for an empty spot here, so this capture is helpful:
                (*it)->dictsset(x,y,0);
                (*it)->dictsNO--; // printf("-- C\n");
              }
            }
          }
        }
      }

      if (movel[movelistIndex] & ENDOFNODE) {
        // printf("eon %d %d %c\n", x, y, co);
        int si = cands->size();
        // printf("si %d \n", si);
        for(int i=0; i<si; i++) {
          MovelistCand* it = (*cands)[i];
          if (it != 0 && (co == '?' || it->node_changes_relevant_region)) {
            if (!it->dictsNO && !it->dictsFound) {
              if (!it->contList.size()) {
                it->dictsF = counter;
                it->dictsFound = true;
                // printf("found pattern\n");
              } else if (!it->dictsFoundInitial) {
                it->dictsFI = counter;
                it->dictsFoundInitial = true;
                // printf("found initial\n");
              } else if (!it->dictsDR) { // found initial position again during processing of contList   ... FIXME need test case for this
                char* d = new char[it->p->sizeX*it->p->sizeY];
                for (int ct=0; ct < it->p->sizeX*it->p->sizeY; ct++) d[ct] = it->dicts[ct];
                MovelistCand* mlc = new MovelistCand(it->p, it->orientation, d, 0, it->mx, it->my);
                mlc->dictsFI = counter;
                cands->push_back(mlc);
                candssize++;
                // printf("push back\n");
              }
            }
          }
          if (it) it->node_changes_relevant_region = false;
        }
        counter.next();
      }

      if (candssize==0 && branchpoints.size()==0) break;
      movelistIndex += 2;
    }

    // printf("assemble results\n");

    if (!patternList.nextMove) { // look at matches w/o continuation
      for(vector<MovelistCand* >::iterator it = cands->begin(); it != cands->end(); it++) {
        if (*it == 0) continue;
        if ((*it)->dictsFound) {
          if ((*it)->p->colorSwitch) {
            numOfSwitched++;
            char* rstr = new char[3];
            rstr[0] = NO_CONT;
            rstr[1] = 0;
            rstr[2] = 1;
            result->push_back(new Hit(new ExtendedMoveNumber((*it)->dictsF), rstr));
          } else {
            char* rstr = new char[3];
            rstr[0] = NO_CONT;
            rstr[1] = 0;
            rstr[2] = 0;
            result->push_back(new Hit(new ExtendedMoveNumber((*it)->dictsF), rstr));
          }
        }
      }
    }

    # pragma omp critical
    {
      if (result->size()) {
        numOfHits += result->size();
        self_numOfSwitched += numOfSwitched;

        char currentWinner = gl.all->at(gl.oldList->at(ctr).second)->winner;

        if (currentWinner == 'B') {
          Bwins += result->size() - numOfSwitched;
          Wwins += numOfSwitched;
        } else if (currentWinner == 'W') {
          Bwins += numOfSwitched;
          Wwins += result->size() - numOfSwitched;
        }

        GameListEntry* gle = gl.all->at(gl.oldList->at(ctr).second);
        if (gle->hits) delete gle->hits;
        gle->hits = result;
        sort(gle->hits->begin(), gle->hits->end(), Hit::cmp_pts);
        gl.currentList->push_back(gl.oldList->at(ctr));
      } else delete result;
    }
    delete cands;
  }
  gl.num_hits = numOfHits;
  gl.num_switched = self_numOfSwitched;
  gl.Bwins = Bwins;
  gl.Wwins = Wwins;
  return 0;
}


// -----------------------------------------------------------------------------------------------


#if (defined(__BORLANDC__) || defined(_MSC_VER))
const hashtype Algo_hash::hashCodes[] = {
  1448047776469843i64 ,  23745670021858756i64 ,  2503503679898819i64 ,
  20893061577159209i64 ,  10807838381971450i64 ,  2362252468869198i64 ,
  24259008893265414i64 ,  12770534669822463i64 ,  6243872632612083i64 ,
  9878602848666731i64 ,  15403460661141300i64 ,  23328125617276831i64 ,
  24399618481479321i64 ,  6553504962910284i64 ,  1670313139184804i64 ,
  12980312942597170i64 ,  20479559860862969i64 ,  9622188310955879i64 ,
  240315181816498i64 ,  15806748501866401i64 ,  11025185739521454i64 ,
  9892014082139049i64 ,  24468178939325513i64 ,  18336761931886570i64 ,
  17607110247268341i64 ,  1659968630984898i64 ,  15644176636883129i64 ,
  21288430710467667i64 ,  21718647773405600i64 ,  8449573198599383i64 ,
  12949198458251018i64 ,  13260609204816340i64 ,  15942818511406502i64 ,
  19422389391992560i64 ,  2306873372585698i64 ,  13245768415868578i64 ,
  3527685889767840i64 ,  16821792770065498i64 ,  14659578113224043i64 ,
  8882299950073676i64 ,  7855747638699870i64 ,  11443553816792995i64 ,
  10278034782711378i64 ,  9888977721917330i64 ,  8622555585025384i64 ,
  20622776792089008i64 ,  6447699412562541i64 ,  21593237574254863i64 ,
  4100056509197325i64 ,  8358405560798101i64 ,  24120904895822569i64 ,
  21004758159739407i64 ,  4380824971205155i64 ,  23810250238005035i64 ,
  11573868012372637i64 ,  21740007761325076i64 ,  20569500166060069i64 ,
  23367084743140030i64 ,  832128940274250i64 ,  3863567854976796i64 ,
  8401188629788306i64 ,  20293444021869434i64 ,  12476938100997420i64 ,
  5997141871489394i64 ,  777596196611050i64 ,  8407423122275781i64 ,
  23742268390341663i64 ,  6606677504119583i64 ,  17099083579458611i64 ,
  128040681345920i64 ,  7441253945309846i64 ,  17672412151152227i64 ,
  14657002484427869i64 ,  3764334613856311i64 ,  7399928989161192i64 ,
  24730167942169592i64 ,  13814924480574978i64 ,  5810810907567287i64 ,
  7008927747711241i64 ,  3714629224790215i64 ,  9946435535599731i64 ,
  20057491299504334i64 ,  15866852457019228i64 ,  123155262761331i64 ,
  1315783062254243i64 ,  24497766846727950i64 ,  12902532251391440i64 ,
  16788431106050494i64 ,  15993209359043506i64 ,  6163570598235227i64 ,
  23479274902645580i64 ,  12086295521073246i64 ,  14074331278381816i64 ,
  1049820141442769i64 ,  5160957003350972i64 ,  24302799572195320i64 ,
  23881606652035662i64 ,  23969818184919245i64 ,  19374430422494128i64 ,
  9346353622623467i64 ,  13646698673919768i64 ,  20787456987251805i64 ,
  19834903548127921i64 ,  8194151691638546i64 ,  7687885124853709i64 ,
  4843137186034754i64 ,  23141719256229263i64 ,  5528755394284040i64 ,
  22362536622784133i64 ,  7624654257445620i64 ,  8792845080211956i64 ,
  24991012676161170i64 ,  5382030845010972i64 ,  1942150054817210i64 ,
  1024267612932772i64 ,  14257279792025309i64 ,  11127353401828247i64 ,
  4123063511789286i64 ,  363215666444395i64 ,  15523634951795520i64 ,
  21114031740764324i64 ,  12549698630972549i64 ,  7906682572409157i64 ,
  9682658163949194i64 ,  14445831019902887i64 ,  19796086007848283i64 ,
  25041651202294181i64 ,  434144873391024i64 ,  24468825775827696i64 ,
  16436890395501393i64 ,  16373785289815135i64 ,  16626551488832360i64 ,
  7748715007439309i64 ,  22731617567631698i64 ,  14232800365889972i64 ,
  10951727445457549i64 ,  8041373240290953i64 ,  24930514145406896i64 ,
  9591184974667554i64 ,  24880672410562956i64 ,  23221721160805093i64 ,
  20593543181655919i64 ,  23599230930155014i64 ,  15520097083998302i64 ,
  14424914931817466i64 ,  7073972177203460i64 ,  16674214483955582i64 ,
  4557916889838393i64 ,  14520120252661131i64 ,  2948253205366287i64 ,
  18549806070390636i64 ,  10409566723123418i64 ,  18398906015238963i64 ,
  21169009649313417i64 ,  18391044531337716i64 ,  2911838512392375i64 ,
  13771057876708721i64 ,  11955633853535396i64 ,  18911960208175147i64 ,
  1483143365895487i64 ,  5864164841327281i64 ,  16798674080914657i64 ,
  21169543712647072i64 ,  2554895121282201i64 ,  12465286616181485i64 ,
  5756888636558955i64 ,  2597276631190750i64 ,  2560624395830604i64 ,
  20296901708171088i64 ,  14642976680682096i64 ,  12194169777111940i64 ,
  938262584370639i64 ,  7206443811292574i64 ,  501111636607822i64 ,
  5705951146039127i64 ,  19098237626875269i64 ,  5726006303511723i64 ,
  5717532750720198i64 ,  4848344546021481i64 ,  7407311808156422i64 ,
  2061821731974308i64 ,  8556380079387133i64 ,  13575103943220600i64 ,
  10594365938844562i64 ,  19966653780019989i64 ,  24412404083453688i64 ,
  8019373982039936i64 ,  7753495706295280i64 ,  838015840877266i64 ,
  5235642127051968i64 ,  10225916255867901i64 ,  14975561937408701i64 ,
  4914762527221109i64 ,  16273933213731410i64 ,  25240707945233645i64 ,
  6477894775523777i64 ,  16128190602024745i64 ,  12452291569329611i64 ,
  51030855211419i64 ,  1848783942303739i64 ,  2537297571305471i64 ,
  24811709277564335i64 ,  23354767332363093i64 ,  11338712562024830i64 ,
  10845782284945582i64 ,  20710115514013598i64 ,  19611282767915684i64 ,
  11160258605900113i64 ,  17875966449141620i64 ,  8400967803093668i64 ,
  6871997953834029i64 ,  13914235659320051i64 ,  8949576634650339i64 ,
  2143755776666584i64 ,  13309009078638265i64 ,  17871461210902733i64 ,
  11987276750060947i64 ,  19212042799964345i64 ,  9684310155516547i64 ,
  1307858104678668i64 ,  8369225045337652i64 ,  11470364009363081i64 ,
  10726698770860164i64 ,  22857364846703600i64 ,  25284735055035435i64 ,
  19224377054148393i64 ,  16403807100295998i64 ,  4653376186522389i64 ,
  15242640882406966i64 ,  15315275662931969i64 ,  11642086728644568i64 ,
  12158439227609947i64 ,  5366950703441186i64 ,  21989897136444615i64 ,
  21241101455718813i64 ,  1591417368086590i64 ,  14579493634035095i64 ,
  23329624772309429i64 ,  4022767503269837i64 ,  12858990365780377i64 ,
  1546772101519453i64 ,  23839228242060485i64 ,  3152020333001361i64 ,
  7700997223270546i64 ,  7886359803633970i64 ,  18794372628879385i64 ,
  22159114735365084i64 ,  7999390508114986i64 ,  17413096555746886i64 ,
  9385231705999634i64 ,  15875377080359488i64 ,  4319895571584052i64 ,
  15831501864738265i64 ,  23927036136254152i64 ,  9023165779396619i64 ,
  6131245054225200i64 ,  20314359892927215i64 ,  1896686091879468i64 ,
  14130616725563771i64 ,  22653904323575475i64 ,  9831497463521490i64 ,
  13110057076369419i64 ,  5902087517632052i64 ,  23714067728868348i64 ,
  10422641883492326i64 ,  10327276345146850i64 ,  795518417987648i64 ,
  25452954487907785i64 ,  3500196309207718i64 ,  14513995844064906i64 ,
  7844549909962914i64 ,  9407804562184273i64 ,  15229768031797498i64 ,
  14111656085687927i64 ,  16834184600349678i64 ,  7291182384885469i64 ,
  17771577974633552i64 ,  21586473553657942i64 ,  18166326806718423i64 ,
  10928317030329388i64 ,  13135712137024532i64 ,  12947681282864548i64 ,
  21220312239923983i64 ,  9606249244876101i64 ,  4653965165819933i64 ,
  5039148287631156i64 ,  3987726544496362i64 ,  11235885894214833i64 ,
  3549024987193191i64 ,  6369560450327424i64 ,  5296536600431238i64 ,
  10833371878822587i64 ,  5746338282416722i64 ,  20335144029844343i64 ,
  14857534135172842i64 ,  13933887642921338i64 ,  3610489245941154i64 ,
  7780064458218242i64 ,  18217608762631328i64 ,  4861734558486078i64 ,
  19138089389909524i64 ,  162404484845663i64 ,  6326150309736266i64 ,
  5691634479075905i64 ,  14377989390160001i64 ,  7788436404648140i64 ,
  20312143630017606i64 ,  6781467023516504i64 ,  7265384191721189i64 ,
  13990392558924592i64 ,  4811546322556989i64 ,  3891404257596968i64 ,
  19222546653408634i64 ,  9733466771346453i64 ,  20011679489309705i64 ,
  11556921572925005i64 ,  13429005557512149i64 ,  16680841455593148i64 ,
  394589115298971i64 ,  22224576785554448i64 ,  18262625753524808i64 ,
  20893780129453860i64 ,  25064972830160559i64 ,  241970110039610i64 ,
  7452533933839720i64 ,  10726026396546933i64 ,  17312051917081899i64 ,
  17281553837379637i64 ,  24008819488103387i64 ,  5193878516496164i64 ,
  21529615734706496i64 ,  22844915602846365i64 ,  17118246686087168i64 ,
  6560869056902581i64 ,  10553021967047717i64 ,  3729950813036887i64 ,
  14459986099519295i64 ,  15808907290234758i64 ,  6234512969275540i64 ,
  18690008075805909i64 ,  492531108753402i64 ,  7721002928884704i64 ,
  4886156035126456i64 ,  21716374046066558i64 ,  11035311630511661i64 ,
  16837692753538891i64 ,  20172053977953882i64 ,  15488511700491202i64 ,
  17477921115358343i64 ,  24726937211646877i64 ,  22480504880004621i64 ,
  18521326635500559i64 ,  8076560603417178i64 ,  22382516625473209i64 ,
  21696842111535623i64 ,  12559160944089288i64 ,  1661142873895453i64 ,
  18379772814447567i64 ,  10295321430586466i64 ,  12378145201769592i64 ,
  11815752235866582i64 };
#else
const hashtype Algo_hash::hashCodes[] = {
  1448047776469843LL ,  23745670021858756LL ,  2503503679898819LL ,
  20893061577159209LL ,  10807838381971450LL ,  2362252468869198LL ,
  24259008893265414LL ,  12770534669822463LL ,  6243872632612083LL ,
  9878602848666731LL ,  15403460661141300LL ,  23328125617276831LL ,
  24399618481479321LL ,  6553504962910284LL ,  1670313139184804LL ,
  12980312942597170LL ,  20479559860862969LL ,  9622188310955879LL ,
  240315181816498LL ,  15806748501866401LL ,  11025185739521454LL ,
  9892014082139049LL ,  24468178939325513LL ,  18336761931886570LL ,
  17607110247268341LL ,  1659968630984898LL ,  15644176636883129LL ,
  21288430710467667LL ,  21718647773405600LL ,  8449573198599383LL ,
  12949198458251018LL ,  13260609204816340LL ,  15942818511406502LL ,
  19422389391992560LL ,  2306873372585698LL ,  13245768415868578LL ,
  3527685889767840LL ,  16821792770065498LL ,  14659578113224043LL ,
  8882299950073676LL ,  7855747638699870LL ,  11443553816792995LL ,
  10278034782711378LL ,  9888977721917330LL ,  8622555585025384LL ,
  20622776792089008LL ,  6447699412562541LL ,  21593237574254863LL ,
  4100056509197325LL ,  8358405560798101LL ,  24120904895822569LL ,
  21004758159739407LL ,  4380824971205155LL ,  23810250238005035LL ,
  11573868012372637LL ,  21740007761325076LL ,  20569500166060069LL ,
  23367084743140030LL ,  832128940274250LL ,  3863567854976796LL ,
  8401188629788306LL ,  20293444021869434LL ,  12476938100997420LL ,
  5997141871489394LL ,  777596196611050LL ,  8407423122275781LL ,
  23742268390341663LL ,  6606677504119583LL ,  17099083579458611LL ,
  128040681345920LL ,  7441253945309846LL ,  17672412151152227LL ,
  14657002484427869LL ,  3764334613856311LL ,  7399928989161192LL ,
  24730167942169592LL ,  13814924480574978LL ,  5810810907567287LL ,
  7008927747711241LL ,  3714629224790215LL ,  9946435535599731LL ,
  20057491299504334LL ,  15866852457019228LL ,  123155262761331LL ,
  1315783062254243LL ,  24497766846727950LL ,  12902532251391440LL ,
  16788431106050494LL ,  15993209359043506LL ,  6163570598235227LL ,
  23479274902645580LL ,  12086295521073246LL ,  14074331278381816LL ,
  1049820141442769LL ,  5160957003350972LL ,  24302799572195320LL ,
  23881606652035662LL ,  23969818184919245LL ,  19374430422494128LL ,
  9346353622623467LL ,  13646698673919768LL ,  20787456987251805LL ,
  19834903548127921LL ,  8194151691638546LL ,  7687885124853709LL ,
  4843137186034754LL ,  23141719256229263LL ,  5528755394284040LL ,
  22362536622784133LL ,  7624654257445620LL ,  8792845080211956LL ,
  24991012676161170LL ,  5382030845010972LL ,  1942150054817210LL ,
  1024267612932772LL ,  14257279792025309LL ,  11127353401828247LL ,
  4123063511789286LL ,  363215666444395LL ,  15523634951795520LL ,
  21114031740764324LL ,  12549698630972549LL ,  7906682572409157LL ,
  9682658163949194LL ,  14445831019902887LL ,  19796086007848283LL ,
  25041651202294181LL ,  434144873391024LL ,  24468825775827696LL ,
  16436890395501393LL ,  16373785289815135LL ,  16626551488832360LL ,
  7748715007439309LL ,  22731617567631698LL ,  14232800365889972LL ,
  10951727445457549LL ,  8041373240290953LL ,  24930514145406896LL ,
  9591184974667554LL ,  24880672410562956LL ,  23221721160805093LL ,
  20593543181655919LL ,  23599230930155014LL ,  15520097083998302LL ,
  14424914931817466LL ,  7073972177203460LL ,  16674214483955582LL ,
  4557916889838393LL ,  14520120252661131LL ,  2948253205366287LL ,
  18549806070390636LL ,  10409566723123418LL ,  18398906015238963LL ,
  21169009649313417LL ,  18391044531337716LL ,  2911838512392375LL ,
  13771057876708721LL ,  11955633853535396LL ,  18911960208175147LL ,
  1483143365895487LL ,  5864164841327281LL ,  16798674080914657LL ,
  21169543712647072LL ,  2554895121282201LL ,  12465286616181485LL ,
  5756888636558955LL ,  2597276631190750LL ,  2560624395830604LL ,
  20296901708171088LL ,  14642976680682096LL ,  12194169777111940LL ,
  938262584370639LL ,  7206443811292574LL ,  501111636607822LL ,
  5705951146039127LL ,  19098237626875269LL ,  5726006303511723LL ,
  5717532750720198LL ,  4848344546021481LL ,  7407311808156422LL ,
  2061821731974308LL ,  8556380079387133LL ,  13575103943220600LL ,
  10594365938844562LL ,  19966653780019989LL ,  24412404083453688LL ,
  8019373982039936LL ,  7753495706295280LL ,  838015840877266LL ,
  5235642127051968LL ,  10225916255867901LL ,  14975561937408701LL ,
  4914762527221109LL ,  16273933213731410LL ,  25240707945233645LL ,
  6477894775523777LL ,  16128190602024745LL ,  12452291569329611LL ,
  51030855211419LL ,  1848783942303739LL ,  2537297571305471LL ,
  24811709277564335LL ,  23354767332363093LL ,  11338712562024830LL ,
  10845782284945582LL ,  20710115514013598LL ,  19611282767915684LL ,
  11160258605900113LL ,  17875966449141620LL ,  8400967803093668LL ,
  6871997953834029LL ,  13914235659320051LL ,  8949576634650339LL ,
  2143755776666584LL ,  13309009078638265LL ,  17871461210902733LL ,
  11987276750060947LL ,  19212042799964345LL ,  9684310155516547LL ,
  1307858104678668LL ,  8369225045337652LL ,  11470364009363081LL ,
  10726698770860164LL ,  22857364846703600LL ,  25284735055035435LL ,
  19224377054148393LL ,  16403807100295998LL ,  4653376186522389LL ,
  15242640882406966LL ,  15315275662931969LL ,  11642086728644568LL ,
  12158439227609947LL ,  5366950703441186LL ,  21989897136444615LL ,
  21241101455718813LL ,  1591417368086590LL ,  14579493634035095LL ,
  23329624772309429LL ,  4022767503269837LL ,  12858990365780377LL ,
  1546772101519453LL ,  23839228242060485LL ,  3152020333001361LL ,
  7700997223270546LL ,  7886359803633970LL ,  18794372628879385LL ,
  22159114735365084LL ,  7999390508114986LL ,  17413096555746886LL ,
  9385231705999634LL ,  15875377080359488LL ,  4319895571584052LL ,
  15831501864738265LL ,  23927036136254152LL ,  9023165779396619LL ,
  6131245054225200LL ,  20314359892927215LL ,  1896686091879468LL ,
  14130616725563771LL ,  22653904323575475LL ,  9831497463521490LL ,
  13110057076369419LL ,  5902087517632052LL ,  23714067728868348LL ,
  10422641883492326LL ,  10327276345146850LL ,  795518417987648LL ,
  25452954487907785LL ,  3500196309207718LL ,  14513995844064906LL ,
  7844549909962914LL ,  9407804562184273LL ,  15229768031797498LL ,
  14111656085687927LL ,  16834184600349678LL ,  7291182384885469LL ,
  17771577974633552LL ,  21586473553657942LL ,  18166326806718423LL ,
  10928317030329388LL ,  13135712137024532LL ,  12947681282864548LL ,
  21220312239923983LL ,  9606249244876101LL ,  4653965165819933LL ,
  5039148287631156LL ,  3987726544496362LL ,  11235885894214833LL ,
  3549024987193191LL ,  6369560450327424LL ,  5296536600431238LL ,
  10833371878822587LL ,  5746338282416722LL ,  20335144029844343LL ,
  14857534135172842LL ,  13933887642921338LL ,  3610489245941154LL ,
  7780064458218242LL ,  18217608762631328LL ,  4861734558486078LL ,
  19138089389909524LL ,  162404484845663LL ,  6326150309736266LL ,
  5691634479075905LL ,  14377989390160001LL ,  7788436404648140LL ,
  20312143630017606LL ,  6781467023516504LL ,  7265384191721189LL ,
  13990392558924592LL ,  4811546322556989LL ,  3891404257596968LL ,
  19222546653408634LL ,  9733466771346453LL ,  20011679489309705LL ,
  11556921572925005LL ,  13429005557512149LL ,  16680841455593148LL ,
  394589115298971LL ,  22224576785554448LL ,  18262625753524808LL ,
  20893780129453860LL ,  25064972830160559LL ,  241970110039610LL ,
  7452533933839720LL ,  10726026396546933LL ,  17312051917081899LL ,
  17281553837379637LL ,  24008819488103387LL ,  5193878516496164LL ,
  21529615734706496LL ,  22844915602846365LL ,  17118246686087168LL ,
  6560869056902581LL ,  10553021967047717LL ,  3729950813036887LL ,
  14459986099519295LL ,  15808907290234758LL ,  6234512969275540LL ,
  18690008075805909LL ,  492531108753402LL ,  7721002928884704LL ,
  4886156035126456LL ,  21716374046066558LL ,  11035311630511661LL ,
  16837692753538891LL ,  20172053977953882LL ,  15488511700491202LL ,
  17477921115358343LL ,  24726937211646877LL ,  22480504880004621LL ,
  18521326635500559LL ,  8076560603417178LL ,  22382516625473209LL ,
  21696842111535623LL ,  12559160944089288LL ,  1661142873895453LL ,
  18379772814447567LL ,  10295321430586466LL ,  12378145201769592LL ,
  11815752235866582LL };
#endif


HashhitF::HashhitF(int GAMEID, char ORIENTATION, char* blob) {
  gameid = GAMEID;
  orientation = ORIENTATION;
  cont = blob[0] == NO_CONT ? 0 : new MoveNC(blob[0], blob[1], blob[2]);
  emn = new ExtendedMoveNumber;
  emn->length = blob[3] * 256 + blob[4];
  emn->data = new int[emn->length];
  for(int i=0; i<emn->length; i++) {
    emn->data[i] = blob[5+2*i]*256 + blob[6+2*i];
  }
}

char* HashhitF::export_blob() {
  // printf("export blob\n");
  char* buf;
  buf = emn ? new char[5 + emn->length*2] : new char[5];
  if (cont) {
    // printf("blob %d %d %d ", cont->x, cont->y, cont->color);
    buf[0] = cont->x;
    buf[1] = cont->y;
    buf[2] = cont->color;
  } else {
    // printf("blob nocont ");
    buf[0] = NO_CONT;
    buf[1] = 0;
    buf[2] = 0;
  }
  if (emn) {
    // printf("emn %d %d", emn->length/256, emn->length%256);
    buf[3] = emn->length/256;
    buf[4] = emn->length%256;
    for (int i=0; i<emn->length; i++) {
      // printf("emn %d %d ", emn->data[i]/256, emn->data[i]%256);
      buf[5+2*i] = emn->data[i]/256;
      buf[6+2*i] = emn->data[i]%256;
    }
  } else {
    // printf("noemn");
    buf[3] = 0;
    buf[4] = 0;
  }
  // printf("\n");
  return buf;
}

HashhitF::HashhitF(const HashhitF& HHF) {
  gameid = HHF.gameid;
  orientation = HHF.orientation;
  emn = new ExtendedMoveNumber(*HHF.emn);
  cont = 0;
  if (HHF.cont) cont = new MoveNC(*HHF.cont);
}

HashhitF::HashhitF(int GAMEID, char ORIENTATION, ExtendedMoveNumber& EMN, MoveNC* CONT) {
  gameid = GAMEID;
  orientation = ORIENTATION;
  emn = new ExtendedMoveNumber(EMN);
  cont = CONT ? new MoveNC(*CONT) : 0;
}

HashhitF::HashhitF() {
  gameid = -1;
  orientation = 0;
  cont = 0;
  emn = 0;
}

HashhitF::~HashhitF() {
  if (cont) delete cont;
  cont = 0;
  if (emn) delete emn;
  emn = 0;
}

HashhitF& HashhitF::operator=(const HashhitF& HHF) {
  if (this != &HHF) {
    gameid = HHF.gameid;
    if (cont) delete cont;
    cont = HHF.cont ? new MoveNC(*HHF.cont) : 0;
    if (emn) delete emn;
    emn = HHF.emn ? new ExtendedMoveNumber(*HHF.emn) : 0;
  }
  return *this;
}



bool cmp_HashhitF(const HashhitF* a, const HashhitF* b) {
  return a->gameid < b->gameid;
}

HashhitCS::HashhitCS(int GAMEID, int POSITION, bool CS) {
  gameid = GAMEID;
  position = POSITION;
  cs = CS;
}

bool cmp_HashhitCS(const HashhitCS* a, const HashhitCS* b) {
  return a->gameid < b->gameid;
}

bool HashhitCS::operator==(const HashhitCS& hhc) {
  return gameid == hhc.gameid && position == hhc.position && cs == hhc.cs;
}


HashVarInfo::HashVarInfo(hashtype CHC, vector<pair<hashtype, ExtendedMoveNumber> > * LFC, ExtendedMoveNumber* MOVENUMBER, int NUMSTONES) {
  chc = CHC;
  numStones = NUMSTONES;
  moveNumber = new ExtendedMoveNumber(*MOVENUMBER);
  lfc = new vector<pair<hashtype, ExtendedMoveNumber> >;
  for(vector<pair<hashtype, ExtendedMoveNumber> >::iterator it = LFC->begin(); it != LFC->end(); it++) {
    lfc->push_back(pair<hashtype, ExtendedMoveNumber>(it->first, it->second));
  }
}


// ---------------------------------------------------------------------------------------------------------


Algo_hash_full::Algo_hash_full(int bsize, SnapshotVector DATA, const string OS_DATA_NAME, int MAXNUMSTONES) : Algorithm(bsize), os_data() {
  branchpoints = 0;
  maxNumStones = MAXNUMSTONES;

  // In case the file does not exist yet, we need to create it: hence open it
  // with the ios::app flag, and close again, then open with the flags we
  // actually want.
  os_data.open(OS_DATA_NAME.c_str(), ios::in | ios::out | ios::binary | ios::app);
  os_data.close();
  os_data.open(OS_DATA_NAME.c_str(), ios::in | ios::out | ios::binary);

  // initialize from DATA
  // data is a boost::unordered_multimap<int = hashCode, ptr_to_file>
  if (DATA.size()) { // allow passing an empty SnapshotVector to this constructor
    hashtype si = DATA.retrieve_hashtype();
    for(hashtype i=0; i<si; i++) {
      hashtype HC = DATA.retrieve_hashtype(); // hash code
      int i1 = DATA.retrieve_int();     // pointer to position in .dd file
      data.push_back(pair<hashtype, int>(HC, i1));
    }
  }
}


SnapshotVector Algo_hash_full::get_data() {
  SnapshotVector v;

  // Add all entries of data to data_p:

  for(vector<pair<hashtype, int> >::iterator it = data.begin(); it != data.end(); it++) {
    vpsip results = new vector<HashhitF* >;
    // printf("data %ld %d\n", it->first, it->second);
    get_HHF(it->second, results, 0);
    for(vector<HashhitF* >::iterator hh = results->begin(); hh != results->end(); hh++) {
      data_p.insert(pair<hashtype, HashhitF>(it->first, HashhitF(**hh)));
      delete *hh;
    }
    delete results;
  }

  // Clear data:

  data.clear();

  // Create list of all hashCodes
  map<hashtype,int> hashcodes;
  vector<hashtype> hc;
  for(boost::unordered_multimap<hashtype, HashhitF>::iterator it = data_p.begin(); it != data_p.end(); it++) {
    map<hashtype,int>::iterator pos = hashcodes.find(it->first);
    if (pos == hashcodes.end()) {
      hashcodes.insert(pair<hashtype, int>(it->first,1));
      hc.push_back(it->first);
    } else
      hashcodes[it->first]++;
  }
  sort(hc.begin(), hc.end());

  // Write everything to os_data
  os_data.seekp(0, ios_base::beg);
  v.pb_hashtype(hc.size());
  // printf("hc size %ld %ld\n", hc.size(), hashcodes.size());
  for(vector<hashtype>::iterator key = hc.begin(); key != hc.end(); key++) {
    v.pb_hashtype(*key);
    v.pb_int(os_data.tellp());
    // printf("tellp %d\n", os_data.tellp());
    data.push_back(pair<hashtype, int>(*key, os_data.tellp())); // set up data so that we can do searches

    int num_occurrences = hashcodes[*key];
    // printf("num_occ %d \n", num_occurrences);
    os_data.write((char*)&num_occurrences, sizeof(num_occurrences));
    pair<boost::unordered_multimap<hashtype, HashhitF>::iterator, boost::unordered_multimap<hashtype, HashhitF>::iterator> res = data_p.equal_range(*key);
    for (boost::unordered_multimap<hashtype, HashhitF>::iterator it = res.first; it != res.second; it++) {
      os_data.write((const char*)&(it->second.gameid), sizeof(it->second.gameid));
      int size_blob = 5 + it->second.emn->length*2;
      os_data.write((const char*)&(size_blob), sizeof(size_blob));
      // printf("call export_blob %d\n", size_blob);
      char* buf = it->second.export_blob();
      os_data.write(buf, size_blob);
      delete [] buf;
    }
  }
  os_data.flush();
  return v;
}


Algo_hash_full::~Algo_hash_full() {
  os_data.close();
}


void Algo_hash_full::initialize_process() {
  // printf("algo_hash_full::initialize_processing\n");
  data_p.clear();
}

void Algo_hash_full::newgame_process(int game_id) {
  numStones = 0;
  gid = game_id;
  moveNumber = new ExtendedMoveNumber(0);
  currentHashCode = 0; // start with empty board
  lfc = new vector<pair<hashtype, ExtendedMoveNumber> >;
  branchpoints = new stack<HashVarInfo>;
}


void Algo_hash_full::process_lfc(int x, int y, char color) {
  // process those items where we are still looking for a continuation (lfc)
  // printf("process_lfc %d %d\n", x, y);
  for(vector<pair<hashtype, ExtendedMoveNumber> >::iterator it = lfc->begin(); it != lfc->end(); it++) {
    MoveNC* continuation = (color == '-') ? 0 : new MoveNC(x,y,color);
    hash_vector.insert(pair<hashtype, HashhitF>(it->first, HashhitF(gid, 0, it->second, continuation)));
    if (continuation) delete continuation;
  }
  delete lfc;
  lfc = new vector<pair<hashtype, ExtendedMoveNumber> >;
}

void Algo_hash_full::AB_process(int x, int y) {
  process_lfc(x, y, 'B');
  currentHashCode += Algo_hash::hashCodes[x + boardsize*y];
  numStones++;
}

void Algo_hash_full::AW_process(int x, int y) {
  process_lfc(x,y,'W');
  currentHashCode -= Algo_hash::hashCodes[x + boardsize*y];
  numStones++;
}

void Algo_hash_full::AE_process(int x, int y, char removed) {
  if (removed == 'B') currentHashCode -= Algo_hash::hashCodes[x + boardsize*y];
  else currentHashCode += Algo_hash::hashCodes[x + boardsize*y];
  numStones--;
}

void Algo_hash_full::endOfNode_process() {
  if (numStones <= maxNumStones) lfc->push_back(pair<hashtype, ExtendedMoveNumber>(currentHashCode, *moveNumber));
  moveNumber->next();
}

void Algo_hash_full::pass_process() {
  // (we do not count pass as continuation)
}

void Algo_hash_full::move_process(Move m) {
  process_lfc(m.x, m.y, m.color);
  int epsilon = (m.color == 'B' || m.color == 'X' ? 1 : -1);
  currentHashCode += epsilon * Algo_hash::hashCodes[m.x + boardsize*m.y];
  numStones++;

  if (m.captures) {
    vector<p_cc>::iterator it;
    for(it = m.captures->begin(); it != m.captures->end(); it++) {
      int xx = it->first;
      int yy = it->second;

      currentHashCode += epsilon * Algo_hash::hashCodes[xx + boardsize*yy];
      numStones--;
    }
  }
}

void Algo_hash_full::branchpoint_process() {
  branchpoints->push(HashVarInfo(currentHashCode, lfc, moveNumber, numStones));
  // printf("push %lld\n", currentHashCode);
}

void Algo_hash_full::endOfVariation_process() {
  process_lfc(19,19,'-');
  delete lfc;
  delete moveNumber;
  currentHashCode = branchpoints->top().chc;
  lfc = branchpoints->top().lfc;
  moveNumber = branchpoints->top().moveNumber;
  numStones = branchpoints->top().numStones;
  // printf("pop %lld\n", currentHashCode);
  branchpoints->pop();
}

void Algo_hash_full::endgame_process(bool commit) {
  if (commit) {
    for(vector<pair<hashtype, ExtendedMoveNumber> >::iterator it = lfc->begin(); it != lfc->end(); it++) { // entries where continuation is missing
      // printf("cm %llu\n", it->first);
      data_p.insert(pair<hashtype, HashhitF>(it->first, HashhitF(gid, 0, it->second, (MoveNC*)0)));
    }
    for(boost::unordered_multimap<hashtype, HashhitF>::iterator it = hash_vector.begin(); it != hash_vector.end(); it++) {  // entries where continuation is available
      // printf("c ok %llu\n", it->first);
      data_p.insert(pair<hashtype, HashhitF>(it->first, it->second));
    }
  }

  hash_vector.clear();
  delete lfc;
  delete moveNumber;
  delete branchpoints;
}



void Algo_hash_full::finalize_process() {
}


hashtype Algo_hash_full::compute_hashkey(Pattern& pattern) {
  if (pattern.sizeX != boardsize || pattern.sizeY != boardsize)
    return NOT_HASHABLE;
  hashtype hashkey = 0;
  int ns = 0;
  for(int i=0; i<boardsize; i++) {
    for(int j=0; j<boardsize; j++) {
      char p = pattern.finalPos[i + boardsize*j];
      if (p == 'x' || p ==  'o' || p == '*') return NOT_HASHABLE;
      else if (p == 'X') {
        hashkey += Algo_hash::hashCodes[i + boardsize*j];
        ns++;
      } else if (p == 'O') {
        hashkey -= Algo_hash::hashCodes[i + boardsize*j];
        ns++;
      }
    }
  }
  if (ns > maxNumStones) return NOT_HASHABLE;
  return hashkey;
}


bool comp_phi(pair<hashtype, int> p1, pair<hashtype, int> p2) {
  return p1.first < p2.first;
}

void Algo_hash_full::get_HHF(int ptr, vpsip results, int orientation) {
  // printf("getHHF %d\n", ptr);
  os_data.seekg(ptr);
  int num_entries;
  os_data.read((char*)&num_entries, sizeof(num_entries));
  // printf("%d\n", num_entries);

  for(int i=0; i<num_entries; i++) {
    int gameid;
    os_data.read((char*)&gameid, sizeof(gameid));
    int si;
    os_data.read((char*)&si, sizeof(si));

    char* i3 = new char[si];
    os_data.read(i3, si);
    // printf("i %d gid %d si %d\n", i, gameid, si);
    HashhitF* HHF = new HashhitF(gameid, 0, i3);
    delete [] i3;

    HHF->orientation = orientation;
    results->push_back(HHF);
  }
}

int Algo_hash_full::search(PatternList& patternList, GameList& gl, SearchOptions& options) {
  // printf("enter algo_hash_full::search\n");
  int numOfHits = 0;
  int self_numOfSwitched = 0;
  int Bwins = 0;
  int Wwins = 0;

  int hash_result = -1; // -1 = failure; 0 = ok, but have to check w/ Algo_movelist, 1 = ok, produced final result
  int plS = patternList.size();
  vpsip results = new vector<HashhitF* >;

  // go through patternList and collect all HashhitF's with appropriate hashCode
  //
  // TODO we could reduce search time by "symmetrizing" hashCodes?!
  for(int N=0; N<plS; N++) {
    hashtype hashCode = compute_hashkey(patternList.data[N]);
    // printf("hashcode %llu\n", hashCode);
    if (hashCode == NOT_HASHABLE) return -1; // failure
    vector<pair<hashtype, int> >::iterator it = lower_bound(data.begin(), data.end(), pair<hashtype, int>(hashCode, 0), comp_phi);
    if (it != data.end() && it->first == hashCode) get_HHF(it->second, results, N);
  }

  if (options.trustHashFull && patternList.pattern.contList.size()==0) hash_result = 1;
  else hash_result = 0;
  if (gl.start_sorted() == 0) {
    sort(results->begin(), results->end(), cmp_HashhitF);
    // printf("res-size %llu\n", results->size());
    vector<HashhitF* >::iterator resultIT = results->begin();

    if (hash_result) { // produce complete results here, do not check with Algo_movelist
      while (resultIT != results->end()) {
        int index = (*resultIT)->gameid;
        gl.setCurrentFromIndex(index);
        int numOfSwitched = 0;
        vector<Hit* >* hits = new vector<Hit* >;
        while ((*resultIT)->gameid == index) {
          // collect all hits for this game
          if ((*resultIT)->emn->total_move_num() <= options.moveLimit) {
            char *label;
            if ((*resultIT)->cont->x != NO_CONT) { // continuation
              label = patternList.updateContinuations((*resultIT)->orientation,
                                                      (*resultIT)->cont->x, (*resultIT)->cont->y, (*resultIT)->cont->color,
                                                      false, // tenuki impossible with full board pattern
                                                      gl.getCurrentWinner(), gl.getCurrentDate());
              if (label) {
                // printf("pb\n");
                hits->push_back(new Hit((*resultIT)->emn, label));
                (*resultIT)->emn = 0;
                numOfSwitched += label[2];
              }
            } else {
              label = new char[3];
              label[0] = NO_CONT;
              label[1] = 0;
              label[2] = patternList.data[(*resultIT)->orientation].colorSwitch;
              numOfSwitched += label[2];
              // printf("pb\n");
              hits->push_back(new Hit((*resultIT)->emn, label));
              (*resultIT)->emn = 0;
            }
          }
          resultIT++;
          if (resultIT == results->end()) break;
        }
        // printf("1\n");
        if (hits->size()) {
          numOfHits += hits->size();
          self_numOfSwitched += numOfSwitched;
          if (gl.getCurrentWinner() == 'B') {
            Bwins += hits->size() - numOfSwitched;
            Wwins += numOfSwitched;
          } else if (gl.getCurrentWinner() == 'W') {
            Bwins += numOfSwitched;
            Wwins += hits->size() - numOfSwitched;
          }
          gl.makeCurrentHit(hits);
        } else delete hits;
      }
    } else { // produce Candidate list, check using another algorithm
      while (resultIT != results->end()) {
        int index = (*resultIT)->gameid;

        // printf("hash search index %d\n", index);
        vector<Candidate* >* candidates = new vector<Candidate* >;
        // store candidate for the first hit for this game
        if ((*resultIT)->emn->total_move_num() <= options.moveLimit) {
          // printf("algo hash full cand 0 0 %d\n", (*resultIT)->orientation);
          candidates->push_back(new Candidate(0,0,(*resultIT)->orientation));
        }

        // ignore all other hits: for full board positions, other hits can only
        // differ by the continuation (due to the presence of variations
        // starting at the node where the pattern was found), and Algo_movelist
        // will take care of finding the different continuations
        while ((*resultIT)->gameid == index) {
          resultIT++;
          if (resultIT == results->end()) break;
        }
        gl.makeIndexCandidate(index, candidates);
      }
    }
    for(vector<HashhitF* >::iterator it = results->begin(); it != results->end(); it++) delete *it;
    delete results;
    gl.end_sorted();
  }
  gl.num_hits = numOfHits;
  gl.num_switched = self_numOfSwitched;
  gl.Bwins = Bwins;
  gl.Wwins = Wwins;
  // printf("hash search end\n");
  return hash_result;
}

// -----------------------------------------------------------------------------------------------------------------------

class vCand : public vector<Candidate* > {
  public:
    void insert_if_new(int l, int t, int ind);
};



void vCand::insert_if_new(int l, int t, int ind) {
  vCand::iterator it = begin();
  while (it != end() && ((*it)->x != l || (*it)->y != t || (*it)->orientation != ind)) it++;
  if (it == end()) {
    push_back(new Candidate(l, t, ind));
    // printf("inserted %d %d %d\n", l, t, ind);
  }
}



// -----------------------------------------------------------------------------------

Algo_hash::Algo_hash(int bsize, SnapshotVector DATA, string OS_DATA_NAME, int MAXNUMSTONES) : Algorithm(bsize) {
  hi = 0;
  maxNumStones = MAXNUMSTONES;

  // In case the file does not exist yet, we need to create it: hence open it
  // with the ios::app flag, and close again, then open with the flags we
  // actually want.
  os_data.open(OS_DATA_NAME.c_str(), ios::in | ios::out | ios::binary | ios::app);
  os_data.close();
  os_data.open(OS_DATA_NAME.c_str(), ios::in | ios::out | ios::binary);

  // initialize from DATA
  if (!DATA.empty()) { // allow passing an empty SnapshotVector to this constructor
    hashtype si = DATA.retrieve_hashtype();
    for(hashtype i=0; i<si; i++) {
      hashtype HC = DATA.retrieve_hashtype();
      int i1 = DATA.retrieve_int();
      data.push_back(pair<hashtype, int>(HC, i1));
    }
  }
}


SnapshotVector Algo_hash::get_data() {
  SnapshotVector v;

  // Add all entries of data to data_p:

  for(vector<pair<hashtype, int> >::iterator it = data.begin(); it != data.end(); it++) {
    vector<HashhitCS* >* results = new vector<HashhitCS* >;
    get_HHCS(it->second, results, false);
    for(vector<HashhitCS* >::iterator hh = results->begin(); hh != results->end(); hh++) {
      data_p.insert(pair<hashtype, pair<int, int> >(it->first, make_pair((*hh)->gameid, (*hh)->position)));
      delete *hh;
    }
    delete results;
  }

  // Clear data

  data.clear();

  // Create list of all hashCodes
  map<hashtype,int> hashcodes;
  vector<hashtype> hc;
  for(boost::unordered_multimap<hashtype, pair<int, int> >::iterator it = data_p.begin(); it != data_p.end(); it++) {
    map<hashtype,int>::iterator pos = hashcodes.find(it->first);
    if (pos == hashcodes.end()) {
      hashcodes.insert(pair<hashtype, int>(it->first,1));
      hc.push_back(it->first);
    } else
      hashcodes[it->first]++;
  }
  sort(hc.begin(), hc.end());

  // Write everything to os_data

  os_data.seekp(0, ios_base::beg);
  v.pb_hashtype(hashcodes.size());
  for(map<hashtype,int>::iterator key = hashcodes.begin(); key != hashcodes.end(); key++) {
    v.pb_hashtype(key->first);
    v.pb_int(os_data.tellp());
    data.push_back(pair<hashtype, int>(key->first, os_data.tellp())); // set up data so that we can do searches

    int num_occurrences = key->second;
    os_data.write((char*)&num_occurrences, sizeof(num_occurrences));
    pair<boost::unordered_multimap<hashtype, pair<int, int> >::iterator, boost::unordered_multimap<hashtype, pair<int, int> >::iterator> res = data_p.equal_range(key->first);
    for (boost::unordered_multimap<hashtype, pair<int, int> >::iterator it = res.first; it != res.second; it++) {
      os_data.write((const char*)&(it->second.first), sizeof(it->second.first));
      os_data.write((const char*)&(it->second.second), sizeof(it->second.second));
    }
  }
  os_data.flush();
  return v;
}

Algo_hash::~Algo_hash() {
  if (hi) delete hi;
  os_data.close();
}



void Algo_hash::initialize_process() {
}

void Algo_hash::newgame_process(int game_id) {
  gid = game_id;
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++) it->initialize();
}

void Algo_hash::AB_process(int x, int y) {
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
    it->addB(x,y);
}

void Algo_hash::AW_process(int x, int y) {
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
    it->addW(x,y);
}

void Algo_hash::AE_process(int x, int y, char removed) {
  if (removed == 'B') {
    for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++) it->removeB(x,y);
  } else {
    for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++) it->removeW(x,y);
  }
}

void Algo_hash::endOfNode_process() {
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++) {
    if (it->numStones <= maxNumStones && it->changed) {
      it->changed = false;
      hash_vector.push_back(it->cHC());
      // printf("push back %ld\n", it->cHC().first);
    }
  }
}

void Algo_hash::pass_process() {
  // (we do not count pass as continuation)
}

void Algo_hash::move_process(Move m) {
  if (m.color == 'B') {
    for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
      it->addB(m.x, m.y);
    if (m.captures) {
      for(vector<p_cc>::iterator cap_it = m.captures->begin(); cap_it != m.captures->end(); cap_it++) {
        for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
          it->removeW(cap_it->first, cap_it->second);
      }
    }
  } else {
    for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
      it->addW(m.x, m.y);
    if (m.captures) {
      for(vector<p_cc>::iterator cap_it = m.captures->begin(); cap_it != m.captures->end(); cap_it++) {
        for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
          it->removeB(cap_it->first, cap_it->second);
      }
    }
  }
}

void Algo_hash::branchpoint_process() {
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
    it->bppush();
}

void Algo_hash::endOfVariation_process() {
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++)
    it->bppop();
}

void Algo_hash::endgame_process(bool commit) {
  for(vector<HashInstance>::iterator it = hi->begin(); it != hi->end(); it++) it->finalize();
  if (commit) {
    for(vector<pair<hashtype, int> >::iterator it = hash_vector.begin(); it != hash_vector.end(); it++) data_p.insert(pair<hashtype, pair<int, int> >(it->first, pair<int, int>(gid, it->second)));
  }
  hash_vector.clear();
}

void Algo_hash::finalize_process() {
}


pair<hashtype, vector<int> >  Algo_hash::compute_hashkey(PatternList& pl, int CS) {
  return pair<hashtype, vector<int> >(NOT_HASHABLE, vector<int>());
}


void Algo_hash::get_HHCS(int ptr, vector<HashhitCS* >* results, bool cs) {
  os_data.seekg(ptr);
  int num_entries;
  os_data.read((char*)&num_entries, sizeof(num_entries));

  for(int i=0; i<num_entries; i++) {
    int i1;
    os_data.read((char*)&i1, sizeof(i1));
    int i2;
    os_data.read((char*)&i2, sizeof(i2));
    // printf("1 %d %d\n", i1, i2);
    results->push_back(new HashhitCS(i1, i2, cs));
  }
  // printf("retrieve results, results->size(): %d\n", results->size());
}



int Algo_hash::search(PatternList& patternList, GameList& gl, SearchOptions& options) {
  // return value: -1 = failure; 0 = ok, but have to check w/ Algo_movelist

  // printf("enter Algo_hash::search\n");
  vector<int> fl, fl2; // stores to which "flip" (with and without CS, resp.) the hashCode belongs

  pair<hashtype, vector<int> > hco = compute_hashkey(patternList, 0);
  if (hco.first == NOT_HASHABLE) return -1; // failure

  vector<HashhitCS* >* results = new vector<HashhitCS* >;
  hashtype hashCode = NOT_HASHABLE;

  hashCode = hco.first;
  // printf("hashCode %ld\n", hashCode);
  fl = hco.second;
  vector<pair<hashtype, int> >::iterator it = lower_bound(data.begin(), data.end(), pair<hashtype, int>(hashCode,0));
  if (it != data.end() && it->first == hashCode) get_HHCS(it->second, results, false);

  bool cs = patternList.data[patternList.size()-1].colorSwitch;
  hashtype hashCode2 = hashCode;
  if (cs) {
    // do the same once again, with cs
    hco = compute_hashkey(patternList, 1);
    if (hco.first == NOT_HASHABLE) return -1; // failure
    hashCode2 = hco.first;
    // printf("hashCode2 %ld\n", hashCode2);
    fl2 = hco.second;
    vector<pair<hashtype, int> >::iterator it = lower_bound(data.begin(), data.end(), pair<hashtype, int>(hashCode2,0));
    if (it != data.end() && it->first == hashCode2) get_HHCS(it->second, results, true);
  }

  // --------------------------------------------
  // printf("enter Algo_hash::search 2, size results: %d\n", results->size());

  if (gl.start_sorted() == 0) {

    sort(results->begin(), results->end(), cmp_HashhitCS);

    vector<HashhitCS* >::iterator resultIT = results->begin();
    while (resultIT != results->end()) {
      int index = (*resultIT)->gameid;

      vCand* candidates = new vCand;
      while ((*resultIT)->gameid == index) {
        // printf("gid %d   ", (*resultIT)->gameid);
        // int pos = (*resultIT)->position % (1<<16);
        int ori = (*resultIT)->position / (1<<16);
        // printf("%d %d\n", pos, ori);
        if (cs && hashCode == hashCode2) {
          // printf("path\n");
          // this is a somewhat pathological case: we have to consider a ColorSwitch, and both hashCodes coincide
          // therefore, need to create two candidates for each hashCode
          for(vector<int>::iterator fl_it = fl.begin(); fl_it != fl.end(); fl_it++) {
            int ind = patternList.flipTable[Pattern::compose_flips(Pattern::PatternInvFlip(ori),*fl_it)];
            candidates->insert_if_new(patternList.data[ind].left, patternList.data[ind].top, ind);
          }
          for(vector<int>::iterator fl_it = fl2.begin(); fl_it != fl2.end(); fl_it++) {
            int ind = patternList.flipTable[8+Pattern::compose_flips(Pattern::PatternInvFlip(ori),*fl_it)];
            candidates->insert_if_new(patternList.data[ind].left, patternList.data[ind].top, ind);
          }
        } else {
          if ((*resultIT)->cs) {
            // TODO works only for corner patterns right now! (really? why?! FIXME)
            for(vector<int>::iterator fl_it = fl2.begin(); fl_it != fl2.end(); fl_it++) {
              int ind = patternList.flipTable[8+Pattern::compose_flips(Pattern::PatternInvFlip(ori),*fl_it)];
              // printf("cand %d %d %d %d CS\n", *fl_it, patternList.data[ind].left, patternList.data[ind].top, ind);
              candidates->insert_if_new(patternList.data[ind].left, patternList.data[ind].top, ind);
            }
          } else {
            for(vector<int>::iterator fl_it = fl.begin(); fl_it != fl.end(); fl_it++) {
              int ind = patternList.flipTable[Pattern::compose_flips(Pattern::PatternInvFlip(ori),*fl_it)];
              // printf("cand %d %d %d %d\n", *fl_it, patternList.data[ind].left, patternList.data[ind].top, ind);
              candidates->insert_if_new(patternList.data[ind].left, patternList.data[ind].top, ind);
            }
          }
        }
        resultIT++;
        if (resultIT == results->end()) break;
      }
      gl.makeIndexCandidate(index, candidates);
    }
    for(vector<HashhitCS* >::iterator it = results->begin(); it != results->end(); it++) delete *it;
    delete results;
    gl.end_sorted();
  } else return -1;
  return 0;
}


// ------------------------------------------------------------------------------------------------------------------------


Algo_hash_corner::Algo_hash_corner(int bsize, SnapshotVector DATA, string OS_DATA_NAME, int SIZE, int MAXNUMSTONES) : Algo_hash(bsize, DATA, OS_DATA_NAME, MAXNUMSTONES) {
  size = SIZE;

  // during processing, we keep track of the four corners with the following four HashInstances:
  hi = new vector<HashInstance>;
  hi->push_back(HashInstance(0,0,size,size,boardsize));
  hi->push_back(HashInstance(0,bsize-size,size,size,boardsize));
  hi->push_back(HashInstance(bsize-size,0,size,size,boardsize));
  hi->push_back(HashInstance(bsize-size, bsize-size, size, size,boardsize));
}

pair<hashtype,vector<int> > Algo_hash_corner::compute_hashkey(PatternList& pl, int CS) {

  pair<hashtype, vector<int> > result = make_pair(NOT_HASHABLE, vector<int>());
  int result_ns = -1;
  if (pl.data[0].sizeX < size || pl.data[0].sizeY < size ||                         // pattern too small?
      pl.data[0].left != pl.data[0].right || pl.data[0].top != pl.data[0].bottom || // no "fixed anchors"?
      (pl.data[0].left != 0 && pl.data[0].left != boardsize-pl.data[0].sizeX) ||    // pattern neither at left, nor at right border?
      (pl.data[0].top != 0 && pl.data[0].top != boardsize-pl.data[0].sizeY)) {      // pattern neither at top nor at bottom border?
                                                                                    // in each of these cases, hashing cannot be applied

    // printf("failure0 %d %d %d %d %d %d %d %d\n", boardsize, size, pl.data[0].sizeX, pl.data[0].sizeY, pl.data[0].left, pl.data[0].right, pl.data[0].top, pl.data[0].bottom);
    return result;
  }

  // for each corner, compute number of stones and (hash code, flips), and return (hashcode, flips) for the corner with
  // the highest number of stones (since probably pattern with many stones are less frequent)

  // select pattern from patternList with correct colorSwitch
  Pattern *pattern;
  // int plOffset = 0;
  if (CS == pl.data[0].colorSwitch) pattern = & pl.data[0];
  else if (CS == pl.data[pl.data.size()-1].colorSwitch) {
    pattern = & pl.data[pl.data.size()/2];
    // plOffset = pl.data.size()/2;
  }
  else return result; // should not happen

  // find all "hashable" corners in the pattern
  // and return respective hashCodes

  for(int offsetX = 0; offsetX <= boardsize-size; offsetX += boardsize-size) { // each corner (2d range = [0..6, 0..6], [12..18, 0..6], [0..6, 12..18], [12..18, 12..18])
    for(int offsetY = 0; offsetY <= boardsize-size; offsetY += boardsize-size) {
      // TODO could improve this a tiny bit if pattern has symmetries: then it would be enough to look at one "corner representative" for each orbit

      // check whether relevant area, i.e. [offsetX .. offsetX+size-1, offsetY .. offsetY+size-1], is contained in pattern
      if (!(pattern->left <= offsetX && pattern->left+pattern->sizeX >= offsetX+size && pattern->top <= offsetY && pattern->top+pattern->sizeY >= offsetY+size)) continue;

      // compute the symmetrized hashKey, and the corresponding "flip" (= board symmetry)
      int ns = 0;
      vector<hashtype> currentHashCode;
      for(int ii = 0; ii < 8; ii++) currentHashCode.push_back(0);

      for(int x=0; x<size; x++) {
        for(int y=0; y<size; y++) {
          char p = pattern->finalPos[x+offsetX-pattern->left + pattern->sizeX*(y+offsetY-pattern->top)];
          if (p == 'x' || p ==  'o' || p == '*') return result;
          else if (p == 'X' || p == 'O') {
            int sign = p == 'X' ? 1 : -1;
            for(int ii = 0; ii < 8; ii++) {
              currentHashCode[ii] = currentHashCode[ii] + sign*Algo_hash::hashCodes[Pattern::flipsX(ii,x+offsetX,y+offsetY,boardsize-1, boardsize-1) + \
                                    boardsize*Pattern::flipsY(ii,x+offsetX,y+offsetY,boardsize-1, boardsize-1)];
            }
            ns++;
          }
        }
      }
      if (2 < ns && ns <= maxNumStones) {
        hashtype m = NOT_HASHABLE; // store minimum here
        for(vector<hashtype>::iterator it = currentHashCode.begin(); it != currentHashCode.end(); it++) {
          // printf("chk %ld\n", *it);
          if (*it != NOT_HASHABLE && (*it < m || m == NOT_HASHABLE)) m = *it;
        }
        vector<int> flip_vector;
        for(int ii = 0; ii < 8; ii++) {
          if (currentHashCode[ii] == m) {
            int f = pl.data[pl.flipTable[ii]].flip;
            vector<int>::iterator fl_it = flip_vector.begin();
            while (fl_it != flip_vector.end() && *fl_it != f) fl_it++;
            if (fl_it == flip_vector.end()) flip_vector.push_back(f);
          }
        }
        // printf("hk.push_back %ld %d, ns: %d", m, flip_vector.size(), ns);
        if (ns > result_ns) {
          result = make_pair(m, flip_vector);
          result_ns = ns;
        }
      }
    }
  }
  return result;
}

// Algo_hash_side::Algo_hash_side(int bsize, int SIZEX, int SIZEY) : Algo_hash(bsize, "SIDE") {
//   sizeX = SIZEX;
//   sizeY = SIZEY;
//   char buf[10];
//   sprintf(buf, "%d_%d", sizeX, sizeY);
//   dbnameext += buf;
//
//   hi = new vector<HashInstance>;
//   for(int i=1; i<bsize-1-sizeX; i++)
//     hi->push_back(HashInstance(i,0,sizeX, sizeY,boardsize));
//   for(int i=1; i<bsize-1-sizeX; i++)
//     hi->push_back(HashInstance(i,bsize-sizeY,sizeX, sizeY,boardsize));
//   for(int i=1; i<bsize-1-sizeX; i++)
//     hi->push_back(HashInstance(0, i, sizeY, sizeX,boardsize));
//   for(int i=1; i<bsize-1-sizeX; i++)
//     hi->push_back(HashInstance(bsize-sizeY, i, sizeY, sizeX,boardsize));
// }

HashInstance::HashInstance(char X, char Y, char SIZEX, char SIZEY, int BOARDSIZE) {
  boardsize = BOARDSIZE;
  xx = X;
  yy = Y;
  pos = xx + boardsize*yy;
  sizeX = SIZEX;
  sizeY = SIZEY;
  branchpoints = 0;
  currentHashCode = 0;
  numStones = 0;
  changed = true;
}

HashInstance::~HashInstance() {
  finalize();
}

void HashInstance::finalize() {
  if (branchpoints) {
    while (branchpoints->size()) {
      delete [] branchpoints->top().first;
      branchpoints->pop();
    }
    delete branchpoints;
    branchpoints = 0;
  }
  if (currentHashCode) {
    delete [] currentHashCode;
    currentHashCode = 0;
  }
}

bool HashInstance::inRelevantRegion(char X, char Y) {
  if (xx <= X && X < xx+sizeX && yy <= Y && Y < yy+sizeY) return true;
  return false;
}

void HashInstance::initialize() {
  // keep track of 8 hashCodes, corresponding to 8 symmetries
  // at the end of each node, the maximum of these values is written to the db.
  currentHashCode = new hashtype[8];
  for(int i=0; i<8; i++) currentHashCode[i] = 0; // start with empty board
  numStones = 0;
  branchpoints = new stack<pair<hashtype*,int> >;
  changed = true; // do record empty pattern ...
}

void HashInstance::addB(char x, char y) {
  if (inRelevantRegion(x,y)) {
    changed = true;
    for(int i=0; i<8; i++) {
      currentHashCode[i] += Algo_hash::hashCodes[Pattern::flipsX(i,x,y,boardsize-1, boardsize-1) + boardsize*Pattern::flipsY(i,x,y,boardsize-1, boardsize-1)];
    }
    numStones++;
  }
}

void HashInstance::addW(char x, char y) {
  if (inRelevantRegion(x,y)) {
    changed = true;
    for(int i=0; i<8; i++) {
      currentHashCode[i] -= Algo_hash::hashCodes[Pattern::flipsX(i,x,y,boardsize-1, boardsize-1) + boardsize*Pattern::flipsY(i,x,y,boardsize-1, boardsize-1)];
    }
    numStones++;
  }
}

void HashInstance::removeB(char x, char y) {
  if (inRelevantRegion(x,y)) {
    changed = true;
    for(int i=0; i<8; i++) {
      currentHashCode[i] -= Algo_hash::hashCodes[Pattern::flipsX(i,x,y,boardsize-1, boardsize-1) + boardsize*Pattern::flipsY(i,x,y,boardsize-1, boardsize-1)];
    }
    numStones--;
  }
}

void HashInstance::removeW(char x, char y) {
  if (inRelevantRegion(x,y)) {
    changed = true;
    for(int i=0; i<8; i++) {
      currentHashCode[i] += Algo_hash::hashCodes[Pattern::flipsX(i,x,y,boardsize-1, boardsize-1) + boardsize*Pattern::flipsY(i,x,y,boardsize-1, boardsize-1)];
    }
    numStones--;
  }
}

pair<hashtype,int> HashInstance::cHC() {
  int flip = 0;
  hashtype minCHC = currentHashCode[0];
  for(int i=0; i<8; i++) {
    // printf("ch %d %ld\n", i, currentHashCode[i]);
    if (currentHashCode[i] < minCHC) {
      minCHC = currentHashCode[i];
      flip = i;
    }
  }
  return make_pair(minCHC, flip*(1<<16)  + pos);
}

void HashInstance::bppush() {
  hashtype* chc = new hashtype[8];
  for(int i=0; i<8; i++) chc[i] = currentHashCode[i];
  branchpoints->push(make_pair(chc, numStones));
}

void HashInstance::bppop() {
  delete [] currentHashCode;
  currentHashCode = branchpoints->top().first;
  numStones = branchpoints->top().second;
  branchpoints->pop();
}



