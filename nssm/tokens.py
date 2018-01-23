"""
Implementations of various tokens.
"""
import abc
import collections
import enum
import math
import typing

__all__ = (
    'TokenType', 'Token', 'UndefinedToken', 'IntToken', 'RealToken',
    'StringToken', 'IdentifierToken', 'OperatorToken',
    'ReserveWordToken', 'MiscToken', 'eos', 'eof', 'int_divide_ass',
    'pow_ass', 'bsl_ass', 'inc', 'dec', 'plus_ass', 'times_ass',
    'divide_ass', 'modulo_ass', 'not_equal', 'power', 'int_divide',
    'bsr', 'bsl', 'equal', 'lte', 'gte', 'band_ass', 'bxor_ass',
    'bor_ass', 'lor', 'land', 'question', 'colon', 'plus', 'minus',
    'modulo', 'bang', 'tilde', 'times', 'divide', 'lt', 'gt', 'ass',
    'band', 'bor', 'bxor', 'comma', 'lparen', 'rparen', 'lsquare',
    'rsquare', 'lbrace', 'rbrace', 'for_rw', 'while_rw', 'if_rw',
    'elif_rw', 'else_rw', 'continue_rw', 'break_rw', 'in_rw',
    'return_rw', 'true_rw', 'false_rw', 'nan_rw', 'null_rw', 'inf_rw'
)


class TokenType(enum.IntFlag):
    """
    Types of token.

    Since we define some tokens as being one or more of another type, it
    begins to make sense to allow a flag system for combining. For example,
    to save code, if we want any value type, we can define ``val_token``
    as being a decimal, real, binary, hex, string, null or identifier token,
    and then just perform a check to see whether it matches ``val_token`` at
    runtime.
    """
    # Makes this function accessible when we define members.

    # Default value, in case of errors. This is the only falsey-token.
    undefined = 0

    # "Compile"-time fixed types
    int = 0x1  # Integer, either base 2, 8, 10 or 16.
    ieee_fpi = 0x2  # Float, base 10.
    string = 0x4  # String of characters.
    null = 0x8  # Null value.
    fixed_value = int | ieee_fpi | string | null
    identifier = 0x10  # Identifier for a variable or builtin
    value = fixed_value | identifier
    # Operators
    operator = 0x20
    reserve_word = 0x40
    # Built in type
    builtin = operator | reserve_word | fixed_value
    # Other token
    other = 0x80


T = typing.TypeVar('T')


class Token(abc.ABC):
    """Abstract type of token."""
    __slots__ = ('_name', '_value', '_token_type')

    def __init__(self, name: str, value: T, token_type: TokenType):
        # Prevent me doing anything to mutate these by accident later.
        # as we expect to rebuild them as nodes in an AST rather than
        # reuse the token type.
        self._name = name
        self._value = value
        self._token_type = token_type

    def __hash__(self):
        """Gets the hash code for the value."""
        return hash(self.value)

    @property
    def name(self) -> str:
        """Token name."""
        return self._name

    @property
    def value(self) -> T:
        """Token raw value."""
        return self._value

    @property
    def token_type(self) -> TokenType:
        """Token type flag."""
        return self._token_type

    def __str__(self):
        return f'{self.name} token with value `{self.value}`'

    def __repr__(self):
        return (f'<{type(self).__name__} '
                f'name={self.name!r} '
                f'value={self.value!r} '
                f'type={self.token_type!r}>)')

    def __eq__(self, other):
        """Equality is determined by matching name and value."""
        if not isinstance(other, Token):
            return False
        else:
            return all(
                getattr(other, a) == getattr(self, a)
                for a in ('name', 'value'))

    def is_type(self, token_type: TokenType):
        return bool(self.token_type & token_type)


class UndefinedToken(Token):
    """Undefined token that is not understood."""

    def __init__(self, value: typing.Any):
        super().__init__('Undefined', value, TokenType.undefined)


class IntToken(Token):
    """Decimal token."""

    def __init__(self, value: int):
        super().__init__('Integer', value, TokenType.int)


class RealToken(Token):
    """Real token."""

    def __init__(self, value: float):
        super().__init__('Real Number', value, TokenType.ieee_fpi)


class StringToken(Token):
    """String token."""

    def __init__(self, value: str):
        super().__init__('String', value, TokenType.string)


class IdentifierToken(Token):
    """Some identifier for a function, variable, builtin, or other object."""

    def __init__(self, identifier_name: str):
        super().__init__('Identifier', identifier_name, TokenType.identifier)


class OperatorToken(Token):
    """An operator."""

    # Maps operator literals to their respective operator
    # objects.
    operators = collections.OrderedDict()

    def __init__(self, name: str, symbol: str):
        super().__init__(name, symbol, TokenType.operator)
        type(self).operators[symbol] = self


class ReserveWordToken(Token):
    """A reserve word."""

    # Maps operator literals to their respective operator
    # objects.
    reserve_words = collections.OrderedDict()

    def __init__(self, identifier: str, **kwargs):
        """
        Defines a reserve word.
        :param identifier: the identifier.
        :param kwargs: see below.

        Kwargs that are used are:
        - ``value`` - specifies a custom value to associate with the
            reserve word.
        - ``additional_types`` - bitfield of any additional types to associate
            the reserve word with.
        """
        value = kwargs.get('value', identifier)
        _types = TokenType.reserve_word | kwargs.get('additional_types', 0)
        super().__init__(identifier, value, _types)
        type(self).reserve_words[identifier] = self


class MiscToken(Token):
    """Another type of token that does not match the existing criteria."""

    # Maps misc tokens to their respective operator
    # objects.
    tokens = collections.OrderedDict()

    def __init__(self, name: str, value: typing.Optional[str]):
        super().__init__(name, value, TokenType.other)
        type(self).tokens[name] = self


"""
Holds fixed-value tokens we allow, such as operators, and represents them
as string values.

This uses a little side effect of the current enum implementation which is
that the members are stored in an attribute called _member_map_ which
is implemented using an ordered dict. This means that the members are
stored in the order in which we inserted them in, and thus can be safely
iterated across by the lexer to determine operators.

TL;DR:

The implementation of enum means that if we specify the `**` token before
the `*` token, then when iterating across the members, `**` will be
yielded by the iterator before `*` will, so we can significantly reduce
the amount of code needed to implement the lexer's determination logic by
simply reverse-searching the member map in this enum using something akin
to the str.startswith() builtin method!

As a consequence, tokens must be declared in here in the order in which they
are resolved, e.g. in decreasing order by number of characters in the token
literal, otherwise if `*` is placed before `**`, then `**` will always
be interpreted as `*`, since `**` starts with `*`.
"""

int_divide_ass = OperatorToken(
    'Integer divide/assign',
    '//=')

pow_ass = OperatorToken(
    'Power assign',
    '**=')

bsr_ass = OperatorToken(
    'Right bit-shift/assign',
    '>>=')

bsl_ass = OperatorToken(
    'Left bit-shift/assign',
    '<<=')

inc = OperatorToken(
    'Increment',
    '++')

dec = OperatorToken(
    'Decrement',
    '--')

plus_ass = OperatorToken(
    'Plus/assign',
    '+=')

minus_ass = OperatorToken(
    'Minus/assign',
    '-=')

times_ass = OperatorToken(
    'Times/assign',
    '*=')

divide_ass = OperatorToken(
    'Divide/assign',
    '/=')

modulo_ass = OperatorToken(
    'Modulo/assign',
    '%=')

not_equal = OperatorToken(
    'Not equal to',
    '!=')

power = OperatorToken(
    'Power',
    '**')

int_divide = OperatorToken(
    'Integer divide',
    '//')

bsr = OperatorToken(
    'Right bit-shift',
    '>>')

bsl = OperatorToken(
    'Left bit-shift',
    '<<')

equal = OperatorToken(
    'Equal to',
    '==')

lte = OperatorToken(
    'Less than or equal to',
    '<=')

gte = OperatorToken(
    'Greater than or equal to',
    '>=')

band_ass = OperatorToken(
    'Bitwise-and/assign',
    '&=')

bxor_ass = OperatorToken(
    'Bitwise-xor/assign',
    '^=')

bor_ass = OperatorToken(
    'Bitwise-or/assign',
    '|=')

lor = OperatorToken(
    'Logical-or',
    '||')

land = OperatorToken(
    'Logical-and',
    '&&')

question = OperatorToken(
    'Question mark',
    '?')

colon = OperatorToken(
    'Colon',
    ':')

plus = OperatorToken(
    'Plus',
    '+')

minus = OperatorToken(
    'Minus',
    '-')

modulo = OperatorToken(
    'Modulo',
    '%')

bang = OperatorToken(
    'Bang',
    '!')

tilde = OperatorToken(
    'Tilde',
    '~')

times = OperatorToken(
    'Times',
    '*')

divide = OperatorToken(
    'Divide',
    '/')

lt = OperatorToken(
    'Less than',
    '<')

gt = OperatorToken(
    'Greater than',
    '>')

ass = OperatorToken(
    'Assignment',
    '=')

band = OperatorToken(
    'Bitwise-and',
    '&')

bor = OperatorToken(
    'Bitwise-or',
    '|')

bxor = OperatorToken(
    'Bitwise-xor',
    '^')

comma = OperatorToken(
    'Comma',
    ',')

lparen = OperatorToken(
    'Left parenthesis',
    '(')

rparen = OperatorToken(
    'Right parenthesis',
    ')')

lsquare = OperatorToken(
    'Left square-bracket',
    '[')

rsquare = OperatorToken(
    'Right square-bracket',
    ']')

lbrace = OperatorToken(
    'Left brace',
    '{')

rbrace = OperatorToken(
    'Right brace',
    '}')


true_rw = ReserveWordToken('true', value=1, additional_types=TokenType.int)
false_rw = ReserveWordToken('false', value=0, additional_types=TokenType.int)
null_rw = ReserveWordToken('null', value=None, additional_types=TokenType.null)
nan_rw = ReserveWordToken('NaN', value=math.nan,
                          additional_types=TokenType.ieee_fpi)
inf_rw = ReserveWordToken('INF', value=math.inf,
                          additional_types=TokenType.ieee_fpi)

eos = MiscToken('End of statement', ';')
eof = MiscToken('End of file', '\0')

for_rw = ReserveWordToken('for')
while_rw = ReserveWordToken('while')
if_rw = ReserveWordToken('if')
elif_rw = ReserveWordToken('elif')
else_rw = ReserveWordToken('else')
continue_rw = ReserveWordToken('continue')
break_rw = ReserveWordToken('break')
in_rw = ReserveWordToken('in')
return_rw = ReserveWordToken('return')
