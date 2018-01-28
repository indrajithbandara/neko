"""
Bunch of uncategorised commands.
"""
import random
import re
import urllib.parse

import asyncio

import neko


tasters = [
    'Try this',
    'Check this out',
    'Is this what you wanted?'
]

required_records = [
    ('respects_paid', '0')
]


binds = {
    re.compile(r'^/shrug\b'): '¯\_(ツ)_/¯',
    re.compile(r'^/(table)?flip\b'): '(╯°□°）╯︵ ┻━┻',
    re.compile(r'^/unflip\b'): '┬──┬﻿ ノ(° - °ノ)'
}


@neko.inject_setup
class UncategorisedCog(neko.Cog):

    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

        # Maps a string concat of the guild and channel snowflake to user ids.
        self.bind_cooldown_buckets = {}

    async def on_message(self, msg):
        """
        When we get a message, we check if certain Discord-app
        binds are at the start. If there is, we reply with that
        bind. It is as close as I can get to actually supporting
        the binds that you can use on desktop, on mobile.
        """
        if not msg.guild or msg.author.bot:
            return

        guild = msg.guild.id
        chan = msg.channel.id

        timeout_k = str(guild) + str(chan)
        timeout_v = self.bind_cooldown_buckets.get(timeout_k)

        # If the user id was mapped under that identity in the
        # buckets, then we are on timeout, so don't bother doing
        # anything else.
        if timeout_v == msg.author.id:
            return

        async def callback():
            if msg.author.id == self.bot.owner_id:
                # Owner privileges, kek.
                return

            # Insert into the dict
            self.bind_cooldown_buckets[timeout_k] = msg.author.id
            # Cooldown for 30s.
            await asyncio.sleep(30)
            # Remove from the dict
            # Specify None to prevent KeyError if it was already
            # removed somehow.
            self.bind_cooldown_buckets.pop(timeout_k, None)

        # Attempt to find the bind (this returns a tuple or None if not found)
        bind = neko.find(lambda r: r.match(msg.content), binds)

        if not bind:
            return
        else:
            bind = binds[bind]

        # Ensure the future, but don't bother waiting.
        asyncio.ensure_future(callback())
        await msg.channel.send(bind)

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
    async def pay_respects(self, ctx, *, _unused_what):
        # Filters out mention syntax. We cant do this from ctx directly
        # sadly, at least I don't think.
        what = ctx.message.clean_content
        # Remove the command prefix.
        # Todo: fix so this isn't aids when I am at an IDE...
        what = what[4:].strip()
        
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
            color=0x54c571)

        await ctx.send(embed=embed)
