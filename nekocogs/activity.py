"""
A cog/thread that cycles through the non-restricted commands and periodically
updates the bot user status to reflect the existence of such commands.
"""

import asyncio
import random
import threading
import time

import discord

import neko


@neko.inject_setup
class ActivityThread(threading.Thread, neko.Cog):
    """
    Handles updating the game every-so-often to a new message.

    I have kind of ditched using Asyncio in a loop on this thread. I keep
    getting issues with something tanking the CPU, and I am not convinced that
    it isn't something to do with this.

    The solution instead is to run a separate thread that sequentially pushes
    events onto this thread's event queue. ``time.sleep`` will yield to another
    process, so this should reduce overhead; albeit at the cost of an extra
    thread.

    This thread will fire and forget as soon as we have initialised this
    cog. It will poll every 10 seconds until the bot is ready. This is messy
    but it will use near to no resources. Each time the thread sleeps, it
    is an opportunity for the OS scheduler to yield to another process
    requesting CPU time.

    Furthermore, the thread is a daemon, so it will automatically die when the
    main thread or last non-daemon thread terminates.
    """
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

        threading.Thread.__init__(
            self,
            name='Activity Changer Loop (daemon)',
            daemon=True
        )

        neko.Cog.__init__(self)

        # Start once ready, then just fire and forget.
        self.start()

    @property
    def loop(self) -> asyncio.BaseEventLoop:
        return self.bot.loop

    def run(self):
        """A hopefully thread-safe loop."""
        # Poll every 10 seconds to see if ready.
        self.logger.info('Waiting for bot to connect to gateway.')
        time.sleep(10)
        while not self.bot.is_ready() and not self.bot.is_closed():
            self.logger.info('... ... still waiting ... ... *yawn* ... ...')
            time.sleep(10)

        self.logger.info('Connected to main thread. Bot is ready. Starting '
                         'loop to dispatch activities NOW.')

        # Main loop to execute once bot is ready.
        while not self.bot.is_closed():
            try:
                self.logger.debug('Creating future in main thread.')
                f: asyncio.Future = self.loop.create_task(self.next_activity())

                while not f.done() and not f.cancelled():
                    # Wait a second or so for the result to finish.
                    time.sleep(1)
            except KeyboardInterrupt:
                return
            except Exception:
                pass
            finally:
                # Wait 30 seconds before the next execution.
                time.sleep(30)

    async def next_activity(self):
        """Acts as an iterator for getting the next activity-change
        coro."""
        # Get a random command, this is more fun.
        command_choice = list(
            filter(
                # Hide superuser commands.
                lambda c: not c.qualified_name.startswith('sudo') and c.enabled,
                self.bot.walk_commands()
            )
        )

        game = random.choice(
            random.choice(command_choice).qualified_names)
        game = self.bot.command_prefix + game

        if game not in self.cache:
            game = discord.Game(
                name=game,
                type=2
            )
            self.cache[game.name] = game
            self.logger.debug(f'Couldn\'t find {game.name} in cache: '
                              f'thus, cached game {game}')
        else:
            self.logger.debug(f'Read cached game {game}')
            game = self.cache[game]

        await self.bot.change_presence(game=game)
