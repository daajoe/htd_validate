#include <iostream>
#include <vector>
#include <algorithm>
#include <sstream>
#include <string>
#include <fstream>
#include <set>
#include <numeric>
#include <iomanip>
using namespace std;

//////////// HELPER //////////////////

const int TIMEOUT_TIME = 1800;

const int INSTANCE_READ_MODE = 1;
const int SOLUTION_READ_MODE = 2;

bool DO_CHECK_CONSTRAINT;

void checkInputConstraint(bool validConstraint, int lineNumber, string failMsg) {
  if (!validConstraint) {
    cerr << "Instance Error (" << lineNumber << "): " << failMsg << endl;
    exit(2);
  }
}

void giveVerdict(double score, string msg) {
  cout << fixed << setprecision(8) << score << "|" << msg << endl;
  exit(0);
}

void checkSolutionConstraint(bool validConstraint, string failMsg) {
  if (DO_CHECK_CONSTRAINT && !validConstraint) {
    #ifdef VERBOSE
      giveVerdict(-TIMEOUT_TIME * 10, failMsg);
    #else
      giveVerdict(-TIMEOUT_TIME * 10, "Wrong Answer");
    #endif
  }
}

void checkConstraint(int mode, bool validConstraint, int lineNumber, string failMsg) {
  if (mode == INSTANCE_READ_MODE) {
    checkInputConstraint(validConstraint, lineNumber, failMsg);
  } else if (mode == SOLUTION_READ_MODE) {
    checkSolutionConstraint(validConstraint, failMsg);
  }
}

vector<string> tokenize(string s) {
  vector<string> tokens;
  stringstream ss(s);
  string tmp;

  while (ss >> tmp) {
    tokens.push_back(tmp);
  }

  return tokens;
}

int parseInt(int mode, string x, int lineNumber = -1) {
  checkConstraint(mode, x.length() > 0, lineNumber, "Expected integer, got empty string");
  
  int sign = 1;
  int ret = 0;

  if (x[0] == '-') {
    sign = -1;
    x = x.substr(1);
  }

  checkConstraint(mode, x.length() > 0, lineNumber, "Expected integer, got non-integer string");

  for (char ch : x) {
    checkConstraint(mode, '0' <= ch && ch <= '9', lineNumber, "Expected integer, got non-integer string");
    ret = 10 * ret + (ch - '0');
  }

  return ret * sign;
}

string intToString(int x) {
  stringstream ss;
  ss << x;

  string ret;
  ss >> ret;

  return ret;
}

set<int> getSetIntersection(vector<int> v1, vector<int> v2) {
  set<int> s1(v1.begin(), v1.end());
  set<int> s2(v2.begin(), v2.end());
  set<int> result;

  set_intersection(s1.begin(), s1.end(), s2.begin(), s2.end(), inserter(result, result.begin()));
  return result;
}

void addVectorToSet(set<int> &s, vector<int> v) {
  for (int iter : v) {
    s.insert(iter);
  }
}

////////////// END OF HELPER //////////////////

class Tree {
  public:
    Tree(int _numVertex = 0) {
      numVertex = _numVertex;
      adjacencyList = vector<vector<int>>(numVertex+1);
      directedList = vector<vector<int>>(numVertex+1);
      parent = vector<int>(numVertex+1, -1);
    }

    int getNumVertex() {
      return numVertex;
    }

    vector<vector<int>> getAdjacencyList() {
      return adjacencyList;
    }

    vector<int> getParent() {
      return parent;
    }

    void addEdge(int u, int v) {
      adjacencyList[u].push_back(v);
      adjacencyList[v].push_back(u);

      directedList[u].push_back(v);
    }

    bool isValidTree() {
      vector<int> numbers(numVertex);
      iota(numbers.begin(), numbers.end(), 1);

      return isRooted() && isValidEdgeNumber() && isConnected(numbers);
    }

    bool isConnectedComponent(vector<int> vertexNumbers) {
      return isConnected(vertexNumbers);
    }

    void makeRooted() {
      vector<bool> hasParent(numVertex+1, 0);
      for (int i = 1 ; i <= numVertex ; i++) {
        for (int v : directedList[i]) {
          hasParent[v] = true;
        }
      }

      int root = -1; // maybe wrong, but will be catched in the validation
      for (int i = 1 ; i <= numVertex ; i++) {
        if (!hasParent[i]) {
          root = i;
        }
      }

      checkSolutionConstraint(root != -1, "Invalid Tree");
      parent[root] = root;

      dfsMakeRooted(root);
    }

    vector<int> getSubtree(int root) {
      vector<int> result;
      dfsSubtree(root, result);

      return result;
    }

  private:
    int numVertex;
    vector<vector<int>> adjacencyList;
    vector<vector<int>> directedList;
    vector<int> parent;

    bool isRooted() {
      return all_of(parent.begin() + 1, parent.end(), [](int iter) {
        return iter > 0;
      });
    }

    bool isValidEdgeNumber() {
      int edgeNum = 0;
      for (vector<int> &adj : adjacencyList) {
        edgeNum += adj.size();
      }

      edgeNum /= 2;
      return edgeNum == numVertex - 1;
    }

    bool isConnected(vector<int> vertexNumbers) {
      set<int> setNumbers(vertexNumbers.begin(), vertexNumbers.end());
      int neighbourCount = 0;

      for (int v : vertexNumbers) {
        for (int adjacent : adjacencyList[v]) {
          neighbourCount += setNumbers.count(adjacent);
        }
      }

      neighbourCount /= 2;
      return neighbourCount == (int)vertexNumbers.size() - 1;
    }

    void dfsMakeRooted(int currentNode) {
      for (int nextNode : directedList[currentNode]) {
        if (parent[nextNode] > 0) {
          continue;
        }

        parent[nextNode] = currentNode;
        dfsMakeRooted(nextNode);
      }
    }

    void dfsSubtree(int currentNode, vector<int> &subtree) {
      subtree.push_back(currentNode);

      for (int nextNode : adjacencyList[currentNode]) {
        if (nextNode == parent[currentNode]) {
          continue;
        }

        dfsSubtree(nextNode, subtree);
      }
    }
};

class Solution {
  public:
    int getNumBags() {
      return numBags;
    }

    int getWidth() {
      return width;
    }

    int getNumVertex() {
      return numVertex;
    }

    int getNumHyperEdge() {
      return numHyperEdge;
    }

    vector<vector<int>> getBags() {
      return bags;
    }

    vector<int> getBagFromId(int id) {
      return bags[id];
    }

    vector<vector<int>> getLambdaInBags() {
      return lambdaInBags;
    }

    vector<int> getLambdaInBagFromId(int id) {
      return lambdaInBags[id];
    }

    Tree getHyperTree() {
      return hypertree;
    }

    void readFromStream(ifstream &is, bool doCheckConstraint) {
      DO_CHECK_CONSTRAINT = doCheckConstraint;
      
      numBags = -1;
      width = -1;
      numVertex = -1;
      numHyperEdge = -1;

      bags.clear();
      lambdaInBags.clear();

      string line;
      int bagCount = 0;

      while (getline(is, line)) {
        vector<string> tokens = tokenize(line);

        if (tokens.empty() || tokens[0] == "c") {
          continue;
        }

        if (tokens[0] == "s") {
          checkSolutionConstraint(numBags == -1, "Multiple header in solution");
          checkSolutionConstraint(tokens.size() == 6, "Header must be 6 tokens <s htd numBags width NumVertex numHyperEdge>");
          checkSolutionConstraint(tokens[1] == "htd", "Second header token must be htd");

          numBags = parseInt(SOLUTION_READ_MODE, tokens[2]);
          width = parseInt(SOLUTION_READ_MODE, tokens[3]);
          numVertex = parseInt(SOLUTION_READ_MODE, tokens[4]);
          numHyperEdge = parseInt(SOLUTION_READ_MODE, tokens[5]);

          hypertree = Tree(numBags);
          bags.resize(numBags + 1);
          lambdaInBags.resize(numBags + 1);

          continue;
        }

        checkSolutionConstraint(numBags != -1, "Other description before header found");

        if (tokens[0] == "b") {
          checkSolutionConstraint(tokens.size() > 2, "Bag description must have at least 3 tokens");

          int bagIdx = parseInt(SOLUTION_READ_MODE, tokens[1]);
          checkSolutionConstraint(1 <= bagIdx && bagIdx <= numBags, "Bag index out of range [1, numBags]");
          checkSolutionConstraint(bags[bagIdx].empty(), "Multiple bag index found");

          set<int> vertexSeen;
          for (int i = 2 ; i < (int)tokens.size() ; i++) {
            int v = parseInt(SOLUTION_READ_MODE, tokens[i]);

            checkSolutionConstraint(!vertexSeen.count(v), "Multiple same vertex in a bag");
            checkSolutionConstraint(1 <= v && v <= numVertex, "Vertex index out of range [1, numVertex]");

            vertexSeen.insert(v);
            bags[bagIdx].push_back(v);
          }

          bagCount++;
          continue;
        }

        if (tokens[0] == "w") {
          checkSolutionConstraint(tokens.size() == 4, "Width function specification must consists of 4 tokens");

          int bagIdx = parseInt(SOLUTION_READ_MODE, tokens[1]);
          int hyperEdgeIdx = parseInt(SOLUTION_READ_MODE, tokens[2]);
          int value = parseInt(SOLUTION_READ_MODE, tokens[3]);

          checkSolutionConstraint(1 <= bagIdx && bagIdx <= numBags, "Width function bag Id out of range [1, numBags]");
          checkSolutionConstraint(1 <= hyperEdgeIdx && hyperEdgeIdx <= numHyperEdge, "Width function hyperedge Id out of range [1, numHyperEdge]");
          checkSolutionConstraint(value == 0 || value == 1, "Width function value must be 0 or 1");

          if (value > 0) {
            lambdaInBags[bagIdx].push_back(hyperEdgeIdx);
            // Should we do further checking that each width function is written at most once?
          }

          continue;
        }

        checkSolutionConstraint(tokens.size() == 2, "Hypertree edge must consists of 2 tokens");

        int u = parseInt(SOLUTION_READ_MODE, tokens[0]);
        int v = parseInt(SOLUTION_READ_MODE, tokens[1]);

        checkSolutionConstraint(1 <= u && u <= numBags, "First hypertree vertex out of range [1, numBags]");
        checkSolutionConstraint(1 <= v && v <= numBags, "Second hypertree vertex out of range [1, numBags]");
        hypertree.addEdge(u, v);
      }

      checkSolutionConstraint(numBags != -1, "No header found");
      checkSolutionConstraint(numBags == bagCount, "Number of bags differs with header");
      checkSolutionConstraint(getMaxWidth() == width, "Width differs with header");
      
      hypertree.makeRooted();
      checkSolutionConstraint(hypertree.isValidTree(), "Hypertree is not valid");
      checkSolutionConstraint(isAllVertexExist(), "There is vertex that is not in any bag");
      checkSolutionConstraint(isAllVertexBagsConnected(), "There exists not connected vertex bags component");
    }

    void write(ostream &stream) {
      stream << "s htd " << numBags << " " << width << " " << numVertex << " " << numHyperEdge << endl;

      vector<vector<int>> adjList = hypertree.getAdjacencyList();
      vector<int> parent = hypertree.getParent();

      for (int i = 1 ; i <= numBags ; i++) {
        if (parent[i] != i) {
          stream << parent[i] << " " << i << endl;
        }
      }

      for (int i = 1 ; i <= numBags ; i++) {
        // print bag
        stream << "b " << i;
        for (int vertex : bags[i]) {
          stream << " " << vertex;
        }
        stream << endl;

        // print lambda
        for (int lambda : lambdaInBags[i]) {
          stream << "w " << i << " " << lambda << " " << 1 << endl;
        }
      }
    }

  private:
    int getMaxWidth() {
      int maxWidth = 0;
      for (vector<int> lambda : lambdaInBags) {
        maxWidth = max(maxWidth, (int)lambda.size());
      }
      return maxWidth;
    }
    
    vector<vector<int>> getContainingVertex() {
      vector<vector<int>> vertexContaining(numVertex + 1);

      for (int i = 1; i <= numBags; i++) {
        for (int v : bags[i]) {
          vertexContaining[v].push_back(i);
        }
      }

      return vertexContaining;
    }

    bool isAllVertexExist() {
      vector<vector<int>> vertexContaining = getContainingVertex();

      for (int i = 1 ; i <= numVertex ; i++) {
        if (vertexContaining[i].empty()) {
          return false;
        }
      }

      return true;
    }

    bool isAllVertexBagsConnected() {
      vector<vector<int>> vertexContaining = getContainingVertex();

      for (int i = 1 ; i <= numVertex ; i++) {
        if (!hypertree.isConnectedComponent(vertexContaining[i])) {
          return false;
        }
      }

      return true;
    }

    int numBags;
    int width;
    int numVertex;
    int numHyperEdge;

    vector<vector<int>> bags;
    vector<vector<int>> lambdaInBags;
    Tree hypertree;
};

class ProblemInstance {
  public:
    int getNumVertex() {
      return numVertex;
    }

    int getNumHyperEdge() {
      return numHyperEdge;
    }

    vector<vector<int>> getHyperEdgeList() {
      return hyperEdgeList;
    }
  
    void readFromStream(ifstream &stream) {
      numVertex = -1;
      numHyperEdge = -1;
      hyperEdgeList.clear();

      string line;
      int lineNum = 0;
      int countHyperEdge = 0;

      while (getline(stream, line)) {
        lineNum++;
        vector<string> tokens = tokenize(line);
        
        if (tokens.empty() || tokens[0] == "c") {
          continue;
        }

        if (tokens[0] == "p") {
          checkInputConstraint(numVertex == -1, lineNum, "Multiple header");
          checkInputConstraint(tokens.size() == 4, lineNum, "Header not consisting of 4 tokens <p htd numVertex numEdge>");
          checkInputConstraint(tokens[0] == "p", lineNum, "First header token must be \"p\"");
          checkInputConstraint(tokens[1] == "htd" || tokens[1] == "htw", lineNum, "Second header token must be \"htd\"");
          
          numVertex = parseInt(INSTANCE_READ_MODE, tokens[2], lineNum);
          numHyperEdge = parseInt(INSTANCE_READ_MODE, tokens[3], lineNum);

          checkInputConstraint(numVertex > 0, lineNum, "numVertex must be positive");
          checkInputConstraint(numHyperEdge > 0, lineNum, "numHyperEdge must be positive");

          hyperEdgeList.resize(numHyperEdge+1);
          continue;
        }

        checkInputConstraint(numVertex != -1, lineNum, "Hyperedge specification before header");
        checkInputConstraint(tokens.size() > 1, lineNum, "Hyperedge must consists of at least one vertice(s)");

        int edgeIdx = parseInt(INSTANCE_READ_MODE, tokens[0], lineNum);
        checkInputConstraint(1 <= edgeIdx && edgeIdx <= numHyperEdge, lineNum, "Edge index out of range [1, numHyperEdge]");
        checkInputConstraint(hyperEdgeList[edgeIdx].empty(), lineNum, "Multiple edge with same index");
        
        set<int> vertexSeen;
        for (int i = 1 ; i < (int)tokens.size() ; i++) {
          int u = parseInt(INSTANCE_READ_MODE, tokens[i], lineNum);

          checkInputConstraint(1 <= u && u <= numVertex, lineNum, "Vertex out of range [1, numVertex]");
          checkInputConstraint(!vertexSeen.count(u), lineNum, "Hyperedge contains multiple vertex with same number");

          vertexSeen.insert(u);
          hyperEdgeList[edgeIdx].push_back(u);
        }

        countHyperEdge++;
      }

      checkInputConstraint(numVertex != -1, -1, "No header found");
      checkInputConstraint(countHyperEdge == numHyperEdge, -1, "Hyperedge number differs from actual");
    }

    void write(ostream &stream) {
      stream << "p htd " << numVertex << " " << numHyperEdge << endl;

      for (int i = 1 ; i <= numHyperEdge ; i++) {
        stream << i;
        for (int v : hyperEdgeList[i]) {
          stream << " " << v;
        }

        stream << endl;
      }
    }

    int validate(Solution &s) {
      DO_CHECK_CONSTRAINT = true;

      checkSolutionConstraint(s.getNumVertex() == numVertex, "Number of vertex from header differs");
      checkSolutionConstraint(s.getNumHyperEdge() == numHyperEdge, "Number of hyperedge from header differs");
      checkSolutionConstraint(isAllHyperEdgeCovered(s), "Not all hyperedge is a subset of some bag");
      checkSolutionConstraint(isLambdaCoveringAllBags(s), "Not all bags are covered by width function");
      checkSolutionConstraint(isSatisfyingAllDescendantCondition(s), "Not all descendant condition satisfied");

      return 1;
    }

  private:
   int numVertex;
   int numHyperEdge;
   vector<vector<int>> hyperEdgeList;

    bool isAllHyperEdgeCovered(Solution &s) {
      for (int i = 1 ; i <= numHyperEdge ; i++) {
        if (!isHyperEdgeCovered(s, i)) {
          return false;
        }
      }

      return true;
    }

    bool isHyperEdgeCovered(Solution &s, int hyperEdgeIdx) {
      for (int i = 1 ; i <= s.getNumBags() ; i++) {
        set<int> intersection = getSetIntersection(s.getBagFromId(i), hyperEdgeList[hyperEdgeIdx]);
        bool allCovered = all_of(hyperEdgeList[hyperEdgeIdx].begin(), hyperEdgeList[hyperEdgeIdx].end(), [intersection](int iter) {
          return intersection.count(iter);
        });

        if (allCovered) {
          return true;
        }
      }

      return false;
    }

    bool isLambdaCoveringAllBags(Solution &s) {
      for (int i = 1 ; i <= s.getNumBags() ; i++) {
        if (!isLambdaCoveringBags(s, i)) {
          return false;
        }
      }

      return true;
    }

    bool isLambdaCoveringBags(Solution &s, int bagIdx) {
      vector<int> lambda = s.getLambdaInBagFromId(bagIdx);
      vector<int> bag = s.getBagFromId(bagIdx);
      set<int> coveredVertex;

      for (int hyperEdgeIdx : lambda) {
        addVectorToSet(coveredVertex, hyperEdgeList[hyperEdgeIdx]);
      }

      return all_of(bag.begin(), bag.end(), [coveredVertex](int iter) {
        return coveredVertex.count(iter);
      });
    }

    bool isSatisfyingAllDescendantCondition(Solution &s) {
      for (int i = 1 ; i <= s.getNumBags() ; i++) {
        if (!isSatisfyingDescendantCondition(s, i)) {
          return false;
        }
      }

      return true;
    }

    bool isSatisfyingDescendantCondition(Solution &s, int bagIdx) {
      vector<int> descendants = s.getHyperTree().getSubtree(bagIdx);
      set<int> bagDescendants;

      for (int descendant : descendants) {
        addVectorToSet(bagDescendants, s.getBagFromId(descendant));
      }

      vector<int> descendantBagVec(bagDescendants.begin(), bagDescendants.end());
      vector<int> bag = s.getBagFromId(bagIdx);
      set<int> bagSet(bag.begin(), bag.end());

      vector<int> lambdas = s.getLambdaInBagFromId(bagIdx);

      for (int lambda : lambdas) {
        set<int> intersection = getSetIntersection(descendantBagVec, hyperEdgeList[lambda]);
        
        bool isSubset = all_of(intersection.begin(), intersection.end(), [bagSet](int iter) {
          return bagSet.count(iter);
        });

        if (!isSubset) {
          return false;
        }
      }

      return true;
    }
};

ProblemInstance problemInstance;
Solution judgeSolution, userSolution;
double userTime;

int main(int argc, char **argv) {
  if (argc < 3) {
    printf("Usage: %s instance_input solution_output [instance_output]\n", argv[0]);
    return 0;
  }

  if (argc >= 5) {
    sscanf(argv[4], "%lf", &userTime);
    // since OPTIL give use 100 * time in seconds..
    // userTime /= 100.0;

    if (userTime > TIMEOUT_TIME) {
      giveVerdict(-TIMEOUT_TIME * 2, "Time Limit Exceeded");
    }
  }

  ifstream instanceInputStream(argv[1]);
  ifstream userOutputStream(argv[2]);

  if (!userOutputStream) {
    // No output
    checkSolutionConstraint(false, "No output produced by user");
  }

  problemInstance.readFromStream(instanceInputStream);
  userSolution.readFromStream(userOutputStream, true);
  if (argc >= 4) {
    ifstream instanceOutputStream(argv[3]);
    judgeSolution.readFromStream(instanceOutputStream, false);
  }

  int valid = problemInstance.validate(userSolution);

  if (argc >= 4) {
    valid &= (userSolution.getWidth() <= judgeSolution.getWidth());
  }

  DO_CHECK_CONSTRAINT = true;
  checkSolutionConstraint(valid, "Reported hypertree decomposition is not optimal");

  giveVerdict(userTime, "SUCCESS");

  return 0;
}
