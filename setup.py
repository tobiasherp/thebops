#!/usr/bin/env python
# -*- coding: latin1 -*- vim: ts=8 sts=4 sw=4 si et tw=79
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from os.path import dirname, abspath, join, sep

def read(name):
    fn = join(dirname(abspath(__file__)), name)
    return open(fn, 'r').read()

__author__ = "Tobias Herp <tobias.herp@gmx.net>"
VERSION = (0,
           1,   # initial version
           ''.join(map(str, (
           16,  # py2/py3 for non-Linux only; ...
           ))),
           ## the Subversion revision is added by setuptools:
           # 'rev-%s' % '$Rev: 1102 $'[6:-2],
           )
__version__ = '.'.join(map(str, VERSION))

console_scripts = [
            '%s_demo = thebops.tools.%s_demo:main' % (s, s.replace('-', '_'))
            for s in [
                'colours',
                'counters',
                'iscales',
                'likeix',
                'opo',
                'optparse',
                'rexxbi',
                'shtools',
                'termwot',
                # the contents of these modules might move
                # once better names are found:
                'misc1',
                ]
            ] + [
            '%s = thebops.%s:main' % (s, s)
            for s in [
                'modinfo',
                ]
            ] + [
            '%s = thebops.tools.%s:main' % (s, s.replace('-', '_'))
            for s in [
                'xfind',
                # 'sort-po',    # still buggy
                ]
            ]

# These functions are currently not functional on Linux systems.
# Thus, they are only included when not installing,
# or with any command on a non-Linux system
# (quick-and-dirtily told from the directory separator character)
from sys import argv
if (sep != '/' or
    not [cmd for cmd in argv[1:]
         if cmd.startswith('install')
         ]):
    console_scripts.extend([
            '%s = thebops.tools.callpy:%s' % (s, s)
            for s in [
                'py2',
                'py3',
                ]
            ])
# from pprint import pprint
if 0:\
pprint({'sys.argv': argv,
        'console_scripts:': console_scripts,
        })

setup(name='thebops'
    , author='Tobias Herp'
    , author_email='tobias.herp@gmx.net'
    , description="Tobias Herp's bag of Python stuff"
    , long_description=read('README.txt')
    , version=__version__
    , packages=find_packages()
    , namespace_packages = ['thebops',
                            'thebops.tools',
                            'thebops.tests',
                            ]
    , entry_points = {
        'console_scripts': console_scripts,
        }
    , include_package_data=True
    , license='GPL'
    )

