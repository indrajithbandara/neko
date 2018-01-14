"""
Abstract cog definition.
"""
import inspect
import typing

import discord.ext.commands as commands
from neko import log

__all__ = ['Cog', 'inject_setup']


class Cog(log.Loggable):
    """Cog class definition."""
    permissions = 0

    @property
    def name(self):
        """Gets the cog name."""
        return type(self).__name__

    def commands(self) -> typing.Iterable[commands.Command]:
        """Yields an iterator of the commands declared in this cog."""
        return set(
            m[1] for m in inspect.getmembers(
                self,
                lambda _m: isinstance(_m, commands.Command)
            )
        )

    def events(self) -> typing.Iterable:
        """Yields an iterator of the events declared in this cog."""
        return (m[1] for m in inspect.getmembers(
            self,
            lambda _m: getattr(_m, '__name__', '').startswith('on_')
        ))

    async def __local_check(self, ctx):
        """
        A check that is performed before invoking
        anything defined in _this_ cog. This can be
        a coroutine.
        :param ctx: the command context.
        """
        pass

    async def __global_check(self, ctx):
        """
        A check that is performed before invoking
        anything anywhere in the bot. This can be a
        coroutine.
        :param ctx: the command context.
        """
        pass

    async def __local_check_once(self, ctx):
        """
        A check that is performed before invoking
        anything defined in _this_ cog for the first time.
        This can be a coroutine.
        :param ctx: the command context.
        """
        pass

    async def __global_check_once(self, ctx):
        """
        A check that is performed before invoking
        anything anywhere in the bot for the first time.
        This can be a coroutine.
        :param ctx: the command context.
        """
        pass

    async def __before_invoke(self, ctx):
        """
        Run before the invocation of any command.
        """
        pass

    async def __after_invoke(self, ctx):
        """
        Run after the invocation of any command, regardless of
        the output.
        """
        pass

    def __unload(self):
        """
        Called when the cog is unloaded.
        This can NOT be a co-routine.
        """
        pass

    # noinspection PyArgumentList
    @classmethod
    def mksetup(cls):
        """
        Returns a setup method. Assign this to a global called "setup".

        This inspects the __init__ method now, also; ensuring to pass
        the bot as a parameter if that is specified.
        """
        signature = inspect.signature(cls.__init__)
        obj_signature = inspect.signature(object.__init__)

        params = set(signature.parameters.keys())

        # If we have the default constructor, then don't pass anything in
        # for now.
        is_obj_constructor = params == set(obj_signature.parameters.keys())
        is_empty_constructor = len(params) == 1 and 'self' in params

        if is_empty_constructor or is_obj_constructor:
            return lambda bot: bot.add_cog(cls())
        elif len(params) == 2 and 'bot' in params:
            return lambda bot: bot.add_cog(cls(bot))
        else:
            raise NotImplementedError(
                f'Unsupported auto-generation of setup for {signature}')


def inject_setup(cog: typing.Type[Cog]):
    """
    Decorates a cog and injects a setup method into global scope for it.
    :param cog: the cog to inject a setup method for
    :return: the cog decorated.
    """
    module = inspect.getmodule(cog)

    if hasattr(module, 'setup'):
        raise RuntimeWarning(f'{module} already has a member called setup.')

    setattr(module, 'setup', cog.mksetup())
    return cog
