"""
Rewrite of Nekozilla (a.k.a. Nekobot) in Python 3.6.

**Why _Nekozilla_?**

_Nekozilla_ is a song by _Different Heaven_ (check it out on YouTube!)

Plus... NEKO!!! >'^w^<
"""

# Expects each file to have __all__ defined
from .book import *
from .client import *
from .cog import *
from .command import *
from .common import *
from .excuses import *
from .http import *
from .io import *
from .log import *
from .perms import *
from .singleton import *
from .strings import *
from .tokens import *


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

__author__ = 'Espeonageon'
__license__ = 'MIT'
__copyright__ = f'Copyright 2017-2018 {__author__}'
__version__ = '2018-Jan-13.1'
__title__ = 'Nekozilla'
__repo_name__ = 'neko'
__repository__ = f'https://github.com/{__author__}/{__repo_name__}'


