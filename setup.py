#!/usr/bin/env python

import sys
from setuptools import setup, find_packages

install_requires = [
    'tornado<6',
    'psutil',
    'mock',
    'six',
]

if sys.version_info < (3, 0):
    install_requires.append('ipcalc')


def read_long_description(filename="README.md"):
    with open(filename) as f:
        return f.read().strip()


setup(
    name="mutornadomon",
    version="0.5.2.dev0",
    author="Uber Technologies, Inc.",
    author_email="dev@uber.com",
    url="https://github.com/uber/mutornadomon",
    license="MIT",
    packages=find_packages(exclude=['tests']),
    keywords=["monitoring", "tornado"],
    description="Library of standard monitoring hooks for the Tornado framework",
    install_requires=install_requires,
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    test_suite="nose.collector",
    tests_require=[
        'nose',
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ]
)
