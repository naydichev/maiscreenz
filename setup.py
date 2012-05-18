from setuptools import setup, find_packages
from os.path import join, dirname
import maiscreenz

setup(
    name             = 'maiscreenz',
    version          = maiscreenz.__version__,
    packages         = find_packages(),
    long_description = open(join(dirname(__file__), 'README.md')).read(),
    entry_points     = {
        'console_scripts':
            [ 'maiscreenz = maiscreenz.core:start_watching' ]
    },
    install_requires = [
        'gntp==0.7',
        'MacFSEvents==0.2.6',
        'paramiko==1.7.7.1',
        'xerox==0.3.1',
    ],
)

maiscreenz.write_sample_config()
