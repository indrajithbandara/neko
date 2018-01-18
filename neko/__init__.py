"""
Rewrite of Nekozilla (a.k.a. Nekobot) in Python 3.6.

**Why _Nekozilla_?**

_Nekozilla_ is a song by _Different Heaven_ (check it out on YouTube!)

Plus... NEKO!!! >'^w^<
"""

# Expects each file to have __all__ defined
from .book import *
from .client import NekoBot
from .cog import *
from .command import *
from .common import *
from .io import *
from .strings import *
from .other.log import with_verbosity


# These are useful to have in the namespace.
# Using the import like this means that `discord` is also imported!
import discord.ext.commands.converter
converters = discord.ext.commands.converter

Paginator = discord.ext.commands.Paginator
Context = discord.ext.commands.Context
GroupMixin = discord.ext.commands.GroupMixin
check = discord.ext.commands.check
cooldown = discord.ext.commands.cooldown
Cooldown = discord.ext.commands.Cooldown
CooldownType = discord.ext.commands.BucketType


__all__ = [
    'NekoBot'
]


def _year():
    import datetime
    # In case some smart-arse sets their system clock back.
    return min(datetime.datetime.utcnow().year, 2018)


# Double quote strings to omit them from setup.py
__author__ = 'Espeonageon'
__license__ = 'MIT'
__copyright__ = f'Copyright 2017-{_year()} {__author__}'
__contributors__ = ['Espeonageon', 'Zcissors'],
__thanks__ = ('Rotom, Smidgey, Purrloin, Bambi and Hal0 for putting up with '
              'my constant yammering on about code, bugs, libraries, APIs, '
              'problems, solutions, queries, Python, SQL, JSON, ..., ..., '
              'you name it.\n\nAlso, thank you for putting up with my spam '
              'from testing. You guys are awesome!')
__version__ = '2018-Jan-18.2'
__title__ = 'Nekozilla'
__repo_name__ = 'neko'
__repository__ = f'https://github.com/{__author__}/{__repo_name__}'


