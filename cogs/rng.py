"""
Various random number generation bits and pieces.
"""
import random

import neko


class RngCog(neko.Cog):
    @neko.command(
        name='coinflip',
        aliases=['toss', 'flip'],
        brief='Flips a coin, or picks from a set of given values...',
        usage='|option1 option2|csgo portal "team fortress 2"')
    async def toss(self, ctx, *, args=None):
        """
        Simulates a coin flip. You can specify optional replacements
        for heads and tails.
        """
        if args is None:
            args = ['Heads', 'Tails']
        else:
            args = neko.parse_quotes(args)

        if len(args) <= 1:
            await ctx.send('Come on. Like I can decide on something from that input..!')
        elif len(set(args)) != len(args):
            await ctx.send('Seriously? You put the same thing more than once!')
        else:
            await ctx.send(random.choice(args))

    @neko.command(
        name='rtd',
        aliases=['dice', 'roll'],
        brief='Rolls a dice.',
        usage='|-sides 14|-n 3|-sides 12 -n 2'
    )
    async def rtd(self, ctx, *args):
        """
        Optional flags:\r
        -sides x: assumes a dice has `x` sides.\r
        -n y: rolls said dice `y` times.
        """
        sides = 6
        n = 1
        args = list(args)

        while len(args) > 0:
            flag = args.pop(0)
            try:
                if flag == '-sides' or flag == '-n':
                    option = args.pop(0)

                    if flag == '-n':
                        n = int(option)
                    else:
                        sides = int(option)
                else:
                    raise neko.NekoCommandError(f'Unrecognised option {flag}')
            except ValueError:
                err = f'{option} must be an integer greater than 0.'
                raise neko.NekoCommandError(err) from None
            except IndexError:
                raise neko.NekoCommandError(
                    f'Missing value for {flag}') from None

        results = []
        for i in range(0, n):
            results.append(str(random.randint(1, sides)))

        await ctx.send(', '.join(results))


setup = RngCog.mksetup()
