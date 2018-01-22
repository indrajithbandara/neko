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

required_records = [
    ('respects_paid', '0')
]


@neko.inject_setup
class UncategorisedCog(neko.Cog):

    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

    async def on_connect(self):
        """
        Creates the uncategorised table in the schema for storing simple
        key-value pairs.
        """
        async with self.bot.postgres_pool.acquire() as conn:
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS nekozilla.uncategorised_stuff (
                  key_name        VARCHAR         PRIMARY KEY 
                                                  CONSTRAINT not_ws CHECK (
                                                    TRIM(key_name) <> ''
                                                  ),
                  value_data      VARCHAR         DEFAULT NULL
                );
                ''')

            # Adds required records
            for k, v in required_records:
                await conn.execute(
                    '''                    
                    INSERT INTO nekozilla.uncategorised_stuff
                    VALUES (($1), ($2))
                    ON CONFLICT DO NOTHING;
                    ''', str(k), str(v))

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

    @neko.command(
        name='f',
        usage='|<what>',
        brief='Press F to pay your respects.')
    async def pay_respects(self, ctx, *, what=None):
        async with ctx.bot.postgres_pool.acquire() as conn:
            # Performs the increment server-side.
            await conn.execute(
                '''
                UPDATE nekozilla.uncategorised_stuff 
                SET value_data = ((
                    SELECT value_data::INT FROM nekozilla.uncategorised_stuff 
                    WHERE key_name = 'respects_paid' 
                    LIMIT 1) + 1)::VARCHAR
                WHERE key_name = 'respects_paid';
                ''')
            total = await conn.fetchval(
                '''
                SELECT value_data FROM nekozilla.uncategorised_stuff
                WHERE key_name = 'respects_paid'
                LIMIT 1; 
                ''')

        title = f'{ctx.author.display_name} has paid their respects '

        if what:
            title += f'for {what}'

        embed = neko.Page(
            title=title,
            description=f'Total: {total}',
            color=0xEB2B36)

        await ctx.send(embed=embed)
