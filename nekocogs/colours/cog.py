"""
Color displaying utilities.
"""
import io

import discord
import neko

from . import utils


def make_colour_embed(r, g, b, a=255):
    """
    Generates an embed to describe the given RGB(A) colour, then returns it.
    """
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

    hsv_h, hsv_s, hsv_v = utils.to_hsv(r, g, b)
    hsv_h = f'{hsv_h:.0f}\N{DEGREE SIGN}'
    hsv_s = f'{hsv_s:.0f}%'
    hsv_v = f'{hsv_v:.0f}%'

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
              f'HSL\t\t({hsl_h}, {hsl_s}, {hsl_l})\n'
              f'HSV\t\t({hsv_h}, {hsv_s}, {hsv_v})')

    footer = (
        f'This is{" " if utils.is_web_safe(r,g,b,a) else " not "}web-safe.')

    if a < 255:
        # Disclaimer.
        footer += ' Embed colour does not take into account alpha. '

    footer = ('Values may not directly match the input, as they are '
              'limited by the gamut of 32-bit RGBA colour-space.')

    embed.set_footer(text=footer)

    return embed


async def single_colour_response(ctx, r, g, b, a=255):
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

        embed = make_colour_embed(r, g, b, a)

        # Get hex colour string
        hex_str = utils.to_hex(r, g, b, a, prefix='')

        embed.url = f'http://www.color-hex.com/color/{hex_str}'

        await ctx.send(
            file=file,
            embed=embed)


class ColourfulCog(neko.Cog):
    @neko.group(
        name='colour',
        aliases=['color'],
        invoke_without_command=True,
        brief='Attempts to display the given colour as input.')
    async def color_group(self, ctx, *args):
        """
        This attempts to work out the colour you are describing in the system
        you are supplying it in. It will then attempt to output a preview of
        said colour.

        Note that you can specify the colour-space manually by giving the
        name of it as the first argument, for example, `colour name dodger blue`
        or `colour hsl 50 50 25`.

        Currently, due to limitations, you must specify CMYK, HSL and HSV
        values explicitly for them to be recognised correctly.

        You can also only pass in one colour at once to this command. See the
        `palette` sub-command for a potential solution.
        """
        if all(arg.isalpha() for arg in args):
            await self.by_name.callback(self, ctx, colour_name=' '.join(args))

        elif len(args) in (3, 4):
            joint = ''.join(args)
            if any(x in joint for x in '.%'):
                await self.rgba_float.callback(self, ctx, *args)
            else:
                await self.rgba_byte.callback(self, ctx, *args)
        else:
            await self.hex_colour.callback(self, ctx, args[0])

    @color_group.command(
        name='hex',
        brief='Displays a given hex colour.',
        usage='#FF057B|0xFF057B|ff057b')
    async def hex_colour(self, ctx, hex_colour):
        """
        Displays a preview of a given hex colour. If no colour is specified,
        then a random 24-bit colour is generated.
        """
        # This validates additionally.
        try:
            r, g, b = utils.from_hex(hex_colour)
            await single_colour_response(ctx, r, g, b)
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
            await single_colour_response(ctx, *colour)
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
            r, g, b, a = (utils.ensure_int_in_0_255(x) for x in (r, g, b, a))
            for x in (r, g, b, a):
                if not 0 <= x < 256:
                    raise TypeError('Must be in range [0, 256)')
            await single_colour_response(ctx, r, g, b, a)
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

            await single_colour_response(ctx, r, g, b, a)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))

    @color_group.command(
        name='cmyk',
        brief='Generates a preview for the given CMYK colour channels. Each '
              'value must be in the range [0, 1].',
        usage='0.5 0.25 0 0.7')
    async def cmyk_float(self, ctx, c, m, y, k):
        """
        Displays info on a colour given in the CMYK (cyan-magenta-yellow-key)
        colour space.

        "Key" may also be defined as "black".
        """
        try:
            r, g, b = utils.from_cmyk(c, m, y, k)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))
        else:
            await single_colour_response(ctx, r, g, b)

    @color_group.command(
        brief='Generates a preview for the given HSL colour channels. Hue '
              'must be an angle between 0 and 360°; Saturation and Lightness '
              'should be percentages.',
        usage='35 48 65|35° 48% 65%')
    async def hsl(self, ctx, h, s, l):
        """
        Displays info on a colour in the HSL (hue-saturation-lightness)
        scale.
        """
        try:
            r, g, b = utils.from_hsl(h, s, l)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))
        else:
            await single_colour_response(ctx, r, g, b)

    @color_group.command(
        brief='Generates a preview for the given HSV colour channels. Hue '
              'must be an angle between 0 and 360°; Saturation and Value '
              'should be percentages.',
        usage='35 48 65|35° 48% 65%',
        aliases=['hsb'])
    async def hsv(self, ctx, h, s, v):
        """
        Displays info on a colour in the HSV (hue-saturation-value) scale.
        """
        try:
            r, g, b = utils.from_hsv(h, s, v)
        except (ValueError, TypeError) as ex:
            raise neko.NekoCommandError(str(ex))
        else:
            await single_colour_response(ctx, r, g, b)

    @neko.cooldown(3, 180, neko.CooldownType.channel)
    @color_group.command(
        brief='Displays several hex-formatted RGB colours in a palette.',
        usage=' #9DD0A5 #D0BD9D #D0AB9D #9DCCD0 #C19DD0|"dodger blue" 0xff0ff0')
    async def palette(self, ctx, *, colours):
        """
        This is experimental, and slow. Thus, there is a cooldown restriction
        on this command to prevent slowing the bot down for everyone else.

        This only supports RGB-hex strings currently, as well as RGB-bytes,
        and HTML colour names. Anything that contains spaces must be surrounded
        by quotes.
        """
        try:
            with ctx.typing(), io.BytesIO() as fp:
                # Parse args
                colours = neko.parse_quotes(colours)

                await ctx.bot.do_job_in_pool(
                    utils.make_palette,
                    fp,
                    *colours)

                file = discord.File(fp, 'palette.png')

                await ctx.send(file=file)
        except (ValueError, TypeError, KeyError) as ex:
            string = f'No match: {ex}'
            raise neko.NekoCommandError(string)

    @color_group.command(brief='Generates a totally random RGB colour.')
    async def random(self, ctx):
        hex_str = hex(neko.random_color())
        r, g, b = utils.from_hex(hex_str)
        await single_colour_response(ctx, r, g, b)
