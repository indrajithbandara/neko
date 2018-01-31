"""
Utilities for commands. These inject various pieces of functionality into the
existing discord.py stuff.
"""
import abc
import traceback
import typing

import asyncio
import discord
import discord.ext.commands as commands

import neko
from neko import book, strings
from neko.other import excuses

__all__ = ['NekoCommand', 'NekoGroup', 'command', 'group', 'NekoCommandError']


class CommandMixin(abc.ABC):
    """Functionality to be inherited by a command or group type."""

    @property
    def qualified_aliases(self):
        """
        Gets a list of qualified alias names.
        """
        fq_names = []
        # noinspection PyUnresolvedReferences
        for alias in self.aliases:
            # noinspection PyUnresolvedReferences
            fq_names.append(f'{self.full_parent_name} {alias}'.strip())
        return fq_names

    @property
    def qualified_names(self):
        """
        Gets a list of the qualified command name and any qualified alias names.
        """
        # noinspection PyUnresolvedReferences
        fq_names = [self.qualified_name]
        fq_names.extend(self.qualified_aliases)
        return fq_names

    @classmethod
    async def on_error(cls, cog, ctx: commands.Context, error):
        """Handles any errors that may occur in a command."""
        ctx.bot.last_error = (type(error), error, error.__traceback__)

        try:
            # For specific types of error, just react.
            reacts = {
                commands.CheckFailure: '\N{NO ENTRY SIGN}',
                commands.MissingRequiredArgument: '\N{THOUGHT BALLOON}',
                commands.CommandOnCooldown: '\N{ALARM CLOCK}',
                commands.DisabledCommand: '\N{MOBILE PHONE OFF}',
                discord.ClientException: '\N{COLLISION SYMBOL}',
            }

            reaction = neko.find(lambda e: issubclass(type(error), e), reacts)
            reaction = reacts[reaction]

            if not issubclass(type(error), discord.NotFound):
                await ctx.message.add_reaction(reaction)
            else:
                pass  # ?? You cant react to something you cant react to.

        except KeyError:
            # If we haven't specified a reaction, we instead do something
            # meaningful.
            error = error.__cause__ if error.__cause__ else error

            if not isinstance(error, NotImplementedError):
                if isinstance(error, Warning):
                    title = f'\N{WARNING SIGN} {error}'
                else:
                    title = '\N{SQUARED SOS} Oh crap...'

                description = strings.capitalise(excuses.get_excuse())
            else:
                title = (
                    '\N{NO PEDESTRIANS} '
                    'Road under construction. Follow diversion.')

                description = ('Seems this feature isn\'t finished! Hassle '
                               'Espy to get on it. ')

            embed = book.Page(
                title=title,
                description=description,
                colour=0xffbf00 if isinstance(error, Warning) else 0xff0000
            )

            if isinstance(error, NekoCommandError):
                pass
            elif not isinstance(error, Warning):
                # We only show info like the cog name, etc if we are not a
                # neko command error. Likewise, we only dump a traceback if the
                # latter holds.
                error_description = strings.pascal_to_space(
                    type(error).__name__
                )

                cog = strings.pascal_to_space(getattr(cog, 'name', str(cog)))
                error_str = str(error).strip()
                if error_str:
                    error_description += f' in {cog}: {str(error)}'
                else:
                    error_description += f' in {cog}.'

                embed.set_footer(text=error_description)
                traceback.print_exception(
                    type(error),
                    error,
                    error.__traceback__
                )

            resp = await ctx.send(embed=embed)
            await asyncio.sleep(10)
            if isinstance(error, NekoCommandError):
                await resp.delete()
                return
            elif isinstance(error, Warning):
                await resp.edit(content='_Warnings were generated._')
            else:
                await resp.edit(content='_**Errors** were generated._')

            async def del_in_10():
                await asyncio.sleep(10 * 60)
                try:
                    await resp.delete()
                finally:
                    return

            asyncio.ensure_future(del_in_10)


class NekoCommand(commands.Command, CommandMixin):
    """
    Implementation of a command.
    """
    async def can_run(self, ctx):
        """
        Determine whether the command is runnable by the given context.

        This overrides the built in functionality by ensuring that
        checks such as ``discord.ext.commands.is_owner()`` do not raise an
        unhandled exception when failing. If an exception is raised, we just
        defer to ``False.``
        """
        try:
            # noinspection PyUnresolvedReferences
            return await super().can_run(ctx)
        except commands.CommandError:
            return False


class NekoGroup(commands.Group, CommandMixin, commands.GroupMixin):
    """
    Implementation of a command group.
    """

    def command(self, **kwargs):
        kwargs.setdefault('cls', NekoCommand)
        return super().command(**kwargs)

    def group(self, **kwargs):
        kwargs.setdefault('cls', NekoGroup)
        return super().command(**kwargs)

    async def can_run(self, ctx):
        """
        Determine whether the command is runnable by the given context.

        This overrides the built in functionality by ensuring that
        checks such as ``discord.ext.commands.is_owner()`` do not raise an
        unhandled exception when failing. If an exception is raised, we just
        defer to ``False.``
        """
        try:
            # noinspection PyUnresolvedReferences
            return await super().can_run(ctx)
        except commands.CommandError:
            return False


# noinspection PyShadowingBuiltins
@typing.overload
def command(*,
            name: typing.Optional[str] = None,
            aliases: typing.Optional[typing.List[str]] = None,
            help: typing.Optional[str] = None,
            brief: typing.Optional[str] = None,
            usage: typing.Optional[str] = None,
            hidden: typing.Optional[bool] = False,
            enabled: typing.Optional[bool] = True,
            parent: typing.Optional[commands.Command] = None,
            checks: typing.Optional[typing.List[typing.Callable]] = None,
            description: typing.Optional[str] = None,
            rest_is_raw: typing.Optional[bool] = False,
            ignore_extra: typing.Optional[bool] = True) \
        -> typing.Callable[[typing.Any], commands.Command]:
    pass


def command(**kwargs) -> typing.Callable[[typing.Any], commands.Command]:
    """
    Decorates a coroutine to make it into a command.

    name: str
        The name of the command.
    callback: coroutine
        The coroutine that is executed when the command is called.
    help: str
        The long help text for the command.
    brief: str
        The short help text for the command. If this is not specified
        then the first line of the long help text is used instead.
    usage: str
        A replacement for arguments in the default help text.
    aliases: list
        The list of aliases the command can be invoked under.
    enabled: bool
        A boolean that indicates if the command is currently enabled.
        If the command is invoked while it is disabled, then
        :exc:`.DisabledCommand` is raised to the :func:`.on_command_error`
        event. Defaults to ``True``.
    parent: Optional[command]
        The parent command that this command belongs to. ``None`` is there
        isn't one.
    checks
        A list of predicates that verifies if the command could be executed
        with the given :class:`.Context` as the sole parameter. If an exception
        is necessary to be thrown to signal failure, then one derived from
        :exc:`.CommandError` should be used. Note that if the checks fail
        then :exc:`.CheckFailure` exception is raised to the
        :func:`.on_command_error` event.
    description: str
        The message prefixed into the default help command.
    hidden: bool
        If ``True``\, the default help command does not show this in the
        help output.
    rest_is_raw: bool
        If ``False`` and a keyword-only argument is provided then the keyword
        only argument is stripped and handled as if it was a regular argument
        that handles :exc:`.MissingRequiredArgument` and default values in a
        regular matter rather than passing the rest completely raw. If ``True``
        then the keyword-only argument will pass in the rest of the arguments
        in a completely raw matter. Defaults to ``False``.
    ignore_extra: bool
        If ``True``\, ignores extraneous strings passed to a command if all its
        requirements are met (e.g. ``?foo a b c`` when only expecting ``a``
        and ``b``). Otherwise :func:`.on_command_error` and local error handlers
        are called with :exc:`.TooManyArguments`. Defaults to ``True``.
    """
    kwargs.setdefault('cls', NekoCommand)
    return commands.command(**kwargs)


# noinspection PyShadowingBuiltins
@typing.overload
def group(*,
          name: typing.Optional[str] = None,
          aliases: typing.Optional[typing.List[str]] = None,
          help: typing.Optional[str] = None,
          brief: typing.Optional[str] = None,
          usage: typing.Optional[str] = None,
          hidden: typing.Optional[bool] = False,
          enabled: typing.Optional[bool] = True,
          parent: typing.Optional[commands.Command] = None,
          checks: typing.Optional[typing.List[typing.Callable]] = None,
          description: typing.Optional[str] = None,
          rest_is_raw: typing.Optional[bool] = False,
          ignore_extra: typing.Optional[bool] = True,
          all_commands: typing.Optional[typing.Dict] = None,
          invoke_without_command: typing.Optional[bool] = False) \
        -> typing.Callable[[typing.Any], commands.Group]:
    pass


def group(**kwargs) -> typing.Callable[[typing.Any], commands.Group]:
    """
    Decorates a coroutine to make it into a command group

    name: str
        The name of the command.
    callback: coroutine
        The coroutine that is executed when the command is called.
    help: str
        The long help text for the command.
    brief: str
        The short help text for the command. If this is not specified
        then the first line of the long help text is used instead.
    usage: str
        A replacement for arguments in the default help text.
    aliases: list
        The list of aliases the command can be invoked under.
    enabled: bool
        A boolean that indicates if the command is currently enabled.
        If the command is invoked while it is disabled, then
        :exc:`.DisabledCommand` is raised to the :func:`.on_command_error`
        event. Defaults to ``True``.
    parent: Optional[command]
        The parent command that this command belongs to. ``None`` is there
        isn't one.
    checks
        A list of predicates that verifies if the command could be executed
        with the given :class:`.Context` as the sole parameter. If an
        exception
        is necessary to be thrown to signal failure, then one derived from
        :exc:`.NekoCommandError` should be used. Note that if the checks fail
        then
        :exc:`.CheckFailure` exception is raised to the
        :func:`.on_command_error` event.
    description: str
        The message prefixed into the default help command.
    hidden: bool
        If ``True``\, the default help command does not show this in the
        help output.
    rest_is_raw: bool
        If ``False`` and a keyword-only argument is provided then the
        keyword
        only argument is stripped and handled as if it was a regular
        argument
        that handles :exc:`.MissingRequiredArgument` and default values in a
        regular matter rather than passing the rest completely raw. If
        ``True``
        then the keyword-only argument will pass in the rest of the
        arguments
        in a completely raw matter. Defaults to ``False``.
    ignore_extra: bool
        If ``True``\, ignores extraneous strings passed to a command if
        all its
        requirements are met (e.g. ``?foo a b c`` when only expecting ``a``
        and ``b``). Otherwise :func:`.on_command_error` and local error
        handlers
        are called with :exc:`.TooManyArguments`. Defaults to ``True``.
    all_commands: dict
        A mapping of command name to :class:`.Command` or superclass
        objects.
    invoke_without_command: bool
        Indicates if the group callback should begin parsing and
        invocation only if no subcommand was found. Useful for
        making it an error handling function to tell the user that
        no subcommand was found or to have different functionality
        in case no subcommand was found. If this is ``False``, then
        the group callback will always be invoked first. This means
        that the checks and the parsing dictated by its parameters
        will be executed. Defaults to ``False``.
    """
    kwargs.setdefault('cls', NekoGroup)
    return commands.command(**kwargs)


class NekoCommandError(RuntimeWarning):
    """
    Indicates an error has occurred in a command, but it is based on validation
    of input, or calculation of a result; as opposed to an error in the code
    itself.

    This is used to flag various problems such as missing arguments in a
    complicated argument parser, or invalid values. This is handled slightly
    differently to any other type of error/warning in the command handler.
    """
    def __init__(self, msg: typing.Union[str, typing.Iterable[str]]):
        if isinstance(msg, str):
            self.msg = msg
        else:
            self.msg = ', '.join(msg)

    def __str__(self):
        return self.msg
