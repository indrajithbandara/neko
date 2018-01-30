"""
Tells you if your username is one of the ones that has been leaked
online with other account details.
"""
import asyncio

import neko

import urllib.parse as url_parse

import bs4

import discord


@neko.inject_setup
class PwnedCog(neko.Cog):

    @neko.command(
        name='pwned',
        brief='Checks a massive online database to determine if you '
              'have had your account details leaked online. Results '
              'are sent via DMs to you for privacy.',
        usage='username')
    async def have_i_been_pwned(self, ctx, username):
        """This command will also work in DMs directly."""
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        data = []

        with ctx.typing():
            end_point = (
                f'https://haveibeenpwned.com/api/v2/breached'
                f'account/{url_parse.quote(username)}')
            try:
                res = await ctx.bot.request('GET', end_point)
                data = await res.json()
            except neko.HttpRequestError as ex:
                if ex.status == 404:
                    self.logger.debug('404 - user is safe from hackermen.')
                else:
                    raise neko.NekoCommandError(str(ex)) from None
            assert isinstance(data, list)

        pag = neko.Paginator(prefix='', suffix='')

        for i, result in enumerate(data):
            title = result['Title']
            domain = result['Domain']
            breach_date = result['BreachDate']
            date_added = result['AddedDate']
            data_classes = ', '.join(result['DataClasses'])
            # Removes HTML from the body.
            description = bs4.BeautifulSoup(result['Description']).text

            states = []
            for state in ('IsVerified', 'IsFabricated',
                          'IsActive', 'IsRetired', 'IsSpamList'):
                if result[state]:
                    states.append(neko.pascal_to_space(state[2:]))

            body = (
                f'**{title}**\n'
                f'__{domain}__\n'
                f'**Breached on**: {breach_date}\n'
                f'**Date added**: {date_added}\n'
                f'**Data affected**: {data_classes}\n'
                f'**Indicators**: '
                + ', '.join(states) + '\n\n' + description
            )

            for line in body.split('\n'):
                pag.add_line(line)
            pag.add_line()

        await ctx.send('Sending results to your inbox, ' + ctx.author.mention)

        await ctx.author.send(f'There are {neko.pluralise(len(data), "leak")} '
                              f'for the account `{username}`.')

        for page in pag.pages:
            await ctx.author.send(page)