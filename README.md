# Nekozilla
A small bot for Discord servers to provide some useful fun commands and features.

## Dependencies

### Python 3.6.4
- [`Discord.py`](https://github.com/rapptz/discord.py) (rewrite) - Main API library for interacting 
    with the Discord Bot Gateway.\*
- [`aiofiles`](https://github.com/Tinche/aiofiles) - Asyncio integration for non-blocking file IO.\*
- [`aiohttp`](https://github.com/aio-libs/aiohttp) - Asyncio integration for HTTP requests.\*
- [`asyncpg`](https://github.com/MagicStack/asyncpg) - Asyncio wrapper for PostgreSQL.\*
- [`pillow`](https://pillow.readthedocs.io/en/5.0.0/) - Python Image Library (PIL) support.\*
- [`wordnik-py3`](https://github.com/wordnik/wordnik-python3) - Wordnik Python3 API wrapper.\*

<small>*\* These dependencies are available directly from PyPi using the `pip` command*</small>

## Configuration

The bot will read a file called `config.json` from the current working directory.

By default, no plugins will be loaded. A file called `plugins.json` should be specified 
containing a list of the fully qualified package names for each extension to load.

Additionally, any external services that require tokens for access will look in a file
called `tokens.json` if it exists for the corresponding token. This should be an object
containing case-insensitive keys mapping to tokens for each API that requires it. If 
keys are not available, the cogs utilising them will fail to load on start-up. Note that
this does not affect the rest of the bot.

The database connection configuration should be supplied in the `config.json` file. This
is designed to work with a PostgreSQL database. A role should be made to access the
database with, and should be granted the `CREATE` permission using:

```sql
GRANT create ON DATABASE postgres TO user;
```

...substituting `postgres` for the database name, and `user` for the username.

The `config.json` file must consist of a root JSON object, and the following mandatory fields:

| Identifier | Data Type | Description |                              
| :-- | :-- | :-- |
| `client_id` | `int` | The bot's client/user ID. |
| `token` | `str` | The bot's token. |
| `owner_id` | `int` | The owner's user ID. They get elevated permissions. |
| `command_prefix` | `str` | The command prefix to respond to. |
| `database` | `dict` | Contains keys for `user`, `password`, `host` and `database` used to connect to a PostgreSQL DBMS. |
