"""
Implementation of a help command.
"""
import asyncio
import getpass
import inspect
import logging
import os
import random
import sys
import time
import threading

import discord

import neko


# Dodger blue.
default_color = 0x1E90FF


class HelpCog(neko.Cog):
    """Provides the inner methods with access to bot directly."""

    permissions = (neko.Permissions.SEND_MESSAGES |
                   neko.Permissions.ADD_REACTIONS |
                   neko.Permissions.READ_MESSAGES |
                   neko.Permissions.MANAGE_MESSAGES)

    def __init__(self, bot: neko.NekoBot):
        """
        Initialises the cog.
        :param bot: the bot.
        """
        self.bot = bot

    @neko.command(
        name='rtfm',
        brief='Shows help for the available bot commands.',
        aliases=['man', 'help'],
        usage='|command|group command')
    async def help_command(self, ctx: neko.Context, *, query=None):
        """
        Shows a set of help pages outlining the available commands, and
        details on how to operate each of them.

        If a command name is passed as a parameter (`help command`) then the
        parameter is searched for as a command name and that page is opened.
        """
        # TODO: maybe try to cache this! It's a fair amount of work each time.

        # Generates the book
        bk = neko.Book(ctx)

        # Maps commands to pages, so we can just jump to the page
        command_to_page = {}

        bk += await self.gen_front_page(ctx)
        command_to_page[None] = 0

        # Walk commands
        cmds = sorted(set(self.bot.walk_commands()),
                      key=lambda c: c.qualified_name)

        # We offset each index in the enumeration by this to get the
        # correct page number.
        offset = len(bk)

        # for i, cmd in enumerate(cmds):
        #    bk += await self.gen_spec_page(ctx, cmd)
        #    # We add 1, as w
        #    command_to_page[cmd.qualified_name] = i + offset
        #
        #    # Also register any aliases.
        #    for alias in cmd.aliases:
        #        # This is the only way to get the fully qualified alias name.
        #        fq_alias = f'{cmd.full_parent_name} {alias}'.strip()
        #        command_to_page[fq_alias] = i + offset

        # This is a lot lighter weight.
        page_index = None
        for i, cmd in enumerate(cmds):
            bk += await self.gen_spec_page(ctx, cmd)

            if page_index is None and query in cmd.qualified_names:
                # I assume checking equality of commands is slower
                # than checking for is None each iteration.
                page_index = i + offset

        # Set the page
        if page_index is None and query:
            await ctx.send(f'I could not find a command called {query}!')
        else:
            if page_index is None:
                page_index = 0

            bk.index = page_index
            await bk.send()

    async def gen_front_page(self, ctx: neko.Context) -> neko.Page:
        """
        Generates an about page. This is the first page of the help
        pagination.

        :param ctx: the command context.
        """

        desc = f'{neko.__copyright__} under the {neko.__license__} license.\n\n'

        # Gets the docstring for the root module if there is one.
        doc_str = inspect.getdoc(neko)
        doc_str = inspect.cleandoc(doc_str if doc_str else '')
        desc += neko.remove_single_lines(doc_str)

        page = neko.Page(
            title=f'{neko.__title__} v{neko.__version__}',
            description=desc,
            color=default_color,
            url=neko.__repository__
        )

        page.set_thumbnail(url=self.bot.user.avatar_url)

        page.add_field(
            name='Repository',
            value=neko.__repository__
        )

        # If we are the bot owner, we do not hide any commands.
        is_bot_owner = await self.bot.is_owner(ctx.author)

        cmds = sorted(self.bot.commands, key=lambda c: c.name)
        cmds = [self.format_command_name(cmd)
                for cmd in cmds
                if is_bot_owner or not cmd.hidden]

        page.add_field(
            name='Available commands',
            value=', '.join(cmds),
            inline=False
        )

        return page

    # noinspection PyUnusedLocal
    async def gen_spec_page(self,
                            ctx: neko.Context,
                            cmd: neko.NekoCommand) -> neko.Page:
        """
        Given a context and a command, generate a help page entry for the
        command.

        :param ctx: the context to use to determine if we can run the command
                here.
        :param cmd: the command to generate the help page for.
        :return: a book page.
        """
        pfx = self.bot.command_prefix
        fqn = cmd.qualified_name
        brief = f'**{fqn}**\n{cmd.brief if cmd.brief else ""}'
        doc_str = neko.remove_single_lines(cmd.help)
        usages = cmd.usage.split('|') if cmd.usage else ''
        usages = map(lambda u: f'• {pfx}{fqn} {u}', usages)
        usages = '\n'.join(sorted(usages))
        aliases = sorted(cmd.aliases)
        cooldown = getattr(cmd, '_buckets')

        if cooldown:
            cooldown: neko.Cooldown = getattr(cooldown, '_cooldown')

        if cmd.parent:
            super_command = self.format_command_name(cmd.parent)
        else:
            super_command = None

        # noinspection PyUnresolvedReferences
        can_run = await cmd.can_run(ctx)

        if isinstance(cmd, neko.GroupMixin):
            def sub_cmd_map(c):
                c = self.format_command_name(c)
                c = f'• {c}'
                return c

            # Cast to a set to prevent duplicates for aliases. Hoping this
            # fixes #9 again.
            # noinspection PyUnresolvedReferences
            sub_commands = map(sub_cmd_map, set(cmd.walk_commands()))
            sub_commands = sorted(sub_commands)
        else:
            sub_commands = []

        if getattr(cmd, 'enabled', False) and can_run:
            color = default_color
        elif not can_run:
            color = 0xFFFF00
        else:
            color = 0xFF0000

        page = neko.Page(
            title=f'Command documentation',
            description=brief,
            color=color
        )

        if doc_str:
            page.add_field(
                name='Description',
                value=doc_str,
                inline=False
            )

        if usages:
            page.add_field(
                name='Usage',
                value=usages,
                inline=False
            )

        if aliases:
            page.add_field(
                name='Aliases',
                value=', '.join(aliases)
            )

        if cooldown:
            string = (
                f'{neko.capitalise(cooldown.type.name)}-scoped '
                f'{neko.pluralise(cooldown.rate, "request", method="per app")} '
                f'for {neko.pluralise(cooldown.per, "second")}.')

            page.add_field(
                name='Cooldown policy',
                value=string
            )

        if sub_commands:
            page.add_field(
                name='Child commands',
                value='\n'.join(sub_commands)
            )

        if super_command:
            page.add_field(
                name='Parent command',
                value=super_command
            )

        if not can_run and cmd.enabled:
            page.set_footer(
                text='You do not hve permission to run the command here.'
            )
        elif not cmd.enabled:
            page.set_footer(
                text='This command has been disabled globally.'
            )

        return page

    @staticmethod
    def format_command_name(cmd: neko.NekoCommand,
                            *,
                            is_full=False) -> str:
        """
        Formats the given command using it's name, in markdown.

        If the command is disabled, it is crossed out.
        If the command is a group, it is proceeded with an asterisk.
            This is only done if the command has at least one sub-command
            present.
        If the command is hidden, it is displayed in italics.

        :param cmd: the command to format.
        :param is_full: defaults to false. If true, the parent command is
                    prepended to the returned string first.
        """
        name = cmd.name

        if not cmd.enabled:
            name = f'~~{name}~~'

        if cmd.hidden:
            name = f'*{name}*'

        if isinstance(cmd, neko.GroupMixin) and getattr(cmd, 'commands'):
            name = f'{name}\*'

        if is_full:
            name = f'{cmd.full_parent_name} {name}'.strip()

        return name


class ActivityThread(threading.Thread, neko.Cog):
    """
    Handles updating the game every-so-often to a new message.

    I have kind of ditched using Asyncio in a loop on this thread. I keep
    getting issues with something tanking the CPU, and I am not convinced that
    it isn't something to do with this.

    The solution instead is to run a separate thread that sequentially pushes
    events onto this thread's event queue. ``time.sleep`` will yield to another
    process, so this should reduce overhead; albeit at the cost of an extra
    thread.

    This thread will fire and forget as soon as we have initialised this
    cog. It will poll every 10 seconds until the bot is ready. This is messy
    but it will use near to no resources. Each time the thread sleeps, it
    is an opportunity for the OS scheduler to yield to another process
    requesting CPU time.

    Furthermore, the thread is a daemon, so it will automatically die when the
    main thread or last non-daemon thread terminates.
    """
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

        threading.Thread.__init__(
            self,
            name='Activity Changer Loop (daemon)',
            daemon=True
        )

        neko.Cog.__init__(self)

        # Start once ready, then just fire and forget.
        self.start()

    @property
    def loop(self) -> asyncio.BaseEventLoop:
        return self.bot.loop

    def run(self):
        """A hopefully thread-safe loop."""
        # Poll every 10 seconds to see if ready.
        self.logger.info('Waiting for bot to connect to gateway.')
        time.sleep(10)
        while not self.bot.is_ready() and not self.bot.is_closed():
            self.logger.info('... ... still waiting ... ... *yawn* ... ...')
            time.sleep(10)

        self.logger.info('Connected to main thread. Bot is ready. Starting '
                         'loop to dispatch activities NOW.')

        # Main loop to execute once bot is ready.
        while not self.bot.is_closed():
            try:
                self.logger.debug('Creating future in main thread.')
                f: asyncio.Future = self.loop.create_task(self.next_activity())

                while not f.done() and not f.cancelled():
                    # Wait a second or so for the result to finish.
                    time.sleep(1)
            except KeyboardInterrupt:
                return
            except Exception:
                pass
            finally:
                # Wait 30 seconds before the next execution.
                time.sleep(30)

    async def next_activity(self):
        """Acts as an iterator for getting the next activity-change
        coro."""
        # Get a random command, this is more fun.
        command_choice = list(
            filter(
                # Hide superuser commands.
                lambda c: not c.qualified_name.startswith('sudo'),
                self.bot.walk_commands()
            )
        )

        game = random.choice(
            random.choice(command_choice).qualified_names)
        game = self.bot.command_prefix + game

        if game not in self.cache:
            game = discord.Game(
                name=game,
                type=2
            )
            self.cache[game.name] = game
            self.logger.debug(f'Couldn\'t find {game.name} in cache: '
                              f'thus, cached game {game}')
        else:
            self.logger.debug(f'Read cached game {game}')
            game = self.cache[game]

        await self.bot.change_presence(game=game)


class OwnerOnlyCog(neko.Cog):
    """Cog containing owner-only commands, such as to restart the bot."""

    permissions = (neko.Permissions.SEND_MESSAGES |
                   neko.Permissions.ADD_REACTIONS |
                   neko.Permissions.READ_MESSAGES |
                   neko.Permissions.MANAGE_MESSAGES)

    async def __local_check(self, ctx):
        """Only the owner can run any commands or groups in this cog."""
        return await ctx.bot.is_owner(ctx.author)

    @neko.group(
        name='sudo',
        usage='|subcommand',
        brief='Commands and utilities only runnable by the bot owner.',
        hidden=True,
        invoke_without_command=True)
    async def command_grp(self, ctx):
        """
        Run without any arguments to show a list of available commands.
        """
        book = neko.PaginatedBook(title='Available commands',
                                  ctx=ctx)

        for command in self.command_grp.commands:
            book.add_line(command.name)

        await book.send()

    @command_grp.command(
        aliases=['stop', 'restart'],
        brief='Kills the event loop and shuts down the bot.')
    async def stop_bot(self, ctx):
        await ctx.send('Okay, will now logout.')
        await ctx.bot.logout()

    @command_grp.command(brief='DM\'s you a bot invite.')
    async def invite(self, ctx):
        await ctx.author.send(ctx.bot.invite_url)

    @command_grp.command(
        brief='Loads a given extension into the bot.',
        usage='extension.qualified.name'
    )
    async def load(self, ctx, *, fqn):
        """
        Loads the given extension name into the bot.

        WARNING! This will not run in an executor. If the extension loading
        process blocks, then the entire bot will block.
        """
        start = time.time()
        ctx.bot.load_extension(fqn)
        delta = (time.time() - start) * 1e4

        await ctx.send(f'Loaded `{fqn}` successfully in {delta:.3}ms')

    @command_grp.command(
        brief='Unloads a given extension from the bot (and any related cogs).',
        usage='extension.qualified.name|-c CogName'
    )
    async def unload(self, ctx, *, fqn):
        """
        Unloads the given extension name from the bot.

        WARNING! This will not run in an executor. If the extension loading
        process blocks, then the entire bot will block.

        Note. If you wish to remove a single cog instead... pass the fqn
        in with the -c flag.
        """
        if fqn.startswith('-c'):
            fqn = fqn[2:].lstrip()
            if fqn not in ctx.bot.cogs:
                raise ModuleNotFoundError(
                    'Cog was not loaded to begin with.'
                )
            func = ctx.bot.remove_cog
        else:
            if fqn not in ctx.bot.extensions:
                raise ModuleNotFoundError(
                    'Extension was not loaded to begin with.'
                )
            func = ctx.bot.unload_extension

        start = time.time()
        func(fqn)
        delta = (time.time() - start) * 1e4

        await ctx.send(f'Unloaded `{fqn}` successfully via '
                       f'{func.__name__} in {delta:.3}ms')

    @command_grp.command(brief='Sets the bot client verbosity (ignores cogs).')
    async def set_bot_verbosity(self, ctx, verbosity='INFO'):
        """
        Sets the logger verbosity for the bot.

        Valid verbosities are: CRITICAL, DEBUG, ERROR, FATAL, NOTSET, WARN,
        WARNING, and INFO. Note that NOTSET is not advisable, and WARN
        is deprecated, so may become unusable in the future; use WARNING
        instead.
        """
        verbosity = verbosity.upper()
        # noinspection PyProtectedMember
        if verbosity not in logging._nameToLevel.keys():
            raise NameError('Invalid verbosity.')
        else:
            bot_logger = getattr(ctx.bot, 'logger')

            if bot_logger and isinstance(bot_logger, logging.Logger):
                ctx.bot.logger.setLevel(verbosity)

            logging.getLogger('discord').setLevel(verbosity)
            print('SET VERBOSITY TO', verbosity, file=sys.stderr)

    @command_grp.command(brief='Sets the logger verbosity for a loaded cog.')
    async def set_cog_verbosity(self, ctx, cog_name, verbosity='INFO'):
        """
        Sets the logger verbosity for a given cog that is assumed to be
        loaded into the bot currently. This is an instant operation.

        Parameters:\r
        - cog_name - the name of the cog (case sensitive), or '*' for all\r
        - verbosity - the verbosity level to set the logger to, defaults to INFO

        Valid verbosities are: CRITICAL, DEBUG, ERROR, FATAL, NOTSET, WARN,
        WARNING, and INFO. Note that NOTSET is not advisable, and WARN
        is deprecated, so may become unusable in the future; use WARNING
        instead.
        """
        verbosity = verbosity.upper()
        # noinspection PyProtectedMember
        if verbosity not in logging._nameToLevel.keys():
            raise NameError('Invalid verbosity.')

        if cog_name == '*':
            for cog in ctx.bot.cogs.values():
                logger = getattr(cog, 'logger')
                if isinstance(logger, logging.Logger):
                    logger.setLevel(verbosity)
        else:
            try:
                cog = ctx.bot.cogs[cog_name]
            except KeyError:
                raise KeyError('This cog isn\'t loaded.') from None
            else:
                logger = getattr(cog, 'logger')
                if logger is None or not isinstance(logger, logging.Logger):
                    raise AttributeError(
                        'This cog lacks a valid logger attribute.'
                    )
                else:
                    logger.setLevel(verbosity)

        await ctx.message.add_reaction('\N{OK HAND SIGN}')

    @command_grp.command(
        name='ping',
        aliases=['health'],
        brief='Literally does nothing useful other than respond and then '
              'delete the message a few seconds later. Exists to quickly '
              'determine if the bot is still running or not.'
    )
    async def ping(self, ctx):
        await ctx.send('Pong.', delete_after=5)
        await ctx.message.delete()

    @command_grp.command(brief='Shows info about the host\'s health.')
    async def host_health(self, ctx):
        """Gets the host health and resource utilisation."""

        if os.name == 'nt':
            raise NotImplementedError(
                'Here\'s a quarter, kid. Go get yourself a real '
                'operating system.'
            )

        up_fut = asyncio.create_subprocess_exec(
            'uptime',
            stdout=asyncio.subprocess.PIPE,
            encoding='ascii'
        )

        # Gets the username
        user = getpass.getuser()

        ps_fut = asyncio.create_subprocess_exec(
            'ps', '-U', user, '-f', '-o', 'pid,comm,%cpu,%mem,cputime,start',
            stdout=asyncio.subprocess.PIPE,
            encoding='ascii'
        )

        up_res = await up_fut
        ps_res = await ps_fut

        up_stdout = [await up_res.stdout.read()]
        ps_stdout = [await ps_res.stdout.read()]

        up_out = b''.join(up_stdout).decode('ascii')
        ps_out = b''.join(ps_stdout).decode('ascii')

        book = neko.PaginatedBook(
            title=up_out,
            ctx=ctx,
            prefix='```',
            suffix='```'
        )
        book.add_lines(ps_out)

        await book.send()

    @command_grp.command()
    async def list_cogs(self, ctx):
        raise NotImplementedError

    @command_grp.command()
    async def list_extensions(self, ctx):
        raise NotImplementedError

    @command_grp.command()
    async def list_commands(self, ctx):
        raise NotImplementedError



def setup(bot):
    HelpCog.mksetup()(bot)
    OwnerOnlyCog.mksetup()(bot)
    ActivityThread.mksetup()(bot)
