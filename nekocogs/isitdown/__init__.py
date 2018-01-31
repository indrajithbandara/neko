"""
Gets the status of various APIs for different online services.
"""
import neko
import neko.other.perms as perms

from . import discord
from . import steam

sub_cogs = [steam.SteamStatusNut, discord.DiscordServiceStatusNut]


class ApiStatusCog(neko.Cog):
    """Collects other cogs' commands for API statuses."""
    permissions = perms.Permissions.NONE

    def __init__(self):
        for cog in sub_cogs:
            self.logger.info(f'Metamorphosing with {cog.__name__}')
            cog_obj = cog()
            self.permissions |= getattr(cog_obj, 'permissions', 0)
            [self.group.add_command(c) for c in cog_obj.commands()]

    @neko.group(
        name='status',
        invoke_without_command=True,
        brief='Tells you if various services are down.',
        usage='|steam|tf2|discord'
    )
    async def group(self, ctx):
        """
        A command group holding a collection of commands for querying
        the status of various online services.
        """
        book = neko.PaginatedBook(title='Available sub-commands', ctx=ctx)

        for command in sorted(self.group.commands, key=lambda c: c.name):
            book.add_line(f'**{command.name}** - {command.brief}')

        await book.send()


setup = ApiStatusCog.mksetup()
