"""
Tag implementation using PostgreSQL backend for storage and management.
"""
import typing

import discord.ext.commands as commands

import neko


async def _is_owner_check(ctx):
    return await ctx.bot.is_owner(ctx.author)


# Allows me to enable/disable all commands in this cog if the
# database is not ready for production use.
should_enable = False


@neko.inject_setup
class TagCog(neko.Cog):
    """
    Holds the command implementations for tags.
    """
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

    @property
    def invalid_tag_names(self) -> typing.Iterable[str]:
        """
        Gets a frozenset of invalid tag names we disallow.
        """
        return frozenset({'add', 'remove', 'global', 'my', 'list', 'edit'})

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
        """
        print('tag')

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
            # First see if the tag already exists.
            await conn.execute('SET search_path TO nekozilla;')
            existing = await conn.fetch(
                'SELECT * FROM tags WHERE name = ($1) AND '
                '(guild = NULL or guild = ($2);', tag_name, ctx.guild.id)
            if len(existing) > 0:
                raise neko.NekoCommandError('Tag already exists')
            elif tag_name in self.invalid_tag_names:
                raise neko.NekoCommandError('Invalid tag name')
            else:
                result = await conn.execute(
                    'INSERT INTO tags (name, created, author, guild, content) '
                    'VALUES (($1), NOW(), ($2), ($3), ($4));',
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
            # First see if the tag already exists.
            await conn.execute('SET search_path TO nekozilla;')
            existing = await conn.fetch(
                'SELECT * FROM tags WHERE name = ($1) AND guild = NULL;',
                tag_name)
            if len(existing) > 0:
                raise neko.NekoCommandError('Tag already exists')
            elif tag_name in self.invalid_tag_names:
                raise neko.NekoCommandError('Invalid tag name')
            else:
                result = await conn.execute(
                    'INSERT INTO tags (name, created, author, guild, content) '
                    'VALUES (($1), NOW(), ($2), NULL, ($3));',
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
        Edits a local tag. Only accessible if you already own the tag.
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
        print('tag list')

