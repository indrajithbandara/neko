"""
Seems there is no way of adding a hook to handle a connection being closed.

This is a massive pain in the arse, to be honest, as the default action is to
dump a load of warning messages when stuff is still registered in a connection
when it is time to close it.

This implementation adds a list to the connection class implementation and
allows the registering of callbacks to perform before we close the connection.

EDIT: also added code to, if debug logging is enabled, display SQL queries
as they are executed.
"""
import asyncpg

import neko
import neko.other.log as log


is_debug = True


class ShutdownHookConnection(asyncpg.Connection):
    # Seems asyncpg complains if I inherit loggable.
    logger = log.get_logger(__file__)
    logger.setLevel('INFO' if not is_debug else 'DEBUG')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_close_callbacks = []

    def add_closing_listener(self, callback):
        """
        Adds a listener for when the connection is about to close.
        :param callback: the callback to add. Must not be a coroutine,
                and accepts only ``self`` as a parameter.
        """
        if neko.is_coroutine(callback):
            raise TypeError('The callback *can not* be a coroutine.')
        else:
            self._on_close_callbacks.append(callback)

    def _on_release(self, stacklevel=1):
        """Fires any callbacks on the connection closing hook."""
        try:
            [callback(self) for callback in self._on_close_callbacks]
        finally:
            super()._on_release(stacklevel=stacklevel)

    async def execute(self, *args, **kwargs):
        args_str = 'in execute:\n' + '\n' + ', '.join([
            ', '.join(str(arg) for arg in args),
            ', '.join(f'{k}={v}' for k, v in kwargs.items())
        ]) + '\n' + '*' * 80

        self.logger.debug(args_str)
        return await super().execute(*args, **kwargs)

    async def fetch(self, *args, **kwargs):
        args_str = 'in fetch:\n' + '\n' + ', '.join([
            ', '.join(str(arg) for arg in args),
            ', '.join(f'{k}={v}' for k, v in kwargs)
        ]) + '\n' + '*' * 80

        self.logger.debug(args_str)
        return await super().fetch(*args, **kwargs)
