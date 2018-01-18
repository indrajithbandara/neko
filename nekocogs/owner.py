"""
Owner-only operations, administrative stuff, etc.
"""

import asyncio
import getpass
import logging
import os
import sys
import time

import neko
import neko.other.perms as perms


@neko.cog.inject_setup
class OwnerOnlyCog(neko.Cog):
    """Cog containing owner-only commands, such as to restart the bot."""

    permissions = (perms.Permissions.SEND_MESSAGES |
                   perms.Permissions.ADD_REACTIONS |
                   perms.Permissions.READ_MESSAGES |
                   perms.Permissions.MANAGE_MESSAGES)

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
        await ctx.bot.do_job_in_pool(ctx.bot.load_extension, fqn)
        delta = (time.time() - start) * 1e4

        await ctx.send(f'Loaded `{fqn}` successfully in {delta:.3f}ms')

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
        await ctx.bot.do_job_in_pool(func, fqn)
        delta = (time.time() - start) * 1e4

        await ctx.send(f'Unloaded `{fqn}` successfully via '
                       f'{func.__name__} in {delta:.3f}ms')

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
            await ctx.message.add_reaction('\N{OK HAND SIGN}')

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
        brief='Literally does nothing useful other than respond and then '
              'delete the message a few seconds later. Exists to quickly '
              'determine if the bot is still running or not.'
    )
    async def ping(self, ctx):
        await ctx.send('Pong.', delete_after=5)
        await ctx.message.delete()

    @command_grp.command(
        aliases=['health'],
        brief='Shows info about the host\'s health.')
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

    @command_grp.command(enabled=False)
    async def list_cogs(self, ctx):
        raise NotImplementedError

    @command_grp.command(enabled=False)
    async def list_extensions(self, ctx):
        raise NotImplementedError

    @command_grp.command(brief='Lists commands in the bot.')
    async def list_commands(self, ctx):
        """
        Lists loaded commands and aliases.
        """

        book = neko.PaginatedBook(
            ctx=ctx,
            title='Loaded commands',
            max_lines=15)

        command_lines = []

        for command in sorted({*ctx.bot.walk_commands()},
                              key=lambda c: c.qualified_name):

            line = f'**{command.qualified_name}** '

            if command.aliases:
                line += f'({", ".join(command.aliases)}) '

            if not command.enabled:
                line += 'disabled '

            cn = command.cog_name
            if cn:
                line += f'cog:{cn} '

            line += f'module:{command.module}'
            command_lines.append(line)
        book.add_lines(command_lines)

        await book.send()

    @neko.command(name='uptime', brief='Says how long I have been running for.')
    async def get_uptime(self, ctx):
        msg = (
            f'Bot logged in at {ctx.bot.start_time} UTC, running without a '
            f'major breaking issue or manual restart for {ctx.bot.up_time}.'
        )

        await ctx.send(msg)
