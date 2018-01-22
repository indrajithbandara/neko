"""
Lexical analysis stage.

Takes a string or strings as input and generates a collection of tokens.
"""
import typing

from . import ex
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
        # Positional information. Row,col is 1-based. Index is 0-based
        self.row = 1
        self.col = 1
        self.index = 0
        self._input = _input

        # Cache this value.
        self._len = len(self._input)

    def __iter__(self):
        """
        Returns an iterator expression that yields the
        next token, if there is one.
        """
        # While true is used because self._skip_whitespace() should be
        # called before performing the check on each iteration, and it saves
        # duplicating code.
        while True:
            # Skip any whitespace.
            self._skip_whitespace()
            if self.index >= self._len:
                break

            # Next character determines what we do.
            next_char = self._peek()

            # A digit will yield some kind of number.
            if next_char.isnumeric():
                yield self._parse_number()

            # Alpha character is an identifier, as is an underscore.
            elif next_char.isalpha() or next_char == '_':
                yield self._parse_identifier()

            # Single/double quotes denote the start of a string.
            elif next_char in '"\'':
                yield self._parse_string()

            # Newline, semicolon denotes end of statement.
            elif next_char in '\n;':
                yield self._parse_end_of_statement()

            # Otherwise, we raise an exception. Invalid token parsed.
            else:
                raise ex.UndefinedTokenError(
                    self.index,
                    self.row,
                    self.col,
                    next_char,
                    self._get_current_line())

        yield tokens.eof
        return None

    def _parse_identifier(self) -> tokens.IdentifierToken:
        """
        Parses an identifier.
        """
        identifier = ''

        # First character must be alpha or underscore.
        curr = self._peek()
        if not curr.isalpha() and curr != '_':
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                '',
                self._get_current_line())
        else:
            identifier += curr
            self._go_forwards()
            curr = self._peek()

        while curr.isalnum() or curr in '_$':
            identifier += curr
            self._go_forwards()
            curr = self._peek()

        return tokens.IdentifierToken(identifier)

    def _parse_number(self) -> typing.Union[
                                    tokens.DecimalToken,
                                    tokens.RealToken
                               ]:
        """
        Attempts to parse an integer or float. An integer can be in binary,
        hexadecimal, octal or decimal format.
        """
        raise NotImplementedError

    def _parse_string(self) -> tokens.StringToken:
        """
        Parses a string.
        """
        raise NotImplementedError

    def _parse_end_of_statement(self) -> tokens.Token:
        """
        This will parse the end of a statement, which can either be a semicolon
        or a newline character. This will also skip any whitespace up to the
        next non-whitespace token, including newlines.
        """
        raise NotImplementedError

    def _skip_whitespace(self) -> None:
        """
        Skips arbitrary whitespace. This will NOT skip newlines, as these
        can be used to delimit statements. If we have no whitespace, this
        will do nothing, so it is safe to call anywhere where you may expect
        an optional series of whitespace characters.
        """
        while self._starts_with(' ', '\t'):
            self._go_forwards()

    def _go_forwards(self, how_far: int=1) -> None:
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
                self.col = 1
                self.row += 1
            else:
                self.col += 1

            self.index += 1
            how_far -= 1

    def _starts_with(self, *strings: str) -> bool:
        """
        Determine if the next section of input to parse starts with the
        given string. This checks from the substring at the current
        parser index onwards.
        :param string: the string to check, or collection of strings to
                ``any``.
        :return: true if it starts with the string, false otherwise.
        """
        # Again, stops bad code.
        assert strings, 'You seem to be passing in an emptystring. That is bad.'

        return any(self._input[self.index:].startswith(s) for s in strings)

    def _peek(self, offset: int=0, count: int=1) -> str:
        """
        Peeks at the substring that is waiting to be tokenize-d.
        :param offset: the offset from the current position to peek at.
        :param count: the number of characters from this offset to peek.
            Defaults to 1.
        :return: the character(s) peeked at. Returns null if EOF.
        """
        # Flags up any bad code.
        assert offset >= 0, 'Negative offset!'
        assert count > 0, 'Non-positive count!'

        start = self.index + offset
        end = start + count
        val = self._input[start:end]

        if len(val) != end - start:
            return '\0'
        else:
            return val

    def _get_current_line(self) -> str:
        """Attempts to extract the current line."""
        # Find end of line.
        index = self.index
        while index < self._len and self._peek(index) not in '\n;\0':
            index += 1

        return self._input[self.index + 1 - self.col:index]
