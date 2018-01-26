"""
Gets and displays XKCD comics.

What else do you expect?
"""
import neko


# Sentient placeholder.
_empty = ''

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']


class XkcdComic:
    def __init__(self, *, month=_empty, num=0, link=_empty, year=_empty,
                 news=_empty, safe_title=_empty, transcript: list=None,
                 alt=_empty, img=_empty, title=_empty, day=_empty, **kwargs):
        if kwargs:
            raise ValueError('Unexpected arguments received: '
                             + ', '.join(kwargs))
        self.month = month
        self.link = link
        self.year = year
        self.news = news
        self.safe_title = safe_title
        self.transcript = transcript if transcript else []
        self.alt = alt
        self.img = img
        self.title = title
        self.day = day
        self.num = num


class XkcdComicNotFoundError(neko.NekoCommandError):
    def __init__(self, num):
        self.num = num

    def __str__(self):
        if self.num:
            return f'XKCD #{self.num} does not exist, or the website is down.'
        else:
            return f'XKCD is unavailable :-('


@neko.inject_setup
class XkcdCog(neko.Cog):
    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

    async def get_comic(self, num: int=None) -> XkcdComic:
        """
        Gets the given XKCD comic number. If no number is specified,
        or it is NoneType, we get the most recent comic instead.
        """
        try:
            if num is not None:
                num = int(num)
                if num < 0:
                    raise ValueError

                url = f'https://xkcd.com/${num}/info.0.json'
            else:
                url = 'https://xkcd.com/info.0.json'

            resp = await self.bot.request('GET', url)
            data = await resp.json()

            if not isinstance(data, dict):
                raise TypeError(f'Expected dict, got {type(data)}.')
            else:
                return XkcdComic(**data)
        except neko.HttpRequestError:
            raise XkcdComicNotFoundError(num)
        except ValueError:
            raise neko.NekoCommandError('Invalid input... you cretin')

    @neko.command(
        brief='Gets the XKCD comic for today. If you give a number, then I '
              'will try to retrieve that comic number instead.',
        usage='|327')
    async def xkcd(self, ctx, number: int=None):
        if number == -1:
            await ctx.send('https://xkcd.com/chesscoaster/')
        elif number == 0:
            await ctx.sen('http://wiki.xkcd.com/geohashing/Main_Page')
        else:

            with ctx.typing():
                comic = await self.get_comic(number)

            date = neko.pluralize(int(comic.day), method='th')
            date += f' {months[int(comic.month) - 1]} {comic.year}'

            page = neko.Page(
                title=comic.title,
                url=comic.link if comic.link else neko.EmptyEmbedField,
                description=date,
                colour=0xFFFFFF)  # XKCD white.

            page.set_author(
                name='XKCD',
                url='https://xkcd.com',
                # Sue me.
                icon_url='https://pbs.twimg.com/profile_images'
                         '/602808103281692673/8lIim6cB_400x400.png')

            page.set_footer(
                text=comic.alt)

            page.set_image(url=comic.img)

            await ctx.send(embed=page)
