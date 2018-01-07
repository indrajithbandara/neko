"""
Urban dictionary wrapper. This will only work in channels that have either
the NSFW flag, or "filthy" in the channel name.
"""
import urllib.parse
import neko


__all__ = ['UrbanDictionaryCog']

# These are pairs of the API and user website endpoints.
random_def = ('http://api.urbandictionary.com/v0/random',
              'https://urbandictionary.com/random.php')
define_def = ('http://api.urbandictionary.com/v0/define',
              'https://urbandictionary.com/define.php')

icon_url = 'https://d2gatte9o95jao.cloudfront.net/assets/apple-touch-icon' \
           '-55f1ee4ebfd5444ef5f8d5ba836a2d41.png '

thumb_url = 'https://vignette.wikia.nocookie.net/logopedia/images/a/a7' \
            '/UDAppIcon.jpg/revision/latest?cb=20170422211150 '


def _big(integer: int):
    ckk = '\N{COMBINING ENCLOSING KEYCAP} '
    return ''.join(f'{c}{ckk}' for c in str(integer))


class UrbanDictionaryCog(neko.Cog):
    """
    Cog for urban dictionary implementation.
    """
    permissions = (neko.Permissions.SEND_MESSAGES |
                   neko.Permissions.ADD_REACTIONS |
                   neko.Permissions.READ_MESSAGES |
                   neko.Permissions.MANAGE_MESSAGES)

    def __local_check(self, ctx):
        """
        We don't want this to be run in the normal chat, but a server I am on
        has a channel for stuff containing foul language that is not necessarily
        designed for NSFW content (under 18's still get access).

        The (mostly crap) solution is to allow any NSFW channels access to the
        command, and also the designated channel. I identify this using the
        name and ID of the channel for now.

        :param ctx: context of the command invocation.
        """
        fc = (ctx.channel.name == 'filthy_channel'
              and ctx.channel.id == 318007837336797185)
        nsfw = ctx.channel.nsfw

        return fc or nsfw

    @neko.command(name='ud', aliases=['urban'], brief='Search UD',
                   usage='|word-or-phrase')
    async def urban(self, ctx, *, phrase: str=None):
        """
        Searches urban dictionary for the given phrase or word.

        If no word is specified, we pick a few random entries.
        """
        if phrase:
            api, user = define_def
            resp = await neko.request('GET', api, params={'term': phrase})
            user = user + '?' + urllib.parse.urlencode({'term': phrase})
        else:
            api, user = random_def
            resp = await neko.request('GET', api)

        # Discard the rest, only be concerned with upto the first 10 results.
        resp = await resp.json()
        results = resp['list'][0:10]

        book = neko.Book(ctx)

        for definition in results:
            page = neko.Page(
                title=definition['word'].title(),
                description=neko.ellipses(definition['definition'], 2000),
                color=0xFFFF00,
                url=user
            )

            page.add_field(
                name='Example of usage',
                value=neko.ellipses(definition['example'], 1024),
                inline=False
            )

            page.add_field(
                name='Author',
                value=definition['author']
            )

            page.add_field(
                name=f'\N{THUMBS UP SIGN}{_big(definition["thumbs_up"])}',
                # No content (little discord trick)
                value=f'\N{THUMBS DOWN SIGN}{_big(definition["thumbs_down"])}ᅠ'
            )

            page.set_thumbnail(url=thumb_url)

            if 'tags' in resp:
                # Seems the tags can contain duplicates. Quick messy solution
                # is to pass it into a set first.
                page.set_footer(text=' '.join({*resp['tags']}),
                                icon_url=icon_url)
            else:
                page.set_footer(text=definition['permalink'], icon_url=icon_url)

            book += page

        await book.send()
