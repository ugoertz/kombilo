import os, glob
# from cx_Freeze import setup, Executable
from distutils.core import setup
import py2exe

doclist = ['doc/'+os.path.split(f)[1] for f in glob.glob('./doc/*')]
giflist = ['icons/'+os.path.split(f)[1] for f in glob.glob('./icons/*')]

# includefiles = [ 'default.cfg', 'data/references' ] + giflist

setup(
        name = "kombilo",
        version = "0.8",
        description = "Kombilo - a go database program",
        # executables = [ target ],
        windows=['kombilo.py'],
        py_modules=['board', 'v'],
        options = { 'py2exe': { 'dll_excludes':  [ 'MSVCP90.dll', 'MSVCR90.dll' ], }
                # 'build_exe': { 'include_files': includefiles,
                #                'includes': [ 're' ], }
                  },
        data_files=[('.', ['default.cfg', ]),
                    ('doc', doclist),
                    ('icons', giflist),
                    ('data', ['data/references'] ),
                   ]
    )

