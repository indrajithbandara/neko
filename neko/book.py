"""
Uses voodoo with embeds and reacts to make itself behave like a book.

18th Jan 2018: Discord Canary seems to be doing some kind of optimisation
which means embeds are getting corrupted. This is not an issue on regular
release versions of Discord, and it seems to be a clientside issue.
"""
__all__ = ['Button', 'Page', 'Book', 'PaginatedBook']

import asyncio
import typing

import discord
import discord.ext.commands as commands

from neko import common
from neko import safeembed


class Page(safeembed.SafeEmbed):
    """For now, this does not alter any functionality."""
    pass


DEV = False

# For debugging. If DEV is a global and is set to True, then
# any coroutine that is called using this ensure_future signature
# will be gathered rather than the future being ensured. This has
# the side effect of running "synchronously". The reason for
# wanting such a function is that any exceptions will propagate
# fully out of gather, whereas they are just printed and ignored
# in asyncio.ensure_future. This is a pain when trying to debug
# any issues, as we cannot get a full traceback.
if DEV:
    def ensure_future(coro, *_):
        return coro
else:
    ensure_future = asyncio.ensure_future


class Button:
    """
    A button for a book. This should decorate a coroutine to perform when
    clicked.
    """
    __slots__ = (
        'invoke',
        'emoji',
        'always_show'
    )

    def __new__(cls, emoji: str, show_if_one_page=True):
        """
        Generates a new button.
        :param emoji: the emoji to decorate the button with.
        :param show_if_one_page: defaults to True. If False, then the button
                is only displayed if more than one page is present in the
                pagination.
        :return: a decorator for a coroutine describing what to do when
                the button is clicked. The first parameter is the parent
                book object, the second is the current page, which is an
                embed.
        """
        if len(emoji) != 1:
            raise ValueError('Emoji must be a single character.')
        else:
            def decorator(coro: typing.Callable[['Book', 'Page'], None]):
                if not common.is_coroutine(coro):
                    raise ValueError('Button must decorate a coroutine.')
                else:
                    btn = object.__new__(cls)

                    setattr(btn, 'emoji', emoji)
                    setattr(btn, 'invoke', coro)
                    setattr(btn, 'always_show', show_if_one_page)

                    return btn

            return decorator


class Book:
    """
    A book is a collection of pages, along with an associated page number.
    """
    __slots__ = (
        'pages',  # Collection of embeds.
        '_page_index',  # 0-based page index. Access via `index` or `page_no`.
        'buttons',  # Collection of buttons.
        '_ctx',  # The context to reply to.
        '_msg',  # The message containing the current page. This is set on send.
        'timeout'  # How long to idle for before destroying pagination.
    )

    def __init__(self,
                 ctx: commands.Context,
                 timeout: float = 120,
                 buttons: typing.Iterable = None):
        """
        Initialises the pages.
        :param ctx: the message context we are replying to.
        :param buttons: the buttons to display on the Book. If none, default
                buttons are generated instead.
        :param timeout: time to wait before destroying pagination.
                Defaults to 120 seconds.
        """
        self.pages = []
        self._page_index = 0

        if timeout <= 0:
            raise ValueError('Timeout must be positive and nonzero.')

        self.timeout = timeout

        if buttons is None:
            buttons = self.generate_buttons()

        self.buttons: typing.Dict[str, Button] = {}

        for button in buttons:
            if not isinstance(button, Button):
                raise TypeError('Each button must be a Button object.')
            else:
                self.buttons[button.emoji] = button

        self._ctx = ctx

    @property
    def context_invoked_from(self) -> commands.Context:
        """Gets the context we were invoked from."""
        return self._ctx

    @property
    def response_message(self) -> typing.Optional[discord.Message]:
        """Gets the response message we sent."""
        return self._msg

    @property
    def index(self):
        """Gets the page index. This is a zero-based index."""
        return self._page_index

    @index.setter
    def index(self, new):
        """
        Sets the page index. This is a zero-based index, but will wrap
        around relative to the start/end of the pages, thus -1 would be
        the same as setting the last page, etc.
        """
        # Wraps the index around at the front and rear.
        while new < 0:
            new += len(self)
        while new >= len(self):
            new -= len(self)

        self._page_index = new

    @property
    def page_no(self):
        """Gets the page number. This is a one-based index."""
        return self._page_index + 1

    @page_no.setter
    def page_no(self, new):
        """
        Sets the page number. This is a one-based index and does not wrap
        around like index does.
        """
        if 0 < new <= len(self.pages):
            self._page_index = new - 1
        else:
            raise IndexError(
                f'Page number {new} is outside range [1...{len(self.pages)}]'
            )

    @property
    def page(self) -> Page:
        """Gets the current page."""
        return self.pages[self._page_index]

    def add_page(self, *, index=None, **kwargs) -> discord.Embed:
        """
        Attempts to create an embed from the given kwargs, adding it
        to the page collection.

        If you have pre-made an embed, then just call `btn.pages.append()`
        instead.

        If index is None, it is added to the end of the collection, otherwise,
        it is inserted at the given index into the list.

        The embed is then returned.
        """
        embed = discord.Embed(**kwargs)

        if index is None:
            self.append(embed)
        else:
            self.insert(index, embed)

        return embed

    def __iter__(self):
        """Iterates across each page in order."""
        yield from self.pages

    def __len__(self):
        """Counts the pages."""
        return len(self.pages)

    def __contains__(self, item):
        """True if the given item is a page in the collection."""
        return item in self.pages

    def __getitem__(self, index: int):
        """Gets the page at the given zero-based index."""
        return self.pages[index]

    def __iadd__(self, other: Page):
        """
        If a Page (a discord Embed) is given, we append the page to the end
        of the collection of pages.
        """
        if not isinstance(other, Page):
            raise TypeError('Expected embed.')
        else:
            self.pages.append(other)
            return self

    def append(self, page: Page):
        """Appends the page."""
        if not isinstance(page, Page):
            raise TypeError('Expected embed.')
        else:
            self.pages.append(page)

    def insert(self, index, page):
        """
        Inserts the page at a given 0-based index.
        """
        index = int(index)
        if not isinstance(page, Page):
            raise TypeError('Expected embed.')
        elif not 0 <= index <= len(self.pages):
            raise IndexError(
                f'Page number {index} is outside range [0,{len(self.pages)}]'
            )
        else:
            self.pages.insert(index, page)

    async def send(self):
        """
        Sends the message and waits for a reaction.
        The button coroutine is performed for any
        reaction added by the sender of the context passed
        to the constructor.

        If nothing is done for timeout seconds, the pagination
        is cleared and this element becomes decayed. This is to
        prevent the application from having an increasing
        number of co-routines in the event loop idling, as this
        will consume more and more memory over time, and likely
        degrade performance.
        """
        if len(self.pages) == 0:
            page = Page(
                title='*HISS*',
                description='Seems there is nothing to see here. This is '
                            'probably an oversight, or just laziness on '
                            'the developer\'s behalf.\n\nYou know what? I '
                            'will go punish him right now.\n\n'
                            '*Shotgun barrel clicks*')

            page.set_footer(text='No nekos were hurt in the making of this '
                                 'embed. A duck was shot, and a cat got sick, '
                                 'but that was about it.')

            self.pages.append(
                page
            )

        ensure_future(self._send_loop())

    async def _send_loop(self):
        # If no page has been shown yet, send a placeholder message.
        if not hasattr(self, '_msg') or self._msg is None:
            msg = await self._ctx.send('Loading pagination...')
            setattr(self, '_msg', msg)

            ensure_future(self._reset_buttons())

        ensure_future(self._update_page())

        try:
            def check(_react, _user):
                return (_react.emoji in self.buttons.keys()
                        and _react.message.id == self._msg.id
                        and _user.id in (
                            self._ctx.author.id, self._ctx.bot.owner_id))

            react, member = await self._ctx.bot.wait_for(
                'reaction_add',
                timeout=self.timeout,
                check=check
            )

            ensure_future(self._msg.remove_reaction(react.emoji, member))
        except asyncio.TimeoutError:
            # Kills the pagination.
            self.decay()
        else:
            await self.buttons[react.emoji].invoke(self, self.page)

    async def _reset_buttons(self):
        """
        Clears all reactions and displays the
        current buttons in insertion order.
        """
        await self._msg.clear_reactions()
        # Must await to ensure correct ordering.
        if len(self) > 1:
            [await self._msg.add_reaction(btn) for btn in self.buttons]
        else:
            for emoji, btn in self.buttons.items():
                if btn.always_show:
                    await self._msg.add_reaction(emoji)

    async def _msg_content(self):
        """
        Gets a string to display for the message content.

        This does not call another coroutine. However, it exists to be
        await-able in order to allow overriding this message.
        """
        return f'Page {self.page_no} of {len(self)}'

    async def _update_page(self):
        """
        Forces the current page to be edited to reflect the current page
        in this Book. This will not touch reactions.
        """
        await self._msg.edit(
            content=await self._msg_content(),
            embed=self.page
        )

    def decay(self):
        """
        Makes the pagination decay into an embed. This effectively
        finalises this element.
        """
        ensure_future(self._msg.clear_reactions())
        ensure_future(self._msg.edit(content=''))

    @staticmethod
    def generate_buttons() -> typing.List[Button]:
        """
        Generates default buttons.

        |<< - Goes to the first page.
         <  - Decrements the page number.
        123 - Takes the page number as input.
         >  - Increments the page number.
        >>| - Goes to the last page.
         X  - Kills the pagination.
        Bin - Kills the embed and original message.
        """

        @Button(
            '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}', 
            False)
        async def first_page(book: Book, __: Page):
            book.index = 0
            await book._send_loop()

        @Button('\N{BLACK LEFT-POINTING TRIANGLE}', False)
        async def previous_page(book: Book, __: Page):
            book.index -= 1
            await book._send_loop()

        @Button('\N{INPUT SYMBOL FOR NUMBERS}', False)
        async def page_picker(book: Book, __: Page):
            prompt = await book._ctx.send(
                'Please enter a page number/offset to go to.'
            )

            try:
                def check(message):
                    ctx = book.context_invoked_from
                    return (
                        message.channel == ctx.channel and
                        message.author.id == ctx.author.id
                    )

                while True:
                    reply = await book._ctx.bot.wait_for(
                        'message',
                        timeout=30,
                        check=check
                    )
                    try:
                        await reply.delete()
                        reply.content = reply.content.strip()
                        i = int(reply.content)
                        is_offset = reply.content.startswith('+') or i < 0
                        if is_offset:
                            book.index += i
                        else:
                            if i < 1 or i > len(book):
                                raise ValueError()
                            else:
                                book.page_no = i
                        await prompt.delete()
                        break
                    except ValueError:
                        await book._ctx.send(
                            'Invalid input. Try again.',
                            delete_after=10
                        )
            except asyncio.TimeoutError:
                await book._ctx.send(
                    'Took too long.',
                    delete_after=10
                )
            finally:
                await book._send_loop()

        @Button('\N{BLACK RIGHT-POINTING TRIANGLE}', False)
        async def next_page(book: Book, __: Page):
            book.index += 1
            await book._send_loop()

        @Button('\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
                False)
        async def last_page(book: Book, __: Page):
            book.index = -1
            await book._send_loop()

        @Button('\N{SQUARED OK}')
        async def close_book(b: Book, __: Page):
            # Doesn't need to do anything apart from remove the page number and
            # the reactions.
            b.decay()

        @Button('\N{PUT LITTER IN ITS PLACE SYMBOL}')
        async def close_and_delete(b: Book, __: Page):
            await b.response_message.delete()
            await b.context_invoked_from.message.delete()

        return [
            first_page,
            previous_page,
            page_picker,
            next_page,
            last_page,
            close_book,
            close_and_delete
        ]


class PaginatedBook(Book):
    """
    Mixes in commands.Paginator functionality with the Book "engine" to make
    for auto-paginating strings without having to have a brain.

    This works by containing a paginator inside the class definition.

    The outer book wrapper can still have pages added to it as normal, however,
    the lines and paragraphs added will be appended as pages to the end of the
    book when it is sent.

    :param prefix: the prefix to each page. Defaults to nothing.
    :param suffix: the suffix to each page. Defaults to nothing.
    :param max_size: the max character count to allow per page. Discord limits
            this anyway (read the API documentation for embed limits). This
            defaults to 1900
    :param max_lines: the max number of lines to allow per page to limit the
            height of embeds. This is not set by default.
    :param ctx: the command context. A required ``keyword`` argument.
    :param title: the title to add to the top of paginated pages. This does not
            affect embeds.
    """

    def __init__(self,
                 *,
                 prefix='',
                 suffix='',
                 max_size=1990,
                 max_lines=None,
                 ctx: commands.Context,
                 title: str):

        if max_lines is not None and max_lines < 1:
            raise ValueError('Cannot set maxlines to be less than 1.')

        super().__init__(ctx)
        self.paginator = commands.Paginator(prefix, suffix, max_size)
        self.title = title
        self.max_lines = max_lines
        self.__pag_curr_lines = 0

    def add_line(self, content='', follow_with_empty=False):
        """
        Adds a line to the current page.
        :param content: the content of the line.
        :param follow_with_empty: defaults to false. If true, a blank line
                proceeds the current line.
        """

        # If the line cannot be fit in a full page, then don't immediately
        # give up. Instead, try to backtrack from the max page length
        # to the nearest space at the rear. If we still cannot resolve this,
        # then raise an error.
        max_len = (self.paginator.max_size
                   - len(self.paginator.prefix) - len(self.paginator.suffix))

        while len(content) >= max_len:
            index = max_len - 1
            while index >= 0 and not content[index].isspace():
                index -= 1

            # If index = -1, then we have failed to find a space
            if index == -1:
                raise RuntimeError(f'Line exceeds max line size of {max_len} '
                                   'but I could not find any spaces, so I am '
                                   'giving up.')

            line = content[:index + 1]
            content = content[index + 1:]
            self.__add_line(line, empty=follow_with_empty)

        self.__add_line(content)

    def __add_line(self, content, empty=False):
        """
        Takes a string to add, and counts the lines. If we go over max_lines
        if that is set, then we page-break at the limit repeatedly.
        :param content: the content to add.
        :param empty: true if to add an empty line after.
        """
        if self.max_lines is not None:
            content = content.split('\n')

            for line in content:
                if self.max_lines <= self.__pag_curr_lines:
                    self.paginator.close_page()
                    self.__pag_curr_lines = 0
                self.paginator.add_line(line)
                self.__pag_curr_lines += 1

            if empty:
                self.paginator.add_line(empty=True)
                self.__pag_curr_lines += 1
        else:
            self.paginator.add_line(content, empty=empty)

    def add_lines(self, content, follow_with_empty=True):
        """
        Adds a paragraph to the current page.
        :param content: the string to split and add.
        :param follow_with_empty: true by default, if true it will add a blank
                line after the content is added.
        """
        if not hasattr(content, '__iter__'):
            raise TypeError('Must be iterable or string (using \\n to delimit)')
        elif isinstance(content, str):
            content = content.split('\n')

        for line in content:
            self.add_line(line)
        if follow_with_empty:
            self.add_line()

    async def send(self):
        """
        Adds each page from the string paginator to the book as an embed.
        """
        for index, page in enumerate(self.paginator.pages):
            if index == 0:
                book_page = Page(title=self.title, description=page)
            else:
                book_page = Page(description=page)
            self.append(book_page)

        await super().send()
