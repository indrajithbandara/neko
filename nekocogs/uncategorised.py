"""
Bunch of uncategorised commands.
"""
import random
import urllib.parse

import neko


tasters = [
    'Try this',
    'Check this out',
    'Is this what you wanted?'
]


@neko.inject_setup
class UncategorisedCog(neko.Cog):

    @neko.command(
        brief="Directs stupid questions to their rightful place.",
        usage="how to buy lime",
        aliases=['lmgtfyd'])
    async def lmgtfy(self, ctx, *, query):
        """
        Garbage question = garbage answer.

        Call `lmgtfyd` to destroy your initial message.
        """
        frag = urllib.parse.urlencode({'q': query})

        if ctx.invoked_with == 'lmgtfyd':
            await ctx.message.delete()

        embed = neko.Page(
            title=query.title(),
            description=random.choice(tasters),
            color=neko.random_color(),
            url=f'http://lmgtfy.com?{frag}'
        )

        await ctx.send(embed=embed)
