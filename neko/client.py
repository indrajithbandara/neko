"""
Implementation of discord.ext.commands.Bot.
"""
import collections
import concurrent.futures
import copy
import datetime
import functools
import json
import logging
import os
import signal
import sys
import traceback
import types

import aiohttp
import asyncpg
import discord
import discord.ext.commands as commands
import neko
import neko.common as common
import neko.io as io
import neko.other.log as log
import neko.other.asyncpgconn as asyncpgconn

__all__ = ['NekoBot', 'HttpRequestError', 'PresenceCache', 'LastError']


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


# Holds our presence.
PresenceCache = collections.namedtuple('PresenceCahce', 'status game afk')


# Holds the last error that occurred.
LastError = collections.namedtuple('LastError', 'type value traceback')


class _LastErrorDated:
    """
    Generated from LastError when we set it to have a persistent timestamp.
    """
    def __init__(self, t_type, value, t_traceback):
        self.type, self.value, self.traceback = t_type, value, t_traceback
        self.date = datetime.datetime.now()


class Tokens(log.Loggable):
    """
    Holds a dictionary. The keys are case insensitive and the type behaves
    as if it were immutable. This provides readonly access
    """
    __token_file = 'tokens.json'

    def __init__(self):
        try:
            file = self.__token_file
            self.logger.info(f'Reading external tokens from {file}')
            data = io.load_or_make_json('tokens.json')

            if not isinstance(data, dict):
                raise TypeError('Expected map of names to keys.')
            else:
                # Ensure no duplicates of keys (case insensitive)
                mapping = (*map(str.lower, data.keys()),)
                if len(mapping) != len({*mapping}):
                    raise ValueError('Duplicate keys found.')
                else:
                    self.__tokens = {}
                    for k, v in data.items():
                        self.__tokens[k.lower()] = v

        except FileNotFoundError:
            raise FileNotFoundError(f'Cannot find {file}') from None

    def __getitem__(self, api_name):
        try:
            return copy.deepcopy(self.__tokens[api_name])
        except KeyError:
            raise KeyError(f'No API key for {api_name} exists.') from None

    def __setitem__(self, *_):
        raise NotImplementedError('No chance.')


class HttpRequestError(RuntimeError):
    """Represents an Http failure."""
    def __init__(self, response):
        self.response = response

    @property
    def status(self) -> int:
        return self.response.status

    @property
    def reason(self) -> str:
        return self.response.reason

    def __str__(self):
        return ' '.join([self.status, self.reason])


class NekoBot(commands.Bot, log.Loggable, metaclass=common.InitClassHookMeta):
    """
    Main bot runner. Takes a path to a JSON file holding the bot configuration.
    Expects the following fields to be present in said file.

      - token (str)
      - client_id (int)
      - command_prefix (str)
      - owner_id (int)
      - database (dict) {
            user - str
            password - str
            host - str (optional)
            database - str
        }

    **New Attributes:**
        - ``_required_perms`` - int - Required permissions used in generating
                invitation URLS.
        - ``client_id`` - int - client id.
        - ``http_pool`` - aiohttp.ClientSession - multipurpose HTTP session for
                use by cogs that require the ability to do HTTP requests.
        - ``logger`` - logging.Logger - Logger object.
        - ``postgres_pool`` - asyncpg.pool.Pool - PostgreSQL connection pool.
        - ``start_time`` - time.time - Time the bot logged in.
        - ``invite_url`` - str - generates an invitation URL.
        - ``up_time`` - time.time - gets the bot's uptime, or None if the bot
                has yet to start.
        - ``last_error`` - LastError - the last error that occurred. This can
                be set by anything in the bot, and is useful for diagnostics.

    **New Methods:**
        - ``async def do_job_in_pool(func, *args, **kwargs)`` - runs func
                in a dedicated thread pool executor without blocking the
                current coroutine event loop.
        - ``def get_token(name)`` - attempts to get the given token from the
                tokens.json file. This file is read once and once only, and that
                is during the ``NekoBot.__init__ method``. All members are
                immutable and will always be deep copies of the initial value.
        - ``async def request(method, url, **kwargs)`` - performs a request in
                the ``http_pool``; HOWEVER. This will also validate and
                sanitise against any exceptions that may occur, or HTTP
                error codes that may get raised.

    **Overridden Methods:**
        - ``async def start()`` - now gets the token from the object's
                ``__token`` attribute. This will then proceed to initialise
                the postgresql async connection pool: ``postgres_pool``, and
                then open an ``aiohttp`` ``ClientSession``: ``http_pool``.
                Finally, the modules are loaded asynchronously in the thread
                pool provided by this class and the bot is started.
        - ``def run()`` - does not accept any parameters. The bot should be
                specified a token via the ``config.json`` file. This now also
                handles signals passed from the kernel such as SIGABRT, SIGSEGV,
                and a few other bits and pieces to attempt to gracefully
                terminate on signal-to-exit. A second signal will forcefully
                disconnect the session. Todo: check this.
        - ``def logout()`` - will now gracefully unload any cogs and extensions,
                and then disconnect the aiohttp and postgres connection pools.
        - ``def add_cog(cog)`` - logs the cog being added, and calculates if the
                required permissions need to be updated for the bot.
        - ``def remove_cog(cog)`` - logs the cog being removed.
        - ``async def on_command_error(...)`` - if the command error is due to
                the command not being found, then instead of outputting
                the error, we just attempt to react a "?" to the sender context.
        - ``async def change_presence(...)`` - if the game/status/afk is not
                specified now, then we do not reset it. This is done by
                internally caching the states.
    """

    def __init__(self):
        """Initialises the bot environment."""
        print(
            neko.__title__,
            neko.__version__,
            neko.__author__,
            file=sys.stderr)

        config = io.load_or_make_json('config.json', default=config_template)

        # Logger verbosity
        verbosity = config.get('verbosity', 'INFO')
        logging.basicConfig(level=verbosity)

        self.__token = common.get_or_die(config, 'token')
        self.client_id = common.get_or_die(config, 'client_id')
        owner_id = common.get_or_die(config, 'owner_id')
        command_prefix = common.get_or_die(config, 'command_prefix')

        super().__init__(
            command_prefix=command_prefix,
            owner_id=owner_id,
        )

        self.__db_conf = common.get_or_die(config, 'database')
        self.__postgres_pool: asyncpg.pool.Pool = None
        self.__http_pool: aiohttp.ClientSession = None

        self.__extra_tokens = Tokens()
        self.__last_error = _LastErrorDated(None, None, None)

        # Remove the injected help command.
        self.remove_command('help')

        # For basic IO bound work, and blocking work.
        self.__thread_pool_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=config.get('max_workers'),
            thread_name_prefix='Nekozilla Threadpool'
        )

        # Field for the bot's start time
        self.start_time: datetime.datetime = None
        self._required_perms = 0
        self.logger.info(f'Add me to a guild at {self.invite_url}')

        # Adds a couple of events I find useful to log.
        @self.listen()
        async def on_connect():
            self.logger.info(f'Connected at {datetime.datetime.now()}')

        @self.listen()
        async def on_resumed():
            self.logger.info(f'Resumed at {datetime.datetime.now()}')

        @self.listen()
        async def on_ready():
            self.logger.info(f'Ready at {datetime.datetime.now()}')

    @property
    def invite_url(self) -> str:
        """Gets the URL to invite the bot to a guild."""
        return (
            'https://discordapp.com/oauth2/authorize?scope=bot&'
            f'client_id={self.client_id}&permissions={self._required_perms}'
        )

    @property
    def last_error(self) -> _LastErrorDated:
        """Includes timestamp."""
        return self.__last_error

    @last_error.setter
    def last_error(self, value: (type, BaseException, types.TracebackType)):
        """Injects timestamp."""
        self.__last_error = _LastErrorDated(*value)

    @property
    def http_pool(self) -> aiohttp.ClientSession:
        """
        Gets the allocated HTTP pool.

        Usage (given ``self`` is called ``bot``):
           res = await bot.http_pool.request(...)
        """
        return self.__http_pool

    @property
    def postgres_pool(self) -> asyncpg.pool.Pool:
        """
        Gets the allocated database connection pool.

        Usage (given ``self`` is called ``bot``):
            with bot.postgres_pool.acquire() as conn:
                await conn.execute('SELECT * FROM table WHERE x = y;')
        """
        return self.__postgres_pool

    @property
    def up_time(self) -> datetime.timedelta:
        """Gets the bot's up-time"""
        return datetime.datetime.utcnow() - self.start_time

    def get_token(self, api_name: str):
        """
        Attempts to get the token for the given API name.
        :param api_name: the API name to attempt to get the token of.
        :return: the token.
        :raises KeyError: if the token is not found.
        """
        return self.__extra_tokens[api_name]

    async def start(self):
        """Starts the bot asynchronously."""
        await self.__init_https_session()
        await self.__init_postgres_pool()

        # Should be thread-safe. We assume nothing else will be in the loop
        # yet, as the bot should not have been started, and we are waiting on
        # the thread to finish the work. This _might_ cause weird behaviour
        # in the future, I am not sure. If it does, then we should just
        # accept that it is a blocking call I guess. The problem is, this
        # may rely on the fact that the HTTPS session or postgres pool are
        # already initialised, so we cannot call this before now without
        # further complications. Fixme.

        # The issue is, we have to
        await self.do_job_in_pool(self.__load_plugins)
        self.start_time = datetime.datetime.utcnow()
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
            try:
                self.unload_extension(p)
            except BaseException:
                pass

        await self.__deinit_postgres_pool()
        await self.__deinit_postgres_pool()
        await super().logout()

    def add_cog(self, cog):
        """Adds a cog to the bot."""
        self.logger.info(f'Loaded cog {type(cog).__name__}')
        self._required_perms |= getattr(cog, 'permissions', 0)

        try:
            super().add_cog(cog)
        except BaseException as ex:
            # If we have an error, attempt to unload the cog again.
            try:
                super().remove_cog(cog)
            finally:
                raise ImportError(ex)

    def remove_cog(self, name):
        """Removes a cog."""
        cog = self.get_cog(name)
        self.logger.info(f'Removing cog {type(cog).__name__}')

        # This will not work, as it will remove a permission regardless of if
        # another module requires it.
        # Fixme.
        # self._required_perms ^= getattr(cog, 'permissions', 0)
        super().remove_cog(name)

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

    async def do_job_in_pool(self, job, *args, **kwargs):
        """
        Executes the given function in a separate thread and waits for it
        to finish. This will not block the async event queue. The result is
        returned, or if an exception occurs, this propagates out of this
        coroutine.
        """
        return await self.loop.run_in_executor(
            self.__thread_pool_executor,
            functools.partial(
                job,
                *args,
                **kwargs
            )
        )

    async def request(self, method, url, **kwargs):
        """
        Performs the given HTTP request in the pool asynchronously, but
        also validates the connection properly for you. If an error occurs, then
        a nice tidy HttpRequestError is raised with all the info you could ever
        need. This is designed to allow direct dumping of error messages
        directly as user output to discord, as I am lazy.

        :param url: URL to access.
        :param method: HTTP method to use.
        :param kwargs: any kwargs to provide to
                ``aiohttp.ClientSession.request``
        :return: the result of the request.
        :raise: HttpRequestError, or any exception raised by aiohttp normally.
                (cba to rtfm right now and list them!)
        """

        valid_responses = {
            *common.between(100, 102),
            *common.between(200, 208),
            *common.between(300, 302),
        }

        resp = await self.http_pool.request(method, url, **kwargs)
        if resp.status not in valid_responses:
            raise HttpRequestError(resp)
        else:
            return resp

    def __load_plugins(self):
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

    async def __init_postgres_pool(self):
        """
        Initialises the Postgres pool and then Ensures the Nekozilla schema
        exists.
        """
        # noinspection PyBroadException
        try:
            postgres_logger = log.get_logger('NekoClient.postgres')

            async def setup_connection(proxy: asyncpg.pool.PoolConnectionProxy):
                # noinspection PyProtectedMember
                prox_conn = proxy._con
                assert isinstance(prox_conn, asyncpgconn.ShutdownHookConnection)

                # Connection, {__str__, }
                def listener(_, log_message):
                    type_name = type(log_message).__name__
                    level = common.find(
                        lambda s: s in type_name.lower(),
                        ('fatal', 'error', 'warn', 'info', 'debug'))

                    if level is None:
                        level = 'info'
                    elif level == 'fatal' or level == 'error':
                        level = 'warning'

                    level = log.as_level(level)

                    msg = f'{type_name}: {log_message}'

                    postgres_logger.log(level, msg)

                # Add listener, add hook to remove listener on release to
                # prevent warnings.
                prox_conn.add_log_listener(listener)
                prox_conn.add_closing_listener(
                    lambda s: s.remove_log_listener(listener)
                )

            self.logger.debug('Creating postgres pool')
            self.__postgres_pool = await asyncpg.create_pool(
                loop=self.loop,
                setup=setup_connection,
                connection_class=asyncpgconn.ShutdownHookConnection,
                **self.__db_conf
            )
        except BaseException:
            traceback.print_exc()
            self.logger.error('Could not initialise database pool. Cogs '
                              'that rely on this pool will likely fail. You '
                              'should be able to just ignore those messages.')
        else:
            self.logger.info('Created postgres pool. Database says HELLO!')
            async with self.postgres_pool.acquire() as conn:
                await conn.execute('CREATE SCHEMA IF NOT EXISTS nekozilla;')

    async def __deinit_postgres_pool(self):
        """Destroys the postgresql pool."""
        # These checks are to prevent further errors if we didn't successfully
        # initialise the postgres connector at startup, as the bot will still
        # attempt to function without it.
        # noinspection PyProtectedMember
        if self.postgres_pool is not None:
            self.logger.info('Closing postgres connection.')
            await self.postgres_pool.close()
        self.logger.debug('Postgres connection was successfully destroyed.')
        self.__postgres_pool = None

    async def __init_https_session(self):
        """Initialises the HTTP session usable by cogs."""
        self.logger.debug('Initialising aiohttp client session (and pool).')
        self.__http_pool = aiohttp.ClientSession(
            loop=self.loop
        )
        self.logger.info('Initialised aiohttp client session (and pool).')

    async def __deinit_https_session(self):
        """Destroys the HTTP session."""
        self.logger.info('Closing aiohttp client session (and pool).')
        if self.http_pool is not None and self.http_pool.closed:
            self.__http_pool.close()
        self.__http_pool = None
        self.logger.debug('Aiohttp client session (and pool) was successfully '
                          'destroyed.')

    @classmethod
    def __init_class__(cls, *_, **__):
        def terminate(signal_no, _):
            """
            Re-raises any termination signal as a KeyboardInterrupt.

            :param signal_no: the signal number we caught.
            :param _: the interrupted stack frame.
            """
            raise KeyboardInterrupt(f'Caught interrupt {signal_no}.')

        if os.name == 'nt':
            print('This bot has not been tested on Windows. Good luck...',
                  file=sys.stderr)
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

    async def on_error(self, _event_method, *args, **kwargs):
        """
        On any kind of error, we should store the error in the exception
        object so I can retrieve it later using a command.
        """
        self.last_error = LastError(*sys.exc_info())
        super().on_error(_event_method, *args, **kwargs)

