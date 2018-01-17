"""
Converts whatever you enter into big letters, and replies it.
"""
import unicodedata

import discord
import re

import neko
import neko.other.perms as perms


__all__ = ['LettersCog']

REG_IND_A = ord('\N{REGIONAL INDICATOR SYMBOL LETTER A}')
COMB_ENCL_KEYCAP = '\N{COMBINING ENCLOSING KEYCAP}'


def _get_big_letter(letter: str):
    """
    Takes a single character and returns the corresponding "big" letter that
    discord recognises.
    """
    letter = letter.lower()
    assert len(letter) <= 1

    if ord('a') <= ord(letter) <= ord('z'):
        # 0x0001F1E6 is :regional_indicator_a:
        return chr(REG_IND_A + ord(letter) - ord('a'))
    elif ord('0') <= ord(letter) <= ord('9'):
        # The digits are parsed as the digit,
        # and then a combining enclosing keycap character.
        return letter + COMB_ENCL_KEYCAP
    else:
        print('Character', letter)
        return {
            '?': '\N{BLACK QUESTION MARK ORNAMENT}',
            '!': '\N{HEAVY EXCLAMATION MARK SYMBOL}',
            ' ': ' ',
            '\n': '\n',
            '+': '\N{heavy plus sign}',
            '-': '\N{heavy minus sign}',
            '÷': '\N{heavy division sign}',
            '×': '\N{cross mark}',
            '➕': '\N{heavy plus sign}',
            '➖': '\N{heavy minus sign}',
            '➗': '\N{heavy division sign}',
            '➡': '\N{black rightwards arrow}',
            '❌': '\N{cross mark}',
            '#': f'#{COMB_ENCL_KEYCAP}',
            '*': f'*{COMB_ENCL_KEYCAP}'
        }.get(letter, '')


def _get_small_letter(letter: str):
    """Gets a small letter!"""
    assert len(letter) == 1

    return {
        'a': 'ᵃ', 'b': 'ᵇ', 'c': 'ᶜ', 'd': 'ᵈ', 'e': 'ᵉ', 'f': 'ᶠ', 'g': 'ᵍ',
        'h': 'ʰ', 'i': 'ᶦ', 'j': 'ʲ', 'k': 'ᵏ', 'l': 'ᶫ', 'm': 'ᵐ', 'n': 'ⁿ',
        'o': 'ᵒ', 'p': 'ᵖ', 'q': 'ˤ', 'r': 'ʳ', 's': 'ˢ', 't': 'ᵗ', 'u': 'ᵘ',
        'v': 'ᵛ', 'w': 'ʷ', 'x': 'ˣ', 'y': 'ʸ', 'z': 'ᶻ', 'A': 'ᴬ', 'B': 'ᴮ',
        'C': 'ᶜ', 'D': 'ᴰ', 'E': 'ᴱ', 'F': 'ᶠ', 'G': 'ᴳ', 'H': 'ᴴ', 'I': 'ᴵ',
        'J': 'ᴶ', 'K': 'ᴷ', 'L': 'ᴸ', 'M': 'ᴹ', 'N': 'ᴺ', 'O': 'ᴼ', 'P': 'ᴾ',
        'Q': 'ᴽ', 'R': 'ᴿ', 'S': 'ˢ', 'T': 'ᵀ', 'U': 'ᵁ', 'V': 'ⱽ', 'W': 'ᵂ',
        'X': 'ˣ', 'Y': 'ʸ', 'Z': 'ᶻ', '0': '⁰', '1': '¹', '2': '²', '3': '³',
        '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹', ' ': ' ',
        '.': '·', ',': '’', '\n': '\n', '!': 'ᵎ'
    }.get(letter, '')


def _unicode_table(characters):
    """Creates a markdown formatted table of results for characters."""
    results = [
        '**Character information**',
        '__**`##  Ct    UTF-CODE DESCRIPTION`**__']

    for i, char in enumerate(characters):
        name = unicodedata.name(char)
        category = unicodedata.category(char)
        decimal = ord(char)
        hexadecimal = f'U+{hex(decimal)[2:]}'

        line = f'`{i+1:02}  {category}  {hexadecimal:>10} {name}`  {char} '
        results.append(line)

    return results


@neko.inject_setup
class LettersCog(neko.Cog):
    """
    Provides a command to say text in BIG LETTERS!

    We technically need the MANAGE_MESSAGES permission, but this is not
    required, as I perform checks to handle if this permission is not set.
    """

    permissions = (perms.Permissions.SEND_MESSAGES |
                   perms.Permissions.READ_MESSAGES)

    @neko.command(
        name='big',
        aliases=['bigd'],
        usage='some text',
        brief='Takes whatever you say and repeats it in BIG LETTERS!')
    async def say_big(self, ctx: neko.Context, *, string: str):
        """
        Call `big` to just show the output.

        Call `bigd` to show the output _and_ delete your original message.
        This requires that the bot has the `MANAGE_MESSAGES` permission.

        If a letter is not available, it is skipped.
        """
        if ctx.invoked_with == 'bigd':
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass
           
        # Fixes #1: space at newline start.
        result = ' '.join(map(_get_big_letter, string))
        result = result.replace('\n ', '\n')

        await ctx.send(result)

    @neko.command(
        name='whisper',
        aliases=['whisperd'],
        usage='some text',
        brief='Takes whatever you say and repeats it in small letters.'
    )
    async def whisper(self, ctx: neko.Context, *, string: str):
        """
        Call `whisper` to just show the output.

        Call `whisperd` to show the output _and_ delete the original message.
        This requires that the bot has the `MANAGE_MESSAGES` permission.

        If a letter is not available, it is skipped; likewise if you are
        missing characters from the font being used on your device, it will
        just output a `□` square.
        """
        if ctx.invoked_with == 'whisperd':
            try:
                await ctx.message.delete()
            except discord.Forbidden:
                pass

        await ctx.send(''.join(_get_small_letter(c) for c in string))

    @neko.command(
        name='say',
        brief='Take a _real_ big guess! Also, put a `d` at the end of the '
              'command name to delete your message first...',
        usage='Trump is a wotsit.',
        aliases=['sayd'])
    async def say_phrase(self, ctx, *, content: str):
        if ctx.invoked_with == 'sayd':
            await ctx.message.delete()
        await ctx.send(content)

    @neko.command(
        name='charinfo',
        brief='Inspects one or more characters and displays information.',
        usage='hello world|\N{THINKING FACE}')
    async def character_info(self, ctx, *, characters: str):
        """
        This will work for a maximum of 20 characters at a time, to prevent
        spamming the chat. Emojis work too. This is useful for working out
        how to display a given character in code.

        The columns represent:\r
        - `##` - The one-based index of the character\r
        - `Ct` - Character category\r
        - `UTF-CODE` - The UTF-8 sequence code (hexadecimal)\r
        - `DESCRIPTION` - The character name and a preview.
        """
        characters = characters[:20]
        results = _unicode_table(characters)

        await ctx.send('\n'.join(results))

    @neko.command(
        name='charlookup',
        brief='Looks for the Unicode character with the given name.',
        usage='ANGRY FACE'
    )
    async def lookup(self, ctx, *, string: str):
        """
        This is the opposite of `charinfo`. It will look up a given string as
        a unicode character name and if it finds a character matching the
        input, it will show unicode information about it.
        """
        try:
            character = unicodedata.lookup(string.upper())
            await ctx.send('\n'.join(_unicode_table(character)))

        except KeyError:
            await ctx.send('No result.')

    @neko.command(
        name='charcode',
        brief='Takes a unicode hexadecimal value, and looks up the character '
              'for that code.',
        usage='U+1f620|0x1f620|u1f260|1f260'
    )
    async def from_char_code(self, ctx, *, codes: str):
        """
        You can specify up to 20 codes at once, separated by spaces.
        """
        codes = codes.lower().split(' ')[:20]

        codes = [re.sub(r'^(u[+]|0x|u)', '', c) for c in codes]
        chars = [chr(int(c, 16)) for c in codes]

        await ctx.send('\n'.join(_unicode_table(chars)))

