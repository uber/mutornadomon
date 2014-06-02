#!/usr/bin/env python
import collections

from setuptools import setup, find_packages
from pip.req import parse_requirements


def get_install_requirements(filename):

    ReqOpts = collections.namedtuple('ReqOpts', [
        'skip_requirements_regex',
        'default_vcs'
    ])

    opts = ReqOpts(None, 'git')

    requires = []
    dependency_links = []

    for ir in parse_requirements(filename, options=opts):
        if ir is not None:
            if ir.url is not None:
                dependency_links.append(str(ir.url))
            if ir.req is not None:
                requires.append(str(ir.req))
    return requires, dependency_links


install_requires, dependency_links = get_install_requirements(
    'requirements.txt')

tests_require, _ = get_install_requirements('requirements-test.txt')


def read_long_description(filename="README.md"):
    with open(filename) as f:
        return f.read().strip()


setup(
    name="mutornadomon",
    version="0.1.5",
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
        "Programming Language :: Python :: 2.7",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
    ]
)
