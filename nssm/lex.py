"""
Lexical analysis stage.

Takes a string or strings as input and generates a collection of tokens.
"""
from . import tokens


class Lexer:
    """
    Implementation of a lexical analyser.

    Usage:

    .. code-block: python
       lex = Lexer('<input here>')

       tokens = [lex]
    """
    def __init__(self, _input: str):
        # Positional information.
        self.row = 0
        self.col = 0
        self.index = 0
        self._input = _input

        # Cache this value.
        self._len = len(self._input)

    def __iter__(self):
        """
        Parses the next token.
        """
        try:
            # parse next bit. This is just a placeholder for now.
            for i in range(0, 10):
                yield i
        except IndexError:
            return

    def _parse_string(self):
        """
        Parses a string.
        """
        raise NotImplementedError

    def _parse_identifier(self):
        """
        Parses an identifier.
        """
        raise NotImplementedError

    def _parse_number(self):
        """
        Attempts to parse an integer or float. An integer can be in binary,
        hexadecimal, octal or decimal format.
        """
        raise NotImplementedError

    def _parse_end_of_statement(self):
        """
        This will parse the end of a statement, which can either be a semicolon
        or a newline character. This will also skip any whitespace up to the
        next non-whitespace token, including newlines.
        """
        raise NotImplementedError

    def _skip_whitespace(self):
        """
        Skips arbitrary whitespace. This will NOT skip newlines.
        """
        raise NotImplementedError

    def _go_forwards(self, how_far: int=1):
        """
        Moves the pointer forwards by ``how_far``. If a newline is encountered,
        then we automatically adjust any indexes.
        :param how_far: how many characters to go forwards.
        """
        # Stops bad code.
        assert how_far != 0, 'Are you sure you want to proceed by 0 characters?'
        assert how_far > 0, 'You seem to be trying to reverse... are you sure?'

        while how_far > 0:
            # Work out how the line and col will change before moving
            # the index forwards.
            if self._peek() == '\n':
                self.col = 0
                self.row += 1
            else:
                self.col += 1

            self.index += 1
            how_far -= 1

    def _starts_with(self, string: str):
        """
        Determine if the next section of input to parse starts with the
        given string. This checks from the substring at the current
        parser index onwards.
        :param string: the string to check.
        :return: true if it starts with the string, false otherwise.
        """
        # Again, stops bad code.
        assert string, 'You seem to be passing in an empty string. That is bad.'

        if len(string) == 1:
            # This may be marginally faster as it does not create a new
            # string each time (I think). If this does turn out to have no
            # performance benefit we may as well just remove it and use
            # startswith for everything.
            return self._input[self.index] == string
        else:
            return self._input[self.index:].startswith(string)

    def _peek(self, offset: int=0, count: int=1):
        """
        Peeks at the substring that is waiting to be tokenize-d.
        :param offset: the offset from the current position to peek at.
        :param count: the number of characters from this offset to peek.
            Defaults to 1.
        :return: the character(s) peeked at.
        """
        # Flags up any bad code.
        assert offset >= 0
        assert count > 0

        start = self.index + offset
        end = start + count
        return self._input[start:end]
