#!/usr/bin/env python
from setuptools import setup, find_packages
VERSION = (0, 1, 0, "a", 1)  # following PEP 386
DEV_N = 1  # for PyPi releases, set this to None

def get_version(short=False):
    version = "%s.%s" % (VERSION[0], VERSION[1])
    if short:
        return version
    if VERSION[2]:
        version = "%s.%s" % (version, VERSION[2])
    if VERSION[3] != "f":
        version = "%s%s%s" % (version, VERSION[3], VERSION[4])
        if DEV_N:
            version = "%s.dev%s" % (version, DEV_N)
    return version

__version__ = get_version()

setup(
    name="python-realtimemagic",
    version=__version__,
    author='Lincoln Loop: Nicolas Lara',
    author_email='info@lincolnloop.com',
    description=("A set of tools to make writting a realtime sockjs server easy(er)"),
    packages=find_packages(),
    #package_data={'realtimemagic': []},
    url="http://github.com/lincolnloop/python-realtimemagic/",
    install_requires=['setuptools', 'tornado==2.3', 'sockjs-tornado==0.0.4', 'eventlet'],
    classifiers=[
        'Development Status :: 0.1 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)