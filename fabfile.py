import os.path
import urllib2
from fabric.api import run, cd, local, lcd, prefix, get, put

# FIXME directories below depend on version!


# --------------- documentation

def deploy_doc():
    with cd('/home/ug/www.u-go.net/k08-bb'):
        run('hg pull -u')  # note: as a prerequisite, the repository must be in the right branch!
    with cd('/home/ug/www.u-go.net/k08-bb/lk'):
        run('swig -c++ -python libkombilo.i')
        run('python setup.py build_ext')
        run('cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
    with cd('/home/ug/www.u-go.net/k08-bb/doc'):
        run('rm -rf ../../dl/kombilo/doc')
        run('sphinx-build -A ugonet_online=1 -b html . ../../dl/kombilo/doc')
    with cd('/home/ug/www.u-go.net/k08-bb/lk/doc'):
        run('doxygen')
        run('rm -rf ../../../dl/libkombilo/doc')
        run('cp -a build/html ../../../dl/libkombilo/doc')


def doc_as_pdf():
    with prefix('source /home/ug/.virtualenvs/k08-bb/bin/activate'):
        with lcd('/home/ug/devel/k08-bb/doc'):
            local('make clean')
            local('make latex')
            local('cp sphinx.sty _build/latex/')
    with lcd('/home/ug/devel/k08-bb/doc/_build/latex/'):
        local('make all-pdf')
        local('mv Kombilo.pdf kombilo-0.8.pdf')


# --------------- pootle

LANGUAGES = ['de', 'eo']


def pootle_start_maintenance():
    run('sudo a2dissite pootlek')
    run('sudo a2ensite pootlek-maintenance')
    run('sudo service apache2 reload')


def pootle_end_maintenance():
    run('sudo a2dissite pootlek-maintenance')
    run('sudo a2ensite pootlek')
    run('sudo service apache2 reload')


def download_po():
    with prefix('source /home/ugy/.virtualenvs/pootlekombilo/bin/activate'):
        with cd('/home/ugy/devel/pootlekombilo/Pootle-2.1.6'):
            run('./manage.py sync_stores --project kombilo')

    with lcd('lang'):
        for lang in LANGUAGES:
            with lcd('%s/LC_MESSAGES' % lang):
                get('/home/ugy/devel/pootlekombilo/Pootle-2.1.6/po/kombilo/%s/kombilo.po' % lang, './kombilo.po')
                local('msgfmt -o kombilo.mo kombilo.po')


def upload_pot():
    '''Adds new strings to po files/removes unecessary ones. To do this:

    * obtain the current po files from pootle
    * create new pot file using pygettext
    * apply msgmerge
    * upload the merged files to pootle
    '''

    pootle_start_maintenance()
    download_po()

    # create new pot file:
    with prefix('source /home/ug/.virtualenvs/k08-bb/bin/activate'):
        with lcd('src'):
            local('pygettext -p ../lang/ kombilo.py v.py kombiloNG.py')

    with lcd('lang'):
        # update kombilo.po file for "en"
        local('msgmerge -U en/LC_MESSAGES/kombilo.po messages.pot')

        # merge other po files and upload them to pootle
        for lang in LANGUAGES:
            local('msgmerge -U %s/LC_MESSAGES/kombilo.po messages.pot' % lang)
            with lcd('%s/LC_MESSAGES' % lang):
                local('msgfmt -o kombilo.mo kombilo.po')
                put('kombilo.po', '/home/ugy/devel/pootlekombilo/Pootle-2.1.6/po/kombilo/%s/kombilo.po' % lang, mode=0660)
                run('chgrp www-data /home/ugy/devel/pootlekombilo/Pootle-2.1.6/po/kombilo/%s/kombilo.po' % lang)

    with prefix('source /home/ugy/.virtualenvs/pootlekombilo/bin/activate'):
        with cd('/home/ugy/devel/pootlekombilo/Pootle-2.1.6'):
            run('./manage.py update_stores --project kombilo')

    pootle_end_maintenance()


# --------------- kombilo main/linux

def deploy_targz():
    with lcd('/home/ug/devel'):
        local('mkdir kombilo')
        local('rm -f kombilo-0.8.tar.gz')
        local('hg clone k08-bb kombilo')
    with lcd('/home/ug/devel/kombilo/'):
        local('hg update default')
    with lcd('/home/ug/devel/kombilo/lk/doc'):
        local('doxygen')

    with lcd('/home/ug/devel/kombilo/lk'):
        local('swig -c++ -python libkombilo.i')
        with prefix('source /home/ug/.virtualenvs/k08-bb/bin/activate'):
            local('python setup.py build_ext')
        local('cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
        local('rm -rf build')
    with prefix('source /home/ug/.virtualenvs/k08-bb/bin/activate'):
        with lcd('/home/ug/devel/kombilo/doc'):
            local('make html')
    with lcd('/home/ug/devel/kombilo'):
        local('rm src/_libkombilo.so')
        local('rm */*.pyc')
        local('rm */*/*.pyc')
        local('rm -rf .hg')
        local('rm -f fabfile.py')
    with lcd('/home/ug/devel'):
        local('tar cfz kombilo-0.8.tar.gz kombilo')
        local('rm -rf kombilo')


# --------------- kombilo main/windows installer

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
    for f in ['sqlite3.dll', 'Pmw.py', 'PmwBlt.py', 'PmwColor.py']:
        local('copy /y c:\\Users\\ug\\kombilo-util\\%s \\Users\\ug\\kombilo\\src\\ ' % f)

    # do py2exe
    with lcd(r'c:\Users\ug\kombilo\src'):
        # clean up
        if os.path.exists('dist'):
            local('rd /q /s dist')
        local('python setup.py py2exe')


def win_innosetup():
    # copy stuff for innosetup
    # vcredist_x86.exe: http://www.microsoft.com/download/en/confirmation.aspx?id=5582
    for f in ['vcredist_x86.exe']:
        local('copy /y c:\\Users\\ug\\kombilo-util\\%s \\Users\\ug\\kombilo\\src\\dist\\ ' % f)

    for f in ['kombilo.ico']:
        local('copy /y c:\\Users\\ug\\kombilo\\%s \\Users\\ug\\kombilo\\src\\dist\\ ' % f)

    # build docs
    with lcd(r'c:\Users\ug\kombilo\doc'):
        local('sphinx-build -b html . ..\src\dist\doc')

    # add source archive
    u = urllib2.urlopen('https://bitbucket.org/ugoertz/kombilo/get/default.zip')  # FIXME
    with open('c:\Users\ug\kombilo\src\dist\kombilo-source.zip', 'wb') as f:
        f.write(u.read())

    # innosetup
    with lcd(r'c:\Users\ug\kombilo'):
        local(r'"c:\Program Files\Inno Setup 5\ISCC" kombilo.iss')


def deploy_win():
    win_libkombilo()
    win_py2exe()
    win_innosetup()
