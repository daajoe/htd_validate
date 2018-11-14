## Input Format


### Hypergraph (.hgr)

The hypergraph format extends the PACE2016 and [PACE2017 graph](https://pacechallenge.wordpress.com/pace-2017/track-a-treewidth/) format.

* Line separator ‘\n’
* Lines starting with character c are interpreted as comments
* Vertices are consecutively numbered from 1 to n
* Problem description
  * Form "p htd NumVertices NumHyperedges"
    * Line starting with character p 
    * followed by the problem descriptor htd 
    * followed by number of vertices n
    * followed by number of hyperedges m
    * each separated by space each time
  * Unique (No other line may start with p)
  * Has to be the first line (except comments)
* Remaining lines indicate a hyperedge
  * consisting of decimal integers separated by space
  * Line: "1 2 3\n" indicates a hyperedge
* Empty lines or lines consisting of spaces may occur and only will be ignored  
* Hypergraphs may contain isolated vertices, multiple hyperedges, and loops

Example:

```AsciiDoc
c This file describes a hypergraph in htd PACE2019 format with 6 vertices and 4 hyperedges
p htd 6 4
1 2 3
2 3 4
c this is a comment and will be ignored
3 4 5
4 5 6
```

Alternative (works by autodetection):
* Problem line in DIMACS edge format: "p edge NumVertices NumHyperedges"
* Starting a line edge lines with character 'e', i.e., "e 1 2 3"

```AsciiDoc
c This file describes a hypergraph in htd PACE2019 format with 6 vertices and 4 hyperedges
p edge 6 4
e 1 2 3
e 2 3 4
c this is a comment and will be ignored
e 3 4 5
e 4 5 6
```



### Hypertree Decomposition Format (.htd)

See: https://arxiv.org/abs/1611.01090 for a compact definition of various hypertree decompositions.


* Line separator ‘\n’
* Lines starting with character c are interpreted as comments
* Vertices are consecutively numbered from 1 to n
* Solution description
  * Form "s htd NumBags MaxBagSize NumVertices NumHyperedges"
    * Line starting with character s
    * followed by the problem descriptor htd
    * followed by number of bags
    * followed by the computed largest bag size (i.e., width+1)
    * followed by number of vertices n
    * followed by number of hyperedges m
    * each separated by space each time
  * Unique (No other line may start with p)
  * Has to be the first line (except comments)
* Bag description
  * BagIDs run consecutively from 1 to b
  * Form "b BagID Vertex1 Vertex2 Vertex3 ..."
    * Lines starting with character b
    * followed by an identifier of the bag
    * followed by the contents of the bag
    * each separated by space each time
  * Example: "b 4 3 4 6 7"
    * specifies that bag number 4 
    * contains the vertices 3, 4, 6, and 7 of the original hypergraph
  * Bags may be empty
  * For every bag i, there must be exactly one line starting with b i. 
* Width description
  * Describe the width function mapping for the bags
  * Value is in {0,1}
  * Form "w BagID VertexID Value"
    * Lines starting with character w
    * followed by an identifier for the bag
    * followed by the vertex
    * followed by the value in {0,1} the function maps to 
    * each separated by space each time
  * In order to save space we allow to skip width descriptions for (bag,vertex) |-> 0 (i.e., if the function is not specified for a (bag,vertex), we implictly assume value 0.)
* Tree description
  * NodeIDs run consecutively from 1 to l
  * Lines not starting with a character in {c,s,b,w} indicate an edge in the tree decomposition
  * Form: "Node1 Node2"
    * Lines starting with an identifier of the node
    * followed by an identifier of the node
    * each separated by space each time
  * The graph described in this way must be a tree
* Empty lines or lines consisting of spaces may occur and only will be ignored  


```AsciiDoc
c This file describes a hypertree decomposition with 5 bags, width 2
c for a hypergraph with 5 vertices and 5 hyperedges
s htd 5 2 5 5
b 1 1 2 3
b 2 2 3 4 1
b 3 3 4 5 1 2
b 4 4 5 1 2 3
b 5 5 1 2
2 1
3 2
4 3
5 4
w 1 1 0
w 1 2 0
w 1 3 1
w 1 4 0
w 1 5 1
c
w 2 1 0
w 2 2 0
w 2 3 1
w 2 4 0
w 2 5 1
c
w 3 1 0
w 3 2 0
w 3 3 1
w 3 4 0
w 3 5 1
c
w 4 1 1
w 4 2 0
w 4 3 1
w 4 4 0
w 4 5 0
c
w 5 1 0
w 5 2 0
w 5 3 0
w 5 4 0
w 5 5 1
```

or in compressed version
```AsciiDoc
c This file describes a hypertree decomposition with 5 bags, width 2
c for a hypergraph with 5 vertices and 5 hyperedges
s htd 5 2 5 5
b 1 1 2 3
b 2 2 3 4 1
b 3 3 4 5 1 2
b 4 4 5 1 2 3
b 5 5 1 2
2 1
3 2
4 3
5 4
w 1 3 1
w 1 5 1
c
w 2 3 1
w 2 5 1
c
w 3 3 1
w 3 5 1
c
w 4 1 1
w 4 3 1
c
w 5 5 1
```
#### Testcases
* Can be found under "htd_validate_tests/tests/validators/htd contains".