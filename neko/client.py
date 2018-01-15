"""
Implementation of discord.ext.commands.Bot.
"""
import asyncio
import logging
import os
import signal
import time
import traceback

import aiofiles
import asyncpg

import discord
import discord.ext.commands as commands

import neko.common as common
import neko.log as log
import neko.io as io

__all__ = ['NekoBot']


config_template = {
    'token': 'token',
    'client_id': 0,
    'owner_id': 0,
    'command_prefix': 'n!',
    'database': {
        'user': 'postgres',
        'password': None,
        'host': 'localhost',
        'database': 'postgres'
    }
}


def terminate(signal_no, _):
    """
    Re-raises any termination signal as a KeyboardInterrupt.

    :param signal_no: the signal number we caught.
    :param _: the interrupted stack frame.
    """
    raise KeyboardInterrupt(f'Caught interrupt {signal_no}.')


# Signals. Apparently Windows doesn't implement all these... go figure.
if os.name == 'nt':
    signals = (
        signal.SIGABRT,
        signal.SIGTERM,
        signal.SIGSEGV
    )
else:
    signals = (
        signal.SIGABRT,
        signal.SIGTERM,
        signal.SIGQUIT,
        signal.SIGSEGV
    )
for signum in signals:
    signal.signal(signum, terminate)


class NekoBot(commands.Bot, log.Loggable):
    """
    Main bot runner. Takes a path to a JSON file
    holding the bot configuration. Expects the following
    fields to be present in said file.

      - token (str)
      - client_id (int)
      - command_prefix (str)
      - owner_id (int)
    """

    def __init__(self):
        """Initialises the bot environment."""
        config = io.load_or_make_json('config.json', default=config_template)

        self.__token = common.get_or_die(config, 'token')
        self.client_id = common.get_or_die(config, 'client_id')
        owner_id = common.get_or_die(config, 'owner_id')
        command_prefix = common.get_or_die(config, 'command_prefix')

        # Logger verbosity
        verbosity = config.get('verbosity', 'INFO')
        logging.basicConfig(level=verbosity)

        super().__init__(
            command_prefix=command_prefix,
            owner_id=owner_id,
        )

        self.__db_conf = common.get_or_die(config, 'database')

        self.postgres_pool: asyncpg.pool.Pool = None

        # Remove the injected help command.
        self.remove_command('help')

        # Field for the bot's start time
        self.start_time: time.time = None
        self._required_perms = 0
        self.logger.info(f'Add me to a guild at {self.invite_url}')

    async def start(self):
        """Starts the bot asynchronously."""
        async def make_pool():
            """Creates the postgresql connection pool."""
            # noinspection PyBroadException
            try:
                self.logger.info('Creating postgres pool')
                self.postgres_pool = await asyncpg.create_pool(**self.__db_conf)
            except BaseException:
                traceback.print_exc()
                self.logger.error('Could not initialise database pool.')
            else:
                self.logger.info('Successfully created pool')
                await self.ensure_db_setup()
        await make_pool()

        # Should work. Todo: make sure this doesn't do weird shit.
        await common.no_block(self._load_plugins)

        self.start_time = time.time()
        await super().start(self.__token)

    def run(self):
        """Runs the bot on the current thread and blocks until completion."""
        try:
            self.loop.run_until_complete(self.start())
        except KeyboardInterrupt or InterruptedError:
            traceback.print_exc()
            try:
                self.loop.run_until_complete(self.logout())
            except KeyboardInterrupt or InterruptedError:
                traceback.print_exc()
        finally:
            self.loop.close()

    async def logout(self):
        """
        Logs out of the discord session.
        """
        self.logger.info('Asked to log-out.')

        # Copy the list of keys. We cant iterate over a list that will
        # change size, and the keys will resize as elements are removed.
        ps = [p for p in self.extensions.keys()]
        for p in ps:
            self.logger.info(f'Unloading extension {p}.')
            self.unload_extension(p)

        # noinspection PyProtectedMember
        if self.postgres_pool is not None and \
                not self.postgres_pool._closed and \
                self.postgres_pool._initialized:
            self.logger.info('Closing database connection.')
            await self.postgres_pool.close()
        await super().logout()

    def add_cog(self, cog):
        """Adds a cog to the bot."""
        self.logger.info(f'Loaded cog {type(cog).__name__}')
        self._required_perms |= getattr(cog, 'permissions', 0)

        super().add_cog(cog)

    def remove_cog(self, name):
        """Removes a cog."""
        cog = self.get_cog(name)
        self.logger.info(f'Removing cog {type(cog).__name__}')
        self._required_perms ^= getattr(cog, 'permissions', 0)
        super().remove_cog(name)

    @property
    def invite_url(self) -> str:
        """Gets the URL to invite the bot to a guild."""
        return (
            'https://discordapp.com/oauth2/authorize?scope=bot&'
            f'client_id={self.client_id}&permissions={self._required_perms}'
        )

    @property
    def up_time(self) -> time.time:
        """Gets the bot's up-time"""
        return time.time() - self.start_time

    def _load_plugins(self):
        """Loads any plugins in the plugins.json file."""
        for p in io.load_or_make_json('plugins.json', default=[]):
            # noinspection PyBroadException
            try:
                self.logger.debug(f'Loading extension {p}.')
                self.load_extension(p)
                self.logger.debug(f'Successfully loaded extension {p}.')
            except discord.ClientException as ce:
                self.logger.warning(f'Failed to load {p} because {ce}')
            except BaseException:
                traceback.print_exc()
                self.logger.error(f'Error loading {p}; continuing without it.')

    async def on_command_error(self, ctx, error):
        """
        Custom handling of command errors. This just adds a react if a
        command cannot be resolved.
        """
        if isinstance(error, commands.CommandNotFound):
            try:
                await ctx.message.add_reaction(
                    '\N{BLACK QUESTION MARK ORNAMENT}'
                )
            except discord.Forbidden:
                await ctx.send('That command doesn\'t exist (and I don\'t have '
                               'the permissions to react to messages. Whelp!')
        else:
            super().on_command_error(ctx, error)

    async def ensure_db_setup(self):
        """Ensures the nekozilla schema exists."""
        file = io.relative_to_here('create_database.sql')
        self.logger.info('Opening and executing ' + file)

        async with aiofiles.open(file) as fp:
            command = await fp.read()

        pool = self.postgres_pool
        # noinspection PyProtectedMember
        if pool is None:
            self.logger.warning('Could not initialise database. '
                                'Check your configuration files.')
        else:
            async with pool.acquire() as conn:
                await conn.execute(command)
