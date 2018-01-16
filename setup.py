from setuptools import setup

import re


with open('dependencies.txt') as deps:
    dependencies = filter(lambda dep: dep.strip(), deps.read().split('\n'))


with open('neko/__init__.py') as neko_init:
    contents = neko_init.read().split('\n')

    package_attrs = {}

    for line in contents:
        for (k, v) in re.findall(r'^__(\w+)__\s?=\s?\'([^\']*)\'', line):
            package_attrs[k] = v

setup(
    packages=['neko', 'nekocogs'],
    requires=dependencies,
    **package_attrs,
)
