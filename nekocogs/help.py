"""
Implementation of a help command.
"""
import inspect

import neko
import neko.other.perms as perms


# Dodger blue.
default_color = 0x1E90FF


async def should_show(cmd, ctx):
    """
    Logic to determine whether to include a given page in the help.

    This filters out all disabled, hidden and unrunnable commands except if
    the ctx was invoked by the bot owner; in this case, everything is
    displayed regardless.

    :param cmd: command to verify.
    :param ctx: context to check against.
    :return: true if we should show it, false otherwise.
    """
    if ctx.author.id == ctx.bot.owner_id:
        return True
    else:
        can_run = await cmd.can_run(ctx)
        is_hidden = cmd.hidden
        is_enabled = cmd.enabled
        return can_run and not is_hidden and is_enabled


@neko.inject_setup
class HelpCog(neko.Cog):
    """Provides the inner methods with access to bot directly."""

    permissions = (perms.Permissions.SEND_MESSAGES |
                   perms.Permissions.ADD_REACTIONS |
                   perms.Permissions.READ_MESSAGES |
                   perms.Permissions.MANAGE_MESSAGES)

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
        all_cmds = sorted(set(self.bot.walk_commands()),
                          key=lambda c: c.qualified_name)

        # We offset each index in the enumeration by this to get the
        # correct page number.
        offset = len(bk)

        # Strip out any commands we don't want to show.
        cmds = [cmd for cmd in all_cmds if await should_show(cmd, ctx)]

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
            name='Notable contributors',
            value=', '.join(neko.__contributors__)
        )

        page.add_field(name='Thanks to', value=neko.__thanks__, inline=False)

        page.add_field(
            name='Repository',
            value=neko.__repository__
        )

        cmds = sorted(self.bot.commands, key=lambda c: c.name)
        cmds = [await self.format_command_name(cmd, ctx)
                for cmd in cmds if await should_show(cmd, ctx)]

        page.add_field(
            name='Available commands',
            value=', '.join(cmds),
            inline=False
        )

        page.add_field(
            name='Notations used in this help utility',
            value='- ~~strike~~ - this command is disabled, or cannot be run '
                  'by your user, or in the current location.\n'
                  '- _italics_ - this command is usually hidden from the main '
                  'list.\n'
                  '- starred\* - this command has sub-commands defined.',
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
        fqn = await self.format_command_name(cmd, ctx, is_full=True)
        brief = cmd.brief if cmd.brief else 'Whelp! No info here!'
        doc_str = neko.remove_single_lines(cmd.help)
        usages = cmd.usage.split('|') if cmd.usage else ''
        usages = map(lambda u: f'• {pfx}{cmd.qualified_name} {u}', usages)
        usages = '\n'.join(sorted(usages))
        aliases = sorted(cmd.aliases)
        cooldown = getattr(cmd, '_buckets')

        if cooldown:
            cooldown: neko.Cooldown = getattr(cooldown, '_cooldown')

        if cmd.parent:
            super_command = await self.format_command_name(cmd.parent, ctx)
        else:
            super_command = None

        # noinspection PyUnresolvedReferences
        can_run = await cmd.can_run(ctx)

        if isinstance(cmd, neko.GroupMixin):
            async def sub_cmd_map(c):
                c = await self.format_command_name(c, ctx, is_full=True)
                c = f'• {c}'
                return c

            # Cast to a set to prevent duplicates for aliases. Hoping this
            # fixes #9 again.
            # noinspection PyUnresolvedReferences
            sub_commands = cmd.walk_commands()
            sub_commands = [await sub_cmd_map(c) for c in sub_commands]
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
            title=await self.format_command_name(cmd, ctx, is_full=True),
            description=brief,
            color=color
        )

        if doc_str:
            page.add_field(
                name='More info',
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
            timeout = cooldown.per
            if timeout.is_integer():
                timeout = int(timeout)

            string = (
                f'{neko.capitalise(cooldown.type.name)}-scoped '
                f'{neko.pluralise(cooldown.rate, "request", method="per app")} '
                f'with timeout of {neko.pluralise(timeout, "second")}.')

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
                text='You do not hve permission to run the command here... '
                     'Sorry!'
            )
        elif not cmd.enabled:
            page.set_footer(
                text='This command has been disabled globally by the dev.'
            )

        return page

    @staticmethod
    async def format_command_name(cmd: neko.NekoCommand,
                                  ctx,
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
        :param ctx: the command context.
        :param is_full: defaults to false. If true, the parent command is
                    prepended to the returned string first.
        """
        if is_full:
            name = f'{cmd.full_parent_name} {cmd.name}'.strip()
        else:
            name = cmd.name

        if not cmd.enabled or not await cmd.can_run(ctx):
            name = f'~~{name}~~'

        if cmd.hidden:
            name = f'*{name}*'

        if isinstance(cmd, neko.GroupMixin) and getattr(cmd, 'commands'):
            name = f'{name}\*'

        return name
