# Nekozilla
A small bot for Discord servers to provide some useful fun commands and features.

## Dependencies

### Python 3.6
- [`Discord.py`](https://github.com/rapptz/discord.py) (rewrite)
- `wordnik-py3` - Wordnik Python3 API wrapper.\*

<small>*\* These dependencies are available directly from PyPi using the `pip` command*</small>

## Configuration

The bot will read a file called `config.json` from the current working directory.

This file must consist of a root JSON object, and the following mandatory fields

| Identifier | Data Type | Description |                              
| :-- | :-- | :-- |
| `client_id` | `int` | The bot's client/user ID. |
| `token` | `str` | The bot's token. |
| `owner_id` | `int` | The owner's user ID. They get elevated permissions. |
| `command_prefix` | `str` | The command prefix to respond to. |
| `database` | `dict` | Contains keys for `user`, `password`, `host` and `database` used to connect to a PostgreSQL DBMS. |
