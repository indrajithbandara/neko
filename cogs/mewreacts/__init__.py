"""
A bunch of catgirl reaction PNGs. I thought they were cool. Sue me.

Todo: find and cite author. These are awesome!
"""
import os
import random
import traceback

import discord

import neko


# Relative to this directory.
bindings_file = neko.relative_to_here('bindings.json')
assets_directory = neko.relative_to_here('assets')


# @neko.with_verbosity('DEBUG')
class MewReactsCog(neko.Cog):
    """Reactions cog."""

    permissions = (
            neko.Permissions.READ_MESSAGES |
            neko.Permissions.SEND_MESSAGES |
            neko.Permissions.MANAGE_MESSAGES |
            neko.Permissions.ATTACH_FILES
    )

    def __init__(self):
        bindings = neko.load_or_make_json(bindings_file)

        # Attempt to locate all files to ensure paths are valid.
        potential_targets = set()
        for im_list in bindings.values():
            [potential_targets.add(im) for im in im_list]

        targets_to_path = {}

        for target in potential_targets:
            path = os.path.join(assets_directory, target)
            if os.path.exists(path) and os.path.isfile(path):
                self.logger.debug(f'Discovered {path}.')
                targets_to_path[target] = path
            else:
                self.logger.warning(f'Could not find {path}. Excluding image.')

        self.images = {}

        for react_name, binding_list in bindings.items():
            valid_list = []
            for image in binding_list:
                if image in targets_to_path and image not in valid_list:
                    valid_list.append(targets_to_path[image])

            if not valid_list:
                self.logger.warning(f'I am disabling {react_name} due to lack '
                                    'of _existing_ files.')
            else:
                self.images[react_name.lower()] = valid_list

    @neko.command(
        name='mew',
        brief='A bunch of reaction images I liked. Call with no argument for '
              'usage info.',
        usage='|GG|Sleepy|etc',
        aliases=['mewd'])
    @neko.cooldown(rate=3, per=120, type=neko.CooldownType.channel)
    async def post_reaction(self, ctx: neko.Context, *, react_name=''):
        """
        Posts a reaction. Run without any commands to see a list of reactions.

        Run `mewd` to destroy the calling message.
        """
        react_name = react_name.lower()

        # If the react is there, then send it!
        if react_name and react_name in self.images:
            try:
                if ctx.invoked_with == 'mewd':
                    await ctx.message.delete()
                file_name = random.choice(self.images[react_name])
                await ctx.send(file=discord.File(file_name))
            except discord.Forbidden:
                ctx.command.reset_cooldown(ctx)
            except FileNotFoundError:
                ctx.command.reset_cooldown(ctx)
                traceback.print_exc()
                raise neko.NekoCommandError('Something broke and the dev was '
                                            'shot. Please try again later ^w^')
        # Otherwise, if the react doesn't exist, or wasn't specified, then
        # list the reacts available.
        else:
            book = neko.PaginatedBook(title='Available reactions', ctx=ctx)
            book.add_lines(map(lambda n: f'- `{n}`', sorted(self.images)))
            await book.send()

            # Reset the cool down.
            ctx.command.reset_cooldown(ctx)


setup = MewReactsCog.mksetup()
