#!/usr/bin/env python
import collections
import sys

from setuptools import setup, find_packages
from pip.req import parse_requirements
from pip.download import PipSession


def get_install_requirements(filename):

    ReqOpts = collections.namedtuple('ReqOpts', [
        'skip_requirements_regex',
        'default_vcs'
    ])

    opts = ReqOpts(None, 'git')

    requires = []
    dependency_links = []

    for ir in parse_requirements(filename, options=opts, session=PipSession()):
        if ir is not None:
            if ir.url is not None:
                dependency_links.append(str(ir.url))
            if ir.req is not None:
                requires.append(str(ir.req))
    return requires, dependency_links


install_requires, dependency_links = get_install_requirements(
    'requirements.txt')

if sys.version_info < (3, 0):
    install_requires_2, dependency_links_2 = get_install_requirements('requirements-py2.txt')
    install_requires += install_requires_2
    dependency_links += dependency_links_2

tests_require, _ = get_install_requirements('requirements-test.txt')


def read_long_description(filename="README.md"):
    with open(filename) as f:
        return f.read().strip()


setup(
    name="mutornadomon",
    version="0.1.10",
    author="James Brown",
    author_email="jbrown@uber.com",
    url="https://github.com/uber/mutornadomon",
    license="MIT",
    packages=find_packages(exclude=['tests']),
    keywords=["monitoring", "tornado"],
    description="Library of standard monitoring hooks for the Tornado framework",
    install_requires=install_requires,
    dependency_links=dependency_links,
    long_description=read_long_description(),
    test_suite="nose.collector",
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Web Environment",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ]
)
