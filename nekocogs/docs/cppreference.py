"""
The mediawiki implementation for en.cppreference is awful for finding info.

I am going to be a horrible person and just scour the HTML content for what I
want instead.

Using regex because if I am going to go at this with a hammer, might as well
do a bloody good job of it.
"""
import collections
import re
import typing

import asyncio
import bs4
import neko

# URLs that are results we should have an interest in.
res_pat = re.compile(r'^/w/c(pp)?/', re.I)

# Actual search endpoint to use. This just uses the HTML search.
host = 'http://en.cppreference.com'
search_ep = host + '/mwiki/index.php'


SearchResult = collections.namedtuple('SearchResult', 'name desc url')


class CppReferenceCog(neko.Cog):

    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

    async def search_for(self, *terms):
        """
        Searches for the given terms, and serialises the result.
        :param terms: terms to search for.
        """
        def search_results_parser(html) -> (str, str):
            """
            Extracts results using BS4. This must be run in an executor of some
            sort.
            """
            bs = bs4.BeautifulSoup(html)

            # Find matching tags.
            tags: typing.List[bs4.Tag] = bs.find_all(
                name='a',
                attrs={'href': res_pat})

            # Generate a collection of SearchResult objects...
            raw_results = []

            for tag in tags:
                href = tag.get('href')

                # Don't match duplicates.
                if any(href in url for _, url in raw_results):
                    continue

                # Fire and forget.
                if not href:
                    continue
                elif not href.startswith('/'):
                    href = '/' + href

                name = tag.text
                url = host + href

                # Again, fire and forget.
                if not name:
                    continue

                raw_results.append((name, url))

            # Get the first 10 results.
            return raw_results[:10]

        def extract_flavour_text(html):
            """
            Extracts flavour info from given HTML.
            """
            bs = bs4.BeautifulSoup(html)

            taster_code = bs.find(
                name='span',
                attrs={'class': lambda c: c is not None and 'mw-geshi' in c})

            if taster_code:
                # Split on lines, strip any whitespace on end of lines, rejoin
                # and remove recursively multiple pairs of newlines to remove
                # empty lines. Also use this time to take advantage of replacing
                # mutliple spaces with no spaces. Not the nicest formatting
                # but discord poops across the line width of code in embeds
                # so we have to make do.
                taster_code = taster_code.text.split('\n')
                taster_code = [line.rstrip() for line in taster_code]
                taster_code = '\n'.join(taster_code)
                taster_code = neko.replace_recursive(taster_code, '\n\n', '\n')
                taster_code = f'`\n{taster_code}`'
            else:
                taster_code = ''

            return taster_code

        async def format_result(name, page):
            """
            Further formats a search result by getting some flavour info.
            """
            retries = 0
            while True:
                try:
                    res = await self.bot.request('GET', page)
                    data = await res.read()
                    break
                except BaseException:
                    if retries > 5:
                        return None
                    else:
                        retries += 1
                        continue

            flavour = await self.bot.do_job_in_pool(
                extract_flavour_text, data)

            return SearchResult(name=name, desc=flavour, url=page)

        resp = await self.bot.request(
            'GET',
            search_ep,
            params={'search': '|'.join(terms)})

        search_results = await self.bot.do_job_in_pool(
            search_results_parser,
            await resp.read())

        results = await asyncio.gather(
            *[format_result(name, url) for name, url in search_results])

        results = [result for result in results if result is not None]

        return results

    @neko.command(
        aliases=['c++', 'c'],
        usage='cstdio|std::stringstream',
        brief='Searches en.cppreference.com for the given query.')
    async def cpp(self, ctx, *, query):
        """
        This is still very experimental, as there is nothing of use in
        the implementation of the en.cppreference.com MediaWiki API, so
        this relies on crawling HTML. This may be relatively slow and
        buggy.
        """

        async with ctx.typing():
            book = neko.Book(ctx)

            results = await self.search_for(query)

            curr_page = None

            for i, result in enumerate(results):
                if curr_page is None:
                    curr_page = neko.Page(
                        title=f'Search results for `{query}`',
                        url=f'http://en.cppreference.com',
                        color=neko.random_colour())

                curr_page.add_field(
                    name=result.name,
                    value='\n'.join((result.desc, result.url)))

                if len(curr_page.fields) > 2 or i + 1 >= len(results):
                    book += curr_page
                    curr_page = None

        if not len(book):
            await ctx.send('No results', delete_after=10)
        else:
            await book.send()
