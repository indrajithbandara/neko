"""
Seems there is no way of adding a hook to handle a connection being closed.

This is a massive pain in the arse, to be honest, as the default action is to
dump a load of warning messages when stuff is still registered in a connection
when it is time to close it.

This implementation adds a list to the connection class implementation and
allows the registering of callbacks to perform before we close the connection.
"""
import asyncpg

from neko.common import is_coroutine


class ShutdownHookConnection(asyncpg.Connection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._on_close_callbacks = []

    def add_closing_listener(self, callback):
        """
        Adds a listener for when the connection is about to close.
        :param callback: the callback to add. Must not be a coroutine,
                and accepts only ``self`` as a parameter.
        """
        if is_coroutine(callback):
            raise TypeError('The callback *can not* be a coroutine.')
        else:
            self._on_close_callbacks.append(callback)

    def _on_release(self, stacklevel=1):
        """Fires any callbacks on the connection closing hook."""
        try:
            [callback(self) for callback in self._on_close_callbacks]
        finally:
            super()._on_release(stacklevel=stacklevel)
