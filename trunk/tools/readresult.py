#!/usr/bin/python
import pickle, sys
f = open(sys.argv[1])
pk = pickle.load(f)
f.close()
print pk
