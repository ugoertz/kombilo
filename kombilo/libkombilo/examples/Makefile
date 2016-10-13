LKPATH = ..
LIBRARIES = -lsqlite3 -lboost_system -lboost_filesystem

cpptest: search.o sgfparser.o abstractboard.o cpptest.o algos.o pattern.o
	g++ -o cpptest cpptest.o search.o sgfparser.o abstractboard.o pattern.o algos.o -fopenmp $(LIBRARIES) 

cpptest.o: cpptest.cpp $(LKPATH)/search.h $(LKPATH)/abstractboard.h $(LKPATH)/sgfparser.h $(LKPATH)/pattern.h $(LKPATH)/algos.h
	g++ -c cpptest.cpp

search.o: $(LKPATH)/search.cpp $(LKPATH)/search.h $(LKPATH)/abstractboard.h $(LKPATH)/sgfparser.h $(LKPATH)/pattern.h $(LKPATH)/algos.h
	g++ -c $(LKPATH)/search.cpp

sgfparser.o: $(LKPATH)/sgfparser.cpp $(LKPATH)/sgfparser.h
	g++ -c $(LKPATH)/sgfparser.cpp

pattern.o: $(LKPATH)/pattern.cpp $(LKPATH)/sgfparser.h $(LKPATH)/abstractboard.h $(LKPATH)/pattern.h
	g++ -c $(LKPATH)/pattern.cpp

algos.o: $(LKPATH)/algos.cpp $(LKPATH)/algos.h $(LKPATH)/sgfparser.h $(LKPATH)/abstractboard.h $(LKPATH)/pattern.h
	g++ -c -fopenmp $(LKPATH)/algos.cpp

abstractboard.o: $(LKPATH)/abstractboard.cpp $(LKPATH)/abstractboard.h
	g++ -c $(LKPATH)/abstractboard.cpp

fast:
	g++ -O3 -o cpptest cpptest.cpp $(LKPATH)/search.cpp $(LKPATH)/sgfparser.cpp $(LKPATH)/abstractboard.cpp $(LKPATH)/algos.cpp $(LKPATH)/pattern.cpp -fopenmp $(LIBRARIES)

clean:
	rm search.o abstractboard.o sgfparser.o algos.o pattern.o cpptest.o cpptest

debug:
	g++ -Wall -g -O0 -o cpptest cpptest.cpp $(LKPATH)/search.cpp $(LKPATH)/sgfparser.cpp $(LKPATH)/algos.cpp $(LKPATH)/abstractboard.cpp $(LKPATH)/pattern.cpp -fopenmp $(LIBRARIES)

sgftest: sgftest.cpp $(LKPATH)/sgfparser.h $(LKPATH)/sgfparser.cpp
	g++ -Wall -g -O0 -o sgftest sgftest.cpp $(LKPATH)/sgfparser.cpp 


