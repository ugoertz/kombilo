import sys
from setuptools import setup, find_packages, Extension


sources = [
        'kombilo/libkombilo/sgfparser.cpp',
        'kombilo/libkombilo/abstractboard.cpp',
        'kombilo/libkombilo/search.cpp',
        'kombilo/libkombilo/algos.cpp',
        'kombilo/libkombilo/pattern.cpp',
        'kombilo/libkombilo/libkombilo_wrap.cxx']

kwargs = {}

if sys.platform.startswith('win'):
    sources.append('kombilo/libkombilo/sqlite3.c')
    kwargs['library_dirs'] = ['C:\\Libraries\\boost_1_62_0', ]
    kwargs['extra_compile_args'] = ['-I.', '-IC:\\Libraries\\boost_1_62_0', '-openmp']
elif sys.platform.startswith('darwin'):
    kwargs['libraries'] = ['stdc++', 'sqlite3']
    kwargs['library_dirs'] = ['/usr/lib', ]
    kwargs['extra_compile_args'] = ['-I.', '-I/usr/local/include', '-I/opt/local/include']  # can use this w/ g++ to max optimization
    kwargs['extra_link_args'] = [ ]
else:
    kwargs['libraries'] = ['stdc++', 'sqlite3']
    kwargs['library_dirs'] = ['/usr/lib', ]
    kwargs['extra_compile_args'] = ['-O3', '-I.', '-fopenmp']  # can use this w/ g++ to max optimization
    kwargs['extra_link_args'] = [ '-lgomp', ]

kwargs['sources'] = sources

sgfext = Extension('kombilo._libkombilo', **kwargs)


setup(
        name = 'kombilo',
        version = '0.8.2',
        description = 'A database program for the game of go',
        author = 'Ulrich Goertz',
        author_email = 'ug@geometry.de',
        url = 'http://u-go.net/kombilo/',
        license = 'MIT License',
        classifiers=[
            'Programming Language :: Python :: 2.7',
            ],
        entry_points = {'gui_scripts': [
            'kombilo = kombilo.kombilo:run',
            'v = kombilo.v:run',
            ], },
        ext_modules = [ sgfext ],
        packages = find_packages(),
        package_data = {'kombilo': [
            'default.cfg',
            'data/*',
            'license.rst',
            'icons/*.*',
            'tests/sgfs/*.sgf', 'tests/db/.keep',
            'libkombilo/*.h',
            'lang/*/LC_MESSAGES/kombilo.?o',
            ], },
        install_requires = [
            'configobj',
            'Pillow',
            'Pmw',
            ],
        tests_require=['pytest'],
        )
