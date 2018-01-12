"""
I/O operations and aliases.
"""

import inspect
import json
import logging
import os

__all__ = ['load_or_make_json', 'relative_to_here']


logger = logging.getLogger(__name__)


def load_or_make_json(file, *, default=None):
    """Loads a JSON file, or makes it if it does not exist."""
    try:
        logger.info(f'Reading {file}.')
        with open(file) as fp:
            return json.load(fp)
    except FileNotFoundError:
        logger.warning(f'{file} not found. Creating empty file.')
        with open(file, 'w') as fp:
            if default is None:
                default = {}
            json.dump(default, fp)
        return default


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
