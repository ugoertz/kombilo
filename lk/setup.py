import sys
from distutils.core import setup, Extension
 
sgfext = Extension('_libkombilo', 
                   sources = ['sgfparser.cpp', 'abstractboard.cpp', 'search.cpp', 'algos.cpp', 'pattern.cpp', 'libkombilo_wrap.cxx'],
                   libraries=['stdc++', 'sqlite3'], 
                   library_dirs=['/usr/lib', ], # '.', './boost', './boost/unordered', './boost/unordered/detail' ],
                   extra_compile_args = ['-O3', '-I.', '-fopenmp'], # can use this w/ g++ to max optimization
                   extra_link_args = [ '-lgomp', ],
                  )

setup(name = 'libkombilo', ext_modules = [ sgfext ])

