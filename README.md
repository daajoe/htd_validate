# Validator for hypertree decompositions 
The library allows to validate a given hypertree decomposition and versions, in particular, fractionalhypertree decompositions.

The library also provides data structures for hypergraphs (following the networkx API) and decompositions (text format extends the PACE 2017 specification for tree decompositions to hypergraphs and hypertree decompositions, generalized hypertree decompositions, and fractional hypertree decompositions).

## Python Version
For the moment we support python27 only.

## Download:
```bash
git clone --recurse-submodules  git@github.com:daajoe/fractionalhypertreewidth.git
````


## External Requirements (requirements.txt)
```bash
pip install -r requirements.txt
```

## Manpage
```bash
bin/htd_validate --help
```

## Validate Hypertree Decompositions
```bash
bin/htd_validate -g hypergraphfile.gr -d hyperdecomposition.htd -t htd
```


## Input Formats

### Hypertrees and Hypertree Decompositions
See [FORMAT_HTD.md](FORMAT_HTD.md)