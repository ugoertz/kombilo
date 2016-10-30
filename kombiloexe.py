# Need this as a starting point for PyInstaller, so that kombilo is considered
# as a Python package and relative imports work. (Similarly to "pip install -e
# ." being required for using Kombilo from a development directory.)


from kombilo import kombilo

if __name__ == '__main__':
    kombilo.run()
