"""
Tag implementation using PostgreSQL backend for storage and management.
"""
import re

import discord.ext.commands as commands

import neko


async def _is_owner_check(ctx):
    return await ctx.bot.is_owner(ctx.author)


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
    async def _get_global(conn, tag_name):
        return await conn.fetch(
            'SELECT * FROM nekozilla.tags WHERE name = ($1) '
            'AND guild IS NULL;',
            tag_name)

    @staticmethod
    async def _get_local(conn, tag_name, guild_id):
        return await conn.fetch(
            'SELECT * FROM nekozilla.tags WHERE name = ($1) AND '
            '(guild IS NULL or guild = ($2));',
            tag_name,
            guild_id)

    @neko.group(
        name='tag',
        brief='Text tags that can be defined and retrieved later',
        usage='tag_name',
        enabled=should_enable,
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

            order = [self._get_local(conn, tag_name, ctx.guild.id),
                     self._get_global(conn, tag_name)]
            if not local_first:
                order = reversed(order)

            result = await neko.async_find(lambda r: r is not None, order)

        if not result:
            raise neko.NekoCommandError('No tag found with that name.')
        else:
            raise NotImplementedError()

    @tag_group.command(
        name='inspect',
        brief='Inspects a given tag, showing who made it.',
        usage='tag_name',
        enabled=False)
    @commands.is_owner()
    async def tag_inspect(self, ctx, tag_name):
        """
        This is only runnable by the bot owner.
        """
        print('tag inspect')

    @tag_group.group(
        name='add',
        brief='Add a local tag for this server',
        usage='tag_name content',
        enabled=should_enable,
        invoke_without_command=True)
    async def tag_add(self, ctx, tag_name, *, content):
        """
        Adds a local tag. The tag cannot contain spaces, and if an existing
        tag exists with the name, then we cannot add it.
        """
        tag_name = tag_name.lower()

        async with self.bot.postgres_pool.acquire() as conn:
            # First, make sure tag is valid.
            if tag_name in self.invalid_tag_names:
                raise neko.NekoCommandError('Invalid tag name')

            # Next, see if the tag already exists.
            existing = await self._get_local(conn, tag_name, ctx.guild.id)
            if len(existing) > 0:
                raise neko.NekoCommandError('Tag already exists')
            else:
                result = await conn.execute(
                    'INSERT INTO nekozilla.tags (name, created, author, guild, '
                    'content) VALUES (($1), NOW(), ($2), ($3), ($4));',
                    tag_name, ctx.author.id, ctx.guild.id, content)

                # TODO: check what result is and what to do with it
                await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @tag_add.command(
        name='global',
        brief='Adds a tag globally.',
        usage='tag_name content',
        enabled=should_enable)
    @commands.is_owner()
    async def tag_add_global(self, ctx, tag_name, *, content):
        """
        This is only currently accessible by the bot owner.
        """
        tag_name = tag_name.lower()

        async with self.bot.postgres_pool.acquire() as conn:
            # First see if the tag is valid
            if tag_name in self.invalid_tag_names:
                raise neko.NekoCommandError('Invalid tag name')

            # Next, see if the tag already exists
            existing = await self._get_global(conn, tag_name)
            if len(existing) > 0:
                raise neko.NekoCommandError('Tag already exists')
            else:
                result = await conn.execute(
                    'INSERT INTO nekozilla.tags (name, created, author, guild, '
                    'content) VALUES (($1), NOW(), ($2), NULL, ($3));',
                    tag_name, ctx.author.id, content)

                # TODO: check what result is and what to do with it
                await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @tag_group.group(
        name='remove',
        brief='Removes a tag from the local server.',
        usage='tag_name',
        enabled=should_enable,
        invoke_without_command=True)
    async def tag_remove(self, ctx, tag_name):
        """
        Removes a local tag. You can only do this if you own the tag.
        """
        print('tag remove')

    @tag_remove.command(
        name='global',
        brief='Deletes a global tag.',
        usage='tag_name',
        enabled=should_enable)
    @commands.is_owner()
    async def tag_remove_global(self, ctx, tag_name):
        """
        Removes a global tag. Only accessible by the bot owner.
        """
        print('tag remove global')

    @tag_group.command(
        name='my',
        brief='Lists tags that _you_ own.',
        enabled=should_enable)
    async def tag_my(self, ctx):
        print('tag my')

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
        print('tag edit')

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
        print('tag edit global')

    @tag_group.command(
        name='list',
        brief='Lists all available tags.',
        enabled=should_enable)
    async def tag_list(self, ctx):
        """
        This lists bot local and global tags.
        """
        async with ctx.bot.postgres_pool.acquire() as conn:
            results = await conn.fetch(
                'SELECT name, created FROM nekozilla.tags '
                'WHERE guild IS NULL OR guild == ($1)',
                ctx.guild.id
            )
            await ctx.send(results)

