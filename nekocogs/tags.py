"""
Tag implementation using PostgreSQL backend for storage and management.
"""
import re

import asyncio
import discord.ext.commands as commands

import neko


# Allows me to enable/disable all commands in this cog if the
# database is not ready for production use.
should_enable = True


@neko.inject_setup
class TagCog(neko.Cog):
    """
    Holds the command implementations for tags.
    """
    invalid_tag_names = neko.PatternCollection(
        'global', 'add', 'remove', 'inspect', 'edit', 'my', 'list',
        re.compile(r'!.*', re.DOTALL)
    )

    def __init__(self, bot: neko.NekoBot):
        if bot.postgres_pool is None:
            raise RuntimeError('Dropping this cog. No database available.')

        self.bot = bot

    async def __local_check(self, ctx):
        """
        Ensures commands are only runnable in guilds.
        """
        return ctx.guild is not None

    async def on_connect(self):
        """
        Ensures the tables actually exist.
        """
        self.logger.info('Ensuring tables exist')
        async with self.bot.postgres_pool.acquire() as conn:
            with open(neko.relative_to_here('create_tags_tbls.sql')) as fp:
                await conn.execute(fp.read())
        self.logger.info('Tables should now exist if they didn\'t already.')

    @staticmethod
    async def _del_msg_soon(send_msg=None, resp_msg=None):
        await asyncio.sleep(5)

        for x in (send_msg, resp_msg):
            if isinstance(x, neko.Context):
                x = x.message
            asyncio.ensure_future(x.delete())

    @neko.group(
        name='tag',
        brief='Text tags that can be defined and retrieved later',
        usage='tag_name',
        invoke_without_command=True)
    async def tag_group(self, ctx, tag_name):
        """
        Displays the tag if it can be found. The local tags are searched
        first, and then the global tags.

        If we start the tag with an "!", then we try the global tags list first
        instead.
        """
        local_first = False
        if tag_name.startswith('!'):
            tag_name = tag_name[1:]
            local_first = True

        async with self.bot.postgres_pool.acquire() as conn:
            g = 'SELECT content FROM nekozilla.tags WHERE LOWER(name) = ($1) '
            async with ctx.channel.typing():
                if not ctx.channel.nsfw:
                    g += 'AND is_nsfw = FALSE '

                g += 'AND guild '

                getter_l = g + '= ($2);'
                getter_g = g + 'IS NULL;'

                # await ctx.send('\n'.join([getter_l, getter_g]))

                res_l = await conn.fetch(getter_l, tag_name, ctx.guild.id)
                res_g = await conn.fetch(getter_g, tag_name)

                results = [*res_l, *res_g] if local_first else [*res_g, *res_l]

            if not results:
                raise neko.NekoCommandError('No tag found with that name.')
            else:
                await ctx.send(results.pop(0)['content'])

    @tag_group.command(
        name='inspect',
        brief='Inspects a given tag, showing who made it.',
        usage='tag_name')
    @commands.is_owner()
    async def tag_inspect(self, ctx, tag_name):
        """
        This is only runnable by the bot owner.
        """
        async with ctx.bot.postgres_pool.acquire() as conn:
            book = neko.Book(ctx)
            async with ctx.typing():
                tag_name = tag_name.lower()
                results = await conn.fetch(
                    'SELECT * FROM nekozilla.tags WHERE LOWER(name) = ($1);',
                    tag_name)

                if not results:
                    raise neko.NekoCommandError('No results.')

                for result in results:
                    data = dict(result)
                    content = data.pop('content')

                    page = neko.Page(
                        title=data.pop('name'),
                        description=content
                    )

                    page.add_field(
                        name='Attributes',
                        value='\n'.join(
                            f'**{k}**: `{v}`' for k, v in data.items()
                        )
                    )

                    book += page

            await book.send()

    @tag_group.group(
        name='add',
        brief='Add a local tag for this server',
        usage='tag_name content',
        invoke_without_command=True)
    async def tag_add(self, ctx, tag_name, *, content):
        """
        Adds a local tag. The tag cannot contain spaces, and if an existing
        tag exists with the name, then we cannot add it.
        """
        tag_name = tag_name.lower()

        # First, make sure tag is valid.
        if tag_name in self.invalid_tag_names:
            raise neko.NekoCommandError('Invalid tag name')

        async with self.bot.postgres_pool.acquire() as conn:
            async with ctx.channel.typing():
                # Next, see if the tag already exists.
                existing = await conn.fetch(
                    '''
                    SELECT 1 FROM nekozilla.tags
                    WHERE LOWER(name) = ($1) AND guild = ($2);
                    ''',
                    tag_name, ctx.guild.id
                )
                if len(existing) > 0:
                    raise neko.NekoCommandError('Tag already exists')

                await conn.execute(
                    '''
                    INSERT INTO nekozilla.tags 
                        (name, author, guild, is_nsfw, content) 
                    VALUES (($1), ($2), ($3), ($4), ($5));
                    ''',
                    tag_name,
                    ctx.author.id,
                    ctx.guild.id,
                    ctx.channel.nsfw,
                    content
                )

            await self._del_msg_soon(ctx, await ctx.send('Added.'))

    @tag_add.command(
        name='global',
        brief='Adds a tag globally.',
        usage='tag_name content')
    @commands.is_owner()
    async def tag_add_global(self, ctx, tag_name, *, content):
        """
        This is only currently accessible by the bot owner.
        """
        tag_name = tag_name.lower()

        # First, make sure tag is valid.
        if tag_name in self.invalid_tag_names:
            raise neko.NekoCommandError('Invalid tag name')

        async with self.bot.postgres_pool.acquire() as conn:
            async with ctx.channel.typing():
                # Next, see if the tag already exists.
                existing = await conn.fetch(
                    '''
                    SELECT 1 FROM nekozilla.tags
                    WHERE LOWER(name) = ($1) AND guild IS NULL;
                    ''',
                    tag_name
                )
                if len(existing) > 0:
                    raise neko.NekoCommandError('Tag already exists')

                await conn.execute(
                    '''
                    INSERT INTO nekozilla.tags 
                        (name, author, is_nsfw, content)
                    VALUES (($1), ($2), ($3), ($4))
                    ''',
                    tag_name,
                    ctx.author.id,
                    ctx.channel.nsfw,
                    content)

            await self._del_msg_soon(ctx, await ctx.send('Added globally.'))

    @classmethod
    async def _delete(cls, tag_name, ctx, is_global=False):
        # First validate the tag name
        if tag_name in cls.invalid_tag_names:
            raise neko.NekoCommandError('Invalid tag name')
        else:
            async with ctx.bot.postgres_pool.acquire() as conn:
                async with ctx.channel.typing():
                    # Cast to an int and then to a string
                    g = ctx.guild.id
                    if ctx.author.id == ctx.bot.owner_id:
                        existing = await conn.fetch(
                            f'''
                            SELECT pk FROM nekozilla.tags
                            WHERE guild
                                {"IS NULL" if is_global else "= ($1)"}
                                AND LOWER(name) = LOWER(($2))
                            LIMIT 1
                            ''',
                            g, tag_name
                        )
                    else:
                        existing = await conn.fetch(
                            f'''
                            SELECT pk FROM nekozilla.tags
                            WHERE guild
                                {"IS NULL" if is_global else "= ($1)"}
                                AND LOWER(name) = LOWER(($2))
                                AND author = ($3)
                            LIMIT 1
                            ''',
                            g, tag_name, ctx.author.id
                        )

                    if existing:
                        existing = existing.pop(0)['pk']
                    else:
                        raise neko.NekoCommandError('No matching tag found.')

                    await conn.execute(
                        'DELETE FROM nekozilla.tags WHERE pk = ($1)',
                        existing
                    )

                await cls._del_msg_soon(
                    ctx,
                    await ctx.send(
                        f'Removed{" globally" if is_global else ""}.'
                    )
                )

    @tag_group.group(
        name='remove',
        brief='Removes a tag from the local server.',
        usage='tag_name',
        invoke_without_command=True)
    async def tag_remove(self, ctx, tag_name):
        """
        Removes a local tag. You can only do this if you own the tag.
        """
        await self._delete(tag_name, ctx)

    @tag_remove.command(
        name='global',
        brief='Deletes a global tag.',
        usage='tag_name')
    @commands.is_owner()
    async def tag_remove_global(self, ctx, tag_name):
        """
        Removes a global tag. Only accessible by the bot owner.
        """
        await self._delete(tag_name, ctx, True)

    @tag_group.command(
        name='my',
        brief='Lists tags that _you_ own.')
    async def tag_my(self, ctx):
        """Shows tags you own globally and in this guild."""
        async with ctx.bot.postgres_pool.acquire() as conn:
            async with ctx.typing():
                results = await conn.fetch(
                    '''
                    SELECT name, is_nsfw, guild
                    FROM nekozilla.tags
                    WHERE author = ($1) AND (guild IS NULL OR guild = ($2))
                    ORDER BY name, created;
                    ''', ctx.author.id, ctx.guild.id)

                book = neko.PaginatedBook(
                    ctx=ctx,
                    title='My Tags',
                    max_lines=10)

                for result in results:
                    name = f'`{result["name"]}`'
                    if result['is_nsfw']:
                        name = f'_{name}_'
                    name += ' in this guild' if result['guild'] else ' globally'
                    book.add_line(name)

            await book.send()

    @tag_group.group(
        name='edit',
        brief='Edits a local tag.',
        usage='tag_name new content',
        enabled=should_enable,
        invoke_without_command=True)
    async def tag_edit(self, ctx, tag_name, *, new_content):
        """
        Edits a local tag. Only accessible if you already own the tag, or you
        are the bot owner.
        """
        raise NotImplementedError

    @tag_edit.command(
        name='global',
        brief='Edits a global tag.',
        usage='tag_name new content',
        enabled=should_enable)
    @commands.is_owner()
    async def tag_edit_global(self, ctx, tag_name, *, new_content):
        """
        Edits a global tag. Only accessible by the bot owner.
        """
        raise NotImplementedError

    @tag_group.command(
        name='list',
        brief='Lists all available tags.')
    async def tag_list(self, ctx):
        """
        This lists bot local and global tags.
        """
        async with ctx.bot.postgres_pool.acquire() as conn:
            results = await conn.fetch(
                '''
                SELECT name, created, is_nsfw, guild IS NULL as is_global
                FROM nekozilla.tags
                WHERE guild IS NULL OR guild = ($1)
                ''',
                ctx.guild.id
            )
            await ctx.send(results)
