"""
An abstract base class that enforces the singleton pattern.

The first time the implementation is instantiated, we create the instance;
every time after that, the same original instance is returned.
"""
import abc
import atexit

__all__ = ['Singleton', 'singleton']


class Singleton:
    """
    Singleton base class implementation.

    Side effect: the constructor must always accept the `self` argument
    and ONLY the `self` argument.

    A hook called __on_exit__ exists that can be overridden to implement
    any tidy-up code for when the application terminates, given that
    no other way of ensuring clean object destruction with finalisation
    routines exists. Being singleton should ensure the lifetime of the
    instance equals that of the entire application.
    """
    def __new__(cls):
        """
        On calling of the singleton.
        """
        if not hasattr(cls, '__instance') or not cls.__instance:
            cls.__instance = object.__new__(cls)

            atexit.register(getattr(cls.__instance, 'on_exit'))

        # noinspection PyTypeChecker
        return cls.__instance

    def on_exit(self):
        """
        Called when the application exits. This does not have to be
        implemented, but it is ensured to be called on exit if any
        shutdown operation needs to be performed.
        """
        pass


def singleton(cls: type) -> object:
    """Handy little decorator to hack-force implement Singleton onto a class."""
    class _SingletonSingleton(Singleton, cls):
        pass

    return _SingletonSingleton()
