"""
Utilises the free wordnik API.

Requires an API key.

Sign up:
    http://www.wordnik.com/signup

Get a key:
    http://developer.wordnik.com/

They seem to say they will send an email, however, I never got one. I checked
in my settings and found the API key there.

The key should be stored in the tokens.json file under "wordnik"
"""
import typing

# Pls fix your file names >.>
import wordnik.swagger as swagger
# noinspection PyPep8Naming
import wordnik.WordApi as wordapi
# noinspection PyPep8Naming
import wordnik.models.Definition as definition

import neko


_api_endpoint = 'http://api.wordnik.com/v4'
_dictionaries = 'all'


class WordnikCog(neko.Cog):
    def __init__(self):
        self.__token = neko.get_token('wordnik')
        self.logger.info(f'Opening API client for Wordnik to {_api_endpoint}')
        self.client = swagger.ApiClient(self.__token, _api_endpoint)

    @neko.command(
        name='def',
        aliases=['define', 'def', 'dfn'],
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
                sourceDictionaries=_dictionaries,
                includeRelated=True
            )

        words: typing.List[definition.Definition] = await neko.no_block(_define)

        # Attempt to favour gcide and wordnet, as they have better definitions
        # imho.
        if words is None:
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

            words: typing.List[definition.Definition] = [
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
