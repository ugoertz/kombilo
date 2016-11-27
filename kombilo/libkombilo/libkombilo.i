%module libkombilo

%include <std_string.i>
%include <std_vector.i>
%include <std_map.i>
%include <std_pair.i>

namespace std {
  %template(vectorc) vector<unsigned char>;
  %template(vectors) vector<string>;
  %template(vectori) vector<int>;
  %template(pairii) pair<int,int>;
  %template(vectorii) vector<pair<int,int> >;
  %template(mapsvi) map<string, vector<int> >;
};


%begin %{
#define SWIG_PYTHON_2_UNICODE
#include "sgfparser.h"
#include "abstractboard.h"
#include "pattern.h"
#include "search.h"
%}

%include "sgfparser.h"
%include "abstractboard.h"
%ignore gis_callback(void *gl, int argc, char **argv, char **azColName);
%ignore gis_callbackNC(void *pair_gl_CL, int argc, char **argv, char **azColName);
%ignore GameListEntry;
%ignore Hit;
%ignore Candidate;
%ignore SnapshotVector;
%ignore GameList::all;
%ignore GameList::currentList;
%include "pattern.h"
%include "search.h"
%template(vectorMNC) std::vector<MoveNC>;
%template(vectorM) std::vector<Move>;
%template(vectorGL) std::vector<GameList* >;


