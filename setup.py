#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from distutils.core import setup

name_ = 'images'
version_ = '0.0.1'
packages_ = [
    'image',
]

classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: Python :: 3",
]

setup(
    name=name_,
    version=version_,
    author='Johan Egneblad',
    author_email='johan.egneblad@DELETEMEgmail.com',
    description='Image library and viewer',
    license="MIT",
    url='https://github.com/eblade/'+name_,
    download_url=('https://github.com/eblade/%s/archive/v%s.tar.gz'
                  % (name_, version_)),
    packages=packages_,
    scripts=['bin/images'],
    classifiers = classifiers
)
