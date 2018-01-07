"""
I/O operations and aliases.
"""

import logging
import json
import os

__all__ = ['load_or_make_json', 'internal_open']


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


def internal_open(file_name, script, mode='r'):
    """
    Gets a resource from the same directory as the script parameter, and
    opens it, returning a file pointer.

    This is kind of similar to Java's object.getClass().getResourceAsStream(...)

    :param file_name: the file name relative to script's directory to open.
    :param script: the script to use relative to the file name.
    :param mode: the file mode, as used in "open". Defaults to 'r'.
    :return: the file pointer.
    """
    path = os.path.join(os.path.dirname(script), file_name)

    return open(path, mode)
