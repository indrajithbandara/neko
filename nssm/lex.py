"""
Lexical analysis stage.

Takes a string or strings as input and generates a collection of tokens.
"""
import inspect
import typing

import unicodedata

from . import ex
from . import tokens

__all__ = ('Lexer',)

# https://en.wikipedia.org/wiki/Escape_sequences_in_C#Table_of_escape_sequences
_fixed_esc_c = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    'v': '\v',
    '\'': '\'',
    '\\': '\\',
    '"': '"'
}


def _is_binary(c):
    """Ensures character is a binary digit."""
    return c in '01'


_is_digit = str.isdigit


def _is_octal(c):
    """Ensures character is an octal digit."""
    return c in '01234567'


def _is_hex(c):
    """Ensures character is a hexadecimal digit."""
    return c in '0123456789ABCDEFabcdef'


class Lexer:
    """
    Implementation of a lexical analyser. These are iterable. In iterating
    over the object, you will change the state and parse the next token.

    To reuse the lexer, you should either make a new object, or call the
    ``reset`` method.

    Usage:

    .. code-block: python
       lex = Lexer('<input here>')

       tokens = [token for token in lex]
    """

    def __init__(self, _input: str):
        # Positional information. Row,col is 1-based. Index is 0-based

        # This saves processing later. Replace any instances of a backslash
        # followed by a new line immediately with emptystring. This allows
        # for continuation of lines in the script.
        _input = _input.replace('\\\n', '')

        self.row = 1
        self.col = 1
        self.index = 0
        self._input = _input

        # Cache this value.
        self._len = len(self._input)

    def reset(self):
        """Resets the state of the Lexer."""
        self.index = 0
        self.row = self.col = 1

    def __len__(self):
        """Gets the stored length of the input."""
        return self._len

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
            if next_char.isnumeric() or next_char == '.':
                yield self._parse_number()

            # Alpha character is an identifier, as is an underscore.
            elif next_char.isalpha() or next_char == '_':
                yield self._parse_identifier_or_rw()

            # Single/double quotes denote the start of a string.
            elif next_char in '"\'':
                yield self._parse_string()

            # Newline, semicolon denotes end of statement.
            elif next_char in '\n;':
                yield self._parse_end_of_statement()

            # Otherwise, we attempt to parse an operator.
            else:
                yield self._parse_operator()

        # Kill the iterator here.
        yield tokens.eof

    def _parse_identifier_or_rw(self) -> typing.Union[
        tokens.IdentifierToken,
        tokens.ReserveWordToken
    ]:
        """
        Parses an identifier or reserve word.
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
                self._current_line)
        else:
            # If it is a reserve word, fetch it.
            for rw, t in tokens.ReserveWordToken.reserve_words.items():
                if self._starts_with(rw):
                    self._go_forwards(len(rw))
                    return t

            # Otherwise, it is definitely an identifier.
            identifier += curr
            self._go_forwards()
            curr = self._peek()

            while curr.isalnum() or curr in '_$':
                identifier += curr
                self._go_forwards()
                curr = self._peek()

            return tokens.IdentifierToken(identifier)

    def _parse_number(self) -> typing.Union[
        tokens.IntToken,
        tokens.RealToken
    ]:
        """
        Attempts to parse an integer or float. An integer can be in binary,
        hexadecimal, octal or decimal format.
        """
        if self._starts_with('0b', '0B'):
            return self._parse_bin()
        elif self._starts_with('0o', '0O'):
            return self._parse_oct()
        elif self._starts_with('0x', '0X'):
            return self._parse_hex()

        # If we reach here, we have a base-10 int, or a float.
        # Floats will have one, or both of a decimal point, and
        # an exponent.
        is_float = False
        number_str = ''

        curr = self._peek()
        if curr.isdigit():
            number_str += self._parse_int()
            curr = self._peek()

        if curr == '.':
            is_float = True
            number_str += '.'
            self._go_forwards()
            curr = self._peek()

        if curr.isdigit():
            number_str += self._parse_int()
            curr = self._peek()

        if curr in 'eE':
            is_float = True
            number_str += 'e'
            self._go_forwards()
            curr = self._peek()
            if curr in '+-':
                number_str += curr
                self._go_forwards()
            number_str += self._parse_int()

        if len(number_str) == 0:
            raise ex.UndefinedTokenError(
                self.index,
                self.row,
                self.col,
                self._peek(),
                self._current_line,
                'Not a number.'
            )
        elif is_float:
            return tokens.RealToken(float(number_str))
        else:
            return tokens.IntToken(int(number_str))

    def _parse_int(self) -> str:
        """Parses a base-10 integer of 1 or more digits."""
        # One or more binary digits must follow.
        int_str = self.__ensure_at_least_one(
            _is_digit,
            'Invalid decimal integer literal.')

        return int_str

    def _parse_hex(self) -> tokens.IntToken:
        """
        Parses a hexadecimal string of digits into an int.
        """
        if not self._starts_with('0x', '0X'):
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                self._peek(),
                self._current_line,
                'Not a hexadecimal token.')
        else:
            self._go_forwards(2)

        # One or more hex digits must follow.
        hex_str = self.__ensure_at_least_one(
            _is_hex,
            'Invalid hexadecimal literal.')

        val = int(hex_str, base=16)
        return tokens.IntToken(val)

    def _parse_oct(self) -> tokens.IntToken:
        """
        Parses an octal string of digits into an int.
        """
        if not self._starts_with('0o', '0O'):
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                self._peek(),
                self._current_line,
                'Not an octal token.')
        else:
            self._go_forwards(2)

        # One or more octal digits must follow.
        oct_str = self.__ensure_at_least_one(
            _is_octal,
            'Invalid octal literal.')

        val = int(oct_str, base=8)
        return tokens.IntToken(val)

    def _parse_bin(self) -> tokens.IntToken:
        """
        Parses a binary string of digits into an int.
        """
        if not self._starts_with('0b', '0B'):
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                self._peek(),
                self._current_line,
                'Not a binary token.')
        else:
            self._go_forwards(2)

        # One or more binary digits must follow.
        bin_str = self.__ensure_at_least_one(
            _is_binary,
            'Invalid binary literal.')

        val = int(bin_str, base=2)
        return tokens.IntToken(val)

    def _parse_string(self) -> tokens.StringToken:
        """
        Parses a string.
        """
        # We match this later.
        opener = self._peek()
        if opener not in '\'"':
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                self._peek(),
                self._current_line,
                'Not a string.')
        else:
            self._go_forwards()

        string = ''

        while True:
            if self.index >= self._len:
                raise ex.UnclosedStringError(
                    self.index,
                    self.row,
                    self.col,
                    self._peek(),
                    self._current_line,
                    'String was not closed')

            curr = self._peek()

            # Handle an escape character
            if curr == '\\':
                self._go_forwards()
                curr = self._peek()

                if curr in _fixed_esc_c:
                    string += _fixed_esc_c[curr]
                    self._go_forwards()

                # Parses utf escape. This is up to 8 UTF-8 characters.
                elif curr == 'u':
                    self._go_forwards()
                    char_seq = self.__ensure_at_least_one(
                        _is_hex,
                        'Invalid UTF-8 literal.')

                    # Parse the char sequence as UTF-8.
                    try:
                        char_seq = chr(int(char_seq, 16))
                    except ValueError as err:
                        # Raised if out of the range 0 <= i <= 0x10FFFF
                        raise ex.InvalidTokenError(
                            self.index,
                            self.row,
                            self.col,
                            self._peek(),
                            self._current_line,
                            str(err)) from None
                    else:
                        string += char_seq
                elif curr == 'N':
                    self._go_forwards(2)
                    descriptor = self.__ensure_at_least_one(
                        lambda c: c != '}',
                        'Invalid UTF-8 character description.')

                    if self._peek() != '}':
                        raise ex.InvalidTokenError(
                            self.index,
                            self.row,
                            self.col,
                            self._peek(),
                            self._current_line,
                            'UTF-8 description was not closed.')

                    try:
                        descriptor = unicodedata.lookup(descriptor)

                        # Skip the '}'
                        self._go_forwards()
                        string += descriptor
                    except KeyError as err:
                        raise ex.InvalidTokenError(
                            self.index,
                            self.row,
                            self.col,
                            self._peek(),
                            self._current_line,
                            str(err)) from None
                else:
                    raise ex.InvalidTokenError(
                            self.index,
                            self.row,
                            self.col,
                            self._peek(),
                            self._current_line,
                            f'Unrecognised escape sequence `\\{self._peek()}`.')
            elif curr != opener:
                string += curr
                # Proceed forwards.
                self._go_forwards()
            else:
                # We have reached the end of the string, and it is valid.
                break

        # Skip the end quote.
        self._go_forwards()

        # Return the parsed string.
        return tokens.StringToken(string)

    def _parse_operator(self) -> tokens.OperatorToken:
        """
        Parses an operator or other Misc token.
        """
        for lit, t in tokens.OperatorToken.operators.items():
            if self._starts_with(lit):
                # Move forwards
                self._go_forwards(len(lit))
                return t

        raise ex.UndefinedTokenError(
            self.index,
            self.row,
            self.col,
            self._peek(),
            self._current_line)

    def _parse_end_of_statement(self) -> tokens.Token:
        """
        This will parse the end of a statement, which can either
        be a semicolon or a newline character. This will also
        skip any whitespace up to the next non-whitespace token,
        including newlines.

        This also strips out consecutive newlines, and handles semicolons
        correctly. ADDITIONALLY, it allows lines to have whitespace on them,
        whilst still ignoring them for the most part.

        Thus `\n\n;\n\n` will be resolved to `EOL,EOF` in this tokenizer.
        This will save slight memory, and means code is slightly shorter too.
        """
        curr = self._peek()
        if curr != ';':
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                curr,
                self._current_line,
                'Not an end of statement.')

        self._go_forwards()

        while True:
            self._skip_whitespace()
            curr = self._peek()
            if curr != ';':
                break
            else:
                self._go_forwards()

        return tokens.eos

    def _skip_whitespace(self) -> None:
        """
        Skips arbitrary whitespace. This will NOT skip newlines, as these
        can be used to delimit statements. If we have no whitespace, this
        will do nothing, so it is safe to call anywhere where you may expect
        an optional series of whitespace characters.
        """
        while self._peek().isspace():
            self._go_forwards()

    def _go_forwards(self, how_far: int = 1) -> None:
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

    def _peek(self, offset: int = 0, count: int = 1) -> str:
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

    @property
    def _current_line(self) -> str:
        """Attempts to extract the current line."""
        # Find end of line.
        index = self.index
        while index < self._len and self._peek(index) not in '\n;\0':
            index += 1

        return self._input[self.index + 1 - self.col:index]

    def __ensure_at_least_one(self,
                              predicate: typing.Callable[[str], bool],
                              desc: typing.Optional[str] = None) -> str:
        """
        Captures characters from the input. We capture as many as we can, but we
        ENFORCE that we get a match on the first character, else we raise an
        InvalidTokenError. The presence of a non-match after this will just
        terminate capturing, and return a string of what we already parsed.

        :param predicate: the predicate to use to validate each character.
        :param desc: the description to use if an error occurs. If this is
                None, or unspecified, then we default to the docstring for the
                predicate. If this is undefined, we supply no message body to
                any error.
        """
        if not desc:
            desc = inspect.cleandoc(inspect.getdoc(predicate))
            if not desc:
                desc = ''

        curr = self._peek()
        if not predicate(curr):
            raise ex.InvalidTokenError(
                self.index,
                self.row,
                self.col,
                curr,
                self._current_line,
                desc)

        parsed = curr
        self._go_forwards()

        while True:
            curr = self._peek()
            if not predicate(curr):
                break
            else:
                parsed += curr
                self._go_forwards()

        assert len(parsed) > 0
        return parsed
