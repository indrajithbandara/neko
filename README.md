# Nekozilla
A small bot for Discord servers to provide some useful fun commands and features.

## What does it do?

Currently, the following commands exit:

- `big`, `bigd` - returns input text in BIG LETTERS WITH COMBINING KEYCAPS.
- `charcode` - takes a UTF-8 character code and displays info about it.
- `charinfo` - takes a UTF-8 character and displays info about it.
- `charlookup` - takes a UTF-8 character description and shows info about it.
- `colour` - various utilities for playing with colour schemes.
    - `colour byte` - takes RGB or RGBA values between `0` and `255` and displays a
        preview of that colour.
    - `colour cmyk` - takes four values between `0` and `1` and displays a preview of
        the CMYK representation of that colourspace.
    - `colour float` - takes RGB or RGBA values between `0` and `1` and displays a 
        preview of that colour.
    - `colour hex` - takes a 3 or 6 character hexadecimal representation of an RGB
        colour and displays a preview of it.
    - `colour hsl` - takes 3 digits and displays the HSL representation.
    - `colour hsv` - takes 3 digits and displays the HSV representation.
    - `colour name` - takes an HTML colour name and displays it.
    - `colour random` - displays a random colour.
    - `colour palette` - takes multiple hex and HTML colour codes and generates a
        palette of those colours, displaying it.
- `cpp` - searches http://en.cppreference.com for a search term.
- `def` - uses the Wordnik API to find definitions for words.
- `f` - _press F to pay respects._
- `help` - comprehensive paginated help utility.
- `iss` - displays information and a generated preview of the current location of the
    international space station.
- `lmgtfy`, `lmgtfyd` - takes a search term and generates a link that sends the user to
    http://lmgtfy.com to satisfy the answer to their dumb question. 
- `mew` - displays a given reaction emote.
- `rtd` - rolls the dice. You can specify how many dice to roll, and how many sides the
    dice should have.
- `rtfs` - read the fine source. This is part of a module that indexes the entire
    namespace of the bot in the background on startup, and generates the links to the
    source code on the line the token is declared on, on GitHub.
- `rtfs_recache` - recaches the source.
- `say`, `sayd` - says stuff.
- `status csgo` - gives the status of CS:GO servers.
- `status discord` - gets some comprehensive service status info for Discord.
- `status dota` - gives the status of Dota2 servers.
- `status steam` - gets the status of vital Steam services.
- `status tf2` - gets the status of Team Fortress 2 services.
- `sudo` - owner-only commands for bot management.
    - `health` - gives info on resource usage for the bot process.
    - `invite` - DMs you an invite link to join the bot to a new guild. This calculates
        permission bits.
    - `list_cogs` - lists loaded cogs.
    - `list_commands` - lists commands loaded by cogs.
    - `list_extensions` - lists extensions that have been loaded.
    - `load` - dynamically loads a Cog that has been imported, or an extension given
        a fully qualified module identifier relative to the root directory of the
        repository.
    - `ping` - replies `pong`. Quick test to ensure the bot is up.
    - `reset_cooldown` - clears any current cooldowns registered for a command.
    - `set_bot_verbosity` - alters the level of logging by the bot.
    - `set_cog_verbosity` - alters the level of logging for a loaded cog.
    - `stop` - kills the bot. If you run the bot as a `systemd` service like I do, then
        this has the effect of restarting the bot.
    - `tb` - gets the full traceback of the last unhandled exception to occur.
    - `test_raise` - tests raising a given number of nested exceptions to test bot
        behaviour and error handling.
    - `unload` - unloads the given loaded cog or extension. See `load`.
    - `update` - runs the `./update` script in the root directory of this repo. This
        will call `git stash` to stash any local changes to the bot source, and then
        perform a `git pull --all` to this repository to download any updates. The
        bot will then attempt to unstash any changes made with `git stash pop` and 
        will print out comprehensive `git diff` information on what has changed. A 
        printout of the total lines of code (for my own interest) is also generated.
        Since I run the bot on a `systemd` service, I can then run `sudo stop` to 
        invoke restarting the bot process. This allows me to deploy any changes to
        the code from anywhere without SSH access to my host.
    - `uptime` - gets bot uptime.
- `tag` - tag system for storing arbitrary strings of text, and single files up to 4MiB
    in size, for later retrieval. General users can only store tags per guild, however,
    a set of owner-only `global` commands exist in this namespace to allow the owner
    to add, edit, remove and promote commands to be recognised globally on any guild.
    Users can also edit and remove their own tags, and view a list of their tags. An
    `inspect` command allows the owner to inspect who made a tag and where, as well as
    when it was last edited.
- `tb` - see `sudo tb`.
- `toss` - tosses a coin, or given two or more strings (quote to prevent delimiting on 
    spaces), the bot picks between the inputs, outputting one of the options as the
    result.
- `ud` - searches Urban Dictionary for the given term, or if no term is specified,
    this fetches a random Urban Dictionary definition.
- `whisper`, `whisperd` - whispers text in very small letters.
- `xkcd` - gets the given XKCD comic, given a comic number. If no number is specified,
    then the most recent comic is fetched instead.

## Other features

- Bot delegates blocking tasks to background threads to improve throughput, and will
    safely output any errors that occur in a user-friendly and non intrusive manner.
- Bot can run without given API tokens, and without a Postgres database without
    malfunctioning.
- All database connections are handled by a delegated connection pool.
- All cogs are safely unloaded on interrupting or ending the process.
- Help is autogenerated and will give results relative to who called it, and where.
    For example, the ordinary user cannot view information about any command in the
    `sudo` command group.
- The bot detects any common unit measurements within a string of text, and will
    attempt to output some useful conversions. This is useful especially for
    metric and imperial measurements of speed/distance/weight, and for 
    fahrenheit/celcius/kelvin measurements. This is fully automated, and the output
    can be dismissed by anyone if it is intrusive.
    
![Example of unit conversion](conv.png)    
    
- The bot displays periodically a random command that can be run in it's status,
    prompting users to try it out.
- If a user on mobile tries to use the `/shrug`, `/tableflip` or `/unflip` macros
    that are only available on desktop, then the bot will reply with that macro's 
    expected result.

## Dependencies

To install and set up any dependencies that do not need custom configuration, run the `install-dependencies.py` script.

### Python 3.6.4
- [`Discord.py`](https://github.com/rapptz/discord.py/tree/rewrite) (rewrite branch) - Main API library for interacting 
    with the Discord Bot Gateway.\*\*
- [`aiofiles`](https://github.com/Tinche/aiofiles) - Asyncio integration for non-blocking file IO.\*
- [`aiohttp`](https://github.com/aio-libs/aiohttp) - Asyncio integration for HTTP requests.\*
- [`asyncpg`](https://github.com/MagicStack/asyncpg) - Asyncio wrapper for PostgreSQL.\*
- [`pillow`](https://pillow.readthedocs.io/en/5.0.0/) - Python Image Library (PIL) support.\*
- [`wordnik-py3`](https://github.com/wordnik/wordnik-python3) - Wordnik Python3 API wrapper.\*
- [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/) - BeautifulSoup HTML data pull-outer.\*
- [`html5lib`](https://html5lib.readthedocs.io/en/latest/) - The chosen HTML5 parser for beautiful soup.\*

<small>*\* These dependencies are available directly from PyPI using the `pip` command*</small>

<small>*\*\* At the current time, this library is __not__ available on PyPI. See following section*</small>

### Installing Discord.py

Do __not__ run `python3.6 -m pip install discord`. This will install the __wrong__ version.

Instead, run one of the following:
```bash
# Windows users
py -3.6 -m pip install -U https://github.com/rapptz/discord.py/zipball/rewrite

# Unix users
python3.6 -m pip install -U git+https://github.com/rapptz/discord.py@rewrite

# Scrubby Unix users without Git or Git-core (git gud --scrub)
python3.6 -m pip install -U https://github.com/rapptz/discord.py/tarball/rewrite
```

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

| Identifier | Data TokenType | Description |                              
| :-- | :-- | :-- |
| `client_id` | `int` | The bot's client/user ID. |
| `token` | `str` | The bot's token. |
| `owner_id` | `int` | The owner's user ID. They get elevated permissions. |
| `command_prefix` | `str` | The command prefix to respond to. |
| `database` | `dict` | Contains keys for `user`, `password`, `host` and `database` used to connect to a PostgreSQL DBMS. |
