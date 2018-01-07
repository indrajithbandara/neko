"""
Implementation of a help command.
"""
import asyncio
import inspect
import random

import discord

import neko

__all__ = ['HelpCog', 'ActivityChangerCog', 'setup']

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

        for i, cmd in enumerate(cmds):
            bk += await self.gen_spec_page(ctx, cmd)
            # We add 1, as w
            command_to_page[cmd.qualified_name] = i + offset

        # Set the page
        try:
            page_index = command_to_page[query]
        except KeyError:
            await ctx.send(f'I could not find a command called {query}!')
        else:
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
            color = 0
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


class ActivityChangerCog(neko.Cog):
    """
    Handles updating the game every-so-often to a new message.
    """
    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

        # Use a lock to determine if the coroutine is running or not.
        # This is used to restart the game-displaying loop on_ready if and
        # only if the coroutine is not already running.
        self.running_lock = asyncio.Lock()

    def next_activity(self):
        """Acts as an iterator for getting the next activity-change coro."""
        # Get a random command, this is more fun.
        command_choice = list(
            filter(
                # Hide superuser commands.
                lambda c: not c.qualified_name.startswith('sudo'),
                self.bot.walk_commands()
            )
        )

        command = random.choice(command_choice)
        return self.bot.change_presence(
            game=discord.Game(
                name=f'for {self.bot.command_prefix}{command.qualified_name}',
                type=3
            )
        )

    async def activity_update_loop(self):
        """Handles changing the status every 20 seconds."""
        with await self.running_lock:
            while True:
                try:
                    await self.next_activity()
                except BaseException:
                    pass
                else:
                    await asyncio.sleep(20)

    async def on_ready(self):
        """On ready, if we are not already running a loop, invoke a new one."""

        # Delay on_ready for a couple of seconds to ensure the previous
        # message had time to show.
        await asyncio.sleep(2)

        # First say "READY!" for 10 seconds.
        await self.bot.change_presence(
            game=discord.Game(name='READY!'),
            status=discord.Status
        )

        await asyncio.sleep(10)

        if not self.running_lock.locked():
            asyncio.ensure_future(self.activity_update_loop())

    async def on_connect(self):
        """When we connect to Discord, show the game as listening to Gateway"""
        try:
            # I like random snippets of data.
            # noinspection PyProtectedMember
            gateway = self.bot.ws._trace[0]
        except IndexError:
            gateway = 'the gateway'

        await self.bot.change_presence(
            game=discord.Game(name=gateway, type=2),
            status=discord.Status.dnd
        )


def setup(bot):
    """Adds the help cog to the bot."""
    HelpCog.mksetup()(bot)
    ActivityChangerCog.mksetup()(bot)
