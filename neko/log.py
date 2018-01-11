import abc
import logging

__all__ = ['Loggable', 'with_verbosity']


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