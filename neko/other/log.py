import abc
import logging

__all__ = ['Loggable', 'with_verbosity', 'get_logger', 'as_level']


class Loggable(abc.ABC):
    """
    Injects a logger into the inheriting class definition under the
    "logger" attribute.
    """
    __slots__ = ['logger']
    logger: logging.Logger

    def __init_subclass__(cls, **__):
        """Injects the logger into the definition of the subclass."""
        cls.logger = logging.getLogger(cls.__qualname__)

    @staticmethod
    def generate_logger(name: str):
        """Wraps around the get_logger method. Provides a singleton logger."""
        return logging.getLogger(name)


def with_verbosity(level):
    """Overrides a logger's verbosity for the class. Mainly a debugging aid."""
    def decorator(cls):
        assert isinstance(cls, type) and issubclass(cls, Loggable)

        cls.logger.setLevel(level)
        return cls
    return decorator


def get_logger(name):
    """
    Gets a singleton logger.
    """
    return Loggable.generate_logger(name)


def as_level(name):
    """
    Returns the associated level with the logger level name provided.
    """
    # noinspection PyProtectedMember
    return logging._nameToLevel[name.upper()]
