"""
Bunch of APIs to various language documentations, etc.
"""
from . import cppreference


cogs = {cppreference.CppReferenceCog}


def setup(bot):
    for cog in cogs:
        bot.add_cog(cog.mksetup()(bot))
