import neko


@neko.inject_setup
class GreeterCog(neko.Cog):
    async def on_member_join(self, member):
        general = neko.find(
            lambda c: c.name == 'general', member.guild.channels
        )

        if general:
            await general.send(
                f'Welcome to {member.guild}, {member.mention}!'
            )

    async def on_member_remove(self, member):
        general = neko.find(
            lambda c: c.name == 'general', member.guild.channels
        )

        if general:
            await general.send(
                f'Oh no! {member.display_name} just left \N{CRYING CAT FACE}...'
            )

    async def on_member_ban(self, guild, user):
        general = neko.find(
            lambda c: c.name == 'general', guild.channels
        )

        if general:
            await general.send(
                f'{user.display_name} just got bent.\n'
                'https://giphy.com/gifs/H99r2HtnYs492'
            )

