#include <fstream>
#include <iostream>
#include <string.h>
#include "../sgfparser.h"

using namespace std;

int main(int argc, char** argv) {
  Cursor c = Cursor("(;PW[White player]AP[Kombilo]\nSZ[19]GC[This is a comment.]\n\n;B[qq])", 0);

  cout << "PW: " << c.root->next->gpv("PW")[0] << endl;
  vector<string> pv;
  pv.push_back("aa");
  pv.push_back("bb");
  c.root->next->set_property_value("AB", pv);
  c.root->next->del_property_value("AB");
  c.root->next->set_property_value("GC", pv);
  c.root->next->del_property_value("AW");
  if (c.root->next->gpv("PB").size()) cout << "PB: " << c.root->next->gpv("PB")[0] << endl;
  // Node* n = Cursor("(;PW[asd]AP[Kombilo]\nSZ[19]GC[adv]\n\n;B[qq])", 0).getRootNode(0);  --- this is not allowed since ~Cursor() deletes all nodes!

  Node* n = c.getRootNode(0);
  vector<string> v = n->keys();
  n = c.next();
  n->add_property_value("C", pv);

  cout << "Keys in root node:" << endl;
  for(vector<string>::iterator it = v.begin(); it != v.end(); it++)
    cout << *it << ": " << c.root->next->gpv(*it)[0] << endl;
  
  cout << endl << endl;
  cout << c.output();
}
