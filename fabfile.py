import os.path
import urllib2
import glob
from fabric.api import run, cd, local, lcd, prefix, get, put

VERSION = '0.8.1'
GIT_BRANCH = 'v0.8'
DEVEL_BASE = '/home/ug/devel'
DEVEL_DIR = 'kombilo'
BASE_DIR = os.path.join(DEVEL_BASE, DEVEL_DIR)
VIRTUALENV = '/bin/bash /home/ug/.virtualenvs/k08/bin/activate'

def deploy_doc():
    with lcd('%s' % BASE_DIR):
        local('git checkout %s' % GIT_BRANCH)
        local('git pull')
    with lcd('%s/lk' % BASE_DIR):
        local('swig -c++ -python libkombilo.i')
        with prefix(VIRTUALENV):
            local('python setup.py build_ext')
        local('cp -n libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
    with prefix(VIRTUALENV):
        with lcd('%s/doc' % BASE_DIR):
            # run('rm -rf ../../dl/kombilo/doc')
            local('make html')
    with lcd('%s/lk/doc' % BASE_DIR):
        local('doxygen')
        #  local('rm -rf ../../../dl/libkombilo/doc')
        #  local('cp -a build/html ../../../dl/libkombilo/doc')


def doc_as_pdf():
    with prefix(VIRTUALENV):
        with lcd('%s/doc' % BASE_DIR):
            local('make clean')
            local('make latexpdf')
    with lcd('%s/doc/_build/latex/' % BASE_DIR):
        local('mv Kombilo.pdf kombilo-%s.pdf' % VERSION)


# --------------- pootle

LANGUAGES = [os.path.basename(lang) for lang in  glob.glob('lang/*') if os.path.basename(lang).find('.') == -1]
LANGUAGES.remove('en')


def pootle_start_maintenance():
    run('sudo a2dissite pootlek')
    run('sudo a2ensite pootlek-maintenance')
    run('sudo service apache2 reload')


def pootle_end_maintenance():
    run('sudo a2dissite pootlek-maintenance')
    run('sudo a2ensite pootlek')
    run('sudo service apache2 reload')


def download_po(ignore_errors=False):
    with prefix('source /home/ugy/.virtualenvs/pootlekombilo/bin/activate'):
        with cd('/home/ugy/devel/pootlekombilo/Pootle-2.1.6'):
            run('./manage.py sync_stores --project kombilo')

    with lcd('lang'):
        for lang in LANGUAGES:
            with lcd('%s/LC_MESSAGES' % lang):
                try:
                    get('/home/ugy/devel/pootlekombilo/Pootle-2.1.6/po/kombilo/%s/kombilo.po' % lang, './kombilo.po')
                except:
                    if not ignore_errors:
                        raise
                else:
                    local('msgfmt -o kombilo.mo kombilo.po')


def upload_pot_new():
    """Upload po files, also for a newly created language, so that we should ignore the "file not found" error in download_po.
    """
    upload_pot(ignore_errors=True)


def upload_pot(ignore_errors=False):
    '''Adds new strings to po files/removes unecessary ones. To do this:

    * obtain the current po files from pootle
    * create new pot file using pygettext
    * apply msgmerge
    * upload the merged files to pootle
    '''

    pootle_start_maintenance()
    download_po(ignore_errors=ignore_errors)

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
    with lcd(DEVEL_BASE):
        local('mkdir kombilo-%s' % VERSION)
        local('rm -f kombilo-%s.tar.gz' % VERSION)
        local('git clone %s kombilo-%s' % (DEVEL_DIR, VERSION))
    with lcd('%s/kombilo-%s' % (DEVEL_BASE, VERSION)):
        local('git checkout v0.7')
    with lcd('%s/kombilo-%s/lk/doc' % (DEVEL_BASE, VERSION)):
        local('doxygen')

    with lcd('%s/kombilo-%s/lk' % (DEVEL_BASE, VERSION)):
        local('swig -c++ -python libkombilo.i')
        with prefix(VIRTUALENV):
            local('python setup.py build_ext')
        local('cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
        local('rm -rf build')
    with prefix(VIRTUALENV):
        with lcd('%s/kombilo-%s/doc' % (DEVEL_BASE, VERSION)):
            local('make html')
    with lcd('%s/kombilo-%s' % (DEVEL_BASE, VERSION)):
        local('rm src/_libkombilo.so')
        local('rm -f */*.pyc')
        local('rm -f */*/*.pyc')
        local('rm -rf .git .gitignore')
        local('rm -f fabfile.py')
    with lcd('%s' % DEVEL_BASE):
        local('tar cfz kombilo-%s.tar.gz kombilo-%s' % (VERSION, VERSION))
        local('rm -rf kombilo-%s' % VERSION)


