"""
Implementations of various tokens.
"""
import enum
import typing


__flag = 1


def _flag():
    global __flag
    val = __flag
    __flag <<= 1
    return val


class Type(enum.IntFlag):
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
    int = _flag()  # Integer, either base 2, 8, 10 or 16.
    real = _flag()  # Float, base 10.
    string = _flag()  # String of characters.
    null = _flag()  # Null value.
    fixed_value = (int | real | string | null)
    identifier = _flag()  # Identifier for a variable or builtin
    value = fixed_value | identifier
    # Operators
    operator = _flag()
    # Other token
    other = _flag()


T = typing.TypeVar('T')


class Token:
    def __init__(self, name: str, value: T, token_type: Type):
        # Prevent me doing anything to mutate these by accident later.
        # as we expect to rebuild them as nodes in an AST rather than
        # reuse the token type.
        self.__name = name
        self.__value = value
        self.__token_type = token_type

    @property
    def name(self) -> str:
        return self.__name

    @property
    def value(self) -> T:
        return self.__value

    @property
    def token_type(self) -> Type:
        return self.__token_type

    def __str__(self):
        return f'{self.name} token'

    def __repr__(self):
        return (f'<Token name={self.name!r} value={self.value!r} '
                f'type={self.token_type!r}>)')


class UndefinedToken(Token):
    """Undefined token that is not understood."""
    def __init__(self, value: typing.Any):
        super().__init__('Undefined', value, Type.undefined)


class DecimalToken(Token):
    """Decimal token."""
    def __init__(self, value: int):
        super().__init__('Integer', value, Type.decimal_int)


class RealToken(Token):
    """Real token."""
    def __init__(self, value: float):
        super().__init__('Real number', value, Type.real)


class StringToken(Token):
    """String token."""
    def __init__(self, value: str):
        super().__init__('String', value, Type.string)


class IdentifierToken(Token):
    """Some identifier for a function, variable, builtin, or other object."""
    def __init__(self, identifier_name: str):
        super().__init__('Identifier', identifier_name, Type.identifier)


class OperatorToken(Token):
    """An operator."""
    def __init__(self, name: str, symbol: str):
        super().__init__(name, symbol, Type.operator)


class MiscToken(Token):
    """Another type of token that does not match the existing criteria."""
    def __init__(self, name: str, value: str):
        super().__init__(name, value, Type.other)


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


# Operators
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

question = MiscToken(
    'Question mark',
    '?')

colon = MiscToken(
    'Colon',
    ':')

lparen = MiscToken(
    'Left parenthesis',
    '(')

rparen = MiscToken(
    'Right parenthesis',
    ')')

lsquare = MiscToken(
    'Left square-bracket',
    '[')

rsquare = MiscToken(
    'Right square-bracket',
    ']')

lbrace = MiscToken(
    'Left brace',
    '{')

rbrace = MiscToken(
    'Right brace',
    '}')

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

comma = MiscToken(
    'Comma',
    ',')

semi = MiscToken(
    'Semicolon',
    ';')


operators = (
    int_divide_ass, pow_ass, bsr_ass, bsl_ass, inc, dec, plus_ass, minus_ass,
    times_ass, divide_ass, modulo_ass, not_equal, power, int_divide, bsr,
    bsl, equal, lte, gte, band_ass, bxor_ass, lor, land
)

other_tokens = (
    lparen, rparen, lsquare, rsquare, lbrace, rbrace, semi, colon, question
)
