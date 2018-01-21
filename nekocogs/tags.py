"""
Tag implementation using PostgreSQL backend for storage and management.
"""
import asyncio
import copy
import re

import discord
import discord.ext.commands as commands

import neko


_create_table = '''
-- Note, BIGINT is 64bit signed
CREATE TABLE IF NOT EXISTS nekozilla.tags (
  pk             SERIAL         PRIMARY KEY NOT NULL UNIQUE,

  name           VARCHAR(30)    NOT NULL
                                CONSTRAINT not_whitespace_name CHECK (
                                  TRIM(name) <> ''
                                ),

  -- Snowflake; if null we assume a global tag.
  guild          BIGINT         DEFAULT NULL,

  -- Date/time created
  created        TIMESTAMP      NOT NULL DEFAULT NOW(),

  -- Optional last date/time modified
  last_modified  TIMESTAMP      DEFAULT NULL,

  -- Snowflake
  author         BIGINT         NOT NULL,

  -- Whether the tag is considered NSFW.
  is_nsfw        BOOLEAN        DEFAULT FALSE,

  -- Tag content. Allow up to 1800 characters.
  content        VARCHAR(1800)  CONSTRAINT not_whitespace_cont CHECK (
                                  TRIM(content) <> ''
                                )
);
'''


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
            await conn.execute(_create_table)

    @staticmethod
    async def _del_msg_soon(send_msg=None, resp_msg=None):
        await asyncio.sleep(5)

        # Reverse delete.
        for x in (resp_msg, send_msg):
            if isinstance(x, neko.Context):
                x = x.message
            await x.delete()

    @staticmethod
    async def _add_tag_list_to_pag(ctx, book):
        async with ctx.bot.postgres_pool.acquire() as conn:
            results = await conn.fetch(
                '''
                SELECT name, is_nsfw, guild IS NULL as is_global
                FROM nekozilla.tags
                WHERE guild IS NULL OR guild = ($1)
                ORDER BY name, created;
                ''',
                ctx.guild.id)
            for result in results:
                name = result['name']
                if result['is_global']:
                    name = f'__{name}__'
                if result['is_nsfw'] and not ctx.channel.nsfw:
                    # Hides NSFW commands from regular users unless in NSFW
                    # channels.
                    if ctx.author.id == ctx.bot.owner_id:
                        name = f'~~{name}~~'
                    else:
                        continue

                book.add_line(f'- {name}')

    @neko.group(
        name='tag',
        brief='Text tags that can be defined and retrieved later',
        usage='tag_name',
        invoke_without_command=True)
    async def tag_group(self, ctx: neko.Context, tag_name=None):
        """
        Displays the tag if it can be found. The local tags are searched
        first, and then the global tags.

        If we start the tag with an "!", then we try the global tags list first
        instead.
        """
        if tag_name is None:
            book = neko.PaginatedBook(ctx=ctx, title='Tags', max_lines=15)

            desc = f'Run {ctx.prefix}help tag <command> for more info.\n\n'

            page = neko.Page(
                title='Tag commands'
            )

            cmds = {*self.tag_group.walk_commands()}
            for cmd in copy.copy(cmds):
                # Remove any commands we cannot run.
                if not await cmd.can_run(ctx) or cmd.hidden:
                    cmds.remove(cmd)

            # Generate strings.
            cmds = {'**' + ' '.join(cmd.qualified_name.split(' ')[1:]) + '** - '
                    + cmd.brief for cmd in cmds}

            for line in sorted(cmds):
                desc += f'{line}\n'

            desc += '\nThe following pages will list the available tags.'

            page.description = desc

            book += page

            async with ctx.typing():
                await self._add_tag_list_to_pag(ctx, book)

            await book.send()
            return

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
                    author = data.pop('author')

                    user: discord.User = await ctx.bot.get_user_info(author)
                    data['author'] = ' '.join([
                        'BOT' if user.bot else '',
                        user.display_name,
                        str(user.id)])

                    page = neko.Page(
                        title=f'`{data.pop("name")}`',
                        description=content
                    )

                    page.set_thumbnail(url=user.avatar_url)

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
                    tag_name)
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
                    if is_global:
                        query = '''
                            SELECT pk from nekozilla.tags
                            WHERE guild IS NULL 
                                AND LOWER(name) = LOWER(($1)) 
                        '''
                        if ctx.author.id != ctx.bot.owner_id:
                            existing = await conn.fetch(
                                query + 'LIMIT 1;',
                                tag_name
                            )
                        else:
                            existing = await conn.fetch(
                                query + ' AND author = ($2) LIMIT 1;',
                                tag_name, ctx.author.id
                            )
                    else:
                        query = '''
                            SELECT pk from nekozilla.tags
                            WHERE guild = ($1)
                                AND LOWER(name) = LOWER(($2)) 
                        '''
                        if ctx.author.id != ctx.bot.owner_id:
                            existing = await conn.fetch(
                                query + ' LIMIT 1;',
                                ctx.guild.id,
                                tag_name
                            )
                        else:
                            existing = await conn.fetch(
                                query + ' AND author = ($3) LIMIT 1;',
                                ctx.guild.id,
                                tag_name,
                                ctx.author.id
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

    @tag_group.command(
        name='promote',
        brief='Promotes a tag to be globally available.',
        usage='tag_name')
    @commands.is_owner()
    async def tag_promote(self, ctx, tag_name):
        """
        Note that the information regarding the guild will be lost when
        this operation is performed. Also note that you can not adjust whether
        the tag is SFW or not. This is a trait set by the type of channel you
        add the tag in. To change this, you need to remove and remake the tag
        in a SFW/NSFW channel.
        """
        # First validate the tag name
        if tag_name in self.invalid_tag_names:
            raise neko.NekoCommandError('Invalid tag name')
        else:
            async with ctx.bot.postgres_pool.acquire() as conn:
                async with ctx.typing():
                    existing_local = await conn.fetch(
                        '''
                        SELECT pk FROM nekozilla.tags
                        WHERE LOWER(name) = ($1) AND guild = ($2);
                        ''',
                        tag_name, ctx.guild.id)

                    # Ensure tag exists locally.
                    if not existing_local:
                        raise neko.NekoCommandError('Cannot find that tag.')

                    existing_global = await conn.fetch(
                        '''
                        SELECT 1 FROM nekozilla.tags
                        WHERE LOWER(name) = ($1) AND guild IS NULL;
                        ''',
                        tag_name)

                    # Ensure tag does not exist globally.
                    if existing_global:
                        raise neko.NekoCommandError('Global tag with that name '
                                                    'already seems to exist.')

                    pk = existing_local[0]['pk']

                    # Update the tag
                    await conn.execute(
                        '''
                        UPDATE nekozilla.tags
                        SET last_modified = NOW(), guild = NULL
                        WHERE pk = ($1);
                        ''',
                        pk)

                await self._del_msg_soon(
                    ctx,
                    await ctx.send('Promoted tag to global status.'))

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

    @classmethod
    async def _update(cls, conn, pk, new_content):
        await conn.execute(
            '''
            UPDATE nekozilla.tags
            SET last_modified = NOW(), content = ($1)
            WHERE pk = ($2);                                       
            ''',
            new_content, pk
        )

    @tag_group.group(
        name='edit',
        brief='Edits a local tag.',
        usage='tag_name new content',
        invoke_without_command=True)
    async def tag_edit(self, ctx, tag_name, *, new_content):
        """
        Edits a local tag. Only accessible if you already own the tag, or you
        are the bot owner.
        """
        is_owner = ctx.author.id == ctx.bot.owner_id
        is_nsfw = ctx.channel.nsfw

        search_query = f'''
            SELECT pk FROM nekozilla.tags
            WHERE LOWER(name) = LOWER(($1))
                {f"AND author = {ctx.author.id}" if not is_owner else ""}
                {"AND is_nsfw = FALSE" if not is_nsfw else ""}
                AND guild = {ctx.guild.id};
            '''

        async with ctx.bot.postgres_pool.acquire() as conn:
            async with ctx.typing():
                results = await conn.fetch(search_query, tag_name)

                # My validation should ensure this.
                assert len(results) <= 1, 'Esp\'s validation is broken! WHEYYY!'

                if not results:
                    raise neko.NekoCommandError('Cannot find that tag.')

                pk = results.pop()['pk']

                await self._update(conn, pk, new_content)
            await self._del_msg_soon(ctx, await ctx.send('Edited.'))

    @tag_edit.command(
        name='global',
        brief='Edits a global tag.',
        usage='tag_name new content')
    @commands.is_owner()
    async def tag_edit_global(self, ctx, tag_name, *, new_content):
        """
        Edits a global tag. Only accessible by the bot owner.
        """
        is_owner = ctx.author.id == ctx.bot.owner_id
        is_nsfw = ctx.channel.nsfw

        search_query = f'''
            SELECT pk FROM nekozilla.tags
            WHERE LOWER(name) = LOWER(($1))
                {f"AND author = {ctx.author.id}" if not is_owner else ""}
                {"AND is_nsfw = FALSE" if not is_nsfw else ""}
                AND guild IS NULL;
            '''

        async with ctx.bot.postgres_pool.acquire() as conn:
            async with ctx.typing():
                results = await conn.fetch(search_query, tag_name)

                # My validation should ensure this.
                assert len(results) <= 1, 'Esp\'s validation is broken! WHEYYY!'

                if not results:
                    raise neko.NekoCommandError('Cannot find that tag.')

                pk = results.pop()['pk']

                await self._update(conn, pk, new_content)
            await self._del_msg_soon(ctx, await ctx.send('Edited.'))

    @tag_group.command(
        name='list',
        brief='Lists all available tags.')
    async def tag_list(self, ctx):
        """
        This lists bot local and global tags.
        """
        book = neko.PaginatedBook(ctx=ctx, title='Tags', max_lines=15)

        async with ctx.typing():
            await self._add_tag_list_to_pag(ctx, book)

        await book.send()
