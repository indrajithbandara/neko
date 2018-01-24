"""
Color displaying utilities.
"""
import io
import struct

import PIL.Image as pil_image
import discord

import neko


# RGBA is big endian
_pixel_packer = struct.Struct('>4B')

_pheight = 25
_pwidth = 25


def _generate_preview(bytes_io: io.BytesIO,
                      red: int,
                      green: int,
                      blue: int,
                      alpha: int):
    """Generates a 25x25 pixel colour preview as a PNG."""
    if not all(0 <= rgba <= 255 for rgba in (red, green, blue, alpha)):
        raise ValueError(
            f'Invalid colour channel in ({red},{green},{blue},{alpha}).')

    img = pil_image.new(
        'RGBA',
        color=(red, green, blue, alpha),
        size=(_pwidth, _pheight))

    bytes_io.seek(0)
    img.save(bytes_io, 'PNG')
    bytes_io.seek(0)


def _to_hex(r: int, g: int, b: int, _a: int=None, *, prefix='#'):
    """
    Takes RGBA colour values from 0 to 255, and generates a hex
    representation. Note the alpha channel is ignored, and is optional.
    :param r: red channel
    :param g: green channel
    :param b: blue channel
    :param prefix: what to prefix to the start. Defaults to '#'
    :return: the string generated.
    """
    return prefix + ''.join(hex(x)[2:] for x in (r, g, b))


def _from_hex(string: str) -> (int, int, int):
    """
    Takes a three or six digit hexadecimal RGB value and returns the value as
    a tuple of red, green and blue byte-sized ints. Each can range between 0
    and 255 inclusive.

    If a 0x or a # is on the start of the string, we ignore it, so you do not
    need to sanitise input for those.

    :param string: the input
    :return: tuple of red, green and blue.
    """


async def colour_response(ctx, r, g, b, a=255):
    """
    Takes a context, as well as RGB and optionally A in the range 0 ≤ x < 256,
    generates a colour, and then sends the result to the caller of the context.

    If A is omitted, it is set to 255, the max value.
    """
    with ctx.typing(), io.BytesIO() as img:
        await ctx.bot.do_job_in_pool(
            _generate_preview,
            img, r, g, b, a)

        file = discord.File(img, 'preview.png')

        # Todo: fill with colour codes or some shit.
        embed = neko.Page(
            title=f'Red: {r}\tGreen: {g}\tBlue: {b}\tAlpha: {a}',
            color=discord.Color.from_rgb(r, g, b))

        if a < 255:
            # Disclaimer.
            embed.set_footer(
                text='Embed colour does not take into account alpha.')

        await ctx.send(
            file=file,
            embed=embed)


@neko.inject_setup
class ColourfulCog(neko.Cog):

    @neko.group(
        name='color',
        aliases=['colour'],
        invoke_without_command=True,
        brief='Displays a given hex colour.')
    async def color_group(self, ctx, hex_colour=None):
        """
        Displays a preview of a given hex colour. If no colour is specified,
        then a random 24-bit colour is generated.
        """

    @color_group.command(
        brief='Generates a preview for the given red, green, blue and '
              'optionally alpha values',
        usage='54 23 186|54 23 186 26',
        aliases=['rgba'])
    async def rgb(self, ctx, r, g, b, a='255'):
        """
        If alpha is omitted, then it gets the value of 255 by default.

        All values must be in the range 0 ≤ x < 256.
        """
        try:
            r, g, b, a = int(r), int(g), int(b), int(a)
            for x in (r, g, b, a):
                if not 0 <= x < 256:
                    raise TypeError('Must be in range [0, 256)')
        except ValueError as ex:
            raise neko.NekoCommandError(f'Please give me valid input! {ex}')
        else:
            await colour_response(ctx, r, g, b, a)
