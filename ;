import re
from setuptools import setup


headers = dict()
src = open('toadie/toadie.py', 'r').read()
variables = {'__version__','__copyright__','__author__','__email__','__license__'}
for var in variables:
    headers[var] = re.search('^{}\s*=\s*"(.*)"'.format(var),
                            src,
                            re.M).group(1)

setup(
    name='toadie',
    version = headers['__version__'],
    py_modules=['toadie'],
    install_requires=[
        'Click',
    ],
    entry_points = {
        "console_scripts": ['toadie = toadie.toadie:main']
    },
    description = "Command line interface for development of microservices with the ambassador pattern.",
    long_description = open('README.rst').read(),
    author = headers['__author__'],
    author_email = headers['__email__'],
)
