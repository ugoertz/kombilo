from fabric.api import run, cd, local, lcd, prefix, env

def deploy_doc():
    with cd('/home/ug/www.u-go.net/k07-bb'):
        run('hg pull -u')
    with cd('/home/ug/www.u-go.net/k07-bb/lk'):
        run('rm -rf ../../dl/kombilo/doc')
        run('swig -c++ -python libkombilo.i')
        run('python setup.py build_ext')
        run('cp libkombilo.py build/lib.linux-*/_libkombilo.so ../src/')
    with cd('/home/ug/www.u-go.net/k07-bb/doc'):
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
        local('mv Kombilo.pdf kombilo-0.7.pdf')


def deploy_targz():
    with lcd('/home/ug/devel'):
        local('mkdir kombilo')
        local('rm -f kombilo-0.7.tar.gz')
        local('hg clone k07-bb kombilo')
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
        local('tar cfz kombilo-0.7.tar.gz kombilo')
        local('rm -rf kombilo')


    

