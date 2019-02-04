CC=g++
CFLAGS=-std=c++11 -O3 -Wall

build: htd_validate.cpp
	$(CC) $(CFLAGS) htd_validate.cpp -o htd_validate

verbose: htd_validate.cpp
	$(CC) $(CFLAGS) -D VERBOSE htd_validate.cpp -o htd_validate

clean: htd_validate
	rm htd_validate
