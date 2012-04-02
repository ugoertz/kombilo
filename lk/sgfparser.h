/*! \file sgfparser.h
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


#ifndef _SGFPARSER_H_
#define _SGFPARSER_H_

#include <string>
#include <vector>
#include <utility>
#include <stack>
#include <map>
using namespace std;


class SGFError {
  public:
    SGFError();
};

class ExtendedMoveNumber {
  public:
    int length;
    int* data; // "even" entries: go right, "odd" entries: go down in game tree.

    ExtendedMoveNumber();
    ExtendedMoveNumber(int LENGTH, int* DATA);
    ExtendedMoveNumber(int D);
    ExtendedMoveNumber(const ExtendedMoveNumber& emn);
    ~ExtendedMoveNumber();

    ExtendedMoveNumber& operator=(const ExtendedMoveNumber& emn);
    void next();
    void down() throw(SGFError);
    int total_move_num();
    // void down();
};


char* SGFescape(const char* s);

class Cursor;

class PropValue {
  public:
    PropValue(std::string IDC, std::vector<std::string>* PV);
    PropValue(const PropValue& pval);
    ~PropValue();
    std::string IDcomplete;
    std::vector<std::string>* pv;
};

class Node {
  public:
    Node* previous;
    Node* next;
    Node* up;
    Node* down;
    int numChildren;
    std::string SGFstring;
    int parsed;
    std::vector<std::string> gpv(const string& prop);
    std::vector<std::string>* get_property_value(const string& prop);
    void set_property_value(const string& IDcomplete, vector<string> propValue) throw(SGFError);  ///< This sets propValue as new this->propValue (changed behavior in comparison with version 0.6!)
    void add_property_value(const string& IDcomplete, vector<string> propValue) throw(SGFError);  ///< adds propValue to this->propValue (and "creates" it if necessary)
    void del_property_value(const string& IDcomplete) throw(SGFError);  // delete data[ID]
    vector<string> keys();

    int posyD; // used when displaying SGF structure graphically as a tree

    Node(Node* prev, char* SGFst) throw(SGFError);
    ~Node();
    ExtendedMoveNumber get_move_number();
    void parseNode() throw(SGFError);
    static int sloppy;
    int level;
  private:
    std::map<std::string, PropValue> data; // use get_property_value to access this

  friend class Cursor;
};

typedef char* char_p;

std::vector<std::string>* parseRootNode(Node* n, std::vector<std::string>* tags) throw(SGFError);

class Cursor {
  public:
    Cursor(const char* sgf, int sloppy) throw(SGFError);
    ~Cursor();

    int atStart;
    int atEnd;
    int height;
    int width;
    Node* root;
    Node* currentN;
    int posx;
    int posy;

    void parse(const char* s) throw(SGFError);
    void game(int n) throw(SGFError); ///< Go to n-th game in this SGF file.
    Node* next(int n=0) throw(SGFError); ///< Go to (n-th variation of) next move. Counting of variations starts at n=0.
    Node* previous() throw(SGFError);
    Node* getRootNode(int n) throw(SGFError);
    char* outputVar(Node* node);
    char* output();
    void add(char* st);
    void delVariation(Node* node);
    void setFlags();  

  protected:
    void delVar(Node* node);
    void deltree(Node* node);

};

std::string nodeToString(std::map<std::string, PropValue >& data) throw(SGFError);
// char* rootNodeToString(PyObject* data);

#endif

