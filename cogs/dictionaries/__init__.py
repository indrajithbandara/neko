"""
Various online dictionaries, thesauruses, etc.
"""
from . import ud
from . import wordnik

__all__ = ['setup']


def setup(bot):
    for cog in {ud.UrbanDictionaryCog, wordnik.WordnikCog}:
        cog.mksetup()(bot)
