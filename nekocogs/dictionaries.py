"""
Various online dictionaries, thesauruses, etc.

Note that the Wordnik integration requires an API key.

Sign up:
    http://www.wordnik.com/signup

Get a key:
    http://developer.wordnik.com/

They seem to say they will send an email, however, I never got one. I checked
in my settings and found the API key there.

The key should be stored in the tokens.json file under "wordnik"
"""
import typing
import urllib.parse

import wordnik.swagger as swagger
import wordnik.WordApi as wordapi
import wordnik.models.Definition as wordnik_definition

import neko
import neko.other.perms as perms


wordnik_endpoint = 'http://api.wordnik.com/v4'
wordnik_dictionaries = 'all'

# These are pairs of the API and user website endpoints.
ud_random_def = ('http://api.urbandictionary.com/v0/random',
                 'https://urbandictionary.com/random.php')
ud_define_def = ('http://api.urbandictionary.com/v0/define',
                 'https://urbandictionary.com/define.php')

ud_icon_url = 'https://d2gatte9o95jao.cloudfront.net/assets/apple-touch-icon' \
              '-55f1ee4ebfd5444ef5f8d5ba836a2d41.png '

ud_thumb_url = 'https://vignette.wikia.nocookie.net/logopedia/images/a/a7' \
               '/UDAppIcon.jpg/revision/latest?cb=20170422211150 '


@neko.inject_setup
class DictionaryCog(neko.Cog):
    """Contains the UrbanDictionary and Wordnik implementations."""

    permissions = (perms.Permissions.SEND_MESSAGES |
                   perms.Permissions.ADD_REACTIONS |
                   perms.Permissions.READ_MESSAGES |
                   perms.Permissions.MANAGE_MESSAGES)

    def __init__(self, bot):
        """Initialises any APIs and the cog."""
        self.__token = bot.get_token('wordnik')
        self.logger.info(f'Opening API client to {wordnik_endpoint}')
        self.client = swagger.ApiClient(self.__token, wordnik_endpoint)
        super().__init__()

    @neko.command(
        name='def',
        aliases=['define', 'dfn'],
        brief='Looks for word definitions.',
        usage='name or phrase')
    async def get_word(self, ctx, *, word: str):
        """
        Gets a definition of a given word or phrase from WordNik
        """
        def _define():
            # Much complex. Very definition. Such API! Wow!
            api = wordapi.WordApi(self.client)

            # *prays to god this isn't lazy iterative.
            return api.getDefinitions(
                word,
                sourceDictionaries=wordnik_dictionaries,
                includeRelated=True
            )
        with ctx.typing():
            words: typing.List[
                wordnik_definition.Definition
            ] = await ctx.bot.do_job_in_pool(_define)

        # Attempt to favour gcide and wordnet, as they have better definitions
        # imho.
        # Fixes #9
        if not words:
            await ctx.send('I couldn\'t find a definition for that.')
        else:

            front = []
            back = []

            for word in words:
                if word.sourceDictionary in ('gcide', 'wordnet'):
                    front.append(word)
                else:
                    back.append(word)

            # Re-join.
            words = [*front, *back]

            words: typing.List[wordnik_definition.Definition] = [
                word for word in words
                if not word.sourceDictionary.startswith('ahd')
            ]

            # Max results to get is 100.
            max_count = min(100, len(words))

            book = neko.Book(ctx)

            for i in range(0, max_count):
                word = words[i]

                text = ''
                if word.partOfSpeech:
                    text += f'**{word.partOfSpeech}** '

                if word.text:
                    text += word.text

                if word.extendedText:
                    text += '\n\n'
                    text += word.extendedText

                page = neko.Page(

                    title=neko.capitalize(word.word),
                    description=neko.ellipses(text, 2000),
                    color=neko.random_colour()
                )

                if word.exampleUses:
                    example = word.exampleUses[0]
                    ex_text = neko.ellipses(example.text, 800)

                    page.add_field(
                        name='Example',
                        value=ex_text,
                        inline=False
                    )

                if word.relatedWords:

                    related = ', '.join([
                        ', '.join(rw.words) for rw in word.relatedWords
                    ])

                    page.add_field(
                        name='Synonyms',
                        value=neko.ellipses(related, 1000)
                    )

                if word.textProns:
                    pron = '\n'.join([tp.raw for tp in word.textProns])
                    pron = neko.ellipses(pron, 400)

                    page.add_field(
                        name='Pronunciations',
                        value=pron,
                    )

                if word.score:
                    page.add_field(
                        name='Scrabble score',
                        value=word.score.value
                    )

                if word.labels:
                    labels = ', '.join(label.text for label in word.labels)
                    labels = neko.ellipses(labels, 300)

                    page.add_field(
                        name='Labels',
                        value=labels
                    )

                if word.notes:
                    notes = []
                    for j, note in enumerate(word.notes):
                        notes.append(f'[{j+1}] {note.value}')

                    notes = neko.ellipses('\n\n'.join(notes), 300)

                    page.add_field(
                        name='Notes',
                        value=notes
                    )

                if word.attributionText:
                    attr = word.attributionText
                else:
                    attr = ('Extracted from '
                            f'{neko.capitalise(word.sourceDictionary)}')

                page.set_footer(text=attr)

                book += page

            await book.send()

    @neko.command(name='ud', aliases=['urban'], brief='Search UD',
                  usage='|word-or-phrase')
    async def urban(self, ctx, *, phrase: str=None):
        """
        Searches urban dictionary for the given phrase or word.

        If no word is specified, we pick a few random entries.
        """
        with ctx.typing():
            if phrase:
                api, user = ud_define_def
                resp = await ctx.bot.request('GET',
                                             api,
                                             params={'term': phrase})
                user = user + '?' + urllib.parse.urlencode({'term': phrase})
            else:
                api, user = ud_random_def
                resp = await ctx.bot.request('GET', api)

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

            ups = definition['thumbs_up']
            downs = definition['thumbs_down']

            page.add_field(
                name=f'\N{THUMBS UP SIGN} {ups}',
                # No content (little discord trick)
                value=f'\N{THUMBS DOWN SIGN} {downs}ᅠ'
            )

            page.set_thumbnail(url=ud_thumb_url)

            if 'tags' in resp:
                # Seems the tags can contain duplicates. Quick messy solution
                # is to pass it into a set first.
                page.set_footer(text=' '.join({*resp['tags']}),
                                icon_url=ud_icon_url)
            else:
                page.set_footer(
                    text=definition['permalink'],
                    icon_url=ud_icon_url
                )

            book += page

        if book.pages:
            await book.send()
        else:
            await ctx.send('I couldn\'t find a definition for that.')


