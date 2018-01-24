"""
Color displaying utilities.
"""
import io

import discord
import neko

from . import utils


async def colour_response(ctx, r, g, b, a=255):
    """
    Takes a context, as well as RGB and optionally A in the range 0 ≤ x < 256,
    generates a colour, and then sends the result to the caller of the context.

    If A is omitted, it is set to 255, the max value.
    """
    with ctx.typing(), io.BytesIO() as img:
        await ctx.bot.do_job_in_pool(
            utils.generate_preview,
            img, r, g, b, a)

        file = discord.File(img, 'preview.png')

        # % alpha
        pct_a = round(100. * a / 255., 2)

        embed = neko.Page(
            color=discord.Color.from_rgb(r, g, b))

        hex_str = utils.to_hex(r, g, b, a).upper()
        short_hex = utils.to_short_hex(r, g, b, a)

        if short_hex:
            short_hex = short_hex.upper()

        rf, gf, bf, af = utils.to_float(r, g, b, a)

        hsl_h, hsl_s, hsl_l = utils.to_hsl(r, g, b)
        hsl_h = f'{hsl_h:.0f}\N{DEGREE SIGN}'
        hsl_s = f'{hsl_s:.0f}%'
        hsl_l = f'{hsl_l:.0f}%'

        cmyk_c, cmyk_m, cmyk_y, cmyk_k = utils.to_cmyk(r, g, b)
        cmyk_c = round(cmyk_c, 2)
        cmyk_m = round(cmyk_m, 2)
        cmyk_y = round(cmyk_y, 2)
        cmyk_k = round(cmyk_k, 2)

        title = utils.HtmlNames.from_value((r, g, b))
        if title:
            # Title case!
            title = title.title()

            if not short_hex:
                title += f' ({hex_str})'
            else:
                title += f' ({hex_str}, {short_hex})'
        else:
            title = hex_str

        embed.title = title

        if a < 255:
            embed.description = f'{pct_a:.0f}% opacity'

        embed.add_field(
            name='RGB and RGBA',
            value=f'RGBb\t{r, g, b}\nRGBAb {r, g, b, a}\n'
                  f'RGBf \t{rf, gf, bf}\nRGBAf  {rf, gf, bf, af}')

        embed.add_field(
            name='Other systems',
            value=f'CMYK   ({cmyk_c}, {cmyk_m}, {cmyk_y}, {cmyk_k})\n'
                  f'HSL\t\t({hsl_h}, {hsl_s}, {hsl_l})')

        footer = (
            f'This is{" " if utils.is_web_safe(r,g,b,a) else " not "}web-safe.')

        if a < 255:
            # Disclaimer.
            footer += ' Embed colour does not take into account alpha.'

        embed.set_footer(text=footer)

        await ctx.send(
            file=file,
            embed=embed)


class ColourfulCog(neko.Cog):
    @neko.group(
        name='colour',
        aliases=['color'],
        invoke_without_command=True,
        brief='Displays a given hex colour.')
    async def color_group(self, ctx, hex_colour=None):
        """
        Displays a preview of a given hex colour. If no colour is specified,
        then a random 24-bit colour is generated.
        """
        # This validates additionally.
        try:
            r, g, b = utils.from_hex(hex_colour)
            await colour_response(ctx, r, g, b)
        except ValueError as ex:
            raise neko.NekoCommandError(str(ex))

    @color_group.command(
        name='name',
        brief='Looks up the given colour name and outputs the result, if it '
              'exists.',
        usage='dodger blue|mocha')
    async def by_name(self, ctx, *, colour_name):
        """
        This currently only holds colours in the HTML specification.

        Find me a list of others and their corresponding hexadecimal values,
        and I will add them to the list.
        """
        try:
            colour = utils.HtmlNames[colour_name]
            await colour_response(ctx, *colour)
        except KeyError:
            raise neko.NekoCommandError('That colour was not found.') from None

    @color_group.command(
        name='byte',
        brief='Generates a preview for the given red, green, blue and '
              'optionally alpha values',
        usage='54 23 186|54 23 186 26')
    async def rgba_byte(self, ctx, r, g, b, a='255'):
        """
        If alpha is omitted, then it gets the value of 255 by default.

        All values must be in the range 0 ≤ x < 256.
        """
        try:
            r, g, b, a = int(r), int(g), int(b), int(a)
            for x in (r, g, b, a):
                if not 0 <= x < 256:
                    raise TypeError('Must be in range [0, 256)')
            await colour_response(ctx, r, g, b, a)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(ex)

    @color_group.command(
        name='float',
        brief='Generates a preview for the given red, green, blue and '
              'optionally alpha channels, interpreting each in range [0,1].',
        usage='0.5 0.25 0.33|0.5 0.25 0.33 0.1')
    async def rgba_float(self, ctx, r, g, b, a=None):
        """
        If alpha is not specified, then it will default to 1.0.

        I will automatically convert percentages to floating point
        values if you give those instead.
        """
        try:
            if r.endswith('%'):
                r = utils.ensure_percentage(r)

            if g.endswith('%'):
                g = utils.ensure_percentage(g)

            if b.endswith('%'):
                b = utils.ensure_percentage(b)

            if a is None:
                a = 1.0
            elif a.endswith('%'):
                a = utils.ensure_percentage(a)

            r, g, b, a = utils.from_float(r, g, b, a)

            await colour_response(ctx, r, g, b, a)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))

    @color_group.command(
        name='cmyk',
        brief='Generates a preview for the given CMYK colour channels. Each '
              'value must be in the range [0, 1].',
        usage='0.5 0.25 0 0.7')
    async def cmyk_float(self, ctx, c, m, y, k):
        """
        Displays info on a colour given in the CMYK (Cyan-Magenta-Yellow-Key)
        colour space.

        "Key" may also be defined as "black".
        """
        try:
            r, g, b = utils.from_cmyk(c, m, y, k)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))
        else:
            await colour_response(ctx, r, g, b)

    @color_group.command(
        brief='Generates a preview for the given HSL colour channels. Hue '
              'must be an angle between 0 and 360°; Saturation and Lightness '
              'should be percentages.',
        usage='35 48 65|35° 48% 65%')
    async def hsl(self, ctx, h, s, l):
        """
        Displays info on a colour in the HSL (hue, saturation, lightness
        scale.
        """
        try:
            r, g, b = utils.from_hsl(h, s, l)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))
        else:
            await colour_response(ctx, r, g, b)
