"""
String manipulations.
"""
import asyncio
import re


__all__ = [
    'capitalise', 'pascal_to_space', 'underscore_to_space', 'pluralise',
    'remove_single_lines', 'replace_recursive', 'ellipses', 'pluralize',
    'capitalize', 'parse_quotes'
]


def replace_recursive(text, to_match, repl=''):
    """
    Works the same as str.replace, but recurses until no matches can be found.
    Thus, ``replace_recursive('hello_wooorld', 'oo', '')`` would replace
    ``wooorld`` with ``woorld`` on the first pass, and ``woorld`` with
    ``world`` on the second.

    Note that ``str.replace`` only performs one pass, so
    ``'wooorld'.replace('oo', 'o')`` would return ``woorld``.

    :param text: the text to operate on.
    :param to_match: the text to match.
    :param repl: what to replace any matches with.
    :return: text, guaranteed to not contain ANY instances of ``to_match``.
    """
    while to_match in text:
        text = text.replace(to_match, repl)
    return text


def capitalise(string):
    """
    Capitalises the first character of a string and returns the string.
    """
    # We don't use a single index, as if the string is zero length, this
    # would raise an out of bounds exception. Instead, using ranges of indexes
    # will only output the maximum length string possible.
    return string[0:1].upper() + string[1:]


# Americans GTFO
capitalize = capitalise


def pascal_to_space(text):
    """
    Takes a string in PascalCaseFormatting and attempts to detect
    any word boundaries. Spaces are inserted in detected word boundaries
    and the modified string is returned.
    """
    # We only match if we have a lowercase letter followed by an uppercase one.
    # We do not account for internal spaces existing.
    result = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text, flags=re.U | re.M)
    return result.title()


def underscore_to_space(text):
    """
    Takes a string of underscore separated words and converts it into
    space separated words.
    """
    # Replace multiple underscores recursively until no more exist.
    # We could use regex, but that is going at it with a hammer.
    # str.replace(self, text, repl) only performs a single pass.

    return replace_recursive(text, '__', '_').replace('_', ' ').title()


def pluralise(cardinality, *args, method='app'):
    """
    Pluralises the given measurement.

    e.g.
          pluralise(12, 'echo', 'es') => '12 echoes'

          pluralise(1, 'echo', 'es') => '1 echo'

          pluralise(1, 'request', method='per append') => 'per request'

          pluralise(32, 'request', method='per append') => 'per 34 requests'

    Do not rely on this in a performance-critical situation. It is slow and
    inefficient; however, for most day-to-day occasional uses, this overhead
    is negligible.

    :param cardinality: numeric value.
    :param args: zero or more arguments, depending on the specified method.
    :param method: the method to pluralise by.

    Methods
    -------
    - **'app[end]'** (default)
        args[0]: singular name (e.g. pass)
        args[1]: plural: what to append on the end (e.g. 'es')

        If cardinality == 1, the singular is used.
        If cardinality != 1, the plural is appended to the singular.

        If args[1] is not specified, it defaults to 's'.

    - **'repl[ace]'**
        args[0]: singular name (e.g. goose)
        args[1]: plural name (e.g. geese)

        If cardinality == 1, the singular is used.
        If cardinality != 1, the plural is used.

    - **'per app[end]'**
        See 'append' for arguments and rules.

        Appends "per " to the start of the result.

        Additionally, if cardinality == 1, the cardinality is omitted from the
        output.

    - **'per repl[ace]'**
        See 'replace' for arguments and rules.

        Appends "per " to the start of the result.

        Additionally, if cardinality == 1, the cardinality is omitted from the
        output.

    - **'th'**
        Expects NO additional arguments.

        Expects cardinality to be an integer. Will not accept a float, or a
        negative integer.

        Assuming the `x` in the following is replaced with the cardinality...

        If cardinality == 0, 4, 5, 6, 10, 11, 12, 13, 14, 15, .. 20, 30, .. etc
            return 'xth'
        If cardinality == 1, 21, 31, .., 101, 121, .. etc
            return 'xst'
        If cardinality == 2, 22, 32, .. etc
            return 'xnd'
        If cardinality == 3, 23, 33, .. etc
            return 'xrd'
    """
    # Make life a bit easier.
    method = method.lower()

    def replace(s, p):
        return f'{cardinality} {s if cardinality == 1 else p}'

    def per_replace(s, p):
        if cardinality - 1:
            return f'per {cardinality} {p}'
        else:
            return f'per {s}'

    try:
        if method.startswith('app'):
            singular = args[0]
            plural = args[1] if len(args) > 1 else 's'
            replace = singular + plural
            return replace(cardinality, singular, replace)
        elif method.startswith('repl'):
            return replace(cardinality, *args)
        elif method.startswith('per app'):
            singular = args[0]
            plural = args[1] if len(args) > 1 else 's'
            replace = singular + plural
            return per_replace(singular, replace)
        elif method.startswith('per repl'):
            return per_replace(*args)
        elif method == 'th':
            if not isinstance(cardinality, int) or cardinality < 0:
                raise TypeError('This method only works with an integer '
                                'cardinality that is greater than or equal '
                                'to zero.')
            tens = cardinality % 100
            units = cardinality % 10
            if tens // 10 == 1 or units > 3 or units == 0:
                return f'{cardinality}th'
            elif units == 1:
                return f'{cardinality}st'
            elif units == 2:
                return f'{cardinality}nd'
            elif units == 3:
                return f'{cardinality}rd'
            else:
                assert False, f'Algorithm won\'t handle input {cardinality}'
        else:
            raise ValueError(f'Unexpected method {method} for args {args}')
    except IndexError:
        raise TypeError('Incorrect number of arguments...')


# Again, damn 'muricans.
pluralize = pluralise


def remove_single_lines(text):
    """
    Replaces single line breaks with spaces. Double line breaks
    are kept as they are. If the text param is None, it is substituted with
    an empty string.
    """
    # To make line sizes a bit easier to handle, we remove single line breaks
    # and replace them with a space, similar to what markdown does. To put a
    # single line break in explicitly, add "\r".
    if text is None:
        text = ''

    d = '\n\n'.join(line.replace('\n', ' ') for line in text.split('\n\n'))
    d = d.replace('\r\n', '\n')
    return d


def ellipses(text: str, max_length: int):
    """
    Takes text as input, and returns it as long as it is less than
    max_length. If it is over this, then ellipses are placed over the last
    three characters and the substring from the start to the boundary is
    returned.

    This makes arbitrarily long text blocks safe to place in messages and
    embeds.
    """
    if len(text) > max_length:
        ellipse = '...'
        return text[0:max_length - len(ellipse)] + ellipse
    else:
        return text


async def get_text_from_html(html):
    """Uses beautifulsoup4 to parse the given HTML asynchronously."""
    try:
        import bs4
    except ImportError:
        raise RuntimeError('Install the beautifulsoup4 package.') from None

    def executor_call():
        soup = bs4.BeautifulSoup(html, "html5lib")
        return soup.get_text()

    return await asyncio.get_event_loop().run_in_executor(
        None,
        executor_call
    )


def parse_quotes(string, quotes=None, delimit_on=None):
    """
    Delimits the given string using a quotation mark parser.
    :param quotes: the quotation marks to delemit on. Defaults to single 
            and double quotations.
    :param delimit_on: the characters to usually separate on. Defaults 
            to space characters
    """
    if not quotes:
        quotes = {'\'', '"'}
    elif isinstance(quotes, str):
        quotes = {quotes}

    if not delimit_on:
        delimit_on = {' '}
    elif isinstance(delimit_on, str):
        delimit_on = {delimit_on}

    # Holds parsed strings.
    stack = None
    strs = []
    current_str = []

    def empty_current():
        """
        Clears the current string if it is not empty, and places it in
        the results list.
        """
        if current_str:
            # Push the current string onto the strs list.
            strs.append(''.join(current_str))
            current_str.clear()

    while string:
        # Stores whether we have mutated the string already in this iteration.
        has_mutated = False
        for quote in quotes:
            if string.startswith(f'\\{quote}'):
                current_str.append(quote)
                string = string[1 + len(quote):]
                # Onto the next character.
                has_mutated = True

            # If the string starts with a quotation, and the stack is either
            # holding the same character (thus a closing quotation), or the
            # stack is empty (thus an opening quotation while not in existing
            #  quotations).
            elif string.startswith(quote) and (quote == stack or stack is None):
                if stack == quote:
                    stack = None
                    empty_current()
                else:
                    stack = quote

                # Onto the next character.
                string = string[len(quote):]
                has_mutated = True

        if has_mutated:
            continue
        elif stack is None:
            for delimiter in delimit_on:
                if string.startswith(delimiter):
                    empty_current()
                    has_mutated = True
                    string = string[len(delimiter):]
            if has_mutated:
                continue
        # Else, just shift the first character.
        current_str.append(string[0])
        string = string[1:]

    # Empty the string if it is not empty.
    empty_current()

    # If the stack is not empty, we have an issue.
    if stack is not None:
        raise ValueError(f'Expected closing {stack} character.')

    return strs
