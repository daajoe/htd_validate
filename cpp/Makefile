CC=g++
CFLAGS=-std=c++11 -O3 -Wall

build: htd_validate.cpp htd_validate_heur.cpp
	$(CC) $(CFLAGS) htd_validate.cpp -o htd_validate
	$(CC) $(CFLAGS) htd_validate_heur.cpp -o htd_validate_heur

verbose: htd_validate.cpp htd_validate_heur.cpp
	$(CC) $(CFLAGS) -D VERBOSE htd_validate.cpp -o htd_validate
	$(CC) $(CFLAGS) -D VERBOSE htd_validate_heur.cpp -o htd_validate_heur

clean: htd_validate htd_validate_heur
	rm htd_validate
	rm htd_validate_heur
