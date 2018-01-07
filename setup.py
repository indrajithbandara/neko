from setuptools import setup

import re

dependencies = [
    # For async http requests
    'aiohttp',

    # Used for connection pools to non-async network-based APIs
    'requests'
    
    # Wordnik integration
    'wordnik-py3'

    # BeautifulSoup4 HTML parser for Python3
    'beautifulsoup4'
]

with open('neko/__init__.py') as neko_init:
    contents = neko_init.read().split('\n')

    package_attrs = {}

    for line in contents:
        for (k, v) in re.findall(r'^__(\w+)__\s?=\s?\'([^\']*)\'', line):
            package_attrs[k] = v

setup(
    packages=['neko'],
    dependencies=dependencies,
    **package_attrs,
)
