"""
Bunch of APIs to various language documentations, etc.
"""
from . import cppreference
from . import python


cogs = (cppreference.CppReferenceCog, python.PyDocCog, cppreference.Coliru)


def setup(bot):
    for cog in cogs:
        cog.mksetup()(bot)
