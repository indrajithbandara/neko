"""
Utilities for commands. These inject various pieces of functionality into the
existing discord.py stuff.
"""
import abc
import traceback
import typing

import discord.ext.commands as commands

from neko import excuses, book, strings

__all__ = ['NekoCommand', 'NekoGroup', 'command', 'group']


class CommandMixin(abc.ABC):
    """Functionality to be inherited by a command or group type."""

    @staticmethod
    async def on_error(cog, ctx: commands.Context, error: BaseException):
        """Handles any errors that may occur in a command."""

        # If there is a missing required argument, react with a thought bubble
        # but do nothing else.
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.message.add_reaction('\N{THOUGHT BALLOON}')
            return

        traceback.print_exception(type(error), error, error.__traceback__)
        error = error.__cause__ if error.__cause__ else error

        if isinstance(error, commands.CheckFailure):
            return

        embed = book.Page(
            title='Whoops! Something went wrong!',
            description=strings.capitalise(excuses.get_excuse()),
            color=0xffbf00 if isinstance(error, Warning) else 0xff0000
        )
        error_description = strings.pascal_to_space(type(error).__name__)

        cog = strings.pascal_to_space(getattr(cog, 'name', str(cog)))
        error_description += f' in {cog}: {str(error)}'

        embed.set_footer(text=error_description)

        await ctx.send(embed=embed)

        traceback.print_exception(type(error), error, error.__traceback__)


class NekoCommand(commands.Command, CommandMixin):
    """
    Implementation of a command.
    """
    pass


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
        :exc:`.CommandError` should be used. Note that if the checks fail then
        :exc:`.CheckFailure` exception is raised to the
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
        :exc:`.CommandError` should be used. Note that if the checks fail
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
