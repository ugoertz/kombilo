import os.path
import urllib2
import glob
from fabric.api import run, cd, local, lcd, prefix, get, put

MAJOR_VERSION = '0.8'
VERSION = '0.8.4'
BASE_DIR = os.path.dirname(__file__)
VIRTUALENV = '/bin/bash /home/ug/.virtualenvs/k08/bin/activate'

DOC_BASEPATH = '/home/ug/docker/ugonet/ugonet/data/media/kombilo/'
DOXY_BASEPATH = '/home/ug/docker/ugonet/ugonet/data/media/libkombilo/'
PDF_PATH = DOC_BASEPATH


def deploy_doc():
    """
    Create and upload html documentation from the documentation files currently
    in place. The script will run doxygen, but will assume that the SWIG created
    files (and also the compiled _libkombilo.so?) are in place. Also, it is
    assumed that doxygen and the packages in requirements-doc.txt are installed.

    This file will overwrite the previous documentation copy on the server.

    Usage: fab -H host_to_upload_to deploy_doc

    Adjust VIRTUALENV, DOC_BASEPATH above, if necessary.
    """

    # run sphinx
    with prefix(VIRTUALENV):
        with lcd('%s/doc' % BASE_DIR):
            local('make clean')
            local('make html')
        with lcd('%s/doc/_build' % BASE_DIR):
            local('tar cfz html.tar.gz html')
            put('html.tar.gz', DOC_BASEPATH)
    with cd(DOC_BASEPATH):
        run('tar xf html.tar.gz')
        run('rm -rf doc%s' % MAJOR_VERSION.replace('.', ''))
        run('mv html doc%s' % MAJOR_VERSION.replace('.', ''))
        run('rm -f html.tar.gz')

    # run doxygen
    with lcd('%s/kombilo/libkombilo/doc' % BASE_DIR):
        local('rm -rf build')
        local('doxygen')
    with lcd('%s/kombilo/libkombilo/doc/build' % BASE_DIR):
        local('tar cfz html.tar.gz html')
        put('html.tar.gz', DOXY_BASEPATH)
    with cd(DOXY_BASEPATH):
        run('tar xf html.tar.gz')
        run('rm -rf doc%s' % MAJOR_VERSION.replace('.', ''))
        run('mv html doc%s' % MAJOR_VERSION.replace('.', ''))
        run('rm -f html.tar.gz')


def doc_as_pdf():
    """
    Create and upload pdf from the documentation files currently in place.

    Usage: fab -H host_to_upload_to doc_as_pdf

    Adjust VIRTUALENV, PDF_PATH above, if necessary.
    """

    with prefix(VIRTUALENV):
        with lcd('%s/doc' % BASE_DIR):
            local('make clean')
            local('make latexpdf')
    with lcd('%s/doc/_build/latex/' % BASE_DIR):
        put('Kombilo.pdf', '%s/kombilo-%s.pdf' % (PDF_PATH, VERSION))


# --------------- deploy source distribution to PyPI -----------------------

# make sure swig generated files are in place (kombilo/libkombilo.py,
# kombilo/libkombilo/libkombilo_wrap.cxx), otherwise generate with ``swig -c++
# -python libkombilo.i`` (in kombilo/libkombilo)

# make sure the *.mo language files are in place (compile with
# ``pybabel compile -D kombilo -d kombilo/lang``

# create sdist package: ``python setup.py sdist``
# (test the package: pip install kombiloXXX.tar.gz in a fresh virtualenv)

# tag github release (not necessary for the deploy process, just for bookkeeping)
# upload to PyPI: ``twine upload dist/kombilo-0.8.tar.gz``


# -------- deploy Windows installer (just some notes) --------------------------

# merge changes into v0.8win branch
# tag the final version there: ``git tag K08winXYZ``
# push the tag: ``git push origin K08winXYZ``
# (this will trigger a build on Appveyor)
# download (and test) the installer exe files from Appveyor
# upload the installer files to u-go.net

