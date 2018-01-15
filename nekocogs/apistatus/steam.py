"""
Gets the API status of various steam services.

Documentation: https://steamgaug.es/docs

API endpoint: https://steamgaug.es/api/v2
"""
import traceback
import sys

import discord

import neko


api_endpoint = 'https://steamgaug.es/api/v2'

steam_core_services = {
    'ISteamClient',
    'SteamCommunity',
    'SteamStore',
    'ISteamUser',
}

service_names = {
    'ISteamClient': 'Steam Client API',
    'SteamCommunity': 'Community API',
    'SteamStore': 'Steam Store',
    'ISteamUser': 'User API',
    'ITFSystem_440': 'TF2 System',
    'IEconItems': 'Item Servers',
    'ISteamGameCoordinator': 'Game Coordinator'
}

game_icon = 'http://cdn.edgecast.steamstatic.com/steamcommunity/public/images' \
            '/avatars/6f/6f9b7a6739b06a8ec55d55ef4131782ab2a0f0af.jpg'

game_thumbs = {
    'steam': 'https://upload.wikimedia.org/wikipedia/commons/thumb/8/83'
             '/Steam_icon_logo.svg/120px-Steam_icon_logo.svg.png ',
    'tf2': 'http://media.steampowered.com/apps/tf2/artwork/thumb_exp_date_2'
           '.jpg',
    'dota2': 'http://cdn.dota2.com/apps/dota2/images/blog/play/dota_logo.png',
    'csgo': 'http://cdn3.avgleague.com/wp-content/uploads/2014/08/csgo-logo.png'
}

steam_color = 0x171a21


def unrecognised_field(response, field):
    """Saves dup'ing code."""
    print(response, file=sys.stderr)
    raise PendingDeprecationWarning('The API might have changed. '
                                    f'What is "{field}"?')


def parse_generic_field(response, key, value):
    """Tries to make sense of a generic key-value pair."""
    if key == 'time':
        key = 'Latency'
        value = f'{value}ms'
    elif key == 'online':
        key = 'Status'
        value = 'OK' if value == 1 else 'Degraded'
    elif key == 'error':
        if value is not None and value == 'No Error':
            return None
        else:
            if value is None:
                value = 'No info given!'

            key = 'Error message'
    else:
        unrecognised_field(response, key)

    return f'**{key}**: {value}'


def parse_stat_list(stat_dict):
    """Parses a simple list of game stats to a multiline string."""
    stats = []
    for stat_k, stat_v in stat_dict.items():
        if not stat_v:
            continue
        elif isinstance(stat_v, (float, int)):
            stat_v = f'{stat_v:,}'
        stats.append(f'**{neko.underscore_to_space(stat_k)}**: {stat_v}')

    return '\n'.join(stats if stats else ['No stats'])


async def get_status(bot):
    """Gets a dict of the status information."""
    response = await bot.request('GET', api_endpoint)
    obj = await response.json()
    assert isinstance(obj, dict)
    return obj


class SteamStatusNut(neko.Cog):
    permissions = (neko.Permissions.SEND_MESSAGES |
                   neko.Permissions.ADD_REACTIONS |
                   neko.Permissions.READ_MESSAGES |
                   neko.Permissions.MANAGE_MESSAGES)

    @neko.command(brief='Gets the Steam API status.')
    async def steam(self, ctx):
        """
        Replies to the given context with the steam status as a formatted embed.
        """

        # Format the response.
        embed = discord.Embed(
            title='Steam API status',
            color=steam_color,
            url='https://steamgaug.es'
        )

        embed.set_footer(
            text='Powered by SteamGauges API v2',
            icon_url=game_icon
        )

        embed.set_thumbnail(url=game_thumbs['steam'])

        with ctx.typing():
            resp = await get_status(ctx.bot)

        for service in steam_core_services:
            if service not in resp:
                unrecognised_field(resp, service)

            service_name = service_names[service]
            data = resp[service]

            strings = []

            for k, v in data.items():
                val = parse_generic_field(resp, k, v)
                if val:
                    strings.append(val)

            if not strings:
                strings = ['No data']

            embed.add_field(
                name=service_name,
                value='\n'.join(strings)
            )

        await ctx.send(embed=embed)

    @neko.command(brief='Gets the CSGO API status.')
    async def csgo(self, ctx):
        embed = discord.Embed(
            title='CS:GO API status',
            color=steam_color,
            url='https://steamgaug.es'
        )

        embed.set_footer(
            text='Powered by SteamGauges API v2',
            icon_url=game_icon
        )

        embed.set_thumbnail(url=game_thumbs['csgo'])

        with ctx.typing():
            resp = await get_status(ctx.bot)

        item_server_str = []
        for k, v in resp['IEconItems']['730'].items():
            val = parse_generic_field(resp, k, v)
            if val:
                item_server_str.append(val)

        coordinator_str = []
        for k, v in resp['ISteamGameCoordinator']['730'].items():
            if k == 'stats':
                embed.add_field(
                    name='Stats',
                    value=parse_stat_list(v),
                    inline=False
                )
            else:
                val = parse_generic_field(resp, k, v)
                if val:
                    coordinator_str.append(val)

        embed.add_field(
            name=service_names['IEconItems'],
            value='\n'.join(item_server_str
                            if item_server_str else ['No data']),
        )

        embed.add_field(
            name=service_names['ISteamGameCoordinator'],
            value='\n'.join(coordinator_str
                            if coordinator_str else ['No data']),
        )

        await ctx.send(embed=embed)

    @neko.command(brief='Gets the Dota 2 API status.', aliases=['dota'])
    async def dota2(self, ctx):
        embed = discord.Embed(
            title='Dota 2 API status',
            color=steam_color,
            url='https://steamgaug.es'
        )

        embed.set_footer(
            text='Powered by SteamGauges API v2',
            icon_url=game_icon
        )

        embed.set_thumbnail(url=game_thumbs['dota2'])

        with ctx.typing():
            resp = await get_status(ctx.bot)

        item_server_str = []
        for k, v in resp['IEconItems']['570'].items():
            val = parse_generic_field(resp, k, v)
            if val:
                item_server_str.append(val)

        coordinator_str = []
        for k, v in resp['ISteamGameCoordinator']['570'].items():
            if k == 'stats':
                embed.add_field(name='Stats', value=parse_stat_list(v))
            else:
                val = parse_generic_field(resp, k, v)
                if val:
                    coordinator_str.append(val)

        embed.add_field(
            name=service_names['IEconItems'],
            value='\n'.join(item_server_str
                            if item_server_str else ['No data']),
        )

        embed.add_field(
            name=service_names['ISteamGameCoordinator'],
            value='\n'.join(coordinator_str
                            if coordinator_str else ['No data']),
        )

        await ctx.send(embed=embed)

    @neko.command(brief='Gets the Team Fortress 2 API status.')
    async def tf2(self, ctx):
        # Format the response.
        embed = discord.Embed(
            title='Team Fortress 2 API status',
            color=steam_color,
            url='https://steamgaug.es'
        )

        embed.set_footer(
            text='Powered by SteamGauges API v2',
            icon_url=game_icon
        )

        embed.set_thumbnail(url=game_thumbs['tf2'])

        with ctx.typing():
            resp = await get_status(ctx.bot)

        coordinator_str = []
        coordinator = resp['ISteamGameCoordinator']['440']

        for k, v in coordinator.items():
            if k == 'schema':
                continue
            elif k == 'stats':
                try:
                    # This may change periodically, so I may have to alter this!
                    war = coordinator[k]['warScore']

                    war_name = 'War: Pyro vs Heavy'
                    summary = ''

                    for side in war:
                        name = 'Pyro' if side['side'] == 0 else 'Heavy'
                        score = side['score']['low']
                        summary += f'**{name}**: {score:,}\n'

                    embed.add_field(name=war_name, value=summary)
                except BaseException:
                    traceback.print_exc()
                    continue
            else:
                val = parse_generic_field(resp, k, v)
                if val:
                    coordinator_str.append(val)

        if not coordinator_str:
            coordinator_str = ['No data']

        embed.add_field(
            name=service_names['ISteamGameCoordinator'],
            value='\n'.join(coordinator_str),
        )

        stress_test = resp['ITFSystem_440']['stress_test']
        stress_test = 'Yes' if stress_test else 'No'

        item_server_str = []
        for k, v in resp['IEconItems']['440'].items():
            val = parse_generic_field(resp, k, v)
            if val:
                item_server_str.append(val)

        if not item_server_str:
            item_server_str = ['No data']

        embed.add_field(
            name=service_names['IEconItems'],
            value='\n'.join(item_server_str),
        )

        embed.add_field(
            name='Currently being stress tested?',
            value=stress_test,
        )

        await ctx.send(embed=embed)
