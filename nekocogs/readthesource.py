"""
Lists source code files used in this project and generates URLs to the source
on GitHub.

This works by crawling through every file and directory with a python extension
recursively in the neko and nekocogs modules, discarding pycache. We then
dynamically load each module or retrieve the cached version if it was already
loaded, and then resolve line numbers to each element we find. This is done
largely by methods in the ``inspect` module.

We then generate URLs to the appropriate files on GitHub using a standard
URL template, and store them in a map for retrieval later.

This will only work if we have ``git`` installed and in the PATH, and if we
are on a valid branch in a valid git directory.

This should work regardless of where the current working directory is placed
also, as it uses the neko module as a start point.

This is still highly experimental and probably buggy code. But I thought it
would be an interesting feature none-the-less.
"""
import asyncio
import copy
import inspect
import os
import shutil
import subprocess
import time

import discord.ext.commands as commands

import neko


# @neko.with_verbosity('DEBUG')
@neko.inject_setup
class ReadTheSourceCog(neko.Cog):
    """
    Redirects people to the source code on GitHub, given a module name, or
    loaded cog name.

    The requirements are that the neko and nekocogs modules are in the same
    directory, and there is a valid git repository there additionally.
    """

    # These are relative to the parent directory of the neko package.
    _start_nodes = {'neko', 'nekocogs', 'nssm', 'nssm_unit_tests'}

    def __init__(self, bot: neko.NekoBot):
        self.index = {}
        self.bot = bot
        self.is_ready = False

    async def on_connect(self):
        """
        Caches the first time we connect only.
        """
        if not self.is_ready:
            await self.__cache()

    async def __cache(self):
        """
        This crawls and indexes the files. To speed this up, we will do this
        in a separate thread once the bot has connected, as only then do we
        assume all files have been loaded into the internal module cache.

        Time taken to finish, and number of cached elements is returned in a
        tuple of (time, cached_num)
        """
        # Wait a little longer for stuff to warm up. This will also prevent
        # slowing the bot down immediately on startup to do this work and wait
        # until the bot is idle.

        await asyncio.sleep(2)

        def do_work():
            start_time = time.time()
            self.__crawl()
            total_time = time.time() - start_time
            self.logger.info(f'Indexing took {total_time:.3f}s and matched '
                             f'{len(self.index)} objects.')
            self.is_ready = True
            return total_time
        return await self.bot.do_job_in_pool(do_work), len(self.index)

    @neko.command(
        name='rtfs',
        aliases=['code'],
        brief='Directs you to my source code.')
    async def read_my_code(self, ctx, element_name):
        """
        Takes a module name, and optional class/member name, and return a
        URL to the source on GitHub.
        """
        if not self.is_ready:
            await ctx.send('Hang on! I am still warming up. Give it a minute '
                           'and try again!')
        elif element_name not in self.index:
            await ctx.send('I can\'t find the file you want. Try searching at '
                           + neko.__repository__)
        else:
            await ctx.send(self.index[element_name])

    @neko.command(
        name='rtfs_recache',
        brief='Recaches the code.',
        hidden=True
    )
    @commands.is_owner()
    async def recache_code(self, ctx):
        self.logger.info('Remote request by owner to recache.')
        with ctx.typing():
            t, num = await self.__cache()
        await ctx.send(f'Cached {neko.pluralise(num, "item")} in '
                       f'{neko.pluralise(t*1000, "millisecond")}.')

    def __crawl(self):
        """
        Attempts to populate the index map in this object with module and
        fully-qualified member names mapping to the appropriate GitHub source
        code URLs. This relies on the __repository__ member of Neko being set,
        Git being installed, and the code being in a Git repository.
        """
        # Get the neko package. This is a better assumption than that the
        # bot is running from the working directory that it exists in.
        base = os.path.join(
            os.path.dirname(
                inspect.getfile(neko)
            ),
            os.pardir
        )

        base = os.path.normpath(base)

        target_nodes = {
            os.path.normpath(os.path.join(base, node))
            for node in self._start_nodes
        }

        if not all(os.path.exists(node) for node in target_nodes):
            raise ModuleNotFoundError(
                'One or more modules were not found. Cannot index.'
            )

        # Assert git is available.
        if not shutil.which('git'):
            raise FileNotFoundError('Git is not installed or accessible.')

        # Assert is a git repo. This command outputs "true" if it is a git
        # repo.
        try:
            git_dir = subprocess.check_output(
                ['git', 'rev-parse', '--git-dir'],
                cwd=base,
                shell=False,
                universal_newlines=True
            ).strip()

            assert git_dir
        except subprocess.CalledProcessError or AssertionError:
            raise FileNotFoundError('Not in a git repository')
        else:
            self.logger.info(f'Is a git repository (detected `{git_dir}`)')

        try:
            branch = subprocess.check_output(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=base,
                shell=False,
                universal_newlines=True
            ).strip()

            assert branch
        except subprocess.CalledProcessError or AssertionError as ex:
            raise RuntimeError(ex)
        else:
            self.logger.info(f'Detected current branch as `{branch}`')

        self.logger.info(
            f'Walking source tree in {" ".join(self._start_nodes)} '
            f' starting at {base}, ignoring sym-links.'
        )

        potential_files = set()

        # Walk the file tree. Attempt to find python source code files!
        for start_node in target_nodes:
            for dirpath, dirnames, filenames in os.walk(start_node):
                if '__pycache__' in dirnames:
                    self.logger.debug(f'Dropping __pycache__ in {dirpath}')
                    dirnames.remove('__pycache__')

                # Drop any files without python extensions
                for file in filenames:
                    if not any(file.endswith(ext)
                               for ext in neko.python_extensions):
                        self.logger.debug(f'Dropping non-python file {file} '
                                          f'in path {dirpath}')
                    else:
                        path = os.path.join(dirpath, file)
                        self.logger.debug(f'Found file {path}')
                        potential_files.add(path)

                self.logger.debug(f'Walking {dirpath}. Found {len(dirnames)} '
                                  f'dirs, {len(filenames)} files to inspect.')

        self.logger.info('Successfully recursed file tree and found '
                         f'{len(potential_files)} files to attempt to index.')

        # Contains a set of keys mapping module name to values of 2-tuples.
        # These tuples contain the file name and the line number of said
        # element.
        file_index = {}

        def index_member(_module, _member, _name, _mod_name=None):
            # _mod_name has to be specified if we are not indexing a member
            # that is a direct child of a module, e.g. a class method. My
            # crappy code here means that if the latter is true, we get
            # incorrect module names otherwise.

            # Get the line number it is declared on.
            module_name = (_module.__name__ if not _mod_name else _mod_name)

            member_name = f'{module_name}.{_name}'

            # If we have a class, recurse to index that...
            if inspect.isclass(_member):
                for sub_member_name, sub_member in inspect.getmembers(_member):
                    if not sub_member_name.startswith('_'):
                        index_member(_member,
                                     sub_member,
                                     sub_member_name,
                                     member_name)

            try:
                _, _line = inspect.getsourcelines(_member)
                file_name = inspect.getfile(_member)

                # Get relative path
                file_name = os.path.relpath(file_name, base)

                # If the relative path begins with .., then we assume
                # it is outside the source tree, so we choose to drop it
                if file_name.startswith(os.pardir):
                    self.logger.debug(f'Dropping {file_name} as outside '
                                      'source tree.')
                    return
                if not any(file_name.startswith(s)
                           for s in self._start_nodes):
                    self.logger.debug(f'Dropping {file_name} as it is not '
                                      'in the chosen index directories.')
                    return
            except OSError as exc:
                self.logger.debug(
                    f'OSError when inspecting {name} in {module.__name__} '
                    f'with message {exc}'
                )
            except TypeError:
                self.logger.debug(f'Giving up on {name} in {rel_path}')
            else:
                self.logger.debug(f'Indexed {member_name} in {file_name}')
                file_index[member_name] = (file_name, _line)

        # Attempt to index the files. Use a shallow copy to enable resizing
        # of original set mid-iteration.
        for file in copy.copy(potential_files):
            rel_path = os.path.relpath(file, base)

            self.logger.debug(f'Inspecting {file} for module...')
            module = inspect.getmodule(None, _filename=file)

            if module is None:
                self.logger.debug(f'Dropping {file}')
                potential_files.remove(file)
                continue
            else:
                self.logger.debug(f'Indexing {file}')

            file_index[module.__name__] = (rel_path, 0)

            for name, member in inspect.getmembers(module):
                index_member(module, member, name)

        # Generate GitHub URLS
        repo = neko.__repository__
        self.logger.info(f'Using {repo} as base for URL generation.')

        for name, (file, line) in file_index.items():
            url = f'{repo}/blob/{branch}/{file}'

            if line > 0:
                url += f'#L{line}'
            self.logger.debug(f'Pointing {name} to {url}')
            self.index[name] = url
