import re
from setuptools import setup
from setuptools import find_packages


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
        'click>=6.3',
        'PyYAML>=3.11',
        'honcho>=0.6.6',
    ],
    entry_points = {
        "console_scripts": ['toadie = toadie.toadie:main']
    },
    description = "Command line interface for development of microservices with the ambassador pattern.",
    long_description = open('README.rst').read(),
    author = headers['__author__'],
    author_email = headers['__email__'],
    license='Apache Software License',
    classifiers=[
    # How mature is this project? Common values are
    #   3 - Alpha
    #   4 - Beta
    #   5 - Production/Stable
    'Development Status :: 3 - Alpha',

    # Indicate who your project is intended for
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',

    # Pick your license as you wish (should match "license" above)
    'License :: OSI Approved :: Apache Software License',

    # Specify the Python versions you support here. In particular, ensure
    # that you indicate whether you support Python 2, Python 3 or both.
    'Programming Language :: Python :: 2.7',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.2',
    'Programming Language :: Python :: 3.3',
    'Programming Language :: Python :: 3.4',
    ],
    keywords='docker,microservices',
    packages=find_packages(exclude=['tests'])
)
