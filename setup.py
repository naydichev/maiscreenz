from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name             = 'maiscreenz',
    version          = '0.2',
    packages         = find_packages(),
    long_description = open(join(dirname(__file__), 'README.md')).read(),
    entry_points     = {
        'console_scripts':
            [ 'maiscreenz = maiscreenz.cli:main' ]
    },
    install_requires = [
        'gntp==0.7',
        'MacFSEvents==0.2.6',
        'paramiko==1.7.7.1',
        'xerox==0.3.1',
    ],
)
