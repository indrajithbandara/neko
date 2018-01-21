"""
Exceptions.
"""
import abc


class NssmError(RuntimeError, abc.ABC):
    """
    Generic type of error.
    """

    @property
    def name(self):
        """Gets the error name."""
        return type(self).__name__

    @abc.abstractmethod
    def __str__(self):
        """Human readable output."""
        pass

    @abc.abstractmethod
    def __repr__(self):
        """Machine readable output."""
        pass


class UndefinedTokenError(NssmError):
    """
    Raised if an undefined token is found.
    :param index: the index of the character.
    :param row: the 1-based index of the current line we are on.
    :param col: the 1-based index of how many chars into that line we are.
    :param token: the character we did not expect.
    :param line: the line of text we were parsing.
    """
    def __init__(self, index: int, row: int, col: int , token: str, line: str):
        self.index = index
        self.row = row
        self.col = col
        self.token = token
        self.line = line

    def __repr__(self):
        """Simple machine readable representation."""
        return (f'<{self.name} ' 
                f'index={self.index!r} '
                f'row={self.row!r} '
                f'col={self.col!r} '
                f'token={self.token!r} '
                f'line={self.line!r}')

    def __str__(self):
        """
        Shows the character we did not expect, a bit like how GCC points
        to errors with a carat ``^``
        """
        output = f'{self.line.rstrip()}\n'
        output += (' ' * self.col)
        output += '^\n'
        output += f'Undefined token in input {self.row}:{self.col}.'
        return output
