"""
Converts whatever you enter into big letters, and replies it.
"""
import unicodedata

import neko

__all__ = ['LettersCog', 'setup']

REG_IND_A = ord('\N{REGIONAL INDICATOR SYMBOL LETTER A}')
COMB_ENCL_KEYCAP = '\N{COMBINING ENCLOSING KEYCAP}'


class LettersCog(neko.Cog):
    """
    Provides a command to say text in BIG LETTERS!
    """

    permissions = (neko.Permissions.MANAGE_MESSAGES |
                   neko.Permissions.SEND_MESSAGES |
                   neko.Permissions.READ_MESSAGES)

    @neko.command(
        name='big',
        usage='some text|\_some text',
        brief='Takes whatever you say and repeats it in BIG LETTERS!')
    async def say_big(self, ctx: neko.Context, *, string: str):
        """
        Add an underscore `_` at the start to also delete your message.
        """
        if string.startswith('_'):
            string = string[1:]
            await ctx.message.delete()
           
        # Fixes #1: space at newline start.
        result = ' '.join(map(self.get_big_letter, string))
        result = result.replace('\n ', '\n')

        await ctx.send(result)

    @staticmethod
    def get_big_letter(letter: str):
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

        await ctx.send('\n'.join(results))



setup = LettersCog.mksetup()
