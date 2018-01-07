"""
Owner-only commands. These do tasks such as restart the bot.
"""
import os
import subprocess
import sys

import discord
import time

import neko

__all__ = ['OwnerOnlyCog', 'setup']


def __run_git_command(dont_stash, *args):
    # We assume sys.argv[0] will be __main__.py.
    # We therefore just get that path, get the dirname
    # and go up one directory to get our working directory
    # to call git in.
    entry_point = os.path.dirname(sys.argv[0])
    entry_point = os.path.join(entry_point, '..')

    # We do not let this run for more than 60 seconds.
    # If it does, a TimeoutExpired exception will be thrown
    # and we allow this to propagate out of this executor, into
    # the command handler, where it shall be handled by the on_error
    # handler I designed.

    # We run git stash first in case there is uncommitted changes.
    if not dont_stash:
        subprocess.run(
            ['git', 'stash'],
            cwd=entry_point,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            encoding='ascii'
        )

    result = subprocess.run(
        ['git', *args],
        cwd=entry_point,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        encoding='ascii'
    )

    if not dont_stash:
        subprocess.run(
            ['git', 'stash', 'apply'],
            cwd=entry_point,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            encoding='ascii'
        )
    return result


async def _git_stash_and_do(ctx, *args, dont_stash=False):
    # Run in an executor to ensure we do not block the event loop.
    async with ctx.channel.typing():
        completed_process = await neko.no_block(
            __run_git_command,
            args=[dont_stash, *args]
        )

        print(completed_process.stdout)
        print(completed_process.stderr, file=sys.stderr)

        stream = 'stderr' if completed_process.returncode else 'stdout'
        stream = getattr(completed_process, stream)

        # If the output is very long, paginate.
        title = f'git {" ".join(args)}'
        if len(stream) > 1900:
            pb = neko.PaginatedBook(
                title=title,
                ctx=ctx,
                max_size=800
            )
            pb.add_lines(stream)
            await pb.send()
        else:
            await ctx.send(
                embed=discord.Embed(
                    title=title,
                    description=stream,
                    color=0x9b2d09
                )
            )


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
        name='stop', aliases=['restart'],
        brief='Kills the event loop and shuts down the bot.')
    async def stop_bot(self, ctx):
        await ctx.send('Okay, will now logout.')
        await ctx.bot.logout()

    @command_grp.command(
        name='invite',
        brief='DM\'s you a bot invite.'
    )
    async def invite(self, ctx):
        await ctx.author.send(ctx.bot.invite_url)

    @command_grp.command(
        name='load',
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
        name='unload',
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



    @command_grp.group(
        name='git',
        brief='Various version control tasks.'
    )
    async def git_group(self, ctx):
        pass

    @git_group.command(
        name='pull',
        brief='Executes `git pull`.'
    )
    async def git_pull(self, ctx):
        await _git_stash_and_do(ctx, 'pull')

    @git_group.command(
        name='checkout',
        brief='Executes `git checkout`.'
    )
    async def git_checkout(self, ctx, *, branch: str):
        await _git_stash_and_do(ctx, 'checkout', branch)

    @git_group.command(
        name='log',
        brief='Executes `git log`.'
    )
    async def git_log(self, ctx):
        """Shows the git log. Suppresses any email information."""
        await _git_stash_and_do(
            ctx,
            'log',
            '-n',
            '30',
            '--oneline',
            dont_stash=True
        )


setup = OwnerOnlyCog.mksetup()
