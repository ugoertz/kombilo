// File: search.cpp
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
#include <sstream>
#include <stdint.h>
#include <inttypes.h>

// FIXME check for security pbms (buffer overflow) in all places where a char[] of fixed length is used! (also in other files)


unsigned long stringhash(int bs, unsigned char *str) { // returns hashcode of char[bs*bs]
  unsigned long hash = 0;
  for(int i=0; i<bs*bs; i++) hash = str[i] + (hash << 6) + (hash << 16) - hash;
  return hash;
}






Candidate::Candidate(char X, char Y, char ORIENTATION) {
  x = X;
  y = Y;
  orientation = ORIENTATION;
}

Hit::Hit(ExtendedMoveNumber* POS, char* LABEL) { // LABEL is a char[3]
  pos = POS; // note that we do not copy these!
  label = LABEL;
}

Hit::~Hit() {
  delete pos;
  delete [] label;
}

Hit::Hit(SnapshotVector& snv) {
  int length = snv.retrieve_int();
  int* data = snv.retrieve_intp();
  pos = new ExtendedMoveNumber(length, data);
  delete [] data;
  label = snv.retrieve_charp();
}

void Hit::to_snv(SnapshotVector& snv) {
  snv.pb_int(pos->length);
  snv.pb_intp(pos->data, pos->length);
  snv.pb_charp(label, 3);
}

bool Hit::cmp_pts(Hit* a, Hit* b) {
  if (a->pos->length != b->pos->length) return a->pos->length < b->pos->length;
  for(int i=0; i < a->pos->length; i++)
    if (a->pos->data[i] != b->pos->data[i]) return a->pos->data[i] < b->pos->data[i];
  return false;
}

SearchOptions::SearchOptions() {
  fixedColor = 0;
  moveLimit = 10000;
  nextMove = 0;
  trustHashFull = false;
  searchInVariations = true;
  algos = (1<<30) - 1; // use all available algorithms
}

SearchOptions::SearchOptions(int FIXEDCOLOR, int NEXTMOVE, int MOVELIMIT) {
  fixedColor = FIXEDCOLOR;
  moveLimit = MOVELIMIT;
  nextMove = NEXTMOVE;
  trustHashFull = false;
  searchInVariations = true;
  algos = (1<<30) - 1; // use all available algorithms
}

SearchOptions::SearchOptions(SnapshotVector& snv) {
  fixedColor = snv.retrieve_int();
  moveLimit = snv.retrieve_int();
  nextMove = snv.retrieve_int();
  trustHashFull = snv.retrieve_int();
  searchInVariations= snv.retrieve_int();
  algos = snv.retrieve_int();
}

void SearchOptions::to_snv(SnapshotVector& snv) {
  snv.pb_int(fixedColor);
  snv.pb_int(moveLimit);
  snv.pb_int(nextMove);
  snv.pb_int(trustHashFull);
  snv.pb_int(searchInVariations);
  snv.pb_int(algos);
}

ProcessOptions::ProcessOptions() {
  processVariations = true;
  sgfInDB = true;
  rootNodeTags = "BR,CA,DT,EV,HA,KM,PB,PC,PW,RE,RO,RU,SZ,US,WR";
  algos = ALGO_FINALPOS | ALGO_MOVELIST | ALGO_HASH_FULL | ALGO_HASH_CORNER;
  algo_hash_full_maxNumStones = 50;
  algo_hash_corner_maxNumStones = 20;
  professional_tag = 0;
}

ProcessOptions::ProcessOptions(string s) {
  int p = 0;
  if (s[p++] == 't') processVariations = true;
  else processVariations = false;

  if (s[p++] == 't') sgfInDB = true;
  else sgfInDB = false;

  professional_tag = s[p++] - (int)'0';

  p++;
  int pn = s.find('|', p) + 1;
  algos = atoi(s.substr(p, pn-p-1).c_str());
  
  p = pn;
  pn = s.find('|', p) + 1;
  algo_hash_full_maxNumStones = atoi(s.substr(p, pn-p-1).c_str());
  
  p = pn;
  pn = s.find('|', p) + 1;
  algo_hash_corner_maxNumStones = atoi(s.substr(p, pn-p-1).c_str());
  
  rootNodeTags = s.substr(pn);
}

string ProcessOptions::asString() {
  string result;
  if (processVariations) result += "t";
  else result += "f";
  if (sgfInDB) result += "t";
  else result += "f";

  char buf[200];
  sprintf(buf, "%d|%d|%d|%d|%s", professional_tag, algos, algo_hash_full_maxNumStones, algo_hash_corner_maxNumStones, rootNodeTags.c_str());
  result += buf;
  return result;
}

void ProcessOptions::validate() {
  string::iterator it = rootNodeTags.begin();
  while (it != rootNodeTags.end()) {
    if (*it == ' ') it = rootNodeTags.erase(it);
    else it++;
  }
  if (rootNodeTags.find("PB") == string::npos) rootNodeTags += ",PB";
  if (rootNodeTags.find("PW") == string::npos) rootNodeTags += ",PW";
  if (rootNodeTags.find("RE") == string::npos) rootNodeTags += ",RE";
  if (rootNodeTags.find("DT") == string::npos) rootNodeTags += ",DT";

  algos |= ALGO_FINALPOS | ALGO_MOVELIST; // these are mandatory at the moment
}

vector<string>* ProcessOptions::SGFTagsAsStrings() {
  vector<string>* SGFtags = new vector<string>;
  int ctr = 0;
  size_t p = 0;
  size_t pn = rootNodeTags.find(',', p);
  while (pn != string::npos) {
    SGFtags->push_back(rootNodeTags.substr(p,pn-p));
    ctr++;
    p = pn+1;
    pn = rootNodeTags.find(',', p);
  }
  SGFtags->push_back(rootNodeTags.substr(p));
  return SGFtags;
}

GameListEntry::GameListEntry(int ID, char WINNER, string GAMEINFOSTR, int DATE) {
  // printf("GLE %d %c %s\n", ID, WINNER, GAMEINFOSTR);
  id = ID;
  date = DATE;
  if (WINNER == 'B' || WINNER == 'b') winner = 'B';
  else if (WINNER == 'W' || WINNER == 'w') winner = 'W';
  else if (WINNER == 'J' || WINNER == 'j') winner = 'J';
  else winner = '-';
  gameInfoStr = GAMEINFOSTR;
  hits = 0;
  candidates = 0;
}

GameListEntry::~GameListEntry() {
  if (hits) {
    for(vector<Hit* >::iterator it = hits->begin(); it != hits->end(); it++) delete *it;
    delete hits;
    hits = 0;
  }
  if (candidates) {
    for(vector<Candidate* >::iterator it = candidates->begin(); it != candidates->end(); it++) delete *it;
    delete candidates;
    candidates = 0;
  }
}

void GameListEntry::hits_from_snv(SnapshotVector& snv) {
  int h_size = snv.retrieve_int();
  if (h_size==-1) hits=0;
  else {
    hits = new vector<Hit* >;
    for(int j=0; j<h_size; j++) {
      hits->push_back(new Hit(snv));
    }
  }
}

int insertEntry(void *gl, int argc, char **argv, char **azColName) {
  char winner = '-';
  if (argv[1] && (argv[1][0] == 'B' || argv[1][0] == 'W' || argv[1][0] == 'J')) winner = argv[1][0];
  else if (argv[1] && (argv[1][0] == '0')) winner = 'J';  // Officially SGF format says that Jigo should be given as RE[0].

  int date = 0;
  if (argv[2]) {
    // date is 12 * year + month - 1, where month in [1..12];
    // the string argv[2] has format YYYY-MM-DD.
    date = ((int)argv[2][0] - (int)'0')*12000 + ((int)argv[2][1] - (int)'0')*1200 + ((int)argv[2][2] - (int)'0')*120 + ((int)argv[2][3] - (int)'0')*12 + ((int)argv[2][5] - (int)'0')*10 + ((int)argv[2][6] - (int)'0') - 1;
  }

  string gameInfoStr = ((GameList*)gl)->format2;
  for(int i=0; i<((GameList*)gl)->numColumns; i++) {
    char strpip1[20];
    sprintf(strpip1, "[[%d[[F", i);
    size_t p = gameInfoStr.find(strpip1);
    if (p != string::npos) {
      if (argv[i]) {
        string fn = argv[i];
        if (fn.size() >= 4 && (fn.substr(fn.size()-4) == ".sgf" || fn.substr(fn.size()-4) == ".mgt")) // BUGFIX Claude Brisson
          gameInfoStr.replace(p, strlen(strpip1), fn.substr(0,fn.size()-4));
        else gameInfoStr.replace(p, strlen(strpip1), fn);
      } else gameInfoStr.erase(gameInfoStr.find(strpip1), strlen(strpip1));
      continue;
    }

    sprintf(strpip1, "[[%d", i);
    p = gameInfoStr.find(strpip1);
    if (p != string::npos) {
      if (argv[i]) gameInfoStr.replace(p, strlen(strpip1), argv[i]);
      else gameInfoStr.erase(gameInfoStr.find(strpip1), strlen(strpip1));
    }
  }
  size_t p = gameInfoStr.find("[[W");
  if (p != string::npos) gameInfoStr.replace(p, 3, 1, winner);

  // printf("id %s\n", argv[0]);
  ((GameList*)gl)->all->push_back(new GameListEntry(atoi(argv[0]), winner, gameInfoStr, date));
  if (date >= DATE_PROFILE_START*12) ((GameList*)gl)->dates_all[date - DATE_PROFILE_START*12]++; // January of year DATE_PROFILE_START is 0; everything before is ignored
  return 0;
}

int dbinfo_callback(void *s, int argc, char **argv, char **asColName) {
  char** cpp = (char**)s;
  if (argc && argv[0]) {
    // printf("dbi_cb %s\n", argv[0]);
    *cpp = new char[strlen(argv[0])+1];
    strcpy(*cpp, argv[0]);
  }
  return 0;
}


GameList::GameList(const char* DBNAME, string ORDERBY, string FORMAT, ProcessOptions* p_options, int BOARDSIZE, int cache) throw(DBError) {
  boardsize = BOARDSIZE;
  labels = 0;
  mrs_pattern = 0;
  searchOptions = 0;
  dbname = new char[strlen(DBNAME)+1];
  strcpy(dbname, DBNAME);
  db = 0;

  // try to retrieve basic options from database
  int rc = sqlite3_open(dbname, &db); 
  if (rc) {
    sqlite3_close(db);
    db = 0;
    throw DBError();
  }
  rc = sqlite3_busy_timeout(db, 200);
  if (rc) throw DBError();
  rc = sqlite3_exec(db, "pragma synchronous = off;", 0, 0, 0);
  if (rc) throw DBError();
  char cache_str[100];
  sprintf(cache_str, "pragma cache_size = %d", cache*1000);
  rc = sqlite3_exec(db, cache_str, 0, 0, 0);
  if (rc) throw DBError();

  rc = sqlite3_exec(db, "create table if not exists db_info ( info text );", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
  char* dbinfo = 0;

  // check whether this is a kombilo db file
  rc = sqlite3_exec(db, "select * from db_info where rowid = 1;", dbinfo_callback, &dbinfo, 0);
  if (rc != SQLITE_OK) throw DBError();
  if (dbinfo) {
    if (strcmp(dbinfo, "kombilo 0.7") && strcmp(dbinfo, "kombilo 0.8")) throw DBError();
    delete [] dbinfo;
  }

  rc = sqlite3_exec(db, "select * from db_info where rowid = 2;", dbinfo_callback, &dbinfo, 0);
  if (rc != SQLITE_OK) throw DBError();

  if (dbinfo) {
    // printf("dbinfo: %s\n", dbinfo);
    p_op = new ProcessOptions(dbinfo);
    delete [] dbinfo;
    char* bsizes = 0;
    rc = sqlite3_exec(db, "select * from db_info where rowid = 3;", dbinfo_callback, &bsizes, 0);
    if (rc != SQLITE_OK) throw DBError();
    if (bsizes) {
      boardsize = atoi(bsizes);
      delete [] bsizes;
    }
    addAlgos(0);
  } else { // if this does not work: create database and read p_options (or use defaults)
    // printf("retrieving dbinfo failed\n");

    // write version information to db_info
    rc = sqlite3_exec(db, "insert into db_info (rowid,info) values (1,'kombilo 0.8')", 0, 0, 0);

    if (p_options == 0) p_op = new ProcessOptions(); // use default values
    else {
      // printf("use p_options\n");
      p_op = new ProcessOptions(*p_options);
      p_op->validate(); // make sure the most important information is contained in rootNodeTags list
    }
    string sql = "insert into db_info (rowid,info) values (2,'";
    sql += p_op->asString();
    sql += "');";
    rc = sqlite3_exec(db, sql.c_str(), 0, 0, 0);
    if (rc != SQLITE_OK) throw DBError();
    sql = "insert into db_info (rowid, info) values (3, '";
    char buf[5];
    sprintf(buf, "%d", boardsize);
    sql += buf;
    sql += "');";
    rc = sqlite3_exec(db, sql.c_str(), 0, 0, 0);
    if (rc != SQLITE_OK) throw DBError();

    addAlgos(1);
  }

  // set up snapshot db
  rc = sqlite3_exec(db, "create table if not exists snapshots ( data text );", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();

  all = 0;
  for(int i = 0; i < (DATE_PROFILE_END - DATE_PROFILE_START)*12; i++) dates_all.push_back(0);
  for(int i = 0; i < DATE_PROFILE_END - DATE_PROFILE_START + 1; i++) dates_all_per_year.push_back(0);
  currentList = oldList = 0;
  resetFormat(ORDERBY, FORMAT);
  // printf("dapy size %d expected %d\n", dates_all_per_year.size(), DATE_PROFILE_END - DATE_PROFILE_START + 1);
  // printf("done\n");
}

void GameList::resetFormat(string ORDERBY, string FORMAT) {
  // printf("enter resetFormat\n");
  if (FORMAT == "") { // use default format string
    numColumns = 5;
    format1 = "id,re,date,pw,pb,dt";
    format2 = "[[3 - [[4 ([[W), [[5, ";
  } else {
    char buf[10];
    format1 = "id,re,date";
    numColumns = 3; // 3 columns already assigned
    format2 = FORMAT;
    size_t p = 0;
    size_t q = 0;
    while (p != string::npos) {
      p = format2.find("[[",p);
      q = format2.find("]]",p);
      if (p+2 < format2.size() && q != string::npos) {
        string col = format2.substr(p+2, q-p-2);
        // check availability
        if (col == "id" || col == "filename" || col == "pos" || col == "duplicate" || p_op->rootNodeTags.find(col) != string::npos) {
          sprintf(buf, "[[%d", numColumns++); 
          format2.replace(p,q+2-p, buf);
          format1 += ",";
          format1 += col;
        } else if (col == "winner") {
          format2.replace(p,q+2-p, "[[W");
        } else if (col == "date") {
          format2.replace(p,q+2-p, "[[2");
        } else if (col == "filename.") {
          sprintf(buf, "[[%d[[F", numColumns++); 
          format2.replace(p, q+2-p, buf);
          format1 += ",filename";
          p += 4;
        }
        p++;
      } else break;
    }
  }
  if (ORDERBY == "" || ORDERBY == "id" || ORDERBY == "ID" || ORDERBY == "Id" || ORDERBY == "iD") orderby = "id";
  else orderby = ORDERBY + ",id";
  // printf("finished parsing\n");

  readDB();
}


void GameList::addAlgos(bool NEW) {
  // create algo pointers; if not new, read data from file
  // FIXME be more careful in validating input ...

  // printf("add algos %d %d %d\n", bs, ctr, p_op->algos);
  for(int i=0; i<20; i++) algo_ps.push_back(0);
  
  string a_dbname(dbname);
  a_dbname[a_dbname.size()-1] = 'a';
  ifstream is(a_dbname.c_str(), ios::binary);
  string dbname_str(dbname);

  if (NEW) {
    algo_ps[0] = new Algo_signature(boardsize, SnapshotVector());
    if (p_op->algos & ALGO_FINALPOS) algo_ps[algo_finalpos] = new Algo_finalpos(boardsize, SnapshotVector());
    if (p_op->algos & ALGO_MOVELIST) algo_ps[algo_movelist] = new Algo_movelist(boardsize, SnapshotVector());
    if (p_op->algos & ALGO_HASH_FULL) algo_ps[algo_hash_full] = new Algo_hash_full(boardsize, SnapshotVector(), dbname_str+"1", p_op->algo_hash_full_maxNumStones);
    if (p_op->algos & ALGO_HASH_CORNER) algo_ps[algo_hash_corner] = new Algo_hash_corner(boardsize, SnapshotVector(), dbname_str+"2", 7, p_op->algo_hash_corner_maxNumStones);
  } else {
    // printf("read algo db\n");
    size_t si;
    { is.read((char *)&si, sizeof(si));
      // printf("read algo db %lld\n", si);
      char* d = new char[si];
      is.read(d, si);
      SnapshotVector data(d, si);
      delete [] d;
      algo_ps[0] = new Algo_signature(boardsize, data);
    }
    if (p_op->algos & ALGO_FINALPOS) {
      is.read((char *)&si, sizeof(si));
      // printf("read algo db %lld\n", si);
      char* d = new char[si];
      is.read(d, si);
      SnapshotVector data(d, si);
      delete [] d;
      algo_ps[algo_finalpos] = new Algo_finalpos(boardsize, data);
    }
    if (p_op->algos & ALGO_MOVELIST) {
      is.read((char *)&si, sizeof(si));
      // printf("read algo db %lld\n", si);
      char* d = new char[si];
      is.read(d, si);
      SnapshotVector data(d, si);
      delete [] d;
      algo_ps[algo_movelist] = new Algo_movelist(boardsize, data);
    }
    if (p_op->algos & ALGO_HASH_FULL) {
      is.read((char *)&si, sizeof(si));
      // printf("read algo db %lld\n", si);
      char* d = new char[si];
      is.read(d, si);
      SnapshotVector data(d, si);
      delete [] d;
      algo_ps[algo_hash_full] = new Algo_hash_full(boardsize, data, dbname_str+"1", p_op->algo_hash_full_maxNumStones);
    }
    if (p_op->algos & ALGO_HASH_CORNER) {
      is.read((char *)&si, sizeof(si));
      // printf("read algo db %lld\n", si);
      char* d = new char[si];
      is.read(d, si);
      SnapshotVector data(d, si);
      delete [] d;
      algo_ps[algo_hash_corner] = new Algo_hash_corner(boardsize, data, dbname_str+"2", 7, p_op->algo_hash_corner_maxNumStones);
    }
  }
  // for(int a=20*ctr; a<20*(ctr+1); a++) printf("aa %d %p\n", a, algo_ps[a]);
  // if (algos & ALGO_HASH_SIDE) 
  //   algo_ps[algo_hash_side] = new Algo_hash_side(boardsize, 6, 4, p_op->algo_hash_side_maxNumStones);
}

void GameList::readDB() throw(DBError) {
  // printf("read dbs\n");
  if (oldList) delete oldList;
  if (currentList) delete currentList;
  if (all) {
    for(vector<GameListEntry* >::iterator it = all->begin(); it != all->end(); it++)
      delete *it;
    delete all;
  }
  current = -1;
  all = new vector<GameListEntry* >;
  currentList = 0;
  oldList = 0;

  int rc;
  rc = sqlite3_exec(db, "begin transaction;", 0, 0, 0);
  if (rc) throw DBError();

  string sql = "select ";
  sql += format1;
  sql += " from GAMES order by ";
  sql += orderby;
  // printf("sql: %s\n", sql.c_str());
  rc = sqlite3_exec(db, sql.c_str(), insertEntry, this, 0);
  if (rc != SQLITE_OK && rc != SQLITE_ERROR) {
    throw DBError(); 
  }
  // printf("read.\n");
  // SQLITE_ERROR may occur since table might not yet exist

  for(int i=0; i < (DATE_PROFILE_END - DATE_PROFILE_START); i++) {
    int sum = 0;
    for(int j = 0; j < 12; j++)
      sum += dates_all[i * 12 + j];
    dates_all_per_year[i] = sum;
    // printf("dapy %d\n", dates_all_per_year[i]);
  }
  readPlayersList();
  readNumOfWins();
  rc = sqlite3_exec(db, "commit;", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
  // printf("read.\n");

  reset();
  // printf("leave readDB\n");
}

GameList::~GameList() {
  // printf("enter ~GameList\n");
  if (mrs_pattern) delete mrs_pattern;
  if (searchOptions) delete searchOptions;
  if (p_op) delete p_op;
  if (labels) delete [] labels;
  for (std::vector<Continuation *>::const_iterator i = continuations.begin(); i != continuations.end(); ++i) {
    delete *i;
  }

  delete [] dbname;
  if (all) {
    for(vector<GameListEntry* >::iterator it = all->begin(); it != all->end(); it++)
      delete *it;
    delete all;
  }
  if (currentList) delete currentList;
  if (oldList) delete oldList;
  for(unsigned int i=0; i<20; i++) 
    if (algo_ps[i]) delete algo_ps[i];
  if (db) sqlite3_close(db);
  db = 0;
  // printf("leave ~GameList\n");
}


int GameList::start() {
  current = 0;
  if (oldList) delete oldList;
  oldList = currentList;
  currentList = new vector<pair<int,int> >;
  if (oldList && oldList->size()) return (*oldList)[0].first;
  else {
    if (oldList) delete oldList;
    oldList = 0;
    return -1;
  }
}

int GameList::startO() {
  current = 0;
  if (oldList) delete oldList;
  oldList = currentList;
  currentList = new vector<pair<int,int> >;
  return oldList->size();
}

int GameList::next() {
  current++;
  if (current < (int)oldList->size()) return (*oldList)[current].first;
  else {
    if (oldList) delete oldList;
    oldList = 0;
    return -1;
  }
}

bool sndcomp(const pair<int,int>& a, const pair<int,int>& b) {
  return a.second < b.second;
}

int GameList::start_sorted() {
  current = 0;
  if (oldList) delete oldList;
  oldList = currentList;
  currentList = new vector<pair<int,int> >;
  if (!oldList || !oldList->size()) {
    if (oldList) delete oldList;
    oldList = 0;
    return -1;
  }
  sort(oldList->begin(), oldList->end());
  return 0;
}

int GameList::end_sorted() {
  sort(currentList->begin(), currentList->end(), sndcomp);
  delete oldList;
  oldList = 0;
  Bwins = Wwins = 0;
  for(vector<pair<int,int> >::iterator it = currentList->begin(); it != currentList->end(); it++) {
    if ((*all)[it->second]->winner == 'B') Bwins++;
    if ((*all)[it->second]->winner == 'W') Wwins++;
  }
  return 0;
}

void GameList::update_dates_current() {
  dates_current.clear();
  for(int i=0; i<(DATE_PROFILE_END - DATE_PROFILE_START)*12; i++) dates_current.push_back(0);
  for(vector<pair<int,int> >::iterator it = currentList->begin(); it != currentList->end(); it++) {
    if ((*all)[it->second]->date >= DATE_PROFILE_START*12) dates_current[(*all)[it->second]->date - DATE_PROFILE_START*12]++;
  }
}

char GameList::getCurrentWinner() {
  return (*all)[(*oldList)[current].second]->winner;
}

int GameList::getCurrentDate() {
  return (*all)[(*oldList)[current].second]->date;
}

vector<Candidate* > * GameList::getCurrentCandidateList() {
  return (*all)[(*oldList)[current].second]->candidates;
}

void GameList::makeCurrentCandidate(vector<Candidate* > * candidates) {
  GameListEntry* gle = (*all)[(*oldList)[current].second];
  if (gle->candidates) delete gle->candidates;
  gle->candidates = candidates;
  currentList->push_back((*oldList)[current]);
}

void GameList::makeCurrentHit(vector<Hit* > * hits) {
  GameListEntry* gle = (*all)[(*oldList)[current].second];
  if (gle->hits) delete gle->hits;
  gle->hits = hits;
  sort(gle->hits->begin(), gle->hits->end(), Hit::cmp_pts);
  currentList->push_back((*oldList)[current]);
}

void GameList::setCurrentFromIndex(int index) {
  int start = current;
  int end = oldList->size();
  int m = start;
  while (start < end) {
    m = (end+start)/2;
    if (index == (*oldList)[m].first) {
      break;
    } else {
      if (index < (*oldList)[m].first) end = m;
      else start = m+1;
    }
  }
  current = m;
}

void GameList::makeIndexHit(int index, vector<Hit* > * hits, vector<int>* CL) {
  int m = get_current_index(index, &current);
  if (m != -1) {
    if (CL)
      CL->push_back(m);
    else {
      currentList->push_back((*oldList)[m]);
      if (hits) {
        if ((*all)[(*oldList)[m].second]->hits) delete (*all)[(*oldList)[m].second]->hits;
        (*all)[(*oldList)[m].second]->hits = hits;
      }
    }
  }
}

void GameList::makeIndexCandidate(int index, vector<Candidate* > * candidates) {
  int m = get_current_index(index, &current);
  if (m != -1) {
    currentList->push_back((*oldList)[m]);
    if (candidates) {
      if ((*all)[(*oldList)[m].second]->candidates) delete (*all)[(*oldList)[m].second]->candidates;
      (*all)[(*oldList)[m].second]->candidates = candidates;
    }
  }
}


void GameList::reset() {
  if (oldList) delete oldList;
  oldList = 0;
  if (currentList) delete currentList;
  currentList = new vector<pair<int,int> >;
  int counter = 0;
  for(vector<GameListEntry* >::iterator it = all->begin(); it != all->end(); it++) {
    if ((*it)->hits) {
      for(vector<Hit* >::iterator ith = (*it)->hits->begin(); ith != (*it)->hits->end(); ith++)
        delete *ith;
      delete (*it)->hits;
      (*it)->hits = 0;
    }
    if ((*it)->candidates) {
      for(vector<Candidate* >::iterator itc = (*it)->candidates->begin(); itc != (*it)->candidates->end(); itc++)
        delete *itc;
      delete (*it)->candidates;
      (*it)->candidates = 0;
    }
    currentList->push_back(make_pair((*it)->id, counter++));
  }
  num_hits = 0;
  num_switched = 0;
  Bwins = BwinsAll;
  Wwins = WwinsAll;
  dates_current.clear();
  for(int i = 0; i < (DATE_PROFILE_END - DATE_PROFILE_START)*12; i++) dates_current.push_back(dates_all[i]);
}

void GameList::tagsearch(int tag) throw(DBError) {
  char sql[200];

  if (!tag) return;
  if (tag > 0) {
    sprintf(sql, "select GAMES.id from GAMES join game_tags on GAMES.id = game_tags.game_id where game_tags.tag_id = %d order by GAMES.id", tag);
    // use join here to make sure we only get IDs from GAMES (does not seem necessary, if game_tags is always updated correctly - but this way we are on the safe side)
  } else {
    sprintf(sql, "select GAMES.id from GAMES except select GAMES.id from GAMES join game_tags on GAMES.id = game_tags.game_id where game_tags.tag_id = %d order by GAMES.id;", -tag);
  }
  gisearch(sql, 1);
}


void GameList::export_tags(string tag_db_name, vector<int> which_tags) {
  // build list of tags to be included as string
  string which = "(";
  if (which_tags.size()) {
    stringstream out;
    vector<int>::iterator it = which_tags.begin();
    out << *it;
    it++;

    for(; it != which_tags.end(); it++) {
      out << ", " << *it;
    }
    which += out.str() + ")";
  }
  // printf("export tags %s\n", which.c_str());
  
  // open db
  sqlite3* tag_db;
  int rc = sqlite3_open(tag_db_name.c_str(), &tag_db); 
  if (rc) {
    sqlite3_close(tag_db);
    throw DBError();
  }
  rc = sqlite3_busy_timeout(tag_db, 200);
  if (rc) {  throw DBError(); }
  rc = sqlite3_exec(tag_db, "pragma synchronous = off;", 0, 0, 0);
  if (rc) {  throw DBError(); }

  // add all tags that are in current db to tag db
  rc = sqlite3_exec(tag_db,
                    "create table if not exists TAGS ( id integer primary key, signature text, fphash integer, tag_id integer, unique(signature, fphash, tag_id) );",
                    0, 0, 0);
  if (rc != SQLITE_OK) {  throw DBError(); }

  char *sql = new char[100+strlen(dbname)];
  sprintf(sql, "attach '%s' as g1;", dbname);
  rc = sqlite3_exec(tag_db, sql, 0, 0, 0);
  if (rc != SQLITE_OK) {  throw DBError(); }
  delete [] sql;

  // write tags into tags db
  if (which_tags.size()) {
    char* sql1 = new char[250+which.size()]; 
    sprintf(sql1, "insert or ignore into TAGS (signature, fphash, tag_id) select g1.GAMES.signature, g1.GAMES.fphash, g1.GAME_TAGS.tag_id from g1.GAMES join g1.GAME_TAGS on g1.GAMES.id = g1.GAME_TAGS.game_id where g1.GAME_TAGS.tag_id in %s;", which.c_str());
    rc = sqlite3_exec(tag_db, sql1, 0, 0, 0);
    delete [] sql1;
  } else
    rc = sqlite3_exec(tag_db, "insert or ignore into TAGS (signature, fphash, tag_id) select g1.GAMES.signature, g1.GAMES.fphash, g1.GAME_TAGS.tag_id from g1.GAMES join g1.GAME_TAGS on g1.GAMES.id = g1.GAME_TAGS.game_id", 0, 0, 0);

  if (rc!=SQLITE_OK) {  throw DBError(); }

  rc = sqlite3_exec(tag_db, "detach g1;", 0, 0, 0);
  if (rc != SQLITE_OK) {  throw DBError(); }

  // close db
  sqlite3_close(tag_db);
}


void GameList::import_tags(string tag_db_name) {
  // open db
  sqlite3* tag_db;
  int rc = sqlite3_open(tag_db_name.c_str(), &tag_db); 
  if (rc) {
    sqlite3_close(tag_db);
    throw DBError();
  }
  rc = sqlite3_busy_timeout(tag_db, 200);
  if (rc) { throw DBError(); }
  rc = sqlite3_exec(tag_db, "pragma synchronous = off;", 0, 0, 0);
  if (rc) { throw DBError(); }

  // add all tags from tag_db to db.GAME_TAGS

  char *sql = new char[200+strlen(dbname)];
  sprintf(sql, "attach '%s' as g1;", dbname);
  rc = sqlite3_exec(tag_db, sql, 0, 0, 0);
  if (rc != SQLITE_OK) { throw DBError(); }
  rc = sqlite3_exec(tag_db, "insert or ignore into g1.GAME_TAGS (game_id, tag_id) select g1.GAMES.id, tags.tag_id from tags join g1.GAMES on g1.GAMES.signature = tags.signature and g1.GAMES.fphash = tags.fphash;", 0, 0, 0);
  if (rc!=SQLITE_OK) { throw DBError(); }
  rc = sqlite3_exec(tag_db, "detach g1;", 0, 0, 0);
  if (rc != SQLITE_OK) { throw DBError(); }

  // close db
  sqlite3_close(tag_db);
}



void GameList::tagsearchSQL(char* query) throw(DBError) {
  char sql[1000];

  sprintf(sql, "select GAMES.id from GAMES where %s order by GAMES.id", query);
  gisearch(sql, 1);
}

void GameList::setTagID(int tag, int i) throw(DBError) {
  int rc = sqlite3_exec(db, "begin transaction", 0, 0, 0);
  if (rc != SQLITE_OK) {
    throw DBError();
  }
  if (!getTagsID(i, tag).size()) {
    char sql[200];
    sprintf(sql, "insert or ignore into GAME_TAGS (game_id, tag_id) values (%d, %d)", i, tag);  // uniqueness ascertained by corresponding constraint in db
    rc = sqlite3_exec(db, sql, 0, 0, 0);
    if (rc != SQLITE_OK) {
      // printf("settagid: %d %d %d\n", i, tag, rc);
      throw DBError();
    }
  }
  rc = sqlite3_exec(db, "commit", 0, 0, 0);
  if (rc != SQLITE_OK) {
    throw DBError();
  }
}

void GameList::setTag(int tag, int start, int end) throw(DBError) {
  if (end==0) end = start+1;
  if (start>end || end > (int)currentList->size()) return;
  int rc = sqlite3_exec(db, "begin transaction", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
  for(int i = start; i < end; i++) {
    if (getTags(i, tag).size()) continue;
    char sql[200];
    sprintf(sql, "insert or ignore into GAME_TAGS (game_id, tag_id) values (%d, %d)", (*all)[(*currentList)[i].second]->id, tag);
    // uniqueness ascertained by corresponding constraint in db
    rc = sqlite3_exec(db, sql, 0, 0, 0);
    if (rc != SQLITE_OK) throw DBError();
  }
  rc = sqlite3_exec(db, "commit", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
}

void GameList::deleteTag(int tag, int i) throw(DBError) {
  char sql[200];
  if (i == -1) sprintf(sql, "delete from game_tags where tag_id=%d", tag);
  else sprintf(sql, "delete from game_tags where game_id=%d and tag_id=%d", (*all)[(*currentList)[i].second]->id, tag);
  int rc = sqlite3_exec(db, sql, 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
}

int gettags_callback(void *res, int argc, char **argv, char **azColName) {
  if (!argc) return 1;
  ((vector<int>*)res)->push_back(atoi(argv[0]));
  return 0;
}

vector<int> GameList::getTagsID(int i, int tag) throw(DBError) {
  vector<int> result;
  char sql[200];
  if (tag==0) sprintf(sql, "select tag_id from game_tags where game_id=%d order by tag_id", i);
  else sprintf(sql, "select tag_id from game_tags where game_id=%d and tag_id=%d", i, tag);
  int rc = sqlite3_exec(db, sql, gettags_callback, &result, 0);
  if (rc != SQLITE_OK) throw DBError();
  return result;
}

vector<int> GameList::getTags(unsigned int i, int tag) throw(DBError) {
  vector<int> result;
  if (i < 0 || i >= currentList->size()) return result;
  char sql[200];
  if (tag==0) sprintf(sql, "select tag_id from game_tags where game_id=%d order by tag_id", (*all)[(*currentList)[i].second]->id);
  else sprintf(sql, "select tag_id from game_tags where game_id=%d and tag_id=%d", (*all)[(*currentList)[i].second]->id, tag);
  int rc = sqlite3_exec(db, sql, gettags_callback, &result, 0);
  if (rc != SQLITE_OK) throw DBError();
  return result;
}


int GameList::get_current_index(int id, int* start) {
  // use this in between start_sorted() and end_sorted() only!
  int end = oldList->size();
  int m = *start;
  while (*start < end) {
    m = (end+*start)/2;
    if (id == (*oldList)[m].first) {
      *start = m;
      return m;
    } else {
      if (id < (*oldList)[m].first) end = m;
      else *start = m+1;
    }
  }
  return -1; 
}


void GameList::sigsearch(char* sig) throw(DBError) {
  if (start_sorted() == 0) { 
    vector<int> result = sigsearchNC(sig);
    for(vector<int>::iterator it = result.begin(); it != result.end(); it++) {
      makeIndexHit(*it, 0);
    }
    end_sorted();
    update_dates_current();
  }
}



vector<int> GameList::sigsearchNC(char* sig) throw(DBError) {
  vector<int> result;
  int rc;
  sqlite3_stmt *ppStmt=0;

  // first prepare sql statement; need some case distinction
  bool sig_contains_wildcards = false;
  for(int i=0; i<12; i++) {
    if (sig[i] == '_') {
      sig_contains_wildcards = true;
      break;
    }
  }

  if (sig_contains_wildcards) { // if sig contains wildcards, then need to search for all flipped sigs --- this could be refined: if wildcards occur only in final positions s.t. flip giving symmetrized sig is unique, could use symmetrized sig
    string query = "select id from GAMES where signature like ? or signature like ? or signature like ? or signature like ? or signature like ? or signature like ? or signature like ? or signature like ? order by id";
    char** sigs = new char*[8];
    for (int f=0; f<8; f++) sigs[f] = flipped_sig(f, sig, boardsize);
    rc = sqlite3_prepare(db, query.c_str(), -1, &ppStmt, 0);
    if (rc != SQLITE_OK || ppStmt==0) throw DBError();
    for (int f=0; f<8; f++) {
      rc = sqlite3_bind_text(ppStmt, f+1, sigs[f], 12, SQLITE_TRANSIENT);
      if (rc != SQLITE_OK || ppStmt==0) throw DBError();
    }
    for (int f=0; f<8; f++) delete [] sigs[f];
    delete [] sigs;
  } else { // no wildcards, so we just search for the symmetrized signature
    char* symmetrized_sig = symmetrize(sig, boardsize);
    string query = "select id from GAMES where signature like ? order by id";
    rc = sqlite3_prepare(db, query.c_str(), -1, &ppStmt, 0);
    if (rc != SQLITE_OK || ppStmt==0) throw DBError();
    rc = sqlite3_bind_text(ppStmt, 1, symmetrized_sig, 12, SQLITE_TRANSIENT);
    if (rc != SQLITE_OK || ppStmt==0) throw DBError();
    delete [] symmetrized_sig;
  }

  // now do the search
  do {
    rc = sqlite3_step(ppStmt);
    if (rc != SQLITE_DONE && rc != SQLITE_ROW) throw DBError();
    if (rc == SQLITE_ROW) result.push_back(sqlite3_column_int(ppStmt, 0));
  } while (rc == SQLITE_ROW);
  rc = sqlite3_finalize(ppStmt);
  if (rc != SQLITE_OK) throw DBError();

  // clean up

  return result;
}

int gis_callback(void *gl, int argc, char **argv, char **azColName) {
  if (!argc) return 1;
  ((GameList*)gl)->makeIndexHit(atoi(argv[0]), 0);
  return 0;
}

void GameList::gisearch(const char* sql, int complete) throw(DBError) {
  if (start_sorted() == 0) { 
    string query;
    if (!complete) query = "select id from GAMES where ";
    query += sql;
    if (!complete) query += " order by id";
    // printf("%s\n", query.c_str());
    int rc = sqlite3_exec(db, query.c_str(), gis_callback, this, 0);
    if( rc!=SQLITE_OK ) throw DBError();

    end_sorted();
    update_dates_current();
  }
}


int gis_callbackNC(void *pair_gl_CL, int argc, char **argv, char **azColName) {
  if (!argc) return 1;
  pair<GameList*, vector<int>* >* pp = (pair<GameList*, vector<int>* >*)pair_gl_CL;
  pp->first->makeIndexHit(atoi(argv[0]), 0, pp->second);
  return 0;
}

vector<int>* GameList::gisearchNC(const char* sql, int complete) throw(DBError) {
  current = 0;
  if (oldList) delete oldList;
  oldList = new vector<pair<int,int> >;
  for(vector<pair<int, int> >::iterator it = currentList->begin(); it != currentList->end(); it++)
    oldList->push_back(*it);
  if (!oldList || !oldList->size()) {
    if (oldList) delete oldList;
    oldList = 0;
    return new vector<int>;
  }
  sort(oldList->begin(), oldList->end());

  vector<int>* CL = new vector<int>;
  string query;
  if (!complete) query = "select id from GAMES where ";
  query += sql;
  if (!complete) query += " order by id";
  // printf("%s\n", query.c_str());
  pair<GameList*, vector<int>* >* pp = new pair<GameList*, vector<int>* >(this, CL);
  int rc = sqlite3_exec(db, query.c_str(), gis_callbackNC, pp, 0);
  if( rc!=SQLITE_OK ) throw DBError();
  delete pp;

  sort(CL->begin(), CL->end());
  delete oldList;
  oldList = 0;
  return CL;
}

int GameList::numHits() {
  return num_hits;
}

int GameList::size() {
  return currentList->size();
}

int GameList::size_all() {
  return all->size();
}

string GameList::resultsStr(GameListEntry* gle) {
  string result;
  if (!gle->hits) return result;
  char buf[20];
  result.reserve(gle->hits->size()*8);
  for(vector<Hit* >::iterator it = gle->hits->begin(); it != gle->hits->end(); it++) {
    sprintf(buf, "%d", (*it)->pos->data[0]);
    result += buf;
    for(int i=1; i<(*it)->pos->length; i++) {
      sprintf(buf, "-%d", (*it)->pos->data[i]);
      result += buf;
    }
    if ((*it)->label[0] != NO_CONT) {
      char lb = lookupLabel((*it)->label[0], (*it)->label[1]); // coordinates of Hit
      if ('0' <= lb && lb <= '9') result += '@';
      result += lb;
    }
    if ((*it)->label[2]) result += "-, ";
    else result += ", ";
  }
  return result;
}

void GameList::setLabel(char x, char y, char label) {
  if (!labels || !mrs_pattern || x < 0 || x >= mrs_pattern->sizeX || y < 0 || y >= mrs_pattern->sizeY) return;
  labels[x+y*mrs_pattern->sizeX] = label;
}

char GameList::lookupLabel(char x, char y) {
  if (!labels || !mrs_pattern || x < 0 || x >= mrs_pattern->sizeX || y < 0 || y >= mrs_pattern->sizeY) return '?';
  return labels[x+y*mrs_pattern->sizeX];
}

Continuation GameList::lookupContinuation(char x, char y) {
  if (!continuations.size() || !mrs_pattern || x < 0 || x >= mrs_pattern->sizeX || y < 0 || y >= mrs_pattern->sizeY) return Continuation(this);
  return *continuations[x+y*mrs_pattern->sizeX];
}

vector<string> GameList::currentEntriesAsStrings(int start, int end) {
  if (end==0) end = currentList->size();
  vector<string> result;
  if (start>end || end > (int)currentList->size()) return result;
  for(int i=start; i<end; i++) {
    result.push_back((*all)[(*currentList)[i].second]->gameInfoStr + resultsStr((*all)[(*currentList)[i].second]));
  }
  return result;
}

string GameList::currentEntryAsString(int i) {
  if (i < 0 || i >= (int)currentList->size()) {
    return "";
  } else return (*all)[(*currentList)[i].second]->gameInfoStr + resultsStr((*all)[(*currentList)[i].second]);
}

int getpropcallback(void *s, int argc, char **argv, char **azColName) {
  char** prop = (char**)s;
  if (argc && argv[0]) {
    *prop = new char[strlen(argv[0])+1];
    strcpy(*prop, argv[0]);
  }
  return 0;
}

string GameList::getSignature(int i) throw(DBError) {
  if (i < 0 || i >= (int)currentList->size()) {
    // printf("index out of range\n");
    return "";
  }
  int index = (*all)[(*currentList)[i].second]->id;
  char* prop = 0;
  char sql[200];
  sprintf(sql, "select signature from GAMES where id = %d;", index);
  // printf("%s\n", sql);
  int rc = sqlite3_exec(db, sql, getpropcallback, &prop, 0);
  if (rc != SQLITE_OK) throw DBError();

  if (!prop) throw DBError();
  string prop_str(prop);
  delete [] prop;
  return prop_str;
}

string GameList::getSGF(int i) throw(DBError) {
  if (!p_op->sgfInDB) return "";
  return getCurrentProperty(i, "sgf");
}

string GameList::getCurrentProperty(int i, string tag) throw(DBError) {
  if (i < 0 || i >= (int)currentList->size()) {
    // printf("index out of range\n");
    return "";
  }
  int index = (*all)[(*currentList)[i].second]->id;
  char* prop = 0;
  char sql[200];
  sprintf(sql, "select %s from GAMES where id = %d;", tag.c_str(), index);
  // printf("%s\n", sql);
  int rc = sqlite3_exec(db, sql, getpropcallback, &prop, 0);
  if (rc != SQLITE_OK) throw DBError();

  if (!prop) return "";
  string prop_str(prop);
  delete [] prop;
  return prop_str;
}

void GameList::search(Pattern& pattern, SearchOptions* so) throw(DBError) {
  if (mrs_pattern) delete mrs_pattern;
  mrs_pattern = new Pattern(pattern);
  if (searchOptions) delete searchOptions;
  if (so) searchOptions = new SearchOptions(*so);
  else searchOptions = new SearchOptions();
  PatternList pl(pattern, searchOptions->fixedColor, searchOptions->nextMove, this);

  if (boardsize != pattern.boardsize) {
    delete searchOptions;
    searchOptions = 0;
    if (oldList) delete oldList;
    oldList = 0;
    if (currentList) delete currentList;
    currentList = new vector<pair<int,int> >;
    return;
  }

  int hash_result = -1;
  // FULL BOARD PATTERN?
  if ((searchOptions->algos & ALGO_HASH_FULL) && pattern.sizeX==pattern.boardsize && pattern.sizeY==pattern.boardsize && algo_ps[algo_hash_full]) {
    hash_result = ((Algo_hash_full*)algo_ps[algo_hash_full])->search(pl, *this, *searchOptions);
    // printf("hash result %d\n", hash_result);
    if (hash_result == 1) {
      // hashing worked and fullboard hash algorithm is trusted
    } else if (hash_result == 0) {
      // hashing worked, but we will check with algo_movelist
      if (searchOptions->algos & ALGO_MOVELIST && algo_ps[algo_movelist])
        algo_ps[algo_movelist]->search(pl, *this, *searchOptions);
    }
  }
  if (hash_result == -1) { // not a full board pattern (or not hashable)
    // printf("hr -1\n");

    // CORNER PATTERN?
    if ((searchOptions->algos & ALGO_HASH_CORNER) && algo_ps[algo_hash_corner]) {
      hash_result = ((Algo_hash_corner*)algo_ps[algo_hash_corner])->search(pl, *this, *searchOptions);
      if (hash_result == 0) {
        // printf("use hash corner\n");
        if (searchOptions->algos & ALGO_MOVELIST && algo_ps[algo_movelist])
          algo_ps[algo_movelist]->search(pl, *this, *searchOptions);
        // printf("%d candidates\n", oldList->size());
      }
    }

    if (hash_result == -1) {
      // printf("no hashing\n");
      if (searchOptions->algos & ALGO_FINALPOS && algo_ps[algo_finalpos])
        algo_ps[algo_finalpos]->search(pl, *this, *searchOptions);
      // printf("%d candidates\n", currentList->size());
      if (searchOptions->algos & ALGO_MOVELIST && algo_ps[algo_movelist])
        algo_ps[algo_movelist]->search(pl, *this, *searchOptions);
    }
  }
  if (labels) delete [] labels;
  labels = pl.sortContinuations();
  for(vector<Continuation* >::iterator it = continuations.begin(); it != continuations.end(); it++)
    delete *it;
  continuations.clear();
  for(vector<Continuation* >::iterator it = pl.continuations.begin(); it != pl.continuations.end(); it++)
    continuations.push_back(*it);
  // printf("cont %d\n", continuations[15+15*19].B+continuations[15+15*19].W);
  pl.continuations.clear();
  update_dates_current();
}


int GameList::plSize() {
  return pl.size();
}

string GameList::plEntry(int i) {
  if (i < 0 || i >= (int)pl.size()) return "";
  else return pl[i];
}

int rpl_callback(void *pl, int argc, char **argv, char **azColName) {
  if (!argc) return 1;
  ((vector<string>*)pl)->push_back(string(argv[0]));
  return 0;
}

void GameList::readPlayersList() throw(DBError) {
  if (pl.size()) pl = vector<string>();
  sqlite3_exec(db, "select p from (select pw p from GAMES union select pb p from GAMES) order by lower(p)", rpl_callback, &pl, 0);
  // we ignore possible errors, since the table might not yet exist
}

int rnw_callback(void *num, int argc, char **argv, char **azColName) {
  int* n = (int*)num;
  if (!argc) return 1;
  *n = atoi(argv[0]);
  return 0;
}

void GameList::readNumOfWins() throw(DBError) {
  int* pi = new int;
  sqlite3_exec(db, "select count(rowid) from GAMES where RE like 'B%'", rnw_callback, pi, 0);
  Bwins = BwinsAll = *pi;
  sqlite3_exec(db, "select count(rowid) from GAMES where RE like 'W%'", rnw_callback, pi, 0);
  Wwins = WwinsAll = *pi;
  delete pi;
}



void GameList::createGamesDB() throw(DBError) {
  SGFtags = p_op->SGFTagsAsStrings();

  string sql1 =          "create table if not exists GAMES ( ";
  sql1 +=                  "id integer primary key, ";
  sql1 +=                  "path text, ";
  sql1 +=                  "filename text, ";
  sql1 +=                  "pos integer default 0, ";
  // sql1 +=                  "duplicate integer, ";
  sql1 +=                  "signature text, ";          // symmetrized signature
  sql1 +=                  "fphash long, ";             // hashcode of final position to detect duplicates
  sql1 +=                  "dbtree text, ";
  sql1 +=                  "date date";

  sql_ins_rnp =            "insert into GAMES (path, filename, pos, dbtree, date";
  string question_marks =  "?,?,?,?,?";

  if (p_op->sgfInDB) {
    sql1 +=                ", sgf text";
    sql_ins_rnp +=         ", sgf";
    question_marks += ",?";
  }

  SGFtagsSize = SGFtags->size();
  int ctr = 0;
  posDT = posSZ = posWR = posBR = posHA = -1;
  for(vector<string>::iterator it = SGFtags->begin(); it != SGFtags->end(); it++) {
    sql1 += ", " + *it + " text";
    sql_ins_rnp += ", " + *it;
    question_marks += ",?";
    if (*it == "DT") posDT = ctr;

    if (*it == "SZ") posSZ = ctr;
    if (*it == "WR") posWR = ctr;
    if (*it == "BR") posBR = ctr;
    if (*it == "HA") posHA = ctr;
    ctr++;
  }
  if (posDT == -1) throw DBError();
  if (posSZ == -1) {
    posSZ = SGFtags->size();
    SGFtags->push_back("SZ");
  }
  if (posWR == -1) {
    posWR = SGFtags->size();
    SGFtags->push_back("WR");
  }
  if (posBR == -1) {
    posBR = SGFtags->size();
    SGFtags->push_back("BR");
  }
  if (posHA == -1) {
    posHA = SGFtags->size();
    SGFtags->push_back("HA");
  }

  sql1 +=                  ");";
  sql_ins_rnp +=           ") values (" + question_marks + ");";
  // printf("sql insert %s\n", sql_ins_rnp.c_str());

  int rc = sqlite3_exec(db, sql1.c_str(), 0, 0, 0);
  if(rc != SQLITE_OK) throw DBError();

  sql1 = "create index if not exists dateindex on GAMES (date);";
  rc = sqlite3_exec(db, sql1.c_str(), 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();

  sql1 = "create table if not exists GAME_TAGS ( id integer primary key, game_id integer, tag_id integer, unique(game_id, tag_id) );";
  rc = sqlite3_exec(db, sql1.c_str(), 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
}

void GameList::start_processing(int PROCESSVARIATIONS) throw(DBError) {
  // printf("enter start_processing %p\n", p_op);
  // printf("dt %d sz %d\n", posDT, posSZ);

  processVariations = (PROCESSVARIATIONS != -1) ? PROCESSVARIATIONS : p_op->processVariations;

  delete_all_snapshots();
  createGamesDB();
  current = 0;
  const char* sql = "begin transaction;";
  int rc = sqlite3_exec(db, sql, 0, 0, 0);
  if (rc) { throw DBError(); }
}

void GameList::finalize_processing() throw(DBError) {
  // printf("enter finalize_processing %d\n", db);
  for(unsigned int a=0; a<20; a++) if (algo_ps[a]) algo_ps[a]->finalize_process();
  int rc = sqlite3_exec(db, "commit;", 0, 0, 0);
  if (rc != SQLITE_OK) {
    sqlite3_close(db);
    db = 0;
    throw DBError();
  }

  if (rc != SQLITE_OK) throw DBError();
  // sqlite3_close(db);
  // db = 0;

  // write algorithm data to file
  
  string a_dbname(dbname);
  a_dbname[a_dbname.size()-1] = 'a';
  ofstream os(a_dbname.c_str(), ios::binary);

  for(vector<algo_p>::iterator it = algo_ps.begin(); it != algo_ps.end(); it++) {
    if (*it) {
      SnapshotVector data = (*it)->get_data();
      size_t size1 = data.size();
      os.write((const char*)&size1, sizeof(size1));
      os.write((const char*)&data[0], size1);
    }
  }
  os.close();

  readDB();
  delete SGFtags;
}

int GameList::process(const char* sgf, const char* path, const char* fn, std::vector<GameList* > glists, const char* DBTREE, int flags) throw(SGFError,DBError) {
  process_results_vector.clear();
  const char* dbtree = "";
  if (DBTREE) dbtree = DBTREE;

  Cursor* c = 0;
  try {
    c = new Cursor(sgf, 1); // parse sgf sloppily
  } catch (SGFError) {
    return 0;
  }

  Node* root = c->root->next;

  int pos = 0;
  while (root) {
    current++;
    int return_val = 0;
    // if (!(current%1000)) {
    //  char* sql = "end transaction;";
    //  int rc = sqlite3_exec(db, sql, 0, 0, 0);
    //  if (rc) {
    //    sqlite3_close(db);
    //    db = 0;
    //    throw DBError();
    //  }
    //  sql = "begin transaction;";
    //  rc = sqlite3_exec(db, sql, 0, 0, 0);
    //  if (rc) {
    //    sqlite3_close(db);
    //    db = 0;
    //    throw DBError();
    //  }
    // }
    vector<string>* rootNodeProperties = parseRootNode(root, SGFtags);
    // for(vector<string>::iterator rnp = rootNodeProperties->begin(); rnp != rootNodeProperties->end(); rnp++)
    // printf("rnp %s\n", rnp->c_str());

    // check board size
    string sz = (*rootNodeProperties)[posSZ];
    // printf("sz %s\n", sz.c_str());
    if (sz=="") sz = "19";
    int bs = atoi(sz.c_str());
    if (bs != boardsize) {
      return_val |= UNACCEPTABLE_BOARDSIZE;
      process_results_vector.push_back(return_val);
      delete rootNodeProperties;
      root = root->down;
      pos++;
      continue;
    }

    // parse DT tag
    string dt = (*rootNodeProperties)[posDT];
    // printf("dt %s\n", dt.c_str());
    string date;

    bool year_found = false;
    int p = 0;
    while (!year_found && p < (int)dt.size()) {
      p = dt.find_first_of("0123456789", p);
      if (p == (int)string::npos || p+4 > (int)dt.size() ) break;
      else {
        year_found = (('0' <= dt[p] && dt[p] <= '9') && ('0' <= dt[p+1] && dt[p+1] <= '9') && ('0' <= dt[p+2] && dt[p+2] <= '9') && ('0' <= dt[p+3] && dt[p+3] <= '9'));
        if (year_found && (int)dt.find_first_of("0123456789", p+4) != p+4) { // success: found 4 digits in a row
          date += dt.substr(p,4);
          date += '-';
          dt.erase(p,4);
        } else {
          while ('0' <= dt[p] && dt[p] <= '9') p++;
          year_found = false;
          continue;
        }
      }
    }
    if (!year_found) date = "0000-00-00";
    else {
      bool month_found = false;
      p = 0;
      while (!month_found && p < (int)dt.size()) {
        p = dt.find_first_of("0123456789", p);
        if (p == (int)string::npos || p+2 > (int)dt.size() ) break;
        else {
          month_found = ('0' <= dt[p] && dt[p] <= '9' && '0' <= dt[p+1] && dt[p+1] <= '9');
          if (month_found && (int)dt.find_first_of("0123456789", p+2) != p+2) {
            date += dt.substr(p,2);
            date += '-';
            dt.erase(p,2);
          } else {
            while ('0' <= dt[p] && dt[p] <= '9') p++;
            month_found = false;
            continue;
          }
        }
      }
      if (!month_found) date += "00-00";
      else {
        bool day_found = false;
        p = 0;
        while (!day_found && p < (int)dt.size()) {
          p = dt.find_first_of("0123456789", p);
          if (p == (int)string::npos || p+2 > (int)dt.size() ) break;
          else {
            day_found = ('0' <= dt[p] && dt[p] <= '9' && '0' <= dt[p+1] && dt[p+1] <= '9');
            if (day_found && (int)dt.find_first_of("0123456789", p+2) != p+2) {
              date += dt.substr(p,2);
            } else {
              while ('0' <= dt[p] && dt[p] <= '9') p++;
              day_found = false;
              continue;
            }
          }
        }
        if (!day_found) date += "00";
      }
    }

    // printf("sql %s\n", sql_ins_rnp.c_str());
    sqlite3_stmt *ppStmt=0;
    int rc = sqlite3_prepare(db, sql_ins_rnp.c_str(), -1, &ppStmt, 0);
    if (rc != SQLITE_OK || ppStmt==0) {
      throw DBError();
    }

    int stmt_ctr = 1;
    rc = sqlite3_bind_text(ppStmt, stmt_ctr++, path, -1, SQLITE_TRANSIENT);
    if (rc != SQLITE_OK) throw DBError();
    rc = sqlite3_bind_text(ppStmt, stmt_ctr++, fn, -1, SQLITE_TRANSIENT); 
    if (rc != SQLITE_OK) throw DBError();
    rc = sqlite3_bind_int(ppStmt, stmt_ctr++, pos);
    if (rc != SQLITE_OK) throw DBError();
    rc = sqlite3_bind_text(ppStmt, stmt_ctr++, dbtree, -1, SQLITE_TRANSIENT);
    if (rc != SQLITE_OK) throw DBError();
    rc = sqlite3_bind_text(ppStmt, stmt_ctr++, date.c_str(), -1, SQLITE_TRANSIENT); 
    if (rc != SQLITE_OK) throw DBError();

    if (p_op->sgfInDB) {
      if (c->root->numChildren == 1) rc = sqlite3_bind_text(ppStmt, stmt_ctr++, sgf, -1, SQLITE_TRANSIENT); 
      else {
        string s= "(";
        s += c->outputVar(root);
        s+= ")";
        rc = sqlite3_bind_text(ppStmt, stmt_ctr++, s.c_str(), -1, SQLITE_TRANSIENT); 
      }
      if (rc != SQLITE_OK) throw DBError();
    }

    for(int i=0; i < SGFtagsSize; i++) {
      rc = sqlite3_bind_text(ppStmt, stmt_ctr++, (*rootNodeProperties)[i].c_str(), -1, SQLITE_TRANSIENT); 
      if (rc != SQLITE_OK) throw DBError();
    }

    rc = sqlite3_step(ppStmt);
    if (rc != SQLITE_DONE)  throw DBError();
    rc = sqlite3_finalize(ppStmt);
    if (rc != SQLITE_OK)  throw DBError();
    int game_id = sqlite3_last_insert_rowid(db);


    // printf("play through the game\n");
    bool commit = true;

    Node* currentN = root;
    for(int a=0; a < 20; a++) 
      if (algo_ps[a]) algo_ps[a]->newgame_process(game_id);

    abstractBoard b = abstractBoard(bs);
    int whichVar = 0;
    stack<VarInfo> branchpoints;

    while (currentN) {
      // printf("nn\n");
      bool caughtSGFError = false;
      char* propValue = 0;

      try {

        // parse current node, watch out for B, W, AB, AW, AE properties
        const char* s = currentN->SGFstring.c_str();
        int lSGFstring = strlen(s);
        int i = 0;
        while (i < lSGFstring && s[i] != ';' && (s[i]==' ' || s[i]=='\n' || s[i]=='\r' || s[i]=='\t')) 
          i++;

        if (i>=lSGFstring || s[i] != ';') throw SGFError();
        i++;

        while (i < lSGFstring) { // while parsing

          while (i < lSGFstring && (s[i]==' ' || s[i]=='\n' || s[i]=='\r' || s[i]=='\t')) 
            i++;
          if (i >= lSGFstring) break;

          char ID[30];
          int IDindex = 0;

          while (i < lSGFstring && s[i] != '[' && IDindex < 30) {
            if (65 <= s[i] && s[i] <= 90)
              ID[IDindex++] = s[i];
            else if (!(97 <= s[i] && s[i] <= 122) && !(s[i]==' ' || s[i]=='\n' || s[i]=='\r' || s[i]=='\t')) {
              throw SGFError();
            }
            i++;
          }

          i++;

          if (i >= lSGFstring || IDindex >= 30 || !IDindex) {
            throw SGFError();
          }
          ID[IDindex] = 0; // found next property ID
          bool IDrelevant= (!strcmp(ID,"B") || !strcmp(ID,"W") || !strcmp(ID,"AB") || !strcmp(ID,"AW") || !strcmp(ID,"AE"));
          propValue = new char[100000];
          int propValueIndex = 0;
          int oldPropValueIndex = 0;

          while (i < lSGFstring) { // while looking for property values of the current property
            while (s[i] != ']' && i < lSGFstring) {
              if (s[i] == '\\') i++;
              if (!IDrelevant || s[i] == '\t' || s[i] == ' ' || s[i] == '\r' || s[i] == '\n') {
                i++;
                continue;
              }
              if (97 <= s[i] && s[i] <= 96+bs) { // valid board coordinate?
                propValue[propValueIndex++] = s[i];
                if (propValueIndex > 99990) throw SGFError();
              } else if (s[i] == 't') { ; // allow passes, but do not record them (we handle them a little sloppily here)
              } else if (s[i] == ':') {
                if (propValueIndex - oldPropValueIndex != 2)
                  throw SGFError();
                char rect1 = 'a';
                char rect2 = 'a';
                i++;
                while (i<lSGFstring && (s[i] == '\t' || s[i] == ' ' || s[i] == '\r' || s[i] == '\n')) i++;
                if (i >= lSGFstring) throw SGFError();
                if (97 <= s[i] && s[i] <= 96+bs) // valid board coordinate?
                  rect1 = s[i];
                else throw SGFError();
                i++;
                while (i<lSGFstring && (s[i] == '\t' || s[i] == ' ' || s[i] == '\r' || s[i] == '\n')) i++;
                if (i >= lSGFstring) throw SGFError();
                if (97 <= s[i] && s[i] <= 96+bs) // valid board coordinate?
                  rect2 = s[i];
                else throw SGFError();
                i++;
                while (i<lSGFstring && (s[i] == '\t' || s[i] == ' ' || s[i] == '\r' || s[i] == '\n')) i++;
                if (i >= lSGFstring) throw SGFError();
                if (s[i] == ']') {
                  char st1 = propValue[propValueIndex-2];
                  char st2 = propValue[propValueIndex-1];
                  propValueIndex -= 2; // do not want to have the first entry twice!
                  for(char x1 = st1; x1 <= rect1; x1++) {
                    for(char x2 = st2; x2 <= rect2; x2++) {
                      propValue[propValueIndex++] = x1;
                      propValue[propValueIndex++] = x2;
                      if (propValueIndex > 99990) throw SGFError();
                    }
                  }
                  oldPropValueIndex = propValueIndex;
                  break;
                } else throw SGFError();
              } else {
                throw SGFError();
              }
              i++;
            }
            if (i >= lSGFstring) throw SGFError();

            if (propValueIndex - oldPropValueIndex != 0 && propValueIndex - oldPropValueIndex != 2) {
              throw SGFError();
            }
            oldPropValueIndex = propValueIndex;

            i++;
            while (i < lSGFstring && (s[i]==' ' || s[i]=='\n' || s[i]=='\r' || s[i]=='\t')) i++;

            if (i >= lSGFstring || s[i] != '[') break; // end of node, or found next property
            else i++; // s[i] == '[', so another property value follows. 
          }
          int p_len = propValueIndex/2;

          if (!propValueIndex) { // in particular, this happens if !IDrelevant
            if (!strcmp(ID, "B") || !strcmp(ID, "W")) {
              for(int a=0; a < 20; a++) 
                if (algo_ps[a]) algo_ps[a]->pass_process();
            }
            delete [] propValue;
            propValue = 0;
            continue;
          }

          if (!strcmp(ID, "B") || !strcmp(ID, "W")) {
            char x = propValue[0]-97; // 97 == ord('a'), (0,0) <= (x,y) <= (bs-1, bs-1)
            char y = propValue[1]-97;

            if (!b.play(x, y, ID)) throw SGFError();
            Move m = b.undostack.back();

            for(int a=0; a < 20; a++) 
              if (algo_ps[a]) algo_ps[a]->move_process(m);
          } else
            if (!strcmp(ID, "AB")) {
              for(int pp=0; pp < p_len; pp++) {
                char x = propValue[2*pp]-97;
                char y = propValue[2*pp+1]-97;
                if (!b.play(x, y, "B")) throw SGFError();
                for(int a=0; a < 20; a++) 
                  if (algo_ps[a]) algo_ps[a]->AB_process(x, y);
              }
            } else
              if (!strcmp(ID, "AW")) {
                for(int pp=0; pp < p_len; pp++) {
                  char x = propValue[2*pp]-97;
                  char y = propValue[2*pp+1]-97;
                  if (!b.play(x, y, "W")) throw SGFError();
                  for(int a=0; a < 20; a++) 
                    if (algo_ps[a]) algo_ps[a]->AW_process(x, y);
                }
              } else {
                if (!strcmp(ID, "AE")) {
                  for(int pp=0; pp < p_len; pp++) {
                    char x = propValue[2*pp]-97;
                    char y = propValue[2*pp+1]-97;
                    char removed = b.getStatus(x,y);
                    if (removed==' ') throw SGFError();
                    b.remove(x,y, false);
                    for(int a=0; a < 20; a++) 
                      if (algo_ps[a]) algo_ps[a]->AE_process(x, y, removed);
                  }
                }
              }
              delete [] propValue;
              propValue = 0;
        } 
      } catch (SGFError) {
        if (propValue) {
          delete [] propValue;
          propValue = 0;
        }
        return_val |= SGF_ERROR;
        caughtSGFError = true;
        if (flags & OMIT_GAMES_WITH_SGF_ERRORS) {
          commit = false;
          // (should exit from the loop here)
        }
      }

      {
        for(int a=0; a < 20; a++) 
          if (algo_ps[a]) algo_ps[a]->endOfNode_process();
      }

      if (processVariations && currentN->numChildren > 1) { // several variations start from this node;
        for(int a=0; a < 20; a++) 
          if (algo_ps[a]) algo_ps[a]->branchpoint_process();
        branchpoints.push(VarInfo(currentN, new abstractBoard(b), 0));
      }

      if (caughtSGFError) currentN = 0; // stop here with this branch
      else currentN = currentN->next;

      if (!currentN && branchpoints.size()) {
        currentN = branchpoints.top().n;
        b = abstractBoard(*branchpoints.top().b);
        whichVar = branchpoints.top().i;
        branchpoints.pop();
        for(int a=0; a < 20; a++) 
          if (algo_ps[a]) algo_ps[a]->endOfVariation_process();
        if (whichVar+2 < currentN->numChildren) {
          for(int a=0; a < 20; a++) 
            if (algo_ps[a]) algo_ps[a]->branchpoint_process();
          branchpoints.push(VarInfo(currentN, new abstractBoard(b), whichVar+1));
        }
        currentN = currentN->next;
        for(int vi=0; vi < whichVar+1; vi++) currentN = currentN->down;
      } 
    } // while
    char* sig = ((Algo_signature*)algo_ps[0])->get_current_signature();
    hashtype fphash = ((Algo_finalpos*)algo_ps[algo_finalpos])->get_current_fphash();

    {

      // check for duplicates (if desired)
      bool is_duplicate = false;
      if (flags & (CHECK_FOR_DUPLICATES|CHECK_FOR_DUPLICATES_STRICT)) {
        vector<int> all_duplicates = ((Algo_signature*)algo_ps[0])->search_signature(sig);
        if (all_duplicates.size()) {
          // printf("all_dupl size %d\n", all_duplicates.size());
          is_duplicate = true;
          if ((flags & CHECK_FOR_DUPLICATES_STRICT) && (p_op->algos & ALGO_FINALPOS)) {
            vector<int>::iterator d_it = all_duplicates.begin();
            while (d_it != all_duplicates.end() && !(fphash == ((Algo_finalpos*)algo_ps[algo_finalpos])->get_fphash(*d_it))) d_it++;
            if (d_it == all_duplicates.end()) is_duplicate = false;
          }
        }
        if (!is_duplicate) {    // need to check the other databases
          for(vector<GameList* >::iterator glit = glists.begin(); glit != glists.end(); glit++) {
            // printf("check others\n");
            GameList* glitp = *glit;
            vector<int> dupls = ((Algo_signature*)glitp->algo_ps[0])->search_signature(sig);
            if (dupls.size()) {
              is_duplicate = true;
              if ((flags & CHECK_FOR_DUPLICATES_STRICT) && (p_op->algos & ALGO_FINALPOS)) {
                vector<int>::iterator did=dupls.begin();
                while(did != dupls.end() && !(fphash == ((Algo_finalpos*)glitp->algo_ps[algo_finalpos])->get_fphash(*did))) did++;
                if (did == dupls.end()) is_duplicate = false;
              }
              if (is_duplicate) break;
            }
          }
        }
        if (is_duplicate) {
          return_val |= IS_DUPLICATE;
          if (flags & OMIT_DUPLICATES) commit = false;
        }
      }

      if (commit) {
        // printf("commit\n");
        // add signature, fphash
        char sql1[150];
#if defined(_WIN32)
        sprintf(sql1, "update GAMES set signature='%s', fphash='%I64d' where id=%d;", sig, (long long)fphash, game_id);
#else
        sprintf(sql1, "update GAMES set signature='%s', fphash='%lld' where id=%d;", sig, (long long)fphash, game_id);
#endif
        // printf("sql1 %s\n", sql1);
        rc = sqlite3_exec(db, sql1, 0, 0, 0);
        if (rc != SQLITE_OK)  throw DBError();

        // evaluate tags
        if ((*rootNodeProperties)[posHA] != "") { // handicap game
          char sql[100];
          sprintf(sql, "insert into GAME_TAGS (game_id, tag_id) values (%d, %d);", game_id, HANDI_TAG);
          rc = sqlite3_exec(db, sql, 0, 0, 0);
          if (rc != SQLITE_OK)  throw DBError();
        }
        if (p_op->professional_tag == 1 ||
            (p_op->professional_tag == 2 && ((*rootNodeProperties)[posWR].find('p') != string::npos || (*rootNodeProperties)[posBR].find('p') != string::npos))) { 
          // tag game as "professional"
          char sql[100];
          sprintf(sql, "insert into GAME_TAGS (game_id, tag_id) values (%d, %d);", game_id, PROFESSIONAL_TAG);
          rc = sqlite3_exec(db, sql, 0, 0, 0);
          if (rc != SQLITE_OK)  throw DBError();
        }
      } else {
        return_val |= NOT_INSERTED_INTO_DB;
        char sql[200];
        sprintf(sql, "delete from GAMES where id=%d", game_id);
        // printf("sql1 %s\n", sql);
        rc = sqlite3_exec(db, sql, 0, 0, 0);
        if (rc) throw DBError();
      }
      for(int a=0; a < 20; a++) {
        if (algo_ps[a]) algo_ps[a]->endgame_process(commit);
      }
    }
    delete [] sig;
    delete rootNodeProperties;
    process_results_vector.push_back(return_val);
    // printf("return_val %d\n", return_val);
    root = root->down;
    pos++;
  }
  delete c;
  return process_results_vector.size();
}

int GameList::process_results(unsigned int i) {
  if (i<0 || i>=process_results_vector.size()) return INDEX_OUT_OF_RANGE;
  return process_results_vector[i];
}


int GameList::snapshot() throw(DBError) {
  // return a handle to a snapshot stored in the main GameList db
  // the snapshot contains copies of
  // - orderby, format1, format2
  // - currentList
  // - all hits in the GameListEntry's of currentList
  // - pattern, labels, continuations, num_hits, num_switched, Bwins, Wwins

  SnapshotVector snapshot;
  snapshot.pb_string(orderby);
  snapshot.pb_string(format1);
  snapshot.pb_string(format2);

  snapshot.pb_int(currentList->size());
  for(vector<pair<int,int> >::iterator it = currentList->begin(); it != currentList->end(); it++) {
    snapshot.pb_int(it->first);
    snapshot.pb_int(it->second);
    vector<Hit* >* hits = (*all)[it->second]->hits;
    if (hits==0) {
      snapshot.pb_int(-1);
    } else {
      snapshot.pb_int(hits->size());
      for (vector<Hit* >::iterator it_h = hits->begin(); it_h != hits->end(); it_h++) {
        (*it_h)->to_snv(snapshot);
      }
    }
  }

  if (mrs_pattern) {
    snapshot.pb_char(1);
    mrs_pattern->to_snv(snapshot);
  } else snapshot.pb_char(0);
  if (searchOptions) {
    snapshot.pb_char(1);
    searchOptions->to_snv(snapshot);
  } else snapshot.pb_char(0);
  if (mrs_pattern && labels && continuations.size()) {
    snapshot.pb_char(1);
    snapshot.pb_charp(labels, mrs_pattern->sizeX * mrs_pattern->sizeY);
    for(int i=0; i<mrs_pattern->sizeX * mrs_pattern->sizeY; i++) continuations[i]->to_snv(snapshot);
  } else snapshot.pb_char(0);
  snapshot.pb_int(num_hits);
  snapshot.pb_int(num_switched);
  snapshot.pb_int(Bwins);
  snapshot.pb_int(Wwins);

  // insert snapshot into database
  sqlite3_stmt *ppStmt=0;
  int rc = sqlite3_prepare(db, "insert into snapshots (data) values (?)", -1, &ppStmt, 0);
  if (rc != SQLITE_OK || ppStmt==0) throw DBError();
  char* snchp = snapshot.to_charp();
  rc = sqlite3_bind_blob(ppStmt, 1, snchp, snapshot.size(), SQLITE_TRANSIENT);
  delete [] snchp;
  if (rc != SQLITE_OK) throw DBError();
  rc = sqlite3_step(ppStmt);
  if (rc != SQLITE_DONE) throw DBError();
  rc = sqlite3_finalize(ppStmt);
  if (rc != SQLITE_OK) throw DBError();
  return sqlite3_last_insert_rowid(db);
}

void GameList::restore(int handle, bool del) throw(DBError) {
  // restore the state of the GameList associated with handle

  // retrieve info associated with handle from db

  char* sn = 0;
  int sn_size = 0;
  sqlite3_stmt *ppStmt=0;
  int rc = sqlite3_prepare(db, "select data from snapshots where rowid = ?", -1, &ppStmt, 0);
  if (rc != SQLITE_OK || ppStmt==0) {
    throw DBError();
  }
  rc = sqlite3_bind_int(ppStmt, 1, handle);
  if (rc != SQLITE_OK) throw DBError();
  rc = sqlite3_step(ppStmt);
  if (rc == SQLITE_ROW) {
    sn = (char*)sqlite3_column_blob(ppStmt, 0);
    sn_size = sqlite3_column_bytes(ppStmt, 0);
  } else throw DBError();

  SnapshotVector snapshot(sn, sn_size);

  // parse info

  string ob = snapshot.retrieve_string();
  string f1 = snapshot.retrieve_string();
  string f2 = snapshot.retrieve_string();
  if (ob != orderby || f1 != format1 || f2 != format2) resetFormat();

  if (oldList) delete oldList;
  oldList = 0;
  if (currentList) delete currentList;
  currentList = new vector<pair<int,int> >;
  for(vector<GameListEntry* >::iterator it = all->begin(); it != all->end(); it++) {
    if ((*it)->hits) {
      for(vector<Hit* >::iterator ith = (*it)->hits->begin(); ith != (*it)->hits->end(); ith++)
        delete *ith;
      delete (*it)->hits;
      (*it)->hits = 0;
    }
    if ((*it)->candidates) {
      for(vector<Candidate* >::iterator itc = (*it)->candidates->begin(); itc != (*it)->candidates->end(); itc++)
        delete *itc;
      delete (*it)->candidates;
      (*it)->candidates = 0;
    }
  }

  for(int i=0; i<(DATE_PROFILE_END - DATE_PROFILE_START)*12; i++) dates_current.push_back(0);
  int cl_size = snapshot.retrieve_int();
  for(int i=0; i<cl_size; i++) {
    int i1 = snapshot.retrieve_int();
    int i2 = snapshot.retrieve_int();

    currentList->push_back(make_pair(i1, i2));
    // if ((*currentList)[currentList->size()-1].second >= all->size()) printf("ouch %d\n", (*currentList)[currentList->size()-1].second);
    (*all)[(*currentList)[currentList->size()-1].second]->hits_from_snv(snapshot);
    if ((*all)[(*currentList)[currentList->size()-1].second]->date >= DATE_PROFILE_START*12) dates_current[(*all)[(*currentList)[currentList->size()-1].second]->date - DATE_PROFILE_START*12]++;
  }

  if (mrs_pattern) delete mrs_pattern;
  if (snapshot.retrieve_char()) mrs_pattern = new Pattern(snapshot);
  else mrs_pattern = 0;

  if (searchOptions) delete searchOptions;
  if (snapshot.retrieve_char()) searchOptions = new SearchOptions(snapshot);
  else searchOptions = 0;

  if (labels) delete [] labels;
  for (std::vector<Continuation* >::const_iterator i = continuations.begin(); i != continuations.end(); ++i) {
    delete *i;
  }
  continuations.clear();

  if (snapshot.retrieve_char()) {
    labels = snapshot.retrieve_charp();
    for(int i=0; i<mrs_pattern->sizeX * mrs_pattern->sizeY; i++) {
      Continuation* c = new Continuation(this);
      c->from_snv(snapshot);
      continuations.push_back(c);
    }
  } else {
    labels = 0;
  }
  num_hits = snapshot.retrieve_int();
  num_switched = snapshot.retrieve_int();
  Bwins = snapshot.retrieve_int();
  Wwins = snapshot.retrieve_int();

  rc = sqlite3_finalize(ppStmt);
  if (rc != SQLITE_OK) throw DBError();
  if (del) { // delete snapshot from db
    char sql[100];
    sprintf(sql, "delete from snapshots where rowid = %d", handle);
    rc = sqlite3_exec(db, sql, 0, 0, 0);
    if (rc != SQLITE_OK) throw DBError();
  }
}

void GameList::delete_snapshot(int handle) throw(DBError) {
  char sql[100];
  sprintf(sql, "delete from snapshots where rowid = %d", handle);
  int rc = sqlite3_exec(db, sql, 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
}

void GameList::delete_all_snapshots() throw(DBError) {
  int rc = sqlite3_exec(db, "drop table snapshots", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
  rc = sqlite3_exec(db, "create table if not exists snapshots ( data text );", 0, 0, 0);
  if (rc != SQLITE_OK) throw DBError();
}

VarInfo::VarInfo(Node* N, abstractBoard* B, int I) {
  n = N;
  b = B;
  i = I;
}

VarInfo::VarInfo(const VarInfo& v) {
  n = v.n;
  b = new abstractBoard(*v.b);
  i = v.i;
}

VarInfo::~VarInfo() {
  delete b;
}



void insert_if_new(vector<int>& d, int i1, int i2) {
  vector<int>::iterator it = d.begin();
  while (it != d.end()) {
    if (*it++ == i1 && *it++ == i2) return;
  }
  d.push_back(i1);
  d.push_back(i2);
}



map<string, vector<int > >  find_duplicates(vector<string> glists, bool strict, bool dupl_within_db) throw(DBError) {

  // TODO Should we check that all glists have the same board size?

  map<string, vector<int> >  duplicates;
  sqlite3* db;
  int rc = sqlite3_open(":memory:", &db); 
  if (rc) {
    sqlite3_close(db);
    throw DBError();
  }
  rc = sqlite3_busy_timeout(db, 200); if (rc) throw DBError();
  rc = sqlite3_exec(db, "pragma synchronous = off;", 0, 0, 0); if (rc) throw DBError();

  rc = sqlite3_exec(db, "create table if not exists sigs ( id integer primary key, db integer, dbid integer, signature text, fphash integer );", 0, 0, 0); if (rc != SQLITE_OK) throw DBError();

  int counter = 0;
  char sql[200];
  for(vector<string>::iterator glit = glists.begin(); glit != glists.end(); glit++) {
    sprintf(sql,          "attach '%s' as g1;", glit->c_str()); rc = sqlite3_exec(db, sql, 0, 0, 0); if (rc != SQLITE_OK) throw DBError();
    rc = sqlite3_exec(db, "begin;", 0, 0, 0); if (rc != SQLITE_OK) throw DBError();
    sprintf(sql,          "insert into sigs (db,dbid,signature,fphash) select %d, id, signature, fphash from g1.GAMES;", counter); rc=sqlite3_exec(db,sql,0,0,0); if (rc!=SQLITE_OK) throw DBError();
    rc = sqlite3_exec(db, "commit;", 0, 0, 0); if (rc != SQLITE_OK) throw DBError();
    rc = sqlite3_exec(db, "detach g1;", 0, 0, 0); if (rc != SQLITE_OK) throw DBError();

    counter++;
  }

  sqlite3_stmt *ppStmt=0;
  if (dupl_within_db || (glists.size()==1))
    sprintf(sql, "select s1.signature, s1.fphash, s2.fphash, s1.db, s1.dbid, s2.db, s2.dbid from sigs as s1 join sigs as s2 on s1.signature = s2.signature where s1.db < s2.db or (s1.db = s2.db and s1.dbid < s2.dbid);");
  else
    sprintf(sql, "select s1.signature, s1.fphash, s2.fphash, s1.db, s1.dbid, s2.db, s2.dbid from sigs as s1 join sigs as s2 on s1.signature = s2.signature where s1.db < s2.db;");

  rc = sqlite3_prepare(db, sql, -1, &ppStmt, 0);
  if (rc != SQLITE_OK || ppStmt==0) throw DBError();

  do {
    rc = sqlite3_step(ppStmt);
    if (rc != SQLITE_DONE && rc != SQLITE_ROW) throw DBError();
    if (rc == SQLITE_ROW) {
      string signature(reinterpret_cast<const char*>(sqlite3_column_text(ppStmt, 0)));
      if (duplicates.find(signature) == duplicates.end()) duplicates[signature] = vector<int>();
      if (!strict || sqlite3_column_int64(ppStmt, 1)==sqlite3_column_int64(ppStmt, 2)) {
        // If there are duplicates within one db or more than 2 dbs,
        // then we want to make sure that each game is added to the duplicates[signature] vector only once,
        // so use insert_if_new to check this.
        insert_if_new(duplicates[signature], sqlite3_column_int(ppStmt, 3), sqlite3_column_int(ppStmt, 4));
        insert_if_new(duplicates[signature], sqlite3_column_int(ppStmt, 5), sqlite3_column_int(ppStmt, 6));
      }
      if (!duplicates[signature].size()) duplicates.erase(signature);
    }
  } while (rc == SQLITE_ROW);
  
  rc = sqlite3_finalize(ppStmt);
  if (rc != SQLITE_OK) throw DBError();

  rc = sqlite3_close(db);
  if (rc != SQLITE_OK) throw DBError();

  return duplicates;
}


