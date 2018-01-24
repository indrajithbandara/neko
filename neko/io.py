"""
I/O operations and aliases.
"""

import inspect
import json
import logging
import os

import yaml


__all__ = (
    'load_or_make_json',
    'relative_to_here',
    'load_or_make_yaml'
)


logger = logging.getLogger(__name__)


def __load_or_make(file, default, loader, dumper):
    """
    Opens or creates a string file name, using the ``default``
    if it doesn't exist to populate the file.

    Uses the method given with loader to load from a file pointer,
    and dumper to serialize to the file.

    Use the load_or_make_* methods to access this method. Don't use it
    directly.
    """
    try:
        logger.info(f'Reading {file}.')
        with open(file) as fp:
            return loader(fp)
    except FileNotFoundError:
        logger.warning(f'{file} not found. Creating empty file.')
        with open(file, 'w+') as fp:
            if default is None:
                default = {}
            dumper(default, fp)
        return default


def load_or_make_json(file, *, default=None):
    """Loads a JSON file, or makes it if it does not exist."""
    if default is None:
        default = {}

    return __load_or_make(file, default, json.load, json.dump)


def load_or_make_yaml(file, *, default=None):
    """Loads a YAML file, or makes it if it does not exist."""
    if default is None:
        default = {}

    return __load_or_make(file, default, yaml.load, yaml.dump)


def relative_to_here(path):
    """
    Gets the absolute path of the path relative to the file you called this
    function from. This works by inspecting the current stack and extracting
    the caller module, then getting the parent directory of the caller as an
    absolute path,
    """
    try:
        frame = inspect.stack()[1]
    except IndexError:
        raise RuntimeError('Could not find a stack record. Interpreter has '
                           'been shot.')
    else:
        module = inspect.getmodule(frame[0])
        assert hasattr(module, '__file__'), 'No __file__ attr, whelp.'

        file = module.__file__

        dir_name = os.path.dirname(file)
        abs_dir_name = os.path.abspath(dir_name)

        return os.path.join(abs_dir_name, path)
