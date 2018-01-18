"""
Contains common helper methods and definitions
"""
import abc
import asyncio
import inspect
import random
import sys
import typing

from neko import strings

__all__ = [
    'find', 'async_find', 'get_or_die', 'is_coroutine', 'python_extensions',
    'random_color', 'random_colour', 'between', 'json_types',
    'InitClassHookMeta'
]

# Valid file extensions for python scripts, compiled binaries, archives,
# cython source, cython headers, etc.
python_extensions = [
    '.py', '.py3', '.pyc', '.pyo', '.pyw', '.pyz', '.pyx', '.pyd', '.pxd'
]

# Valid JSON types, or types a caller would expect as a return type from
# JSON deserialization.
json_types = typing.Union[int, float, str, bool, dict, list, None]


def find(predicate: typing.Callable,
         iterable: typing.Iterable):
    """
    Finds the first element in an iterable matching a predicate.

    :param predicate: predicate that returns true for any match.
    :param iterable: iterable to iterate over.
    :return: the first match; None if there is not one available.
    """
    for element in iterable:
        if predicate(element):
            return element
    return None


async def async_find(predicate: typing.Callable,
                     iterable: typing.Union[
                         typing.AsyncIterable,
                         typing.Iterable
                     ]):
    """
    Finds the first element in an iterable matching a predicate.

    This is slower than ``find``, but it allows for an async-marked predicate
    and awaitable elements in iterables. It also accepts iterable being
    an async iterator, which is rather classy, I would say.

    :param predicate: predicate that returns true for any match.
    :param iterable: iterable to iterate over (must be a coroutine
    :return: the first match; None if there is not one available.
    """
    if not is_coroutine(predicate):
        predicate = asyncio.coroutine(predicate)

    if hasattr(iterable, '__aiter__'):
        async for element in iterable:
            element = await element if is_coroutine(element) else element
            if await predicate(element):
                return element
    else:
        for element in iterable:
            element = await element if is_coroutine(element) else element
            if await predicate(element):
                return element

    return None


def get_or_die(d: typing.Dict,
               key: typing.Any,
               failure_msg: str=None) -> typing.Any:
    """
    Gets a the value associated with a key in a given dict.

    If said key is not present, then a friendly error message is
    printed, and the Python interpreter will terminate with exit code 2.

    This is intended for use when parsing configurations that have required
    keys. This will not dump an irrelevant traceback to stderr like an
    unhandled error would.
    """
    if not failure_msg:
        failure_msg = f'Failed to find required field {key}.'
    else:
        if not failure_msg[-1] in ('!', '?', '.'):
            failure_msg += '.'
        failure_msg = strings.capitalise(failure_msg)

    try:
        return d[key]
    except KeyError:
        # Gets the traceback frame for the function invocation (second frame
        # on the stack)
        where = inspect.stack()[1]

        # where[1] = file name
        # where[2] = line
        # where[3] = function name
        print(failure_msg,
              f'\nOccurred in {where[1]}:{where[2]} ({where[3]}).',
              'Please fix this. Will now exit.',
              file=sys.stderr)
        exit(2)


def is_coroutine(coro):
    """Returns true if the argument is a coroutine or coroutine function."""
    return inspect.iscoroutine(coro) or inspect.iscoroutinefunction(coro)


def random_colour(bits=24):
    """Returns a random 24-bit colour hex value."""
    return random.randint(0, (2 ** bits) - 1)


# MAKE AMERICA GREAT AGAIN
random_color = random_colour


def between(start: int, stop: int, step: int=1):
    """
    Like ``range()``, but this INCLUDES the stop value.

    ``range`` produces results in the range [start, stop)
    ``between`` produces results in the range [start, stop]

    :param start: start value.
    :param stop: end value (inclusive).
    :param step: step to perform each time. Defaults to ``+1``.
    :return: a range object.
    """
    return range(start, stop + 1, step)


class InitClassHookMeta(abc.ABC, type):
    """
    Adds a piece of code to call a method called __init_class__ if it exists.

    This works just as __init__ does, but on a class basis, and just the once.
    """
    def __init_subclass__(mcs, **kwargs):
        on_init = getattr(mcs, '__init_class__')
        on_init(mcs)

    @classmethod
    def __init_class__(mcs, *_, **__):
        pass
