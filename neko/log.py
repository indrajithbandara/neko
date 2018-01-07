import abc
import logging

__all__ = ['Loggable']


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
    def get_logger(name: str):
        """Wraps around the get_logger method. Provides a singleton logger."""
        return logging.getLogger(name)
