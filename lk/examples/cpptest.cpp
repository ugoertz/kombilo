#include <fstream>
#include <string.h>
#include "boost/filesystem/operations.hpp"
#include "../search.h"

using namespace std;
using boost::filesystem::directory_iterator;


const string SGFPATH = "/home/ug/go/gogod11W"; // FIXME // replace by a path containing sgf files
// const string SGFPATH = "/home/ug/devel/lk/examples/t3"; // FIXME // replace by a path containing sgf files


int main(int argc, char** argv) {

  // ----------------- parse command line arguments ---------------------------------
  int algos = ALGO_FINALPOS | ALGO_MOVELIST | ALGO_HASH_FULL | ALGO_HASH_CORNER;
  bool process = false;
  for(int i=1; i<argc; i++) {
    if (!strcmp(argv[i], "-nh")) // disable hashing
      algos = ALGO_FINALPOS | ALGO_MOVELIST;
    if (!strcmp(argv[i], "-p")) process = true;
  }

  // ----------------- set up processing options -----------------------------------
  ProcessOptions* p_op = new ProcessOptions;

  // ----------------- create GameList instance -----------------------------------
  GameList gl("./kombilo1.db",
      "id", "[[PW]] - [[PB]] ([[winner]]), [[filename.]], ", 0);

  // printf("start\n");

  // ---------------- process SGF games ---------------------------------------------
  if (process) { // process sgf's. must be first argument
    printf("start processing\n");
    // GameList gl1("./kombilo1.db", "id", "[[PW]] - [[PB]] ([[winner]]), [[filename.]], ", p_op);
    vector<GameList* > glv;
    // glv.push_back(&gl1);
    gl.start_processing();
    directory_iterator end_itr;
    string path = SGFPATH;
    int counter = 0;
    for(directory_iterator it(path); it != end_itr; ++it) {
      string n = it->path().filename().string();
      if (n.substr(n.size()-4) == ".sgf") {
        ifstream infile;
        // printf("%s\n", n.c_str());
        infile.open(it->path().string().c_str());

        string sgf;
        string line;
        while (!infile.eof()) {
          getline(infile, line);
          sgf += line + "\n";
        }
        infile.close();
        int flags = CHECK_FOR_DUPLICATES| CHECK_FOR_DUPLICATES_STRICT; // | OMIT_DUPLICATES 
        if (gl.process(sgf.c_str(), path.c_str(), n.c_str(), glv, "", flags)) {
          if (gl.process_results()) printf("process res %d\n", gl.process_results());
          if (gl.process_results() & IS_DUPLICATE) printf("is duplicate: %d\n", counter);
        }
        counter++;
      }
    }
    printf("finalize...\n");
    gl.finalize_processing();
    printf("Now %d games in db.\n", gl.size());
  }
  printf("%d games.\n", gl.size());
  delete p_op;

  // ------------------- set up search pattern ----------------------------------------

  // Pattern p(CENTER_PATTERN, 19, 2, 2, ".XXO", "D..F");

  // Pattern p(CENTER_PATTERN, 19, 3, 3, ".X.XXXXOX", vector<MoveNC>());
  // Pattern p(2,2,4,4, 19, 3, 3, ".X.XXXXOX", vector<MoveNC>()); // "fixed anchor"

  // anchor varies only in small region of board: the first 4 entries 
  // (left, right, top, bottom) describe the rectangle which may contain the top left point of the pattern.
  // The coordinates range from 0 to boardsize-1
  // For example, CORNER_NW_PATTERN corresponds to (0,0,0,0)
  // Pattern p(2,3,4,6, 19, 3, 3, ".X.XXXXOX", vector<MoveNC>()); 
  
  // Pattern p(CORNER_NW_PATTERN,19,8,8,"...................X......X.......XO......OO....................");
  // Pattern p(CORNER_NW_PATTERN,19,8,8, "...................X.........O....O........................X....");
  // Pattern p(CORNER_NW_PATTERN,19,8,8, "...................O.........X....X........................O....");

  // vector<MoveNC> contList;
  // contList.push_back(MoveNC(3, 2, 'X'));
  // contList.push_back(MoveNC(3, 4, 'O'));
  // contList.push_back(MoveNC(4, 4, 'X'));
  // contList.push_back(MoveNC(4, 5, 'O'));
  // contList.push_back(MoveNC(4, 3, 'X'));
  // contList.push_back(MoveNC(3, 5, 'O'));

  // Pattern p(CORNER_NE_PATTERN,19,7,7, ".................................................", contList);
  Pattern p(CORNER_NW_PATTERN,19,7,7, ".................X.....X......XO.....OO..........");
  // Pattern p(CORNER_SE_PATTERN,19,7,7, "...........X......O.....O.X..O...................");
  //Pattern p(CORNER_SW_PATTERN,19,7,7, "...X.....X.X.X.XOXOX..OOO.X.....OOX......O.......");
  // 19,8,8"
  // Pattern p(CORNER_NW_PATTERN, 19, 10, 11, ".......................X.X......X.........XO........OO.......................................O................");

  // Pattern p(CENTER_PATTERN, 19, 3, 5, ".X.....OX..X...");
  // Pattern p(CENTER_PATTERN, 19, 2, 2, "XOX.");
  // vector<MoveNC> contList;
  // contList.push_back(MoveNC(6,15,'X'));
  // contList.push_back(MoveNC(6,13,'O'));
  // contList.push_back(MoveNC(4,15,'X'));
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, ".....................O.O........OX......XO......X.OXX.XX...X,.OOXXX..OOOX.O....X.OXOOXOO..OX.......XOXXOXXOOXXOO....OX.XXXOOOXO.O.O...OXX..XOX..XO.X.XO...O.......X.....XO..O.,X....,.....XOO................X......X............X....O...........................................O.O...........O.....,.....X...........X.O.X............................................", contList);
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, "..O.O....X...XXXXX.OOXO....OXO.XXOOOXOXXXXOO.OOXO.OXO..O..X.X..OOX,X.XO.O.....XOOOXOXX..XO......X.XOXXX..XXXO........XOX..XXOOXO.OOO.....OOXOXOO.O...XX...X..OXXOO.XOX........O..OX.,..X..X.....X...OX...X..........O....XXXO...XO...X...OOOXOOXX...X....O..OX.O..OX..........OXX....OX..OO..O.OOOOX..O.OX..XX..OOXXXOX.XOOX..X....XXXXXOX...OX.......X.O.XO.............");

  // Pattern p(FULLBOARD_PATTERN,19,19,19,".........................O.................OX......O..O...O.O...........X........X........X......X.X...........O............................O................X................XXOOO.X..............X...............OOOOO.X...........XXXXO.O...............OXXO.............X....XXXX..O.........XXXXOOO.O.O.X.....OOXOO...OXOXX.......OOX......X........................");

// ...................
// ...................
// ............X.O....
// ................X..
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
// ...................
  // Pattern p(FULLBOARD_PATTERN,19,19,19,"........................................................................O.......................................................................................................................................................................................................................X........................................................................", vector<MoveNC>(), "........................................ABC................DEF................GHU............................................................................................................................T.................................................................................X..........JKLM...............NOPQ.................RS.....................");
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, ".........................................OOX.......X.......O.XX...X.....O........................O.............O.......................................................................................................................................................X....O.....................X.......O.X......X....X.O..OX.........................................."); 
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, "............................................................X...........O..............................................................................................................................................................................................X.......................X............O..............O.X..........................................."); // a2
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, "...........................................X.......X........O...........O........................O.............O................................................................................................................................................................................X...........X............................................................"); // a4
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, "........................................................................................................................................................................................................................................................................................................................................................................."); // empty board
  
  // vector<MoveNC> contList;
  // contList.push_back(MoveNC(3,15,'X'));
  // contList.push_back(MoveNC(15,3,'O'));
  // contList.push_back(MoveNC(15,15,'X'));
  // Pattern p(FULLBOARD_PATTERN, 19, 19, 19, ".........................................................................................................................................................................................................................................................................................................................................................................", contList);



  // -------------------- set up search options ----------------------------------
  SearchOptions so;
  so.fixedColor = 0;
  so.algos = algos;
  // so.trustHashFull = true;
  // SearchOptions so(0,0,50); // use move limit
  // so.searchInVariations = false;
  // so.nextMove = 2;
  
  // -------------------- do pattern search --------------------------------------
  for(int i=0; i<1; i++) {
  gl.reset();
  gl.search(p, &so);
  printf("num games: %d, num hits: %d\n", gl.size(), gl.numHits());
  // ------------------- print some statistics ------------------------------------------

  printf("Search pattern:\n");
  printf("%s\n", p.printPattern().c_str());
  printf("Continuations:\n");
  for(int y=0; y<p.sizeY; y++) {
    for(int x=0; x<p.sizeX; x++) {
      printf("%c", gl.lookupLabel(x,y));
    }
    printf("\n");
  }
  printf("\n");
  printf("Statistics:\n"); 
  printf("num hits: %d, num switched: %d, B wins: %d, W wins: %d\n", gl.num_hits, gl.num_switched, gl.Bwins, gl.Wwins);

  printf("Continuation | Black      ( B wins / W wins ) | White      (B wins / W wins) |\n");
  for(int y=0; y<p.sizeY; y++) {
    for(int x=0; x<p.sizeX; x++) {
      if (gl.lookupLabel(x,y) != '.') {
        Continuation cont = gl.lookupContinuation(x,y);
        printf("      %c      |   %3d[%3d] (    %3d /    %3d ) |   %3d[%3d] (   %3d /    %3d) | %1.1f /  %1.1f | %d | %d |  \n",
            gl.lookupLabel(x,y), cont.B, cont.tB, cont.wB, cont.lB, cont.W, cont.tW, cont.wW, cont.lW, 
            cont.wW*100.0/cont.W, cont.wB*100.0/cont.B,
            cont.earliest_B(), cont.earliest_W());
      }
    }
  }
  printf("\n");
  printf("\n");
  gl.setTag(11, 0, gl.size());
  }

  vector<int> which_tags;
  which_tags.push_back(2);
  which_tags.push_back(11);
  which_tags.push_back(10);
  gl.export_tags("tags", which_tags);

  // create a tag for this pattern and tag all games found in the pattern search

  int p_tag = 10;
  gl.setTag(p_tag, 0, gl.size());


  // ------------------- print some information about current list of games ------------

  vector<string> res = gl.currentEntriesAsStrings();
  // for(vector<string>::iterator it = res.begin(); it != res.end(); it++)
  //   printf("%s\n", it->c_str());
  for(int i=0; i< (gl.size() < 10 ? gl.size() : 10); i++) printf("%s\n", gl.currentEntryAsString(i).c_str());

  // ------- date profile -----------------------

  printf("\n\nDate profile:\n\n");
  for(int year=1980; year<2000; year++) {
    int sum_all = 0;
    for(int j=0; j<12; j++) sum_all += gl.dates_all[year*12-1600*12+j];
    int sum_current = 0;
    for(int j=0; j<12; j++) sum_current += gl.dates_current[year*12-1600*12+j];
    printf("%d: %d %d\n", year, sum_all, sum_current);
  }

  // ------------------- game info search

  printf("Game info search: pw = 'Cho Chikun' or pb = 'Cho Chikun'\n");
  gl.reset();
  gl.gisearch("pw = 'Cho Chikun' or pb = 'Cho Chikun'");
  printf("%d games in db involving Cho Chikun.\n\n\n", gl.size());

  // -------------------- game info search without changing GameList
  
  printf("Game info search: pw = 'Cho Chikun' or pb = 'Cho Chikun'\n");
  gl.reset();
  vector<int>* CL = gl.gisearchNC("pw = 'Cho Chikun' or pb = 'Cho Chikun'");
  printf("%ld games in db involving Cho Chikun.\n", CL->size());
  printf("%d games in db.\n\n\n", gl.size());
  delete CL;

  printf("Game info search: date >= '2000' and date < '2005' \n");
  gl.reset();
  CL = gl.gisearchNC("date >= '2000-00-00' and date < '2006-00-00'");
  printf("%ld games in db played between 2000 and 2005.\n", CL->size());
  printf("%d games in db.\n\n\n", gl.size());
  delete CL;


  // ------------------- check for duplicates ---------------------------------

  gl.reset();
  printf("Looking for duplicates:\n");
  vector<string> vs;
  // vs.push_back("t3.db"); // Could extend duplicate check to other databases
  map<string, vector<int> > d = find_duplicates(vs);
  for(map<string, vector<int> >::iterator it = d.begin(); it != d.end(); it++) {
    printf("sig: %s\n", it->first.c_str());
    vector<int>::iterator it1 = it->second.begin(); 
    while (it1 != it->second.end()) printf("db: %d, id: %d\n", *it1++, *it1++);
  }

  // printf("--------------------------------------------------- \n");

  // ------------------- snapshot ---------------------------------------------

  printf("Test snapshot/restore.\n");
  gl.delete_all_snapshots(); 
  printf("Do a pattern search.\n");
  gl.search(p, &so);
  int handle = gl.snapshot();
  printf("Number of games: %d, number of hits: %d\n", gl.size(), gl.numHits());
  printf("Saved as snapshot %d.\n\n", handle);

  gl.reset();
  printf("Reset gamelist\n");
  printf("num games: %d, num hits: %d\n\n", gl.size(), gl.numHits());

  gl.restore(handle, true);
  printf("Restore snapshot.\n");
  printf("num games: %d, num hits: %d\n\n\n", gl.size(), gl.numHits());

  // -----------------------------------------------
  printf("Reset gamelist and search for tag we created.\n");
  gl.reset();
  gl.tagsearch(p_tag);
  printf("num games: %d, num hits: %d\n", gl.size(), gl.numHits());

  printf("Remove tag from db and search again.\n");
  gl.deleteTag(p_tag);
  gl.tagsearch(p_tag);
  printf("num games: %d, num hits: %d\n\n\n", gl.size(), gl.numHits());

  // ------- list of all players ---------------

  printf("%d players in the database\n", gl.plSize());
  for(int i=0; i < (gl.plSize()<10 ? gl.plSize() : 10); i++)
    printf("%s\n", gl.plEntry(i).c_str());

}
