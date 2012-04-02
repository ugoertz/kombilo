import os.path
import urllib2
from fabric.api import run, cd, local, lcd, prefix, env

def deploy_doc():
    with cd('/home/ug/www.u-go.net/k07-bb'):
        run('hg pull -u') # note: as a prerequisite, the repository must be in the right branch!
    with cd('/home/ug/www.u-go.net/k07-bb/lk'):
        run('swig -c++ -python libkombilo.i')
        run('python setup.py build_ext')
        run('cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
    with cd('/home/ug/www.u-go.net/k07-bb/doc'):
        run('rm -rf ../../dl/kombilo/doc')
        run('sphinx-build -A ugonet_online=1 -b html . ../../dl/kombilo/doc')
    with cd('/home/ug/www.u-go.net/k07-bb/lk/doc'):
        run('doxygen')
        run('rm -rf ../../../dl/libkombilo/doc')
        run('cp -a build/html ../../../dl/libkombilo/doc')


def doc_as_pdf():
    with prefix('source /home/ug/.virtualenvs/k07-bb/bin/activate'):
        with lcd('/home/ug/devel/k07-bb/doc'):
            local('make clean')
            local('make latex')
            local('cp sphinx.sty _build/latex/')
    with lcd('/home/ug/devel/k07-bb/doc/_build/latex/'):
        local('make all-pdf')
        local('mv Kombilo.pdf kombilo-0.7.1.pdf')


def deploy_targz():
    with lcd('/home/ug/devel'):
        local('mkdir kombilo')
        local('rm -f kombilo-0.7.1.tar.gz')
        local('hg clone k07-bb kombilo')
    with lcd('/home/ug/devel/kombilo/'):
        local('hg update v0.7')
    with lcd('/home/ug/devel/kombilo/lk/doc'):
        local('doxygen')

    with lcd('/home/ug/devel/kombilo/lk'):
        local('swig -c++ -python libkombilo.i')
        with prefix('source /home/ug/.virtualenvs/k07-bb/bin/activate'):
            local('python setup.py build_ext')
        local('cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
        local('rm -rf build')
    with prefix('source /home/ug/.virtualenvs/k07-bb/bin/activate'):
        with lcd('/home/ug/devel/kombilo/doc'):
            local('make html')
    with lcd('/home/ug/devel/kombilo'):
        local('rm src/_libkombilo.so')
        local('rm */*.pyc')
        local('rm */*/*.pyc')
        local('rm -rf .hg')
        local('rm -f fabfile.py')
    with lcd('/home/ug/devel'):
        local('tar cfz kombilo-0.7.1.tar.gz kombilo')
        local('rm -rf kombilo')




def win_libkombilo():
    # copy boost
    if not os.path.exists(r'c:\Users\ug\kombilo\lk\boost'):
        local(r'xcopy /i /s c:\Users\ug\kombilo-util\boost_1_49_0\boost c:\Users\ug\kombilo\lk\boost ')


    with lcd(r'c:\Users\ug\kombilo\lk'):
        # clean up
        if os.path.exists('build'):
            local('rd /q /s build')

        # SWIG
        local(r'"c:\Program Files\swigwin-2.0.4\swig" -c++ -python libkombilo.i')

        # build extension
        local('python setup.py build_ext')

        # copy
        local(r'copy /y libkombilo.py ..\src\ ')
        local(r'copy /y build\lib.win32-2.7\_libkombilo.pyd ..\src\ ')


def win_py2exe():
    # copy stuff for py2exe
    # to create the Pmw.py file use http://pmw.cvs.sourceforge.net/viewvc/pmw/Pmw/Pmw_0_0_0/bin/bundlepmw.py?revision=1.3&view=markup
    for f in ['sqlite3.dll', 'Pmw.py', 'PmwBlt.py', 'PmwColor.py' ]:
        local('copy /y c:\\Users\\ug\\kombilo-util\\%s \\Users\\ug\\kombilo\\src\\ ' % f)

    # do py2exe
    with lcd(r'c:\Users\ug\kombilo\src'):
        # clean up
        if os.path.exists('dist'): local('rd /q /s dist')
        local('python setup.py py2exe')

def win_innosetup():
    # copy stuff for innosetup
    # vcredist_x86.exe: http://www.microsoft.com/download/en/confirmation.aspx?id=5582
    for f in ['vcredist_x86.exe']:
        local('copy /y c:\\Users\\ug\\kombilo-util\\%s \\Users\\ug\\kombilo\\src\\dist\\ ' % f)

    for f in ['kombilo.ico' ]:
        local('copy /y c:\\Users\\ug\\kombilo\\%s \\Users\\ug\\kombilo\\src\\dist\\ ' % f)

    # build docs
    with lcd(r'c:\Users\ug\kombilo\doc'):
       local('sphinx-build -b html . ..\src\dist\doc')

    # add source archive
    u = urllib2.urlopen('https://bitbucket.org/ugoertz/kombilo/get/v0.7.zip')
    with open('c:\Users\ug\kombilo\src\dist\kombilo-source.zip', 'wb') as f:
        f.write(u.read())

    # innosetup
    with lcd(r'c:\Users\ug\kombilo'):
        local(r'"c:\Program Files\Inno Setup 5\ISCC" kombilo.iss')


def deploy_win():
    win_libkombilo()
    win_py2exe()
    win_innosetup()



    

