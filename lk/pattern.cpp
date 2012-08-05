// File: pattern.cpp
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
#include "search.h"
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

char* flipped_sig(int f, char* sig, int boardsize) {
  char* next = new char[13];
  next[12] = 0;
  for(int i=0; i<6; i++) {
    if ('a' <= sig[2*i] && sig[2*i] <= 's')
      next[2*i] = Pattern::flipsX(f, sig[2*i]-'a', sig[2*i+1]-'a', boardsize-1, boardsize-1)+'a';
    else next[2*i] = sig[2*i];
    if ('a' <= sig[2*i+1] && sig[2*i+1] <= 's')
      next[2*i+1] = Pattern::flipsY(f, sig[2*i]-'a', sig[2*i+1]-'a', boardsize-1, boardsize-1)+'a';
    else next[2*i+1] = sig[2*i+1];
  }
  return next; // must be delete[]'d by caller
}


char* symmetrize(char* sig, int boardsize) {
  // symmetrize signature
  char* min_signature = new char[13];
  for(int i=0; i<12; i++) min_signature[i] = sig[i];
  min_signature[12] = 0;
  for (int f=0; f<8; f++) { // for all flips
    // compute flipped signature
    char* next = flipped_sig(f, sig, boardsize);

    // if next < min_signature, then swap
    for(int j=0; j<12; j++) {
      if (next[j] > min_signature[j]) break;
      if (next[j] < min_signature[j]) {
        char* help = next;
        next = min_signature;
        min_signature = help;
        break;
      }
    }
    delete [] next;
  }
  return min_signature;
}


SnapshotVector::SnapshotVector() : vector<unsigned char>() {
  current = begin();
}

SnapshotVector::SnapshotVector(char* c, int size) : vector<unsigned char>() {
  for(int i=0; i<size; i++) {
    push_back(c[i]);
    // printf("in %d\n", c[i]);
  }
  current = begin();
}

void SnapshotVector::pb_int(int d) {
  for(int i = 0; i < 4; i++) {
    push_back((unsigned char)(d % 256));
    d = d >> 8;
  }
}

void SnapshotVector::pb_hashtype(hashtype d) {
  for(int i = 0; i < 8; i++) {
    push_back((unsigned char)(d % 256));
    d = d >> 8;
  }
}

void SnapshotVector::pb_int64(int64_t d) {
  for(int i = 0; i < 8; i++) {
    push_back((unsigned char)(d % 256));
    d = d >> 8;
  }
}

void SnapshotVector::pb_charp(const char* c, int size) {
  pb_int(size);
  // printf("pb charp size %d\n", size);
  for(int i=0; i<size; i++) {
    push_back(c[i]);
    // printf("pb charp %d\n", c[i]);
  }
}

void SnapshotVector::pb_intp(int* p, int size) {
  pb_int(size);
  for(int i=0; i<size; i++) pb_int(p[i]);
}

void SnapshotVector::pb_string(string s) {
  pb_int(s.size());
  for(unsigned int i=0; i<s.size(); i++) push_back(s[i]);
}

void SnapshotVector::pb_char(char c) {
  push_back(c);
}

int SnapshotVector::retrieve_int() {
  int result = 0;
  for(int i=0; i<4; i++) {
    result += ((int)*current) << (i*8);
    current++;
  }
  return result;
}

int64_t SnapshotVector::retrieve_int64() {
  int64_t result = 0;
  for(int i=0; i<8; i++) {
    result += ((int64_t)*current) << (i*8);
    current++;
  }
  return result;
}

hashtype SnapshotVector::retrieve_hashtype() {
  hashtype result = 0;
  for(int i=0; i<8; i++) {
    result += ((hashtype)*current) << (i*8);
    current++;
  }
  return result;
}

int* SnapshotVector::retrieve_intp() {
  int sz = retrieve_int();
  int* result = new int[sz];
  for(int i=0; i<sz; i++)
    result[i] = retrieve_int();
  return result;
}

char SnapshotVector::retrieve_char() {
  char c = *current;
  current++;
  return c;
}

char* SnapshotVector::retrieve_charp() {
  int sz = retrieve_int();
  // if (sz<=0) printf("oops .. %d \n", sz);
  char* result = new char[sz];
  for(int i=0; i<sz; i++) {
    result[i] = *current;
    current++;
  }
  return result;
}

string SnapshotVector::retrieve_string() {
  int sz = retrieve_int();
  char* s = new char[sz+1];
  for(int i=0; i<sz; i++) {
    s[i] = *current;
    current++;
  }
  s[sz] = 0;
  string result(s);
  delete [] s;
  return result;
}

char* SnapshotVector::to_charp() {
  char* result = new char[size()];
  int counter = 0;
  for(SnapshotVector::iterator it = begin(); it != end(); it++) result[counter++] = *it;
  return result;
}


PatternError::PatternError() {}

Continuation::Continuation(GameList* gl) {
  gamelist = gl;
  x = 0;
  y = 0;
  B  = 0;
  W  = 0;
  tB = 0;
  tW = 0;
  wB = 0;
  lB = 0;
  wW = 0;
  lW = 0;
  label ='-';
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    dates_B.push_back(0);
    dates_W.push_back(0);
  }
}

Continuation::Continuation(const Continuation& c) {
  gamelist = c.gamelist;
  x = c.x;
  y = c.y;
  B  = c.B;
  W  = c.W;
  tB = c.tB;
  tW = c.tW;
  wB = c.wB;
  lB = c.lB;
  wW = c.wW;
  lW = c.lW;
  label = c.label;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    dates_B.push_back(c.dates_B[i]);
    dates_W.push_back(c.dates_W[i]);
  }
}

Continuation& Continuation::operator=(const Continuation& c) {
  if (&c != this) {
    gamelist = c.gamelist;
    x = c.x;
    y = c.y;
    B  = c.B;
    W  = c.W;
    tB = c.tB;
    tW = c.tW;
    wB = c.wB;
    lB = c.lB;
    wW = c.wW;
    lW = c.lW;
    label = c.label;
    dates_B.clear();
    dates_W.clear();
    for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
      dates_B.push_back(c.dates_B[i]);
      dates_W.push_back(c.dates_W[i]);
    }
  }
  return *this;
}

int Continuation::total() {
  return B + W;
}

int Continuation::earliest_B() {
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (dates_B[i] > 0) return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::earliest_W() {
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (dates_W[i] > 0) return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::earliest() {
  if (!W) return earliest_B();
  else if (!B) return earliest_W();
  return min(earliest_B(), earliest_W());
}

int Continuation::latest_B() {
  for(int i = DATE_PROFILE_END - DATE_PROFILE_START; i >= 0; i--) {
    if (dates_B[i] > 0) return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::latest_W() {
  for(int i = DATE_PROFILE_END - DATE_PROFILE_START; i >= 0; i--) {
    if (dates_W[i] > 0) return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::latest() {
  if (!W) return latest_B();
  else if (!B) return latest_W();
  return max(latest_B(), latest_W());
}


float Continuation::average_date_B() {
  if (!B) return 0;
  float sum = 0;
  float d = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i]) {
      sum += dates_B[i] * (i + DATE_PROFILE_START) * 1.0/gamelist->dates_all_per_year[i];
      d += dates_B[i] * 1.0/gamelist->dates_all_per_year[i];
    }
  };
  return sum / d;
}

float Continuation::average_date_W() {
  if (!W) return 0;
  float sum = 0;
  float d = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i]) {
      sum += dates_W[i] * (i + DATE_PROFILE_START) * 1.0/gamelist->dates_all_per_year[i];
      d += dates_W[i] * 1.0/gamelist->dates_all_per_year[i];
    }
  }
  return sum / d;
}

float Continuation::average_date() {
  if (!W) return average_date_B();
  else if (!B) return average_date_W();
  float sum = 0;
  float d = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i]) {
      sum += (dates_B[i] + dates_W[i]) * (i + DATE_PROFILE_START) * 1.0/gamelist->dates_all_per_year[i];
      d += (dates_B[i] + dates_W[i]) * 1.0/gamelist->dates_all_per_year[i];
    }
  }
  return sum / d;
}

int Continuation::became_popular_B() {
  if (!B) return 0;
  float sum_squares = 0;
  int ctr = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    // printf("bcb0 %d\n", dates_B[i]);
    if (gamelist->dates_all_per_year[i] && dates_B[i]) {
      sum_squares += dates_B[i] * dates_B[i]*1.0/(gamelist->dates_all_per_year[i] * gamelist->dates_all_per_year[i]);
      ctr++;
    }
  }
  float s = sqrt(sum_squares / ctr);
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && dates_B[i]*1.0/gamelist->dates_all_per_year[i] >= s)
      return (i + DATE_PROFILE_START);
  }
  return -1;
}

int Continuation::became_popular_W() {
  if (!W) return 0;
  float sum_squares = 0;
  int ctr = 0;
  // printf("dapy size %d expected %d\n", gamelist->dates_all_per_year.size(), DATE_PROFILE_END - DATE_PROFILE_START + 1);
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && dates_W[i]) {
      sum_squares += (float)dates_W[i] * dates_W[i]*1.0/(gamelist->dates_all_per_year[i] * gamelist->dates_all_per_year[i]);
      ctr++;
    }
  }
  float s = sqrt(sum_squares / ctr);
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && dates_W[i]*1.0/gamelist->dates_all_per_year[i]>= s)
      return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::became_popular() {
  if (!W) return became_popular_B();
  else if (!B) return became_popular_W();

  float sum_squares = 0;
  int ctr = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && (dates_B[i] + dates_W[i])) {
      sum_squares += (((float)dates_B[i] + dates_W[i]) * (dates_B[i] + dates_W[i]))*1.0/(gamelist->dates_all_per_year[i] * gamelist->dates_all_per_year[i]);
      ctr++;
    }
  }
  float s = sqrt(sum_squares / ctr);
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && (dates_B[i] + dates_W[i])*1.0/gamelist->dates_all_per_year[i]>= s) return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::became_unpopular_B() {
  if (!B) return 0;
  float sum_squares = 0;
  int ctr = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    // printf("bcb0 %d\n", dates_B[i]);
    if (gamelist->dates_all_per_year[i] && dates_B[i]) {
      sum_squares += dates_B[i] * dates_B[i]*1.0/(gamelist->dates_all_per_year[i] * gamelist->dates_all_per_year[i]);
      ctr++;
    }
  }
  float s = sqrt(sum_squares / ctr);
  for(int i = (DATE_PROFILE_END - DATE_PROFILE_START); i >= 0; i--) {
    if (gamelist->dates_all_per_year[i] && dates_B[i]*1.0/gamelist->dates_all_per_year[i] >= s)
      return (i + DATE_PROFILE_START);
  }
  return -1;
}

int Continuation::became_unpopular_W() {
  if (!W) return 0;
  float sum_squares = 0;
  int ctr = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && dates_W[i]) {
      sum_squares += (float)dates_W[i] * dates_W[i]*1.0/(gamelist->dates_all_per_year[i] * gamelist->dates_all_per_year[i]);
      ctr++;
    }
  }
  float s = sqrt(sum_squares / ctr);
  for(int i = (DATE_PROFILE_END - DATE_PROFILE_START); i >= 0; i--) {
    if (gamelist->dates_all_per_year[i] && dates_W[i]*1.0/gamelist->dates_all_per_year[i]>= s)
      return i + DATE_PROFILE_START;
  }
  return -1;
}

int Continuation::became_unpopular() {
  if (!W) return became_unpopular_B();
  else if (!B) return became_unpopular_W();

  float sum_squares = 0;
  int ctr = 0;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    if (gamelist->dates_all_per_year[i] && (dates_B[i] + dates_W[i])) {
      sum_squares += (((float)dates_B[i] + dates_W[i]) * (dates_B[i] + dates_W[i]))*1.0/(gamelist->dates_all_per_year[i] * gamelist->dates_all_per_year[i]);
      ctr++;
    }
  }
  float s = sqrt(sum_squares / ctr);
  for(int i = (DATE_PROFILE_END - DATE_PROFILE_START); i >= 0; i--) {
    if (gamelist->dates_all_per_year[i] && (dates_B[i] + dates_W[i])*1.0/gamelist->dates_all_per_year[i]>= s) return i + DATE_PROFILE_START;
  }
  return -1;
}

void Continuation::from_snv(SnapshotVector& snv) {
  x = snv.retrieve_int();
  y = snv.retrieve_int();
  B = snv.retrieve_int();
  W = snv.retrieve_int();
  tB = snv.retrieve_int();
  tW = snv.retrieve_int();
  wB = snv.retrieve_int();
  lB = snv.retrieve_int();
  wW = snv.retrieve_int();
  lW = snv.retrieve_int();
  label = snv.retrieve_char();
  dates_B.clear();
  dates_W.clear();
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    dates_B.push_back(snv.retrieve_int());
  }
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    dates_W.push_back(snv.retrieve_int());
  }
}

void Continuation::to_snv(SnapshotVector& snv) {
  snv.pb_int(x);
  snv.pb_int(y);
  snv.pb_int(B);
  snv.pb_int(W);
  snv.pb_int(tB);
  snv.pb_int(tW);
  snv.pb_int(wB);
  snv.pb_int(lB);
  snv.pb_int(wW);
  snv.pb_int(lW);
  snv.pb_char(label);
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    snv.pb_int(dates_B[i]);
  }
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    snv.pb_int(dates_W[i]);
  }
}

void Continuation::add(const Continuation c) {
  B += c.B;
  W += c.W;
  tB += c.tB;
  tW += c.tW;
  wB += c.wB;
  lB += c.lB;
  wW += c.wW;
  lW += c.lW;
  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START + 1); i++) {
    dates_B[i] += c.dates_B[i];
    dates_W[i] += c.dates_W[i];
  }
}

Symmetries::Symmetries(char sX, char sY) {
  sizeX = sX;
  sizeY = sY;
  dataX = new char[sizeX*sizeY];
  dataY = new char[sizeX*sizeY];
  dataCS = new char[sizeX*sizeY];
  for(int i=0; i<sizeX*sizeY; i++) {
    dataX[i] = -1;
    dataY[i] = -1;
    dataCS[i] = -1;
  }
}

Symmetries::~Symmetries() {
  delete [] dataX;
  delete [] dataY;
  delete [] dataCS;
}

Symmetries::Symmetries(const Symmetries& s) {
  sizeX = s.sizeX;
  sizeY = s.sizeY;
  dataX = new char[sizeX*sizeY];
  dataY = new char[sizeX*sizeY];
  dataCS = new char[sizeX*sizeY];
  for(int i=0; i<sizeX*sizeY; i++) {
    dataX[i] = s.dataX[i];
    dataY[i] = s.dataY[i];
    dataCS[i] = s.dataCS[i];
  }
}

Symmetries& Symmetries::operator=(const Symmetries& s) {
  if (&s != this) {
    sizeX = s.sizeX;
    sizeY = s.sizeY;
    delete [] dataX;
    delete [] dataY;
    delete [] dataCS;
    dataX = new char[sizeX*sizeY];
    dataY = new char[sizeX*sizeY];
    dataCS = new char[sizeX*sizeY];
    for(int i=0; i<sizeX*sizeY; i++) {
      dataX[i] = s.dataX[i];
      dataY[i] = s.dataY[i];
      dataCS[i] = s.dataCS[i];
    }
  }
  return *this;
}

void Symmetries::set(char i, char j, char k, char l, char cs) throw(PatternError) {
  if (0 <= i && i < sizeX && 0 <= j && j < sizeY) {
    dataX[i + j*sizeX] = k;
    dataY[i + j*sizeX] = l;
    dataCS[i + j*sizeX] = cs;
  }
  else throw PatternError();
}

char Symmetries::getX(char i, char j) throw(PatternError) {
  if (0 <= i && i < sizeX && 0 <= j && j < sizeY) return dataX[i + j*sizeX];
  else throw PatternError();
  return -1;
}

char Symmetries::getY(char i, char j) throw(PatternError) {
  if (0 <= i && i < sizeX && 0 <= j && j < sizeY) return dataY[i + j*sizeX];
  else throw PatternError();
  return -1;
}

char Symmetries::getCS(char i, char j) throw(PatternError) {
  if (0 <= i && i < sizeX && 0 <= j && j < sizeY) return dataCS[i + j*sizeX];
  else throw PatternError();
  return -1;
}

char Symmetries::has_key(char i, char j) throw(PatternError) {
  if (0 <= i && i < sizeX && 0 <= j && j < sizeY) {
    if (dataX[i + j*sizeX] == -1) return 0;
    else return 1;
  }
  else throw PatternError();
  return 0;
}


// ----------- class Pattern -----------------------------------------------

int Pattern::operator==(const Pattern& p) {
  if (boardsize != p.boardsize) return 0;
  if (sizeX != p.sizeX || sizeY != p.sizeY) return 0;
  if (left != p.left || right != p.right || top != p.top || bottom != p.bottom) return 0; 
  for(int i=0; i < sizeX*sizeY; i++)
    if (initialPos[i] != p.initialPos[i]) return 0;
  if (contList != p.contList) return 0;
  return 1;
}


char Pattern::BW2XO(char c) {
  if (c == 'B') return 'X';
  if (c == 'W') return 'O';
  return c;
}

char Pattern::getInitial(int i, int j) {
  return initialPos[i + sizeX*j];
}
 
char Pattern::getFinal(int i, int j) {
  return finalPos[i + sizeX*j];
}
 

Pattern::Pattern() {
  initialPos = 0;
  finalPos = 0;
  flip = 0;
  colorSwitch = 0;
  sizeX = 0;
  sizeY = 0;
  boardsize = 0;
  contLabels = 0;
}


Pattern::Pattern(int type, int BOARDSIZE, int sX, int sY, const char* iPos, const char* CONTLABELS) {
  flip = 0;
  colorSwitch = 0;
  sizeX = sX;
  sizeY = sY;
  boardsize = BOARDSIZE;
  if (CONTLABELS) {
    contLabels = new char[sizeX * sizeY];
    for(int i=0; i<sizeX*sizeY; i++) contLabels[i] = CONTLABELS[i];
  } else contLabels = 0;

  if (type == CORNER_NW_PATTERN || type == FULLBOARD_PATTERN) {
    left = right = top = bottom = 0;
  } else if (type == CORNER_NE_PATTERN) {
    top = bottom = 0;
    left = right = boardsize - sizeX;
  } else if (type == CORNER_SE_PATTERN) {
    top = bottom = boardsize - sizeY;
    left = right = boardsize - sizeX;
  } else if (type == CORNER_SW_PATTERN) {
    top = bottom = boardsize - sizeY;
    left = right = 0;
  } else if (type == SIDE_N_PATTERN) {
    top = bottom = 0;
    left = 1;
    right = boardsize -1 - sizeX;
  } else if (type == SIDE_E_PATTERN) {
    left = right = boardsize - sizeX;
    top = 1;
    bottom = boardsize -1 - sizeY;
  } else if (type == SIDE_W_PATTERN) {
    left = right = 0;
    top = 1;
    bottom = boardsize -1 - sizeY;
  } else if (type == SIDE_S_PATTERN) {
    top = bottom = boardsize - sizeY;
    left = 1;
    right = boardsize -1 - sizeX;
  } else if (type == CENTER_PATTERN) {
    left = top = 1;
    right = boardsize -1 - sizeX;
    bottom = boardsize -1 - sizeY;
  }

  initialPos = new char[sizeX * sizeY];
  finalPos = new char[sizeX*sizeY];
  for(int i=0; i<sizeX*sizeY; i++) {
    initialPos[i] = iPos[i];
    finalPos[i] = iPos[i];
  }
  // std::cout << printPattern() << std::endl;
}



Pattern::Pattern(int type, int BOARDSIZE, int sX, int sY, const char* iPos, const vector<MoveNC>& CONTLIST, const char* CONTLABELS) {
  flip = 0;
  colorSwitch = 0;
  sizeX = sX;
  sizeY = sY;
  boardsize = BOARDSIZE;
  if (CONTLABELS) {
    contLabels = new char[sizeX * sizeY];
    for(int i=0; i<sizeX*sizeY; i++) contLabels[i] = CONTLABELS[i];
  } else contLabels = 0;

  if (type == CORNER_NW_PATTERN || type == FULLBOARD_PATTERN) {
    left = right = top = bottom = 0;
  } else if (type == CORNER_NE_PATTERN) {
    top = bottom = 0;
    left = right = boardsize - sizeX;
  } else if (type == CORNER_SE_PATTERN) {
    top = bottom = boardsize - sizeY;
    left = right = boardsize - sizeX;
  } else if (type == CORNER_SW_PATTERN) {
    top = bottom = boardsize - sizeY;
    left = right = 0;
  } else if (type == SIDE_N_PATTERN) {
    top = bottom = 0;
    left = 1;
    right = boardsize -1 - sizeX;
  } else if (type == SIDE_E_PATTERN) {
    left = right = boardsize - sizeX;
    top = 1;
    bottom = boardsize -1 - sizeY;
  } else if (type == SIDE_W_PATTERN) {
    left = right = 0;
    top = 1;
    bottom = boardsize -1 - sizeY;
  } else if (type == SIDE_S_PATTERN) {
    top = bottom = boardsize - sizeY;
    left = 1;
    right = boardsize -1 - sizeX;
  } else if (type == CENTER_PATTERN) {
    left = top = 1;
    right = boardsize -1 - sizeX;
    bottom = boardsize -1 - sizeY;
  }

  initialPos = new char[sizeX * sizeY];
  finalPos = new char[sizeX*sizeY];
  for(int i=0; i<sizeX*sizeY; i++) {
    initialPos[i] = iPos[i];
    finalPos[i] = iPos[i];
  }
  contList = CONTLIST;
}

Pattern::Pattern(int le, int ri, int to, int bo, int BOARDSIZE, int sX, int sY, const char* iPos) throw(PatternError) {
  // check whether anchor rectangle is valid
  if (le < 0 || ri+sX > BOARDSIZE || to < 0 || bo+sY > BOARDSIZE || ri < le || bo < to) throw PatternError();

  flip = 0;
  colorSwitch = 0;

  left = le;
  right = ri;
  top = to;
  bottom = bo;
  boardsize = BOARDSIZE;

  sizeX = sX;
  sizeY = sY;
  contLabels = 0;

  initialPos = new char[sizeX * sizeY];
  finalPos = new char[sizeX*sizeY];
  for(int i=0; i<sizeX*sizeY; i++) {
    initialPos[i] = iPos[i];
    finalPos[i] = iPos[i];
  }
}

Pattern::Pattern(int le, int ri, int to, int bo, int BOARDSIZE, int sX, int sY,
                 const char* iPos, const vector<MoveNC>& CONTLIST, const char* CONTLABELS) throw(PatternError) {
  // check whether anchor rectangle is valid
  if (le < 0 || ri+sX > BOARDSIZE || to < 0 || bo+sY > BOARDSIZE || ri < le || bo < to) throw PatternError();

  flip = 0;
  colorSwitch = 0;

  left = le;
  right = ri;
  top = to;
  bottom = bo;
  boardsize = BOARDSIZE;

  sizeX = sX;
  sizeY = sY;
  if (CONTLABELS) {
    contLabels = new char[sizeX * sizeY];
    for(int i=0; i<sizeX*sizeY; i++) contLabels[i] = CONTLABELS[i];
  } else contLabels = 0;

  initialPos = new char[sizeX * sizeY];
  finalPos = new char[sizeX*sizeY];
  for(int i=0; i<sizeX*sizeY; i++) {
    initialPos[i] = iPos[i];
    finalPos[i] = iPos[i];
  }

  contList = CONTLIST;
}

Pattern::Pattern(SnapshotVector& snv) {
  flip = snv.retrieve_int();
  colorSwitch = snv.retrieve_int();
  left = snv.retrieve_int();
  right = snv.retrieve_int();
  top = snv.retrieve_int();
  bottom = snv.retrieve_int();
  boardsize = snv.retrieve_int();
  sizeX = snv.retrieve_int();
  sizeY = snv.retrieve_int();
  if (snv.retrieve_char()) { // contLabels?
    contLabels = snv.retrieve_charp();
  } else contLabels = 0;
  initialPos = snv.retrieve_charp();
  finalPos = snv.retrieve_charp();

  int size = snv.retrieve_int();
  for(int i=0; i<size; i++)
    contList.push_back(MoveNC(snv.retrieve_char(), snv.retrieve_char(), snv.retrieve_char())); // x, y, color
}

void Pattern::to_snv(SnapshotVector& snv) {
  snv.pb_int(flip);
  snv.pb_int(colorSwitch);
  snv.pb_int(left);
  snv.pb_int(right);
  snv.pb_int(top);
  snv.pb_int(bottom);
  snv.pb_int(boardsize);
  snv.pb_int(sizeX);
  snv.pb_int(sizeY);
  if (contLabels) {
    snv.pb_char(1);
    snv.pb_charp(contLabels, sizeX*sizeY);
  } else snv.pb_char(0);
  snv.pb_charp(initialPos, sizeX*sizeY);
  snv.pb_charp(finalPos, sizeX*sizeY);
  snv.pb_int(contList.size());
  for(vector<MoveNC>::iterator it = contList.begin(); it != contList.end(); it++) {
    snv.pb_char(it->x);
    snv.pb_char(it->y);
    snv.pb_char(it->color);
  }
}

Pattern::~Pattern() {
  if (initialPos) delete [] initialPos;
  if (finalPos) delete [] finalPos;
  if (contLabels) delete [] contLabels;
}

Pattern::Pattern(const Pattern& p) {
  left = p.left;
  right = p.right;
  top = p.top;
  bottom = p.bottom;
  boardsize = p.boardsize;
  sizeX = p.sizeX;
  sizeY = p.sizeY;
  flip = p.flip;
  colorSwitch = p.colorSwitch;

  initialPos = new char[sizeX*sizeY];
  finalPos = new char[sizeX*sizeY];
  if (p.contLabels) contLabels = new char[sizeX*sizeY];
  else contLabels = 0;
  for(int i=0; i<sizeX*sizeY; i++) {
    initialPos[i] = p.initialPos[i];
    finalPos[i] = p.finalPos[i];
    if (p.contLabels) contLabels[i] = p.contLabels[i];
  }
  contList = p.contList;
}

Pattern& Pattern::operator=(const Pattern& p) {
  if (&p != this) {
    left = p.left;
    right = p.right;
    top = p.top;
    bottom = p.bottom;
    boardsize = p.boardsize;
    sizeX = p.sizeX;
    sizeY = p.sizeY;
    flip = p.flip;
    colorSwitch = p.colorSwitch;

    if (initialPos) delete [] initialPos;
    if (finalPos) delete [] finalPos;
    if (contLabels) delete [] contLabels;

    initialPos = new char[sizeX*sizeY];
    finalPos = new char[sizeX*sizeY];
    if (p.contLabels) contLabels = new char[sizeX*sizeY];
    else contLabels = 0;
    for(int i=0; i<sizeX*sizeY; i++) {
      initialPos[i] = p.initialPos[i];
      finalPos[i] = p.finalPos[i];
      if (p.contLabels) contLabels[i] = p.contLabels[i];
    }
    contList = p.contList;
  }
  return *this;
}


Pattern& Pattern::copy(const Pattern& p) {
  if (&p != this) {
    left = p.left;
    right = p.right;
    top = p.top;
    bottom = p.bottom;
    boardsize = p.boardsize;
    sizeX = p.sizeX;
    sizeY = p.sizeY;
    flip = p.flip;
    colorSwitch = p.colorSwitch;

    if (initialPos) delete [] initialPos;
    if (finalPos) delete [] finalPos;

    initialPos = new char[sizeX*sizeY];
    finalPos = new char[sizeX*sizeY];
    if (p.contLabels) contLabels = new char[sizeX*sizeY];
    else contLabels = 0;
    for(int i=0; i<sizeX*sizeY; i++) {
      initialPos[i] = p.initialPos[i];
      finalPos[i] = p.finalPos[i];
      if (p.contLabels) contLabels[i] = p.contLabels[i];
    }
    contList = p.contList;
  }
  return *this;
}

string Pattern::printPattern() {
  string result;
  char buf[100];
  sprintf(buf, "boardsize: %d, area: %d, %d, %d, %d\nsize: %d, %d\n", boardsize, left, right, top, bottom, sizeX, sizeY);
  result += buf;
  for(int i=0; i<sizeY; i++) {
    for(int j=0; j<sizeX; j++) {
      if (initialPos[i*sizeX + j] == 'X' || initialPos[i*sizeX + j] == 'O' || initialPos[i*sizeX + j] == 'x' || initialPos[i*sizeX + j] == 'x' || initialPos[i*sizeX+j] == '*') result += initialPos[i*sizeX+j];
      else result += '.';
    }
    result += "\n";
  }
  result += "\n";
  return result;
}


int Pattern::flipsX(int i, int x, int y, int XX, int YY) {
  if (i==0) return x;
  if (i==1) return XX-x;
  if (i==2) return x;
  if (i==3) return XX-x;
  if (i==4) return y;
  if (i==5) return YY-y;
  if (i==6) return y;
  if (i==7) return YY-y;
  return -1;
}

int Pattern::flipsY(int i, int x, int y, int XX, int YY) {
  if (i==0) return y;
  if (i==1) return y;
  if (i==2) return YY-y;
  if (i==3) return YY-y;
  if (i==4) return x;
  if (i==5) return x;
  if (i==6) return XX-x;
  if (i==7) return XX-x;
  return -1;
}


int Pattern::PatternInvFlip(int i) {
  if (i == 5) return 6;
  if (i == 6) return 5;
  return i;
}

const int composition_table[] = {
  0, 1, 2, 3, 4, 5, 6, 7,
  1, 0, 3, 2, 5, 4, 7, 6,
  2, 3, 0, 1, 6, 7, 4, 5,
  3, 2, 1, 0, 7, 6, 5, 4,
  4, 6, 5, 7, 0, 2, 1, 3,
  5, 7, 4, 6, 1, 3, 0, 2,
  6, 4, 7, 5, 2, 0, 3, 1,
  7, 5, 6, 4, 3, 1, 2, 0 };

int Pattern::compose_flips(int i, int j) {
  return composition_table[j+8*i];
}

PatternList::PatternList(Pattern& p, int fColor, int nMove, GameList* gl) throw(PatternError) {
  pattern.copy(p);
  fixedColor = fColor;
  nextMove = nMove;
  special = -1;
  flipTable = new int[16];
  for(int i=0; i<16; i++) flipTable[i] = -1; // (patternList() relies on this)

  patternList();
  for(int i=0; i < pattern.sizeX * pattern.sizeY; i++)
    continuations.push_back(new Continuation(gl));
}

PatternList::~PatternList() {
  for (std::vector<Continuation* >::const_iterator i = continuations.begin(); i != continuations.end(); ++i) {
    delete *i;
  }
  delete [] flipTable;
}

char PatternList::invertColor(char co) {
  if (co == 'X') return 'O';
  if (co == 'x') return 'o';

  if (co == 'O') return 'X';
  if (co == 'o') return 'x';

  return co;
}

void PatternList::patternList() {
  vector<Pattern> lCS;
  vector<pair<int,int> > sy;  // consisting of all pairs (flip, color-switch) stabilizing the given pattern
  int boardsize = pattern.boardsize;

  // for all eight board symmetries, compute "flipped" pattern (and possibly the flipped pattern with black/white exchanged)
  for(int f = 0; f < 8; f++) {
    int newSizeX = max(Pattern::flipsX(f,0,0,pattern.sizeX,pattern.sizeY),
                       Pattern::flipsX(f,pattern.sizeX,pattern.sizeY,pattern.sizeX,pattern.sizeY));
    int newSizeY = max(Pattern::flipsY(f,0,0,pattern.sizeX,pattern.sizeY),
                       Pattern::flipsY(f,pattern.sizeX,pattern.sizeY,pattern.sizeX,pattern.sizeY));

    int newLeft = min(Pattern::flipsX(f,pattern.left,pattern.top,boardsize-1,boardsize-1),
                      Pattern::flipsX(f,pattern.right+pattern.sizeX-1,pattern.bottom+pattern.sizeY-1,
                                      boardsize-1,boardsize-1));
    int newRight = max(Pattern::flipsX(f,pattern.left,pattern.top,boardsize-1,boardsize-1),
                       Pattern::flipsX(f,pattern.right+pattern.sizeX-1,pattern.bottom+pattern.sizeY-1,
                                       boardsize-1,boardsize-1)) - (newSizeX-1);
    int newTop = min(Pattern::flipsY(f,pattern.left,pattern.top,boardsize-1,boardsize-1),
                     Pattern::flipsY(f,pattern.right+pattern.sizeX-1,pattern.bottom+pattern.sizeY-1,
                                     boardsize-1,boardsize-1));
    int newBottom = max(Pattern::flipsY(f,pattern.left,pattern.top,boardsize-1,boardsize-1),
                        Pattern::flipsY(f,pattern.right+pattern.sizeX-1,pattern.bottom+pattern.sizeY-1,
                        boardsize-1,boardsize-1)) - (newSizeY - 1);

    // printf("%d, %d, %d, %d, %d, %d, %d\n", f, newSizeX, newSizeY, newLeft, newRight, newTop, newBottom);
    char* newInitialPos = new char[pattern.sizeX*pattern.sizeY];
    int i=0;
    for(i=0; i<pattern.sizeX; i++) {
      for(int j=0; j<pattern.sizeY; j++) {
        newInitialPos[Pattern::flipsX(f,i,j,pattern.sizeX-1,pattern.sizeY-1) + \
                      newSizeX*Pattern::flipsY(f,i,j,pattern.sizeX-1,pattern.sizeY-1)] = pattern.getInitial(i, j);
      }
    }

    vector<MoveNC> newContList;
    for(i=0; (unsigned int)i<pattern.contList.size(); i++) {
      newContList.push_back(MoveNC(Pattern::flipsX(f, pattern.contList[i].x, pattern.contList[i].y, 
                                                      pattern.sizeX-1,pattern.sizeY-1),
                                  Pattern::flipsY(f, pattern.contList[i].x, pattern.contList[i].y,
                                                      pattern.sizeX-1,pattern.sizeY-1),
                                  pattern.contList[i].color));
    }

    Pattern pNew(newLeft, newRight, newTop, newBottom, pattern.boardsize, newSizeX, newSizeY,
                 newInitialPos, newContList);

    pNew.flip = f;
    // printf("new size %d %d\n", pNew.sizeX, pNew.sizeY);

    delete [] newInitialPos;

    vector<Pattern>::iterator it;
    bool foundNewPattern = true;
    for(it = data.begin(); it != data.end(); it++) {
      if (pNew == *it) {
        foundNewPattern = false;
        flipTable[f] = flipTable[it->flip];
        break;
      }
    }
    if (foundNewPattern) {
      flipTable[f] = data.size();
      data.push_back(pNew);
      // cout << pNew.printPattern();
    }

    if (pNew == pattern) sy.push_back(pair<int,int>(f,0)); // if this flip gave rise to the same pattern, we have found a symmetry of the pattern

    if (!fixedColor) { // also compute color-swapped pattern, if this is asked for (!fixedColor),
      char* newInitialPos = new char[pattern.sizeX*pattern.sizeY];
      for(int i=0; i<pattern.sizeX; i++) {
        for(int j=0; j<pattern.sizeY; j++) {
          newInitialPos[Pattern::flipsX(f,i,j,pattern.sizeX-1,pattern.sizeY-1) + newSizeX*Pattern::flipsY(f,i,j,pattern.sizeX-1,pattern.sizeY-1)] =
            invertColor(pattern.getInitial(i, j));
        }
      }
      vector<MoveNC> newContList;
      {
        for(unsigned int i=0; i<pattern.contList.size(); i++) {
          newContList.push_back(MoveNC(Pattern::flipsX(f, pattern.contList[i].x, pattern.contList[i].y, 
                  pattern.sizeX-1,pattern.sizeY-1),
                Pattern::flipsY(f, pattern.contList[i].x, pattern.contList[i].y,
                  pattern.sizeX-1,pattern.sizeY-1),
                invertColor(pattern.contList[i].color)));
        }
      }

      // printf("new size %d %d", newSizeX, newSizeY);
      Pattern pNew1(newLeft, newRight, newTop, newBottom, pattern.boardsize, newSizeX, newSizeY,
                    newInitialPos, newContList);
      pNew1.flip = f;
      pNew1.colorSwitch = 1;

      delete [] newInitialPos;

      bool foundNewPattern = true;
      int lCS_ctr = 0;
      for(vector<Pattern>::iterator it = lCS.begin(); it != lCS.end(); it++) {
        if (pNew1 == *it) {
          foundNewPattern = false;
          flipTable[f+8] = lCS_ctr;
          break;
        }
        lCS_ctr++;
      }
      if (foundNewPattern) {
        lCS.push_back(pNew1);
        // cout << pNew1.printPattern();
      }

      if (pNew1 == pattern) { // can get back original pattern by applying CS + flip f.
        sy.push_back(pair<int,int>(f,1));
        if (nextMove) special = Pattern::PatternInvFlip(f);
      }
    }
  }

  int lCS_ctr = 0;
  for(vector<Pattern>::iterator it = lCS.begin(); it != lCS.end(); it++) {
    bool contained_in_l = false;
    for(vector<Pattern>::iterator it_l = data.begin(); it_l != data.end(); it_l++)
      if (*it == *it_l) {
        contained_in_l = true;
        flipTable[8+it->flip] = flipTable[it_l->flip];
        break;
      }
    if (!contained_in_l) {
      flipTable[8+it->flip] = data.size();
      data.push_back(*it);
    }
    for(int ii=it->flip+1; ii<8; ii++) 
      if (flipTable[8+ii] == lCS_ctr) flipTable[8+ii] = flipTable[8+it->flip];
    lCS_ctr++;
  }

  // cout << endl << endl << "fliptable: ";
  // for(int ii=0; ii<16; ii++) cout << ii << ", ";
  // cout << endl << endl;


  Symmetries symm(pattern.sizeX, pattern.sizeY);
  for(int i=0; i<symm.sizeX; i++)
    for(int j=0; j<symm.sizeY; j++)
      symm.set(i,j, i,j,0);

  for(vector<pair<int,int> >::iterator it_s=sy.begin(); it_s!=sy.end(); it_s++) {
    int s = it_s->first;
    int newSizeX = max(Pattern::flipsX(s,0,0,pattern.sizeX,pattern.sizeY),
                       Pattern::flipsX(s,pattern.sizeX,pattern.sizeY,pattern.sizeX,pattern.sizeY));
    int newSizeY = max(Pattern::flipsY(s,0,0,pattern.sizeX,pattern.sizeY),
                       Pattern::flipsY(s,pattern.sizeX,pattern.sizeY,pattern.sizeX,pattern.sizeY));
    int c = it_s->second;
    Symmetries symm1(newSizeX, newSizeY);

    for(int i=0; i < pattern.sizeX; i++) {
      for(int j=0; j < pattern.sizeY; j++) {
        int fX = Pattern::flipsX(s, i, j, pattern.sizeX-1, pattern.sizeY-1);
        int fY = Pattern::flipsY(s, i, j, pattern.sizeX-1, pattern.sizeY-1);
        if ((i != fX || j != fY) && !symm1.has_key(fX, fY))
          symm1.set(i,j, fX, fY, c);
      }
    }

    int cs;
    for(int i=0; i<symm.sizeX; i++)
      for(int j=0; j<symm.sizeY; j++)
        if (symm1.has_key(symm.getX(i,j), symm.getY(i,j))) {
          cs = ((symm1.getCS(symm.getX(i,j),symm.getY(i,j)) || symm.getCS(i,j)) && !(symm1.getCS(symm.getX(i,j),symm.getY(i,j)) && symm.getCS(i,j))) ?  1 : 0;
          symm.set(i,j,symm1.getX(symm.getX(i,j),symm.getY(i,j)), symm1.getY(symm.getX(i,j),symm.getY(i,j)), cs);
        }
  }

  // now take care of contLabels
  if (pattern.contLabels) {
    for(int i=0; i<symm.sizeX; i++)
      for(int j=0; j<symm.sizeY; j++) {
        if ((symm.getX(i,j)!=i || symm.getY(i,j)!=j) && pattern.contLabels[i+j*pattern.sizeX]!='.' && pattern.contLabels[symm.getX(i,j)+symm.getY(i,j)*pattern.sizeX]=='.') {
          for(int ii=0; ii<symm.sizeX; ii++)
            for(int jj=0; jj<symm.sizeY; jj++)
              if (symm.getX(ii,jj) == symm.getX(i,j) && symm.getY(ii,jj) == symm.getY(i,j) && (ii!=i || jj!=j)) {
                // printf("remap %d %d %d %d\n", ii,jj, i, j);
                symm.set(ii, jj, i, j, symm.getCS(ii,jj));
              }
          symm.set(symm.getX(i,j), symm.getY(i,j), i, j, symm.getCS(i,j));
          symm.set(i,j,i,j,0);
        }
      }
  }

  symmetries.push_back(symm);

  vector<Pattern>::iterator it = data.begin();
  it++;
  for(; it != data.end(); it++) {
    // printf("ne %d, %d\n", it->sizeX, it->sizeY);
    int f = it->flip;
    Symmetries s(it->sizeX, it->sizeY);
    for(int i=0; i<pattern.sizeX; i++) {
      for(int j=0; j<pattern.sizeY; j++) {
        if (!it->colorSwitch) {
          s.set(Pattern::flipsX(f,i,j,pattern.sizeX-1,pattern.sizeY-1), 
              Pattern::flipsY(f,i,j,pattern.sizeX-1,pattern.sizeY-1), 
              symm.getX(i,j), symm.getY(i,j), symm.getCS(i,j));
        } else {
          s.set(Pattern::flipsX(f,i,j,pattern.sizeX-1,pattern.sizeY-1), 
              Pattern::flipsY(f,i,j,pattern.sizeX-1,pattern.sizeY-1), 
              symm.getX(i,j), symm.getY(i,j), 1-symm.getCS(i,j));
        }
      }
    }
    symmetries.push_back(s);
  }

}


Pattern PatternList::get(int i) {
  return data[i];
}


int PatternList::size() {
  return data.size();
}


char* PatternList::updateContinuations(int index, int x, int y, char co, bool tenuki, char winner, int date) {
  char xx;
  char yy;
  char cSymm;
  char cc;
  xx = symmetries[index].getX(x,y);
  yy = symmetries[index].getY(x,y);
  cSymm = symmetries[index].getCS(x,y);
  if (co == 'X' || co == 'B') {
    if (cSymm) cc = 'W'; else cc = 'B';
  } else {
    if (cSymm) cc = 'B'; else cc = 'W';
  }

  if ((nextMove == 1 && cc == 'W') || (nextMove == 2 && cc == 'B')) {
    if (special != -1) {
      char xx1 = xx;
      // printf("s1 xx %d, yy %d sp %d\n", xx, yy, special);
      xx = Pattern::flipsX(special, xx, yy, pattern.sizeX-1, pattern.sizeY-1);
      yy = Pattern::flipsY(special, xx1, yy, pattern.sizeX-1, pattern.sizeY-1);
      // printf("s2 xx %d, yy %d\n", xx, yy);
      cc = (cc == 'B') ? 'W' : 'B';
      cSymm = 1-cSymm;
    } else {
      return 0;
    }
  }

  Continuation* cont = continuations[xx + pattern.sizeX*yy];
  if (cc == 'B') {
    // printf("B xx %d, yy %d\n", xx, yy);
    cont->B++;
    if (tenuki) cont->tB++;
    if ((winner == 'B' && !cSymm) || (winner == 'W' && cSymm)) cont->wB++;
    else if ((winner == 'W' && !cSymm) || (winner == 'B' && cSymm)) cont->lB++;

    if (date/12 - DATE_PROFILE_START >= 0 && date/12 < DATE_PROFILE_END) {
      cont->dates_B[date/12 - DATE_PROFILE_START]++;
    }
  } else {
    // printf("W xx %d, yy %d\n", xx, yy);
    cont->W++;
    if (tenuki) cont->tW++;
    if ((winner == 'B' && !cSymm) || (winner == 'W' && cSymm)) cont->wW++;
    else if ((winner == 'W' && !cSymm) || (winner ='B' && cSymm)) cont->lW++;

    if (date/12 - DATE_PROFILE_START >= 0 && date/12 < DATE_PROFILE_END) {
      cont->dates_W[date/12 - DATE_PROFILE_START]++;
    }
  }

  char* result = new char[3];
  result[0] = xx;
  result[1] = yy;
  result[2] = cSymm;
  return result;
}


char* PatternList::sortContinuations() {
  char* labels = new char[pattern.sizeX*pattern.sizeY+1];
  labels[pattern.sizeX * pattern.sizeY] = 0; // so we can just printf the labels as a string
  for(int i=0; i<pattern.sizeX*pattern.sizeY; i++) {
    if (continuations[i]->B || continuations[i]->W) labels[i] = '?'; // need to assign label
    else labels[i] = '.';
  }
  string labelList = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
  size_t labelIndex = 0;

  // assign labels which are in the contLabels array passed to the original pattern
  // (these will usually be labels "already present in the SGF file")
  
  if (pattern.contLabels) {
    for(int i=0; i<pattern.sizeX*pattern.sizeY; i++) {
      if (pattern.contLabels[i] != '.') {
        labels[i] = pattern.contLabels[i];
        size_t j = labelList.find(pattern.contLabels[i]);
        if (j != string::npos) labelList.erase(j,1);
      }
    }
  }

  // now give labels to the remaining points, starting with the one with
  // most hits
  
  int max_hits = 0;
  int max_hits_index = 0;
  while (max_hits != -1 && labelIndex < labelList.size()) {
    for(int i=0; i<pattern.sizeX*pattern.sizeY; i++) {
      if (labels[i] == '?' && continuations[i]->B + continuations[i]->W > max_hits) {
        max_hits = continuations[i]->B + continuations[i]->W;
        max_hits_index = i;
      }
    }
    if (max_hits != 0) { // found another point needing a label
      labels[max_hits_index] = labelList[labelIndex++];
      max_hits = 0;
    } else max_hits = -1; // done
  }
  return labels;
}

