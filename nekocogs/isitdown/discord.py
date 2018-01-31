"""
Discord service status.
"""
import datetime
import re
import typing

import asyncio

import neko
import neko.other.perms as perms


endpoint_base = 'https://status.discordapp.com/api'
api_version = 'v2'

# Max fields per page on short pages
max_fields = 4


def get_endpoint(page_name):
    """Produces the endpoint URL."""
    return f'{endpoint_base}/{api_version}/{page_name}'


def get_impact_color(impact, is_global=False):
    return {
        'none': 0x00ff00 if is_global else 0x0,
        'minor': 0xff0000,
        'major': 0xffa500,
        'critical': 0xff0000,
    }.get(impact.lower(), 0x0)


def find_highest_impact(entries):
    print(entries)

    for state in ('critical', 'major', 'minor', 'none'):
        for entry in entries:
            if entry['Impact'].lower() == state:
                return state.title()
    return 'None'


def make_incident_body(incident):
    created = friendly_date(incident['Created At'])
    updated = incident.get('Updated At')
    updated = friendly_date(updated) if updated else 'N/A'
    monitoring = incident.get('Monitoring At')
    monitoring = friendly_date(monitoring) if monitoring else 'N/A'

    recent_update = incident.get('updates')
    recent_update = recent_update[0] if recent_update else None

    if recent_update:
        ru_message = f'**Most recent update**:'

        updated_at = recent_update.get('Updated At')
        created_at = recent_update.get('Created At')
        body = recent_update.get('Body')

        if updated_at:
            ru_message += f'\n- Last updated at {friendly_date(updated_at)}'
        elif created_at:
            ru_message += f'\n- Created at {friendly_date(created_at)}'

        ru_message += f'\n{body}'

    return (
        f'**Status**: {incident["Status"]}\n'
        f'**Created**: {created}\n'
        f'**Updated**: {updated}\n'
        f'**Monitoring**: {monitoring}\n'
        f'{ru_message if recent_update else "No updates yet."}'
    )


def parse_timestamp(timestamp):
    """
    Discord use a timestamp that is not compatible with Python by
    default, which is kind of annoying.

    Expected format: YYYY-mm-ddTHH:MM:SS.sss(sss)?[+-]hh:mm

    :param timestamp: timestamp to parse.
    :return: datetime object.
    """

    if timestamp is None:
        return None

    # Remove the periods, T and colons.
    timestamp = re.sub(r'[:.T]', '', timestamp, flags=re.I)

    # extract the date part and time part.
    if '+' in timestamp:
        dt, tz = timestamp.rsplit('+', maxsplit=1)
        tz = '+' + tz
    else:
        dt, tz = timestamp.rsplit('-', maxsplit=1)
        tz = '-' + tz

    # Remove hyphens from date (we didn't want to mess up the timezone earlier)
    dt = dt.replace('-', '')

    expected_dt_len = len('YYYYmmddHHMMSSssssss')
    # Append zeros onto the end to make it in microseconds.
    dt = dt + ('0' * (expected_dt_len - len(dt)))

    timestamp = dt + tz
    return datetime.datetime.strptime(timestamp, '%Y%m%d%H%M%S%f%z')


def friendly_date(value: datetime.datetime):
    """Creates a friendly date format for the given datetime."""

    if value is None:
        return 'N/A'

    day = neko.pluralise(value.day, method='th')
    rest = value.strftime('%B %Y at %H:%M %Z')
    return f'{day} {rest}'


class DiscordServiceStatusNut(neko.Cog):
    """
    Holds the service status command.
    """
    permissions = (perms.Permissions.SEND_MESSAGES |
                   perms.Permissions.ADD_REACTIONS |
                   perms.Permissions.READ_MESSAGES |
                   perms.Permissions.MANAGE_MESSAGES)

    @neko.command(
        brief='Check if Discord is down (again)'
    )
    async def discord(self, ctx: neko.Context):
        """
        Gets a list of all Discord systems, and their service
        status.

        Lists of upcoming scheduled maintenances and unresolved
        incidents will be implemented eventually.
        """
        book = neko.Book(ctx)

        async with ctx.message.channel.typing():

            bot = ctx.bot

            """
            status = await self.get_status(bot)
            components = await self.get_components(bot)
            incidents = await self.get_incidents(bot)
            sms = await self.get_scheduled_maintenances(bot)
            """

            stat_res, comp_res, inc_res, sms_res = await asyncio.gather(
                bot.http_pool.get(get_endpoint('summary.json')),
                bot.http_pool.get(get_endpoint('components.json')),
                bot.http_pool.get(get_endpoint('incidents.json')),
                bot.http_pool.get(get_endpoint('scheduled-maintenances.json'))
            )

            status, components, incidents, sms = await asyncio.gather(
                self.get_status(stat_res),
                self.get_components(comp_res),
                self.get_incidents(inc_res),
                self.get_scheduled_maintenances(sms_res)
            )

            # Make the front page!
            if status['indicator'] == 'None':
                desc = ''
            else:
                desc = f'**{status["indicator"]}**\n\n'

            desc += (f'{status["description"]}\n\n'
                     f'Last updated: {friendly_date(status["updated_at"])}.')

            if not incidents['unresolved']:
                color = status['color']
            else:
                color = get_impact_color(
                    find_highest_impact(incidents['unresolved']))

            """
            PAGE 1
            ------

            Overall status
            """
            page = neko.Page(
                title='Discord API Status',
                description=desc,
                color=color,
                url=status['url']
            )

            if incidents['unresolved']:
                first = incidents['unresolved'][0]
                name = first['Name']
                body = make_incident_body(first)

                page.add_field(name=name, value=body, inline=False)

            book += page

            """
            PAGE 2
            ------

            Overall status again, but with more information on showcase
            components.
            """
            page = neko.Page(
                title='Discord API Status',
                description=desc,
                color=color,
                url=status['url']
            )

            for component in components['showcase']:
                title = component.pop('Name')
                desc = []
                for k, v in component.items():
                    line = f'**{k}**: '
                    if isinstance(v, datetime.datetime):
                        line += friendly_date(v)
                    else:
                        line += str(v)
                    desc.append(line)
                page.add_field(
                    name=title,
                    value='\n'.join(desc),
                    inline=False
                )

            book += page

            """
            PAGE 3
            ======

            Non showcase components
            """
            page = None

            fields = 0
            for component in components['rest']:
                if fields >= max_fields:
                    book += page
                    page = None
                    fields = 0

                if page is None:
                    page = neko.Page(
                        title='Other components',
                        description='Other minor components for Discord.',
                        color=color,
                        url=status['url']
                    )

                title = component.pop('Name')
                desc = []
                for k, v in component.items():
                    line = f'**{k}**: '
                    if isinstance(v, datetime.datetime):
                        line += friendly_date(v)
                    else:
                        line += str(v)
                    desc.append(line)

                page.add_field(
                    name=title,
                    value='\n'.join(desc),
                    inline=False
                )
                fields += 1

            if fields > 0:
                book += page

            """
            PAGE 3
            ======
            
            Incidents.
            """
            page = neko.Page(
                title='Unresolved incidents',
                color=color
            )

            if incidents['unresolved']:
                incident = incidents['unresolved'][0]

                name = f'**{incident["Name"]}**'
                desc = make_incident_body(incident)

                page.description = name + '\n\n' + desc.strip()

            for incident in incidents['unresolved'][1:3]:
                body = make_incident_body(incident)
                name = incident['Name']

                body = name + '\n\n' + body

                page.add_field(
                    name='\u200b',
                    value=body.strip()
                )

            book += page

            """
            PAGE 4
            ======

            Resolved incidents.
            """
            page = neko.Page(
                title='Resolved incidents',
                color=color,
            )

            if incidents['resolved']:
                incident = incidents['resolved'][0]

                name = f'**{incident["Name"]}**'
                desc = make_incident_body(incident)
                page.description = name + '\n\n' + desc.strip()

            # Add the next three most recent.
            for incident in incidents['resolved'][1:3]:
                body = make_incident_body(incident)
                name = f'**{incident["Name"]}**'

                body = name + '\n\n' + body.strip()

                page.add_field(name='\u200b', value=body)

            book += page

            await book.send()

            # TODO: maybe finish implementing this when I feel like it.

    @staticmethod
    async def get_status(res) -> typing.Dict[str, typing.Any]:
        """
        Gets the short overall status of Discord.

        :param res: the http response.
        :return: a map of:
            description - str, None
            color - int
            indicator - str
            updated_at - datetime
            url - str
        """
        res = await res.json()

        updated_at = res['page']['updated_at']
        updated_at = parse_timestamp(updated_at)

        return {
            'description': res['status']['description'],
            'color': get_impact_color(res['status']['indicator'], True),
            'indicator': res['status']['indicator'].title(),
            'updated_at': updated_at,
            'url': res['page']['url']
        }

    @staticmethod
    async def get_components(res, hide_un_degraded=True) \
            -> typing.Dict[str, typing.List]:
        """
        Gets the status of individual components of Discord.

        :param res: the http response.
        :param hide_un_degraded: defaults to true. If true, we respect the
               API's intent to hide any component marked true under
               "only_show_if_degraded" unless the component is actually
               degraded.
        :return: a dict containing two lists: 'showcase' and 'rest'.
                Both lists contain components, with fields:

                status - str
                name - str
                created_at - datetime
                updated_at - datetime
                description - str, None
        """
        res = await res.json()

        # Anything that is not set to "showcase" belongs in the
        # rest list instead.
        showcase_result = []
        rest_result = []

        components: list = res['components']
        for component in components:
            comp_dict = {}

            for k, v in component.items():
                # Skip these keys.
                if k in ('id', 'page_id', 'position', 'group',
                         'only_show_if_degraded', 'showcase', 'group_id'):
                    continue
                elif v is None:
                    continue

                friendly_key = neko.underscore_to_space(k)

                # If a date/time
                if k in ('created_at', 'updated_at'):
                    comp_dict[friendly_key] = parse_timestamp(v)
                elif k == 'status':
                    # This is always formatted with underscores (enum really)
                    comp_dict[friendly_key] = neko.underscore_to_space(v)
                else:
                    comp_dict[friendly_key] = v

            # Determine whether to skip the only-show-if-degraded element
            # if it is flagged as such.
            show_always = not component['only_show_if_degraded']
            if not show_always:
                is_degraded = component['status'] != 'operational'
                should_hide = not show_always and is_degraded
                if hide_un_degraded and should_hide:
                    continue

            if component['showcase']:
                showcase_result.append(comp_dict)
            else:
                rest_result.append(comp_dict)

        return {'showcase': showcase_result, 'rest': rest_result}

    @classmethod
    async def get_incidents(cls, res) -> typing.Dict[str, typing.List]:
        """
        Gets a dict containing two keys: 'resolved' and 'unresolved'.

        These contain incidents and incident updates.

        Due to the quantity of information this returns, we only get the
        first 5, resolved. All unresolved are returned.

        :param res: the http response.
        """
        max_resolved = 5

        res = (await res.json())['incidents']

        unresolved = []
        resolved = []

        for inc in res:
            if inc['status'] in ('investigating', 'identified', 'monitoring'):
                target = unresolved
            elif len(resolved) < max_resolved:
                target = resolved
            else:
                continue

            incident = {}

            for k, v in inc.items():
                if k in ('id', 'page_id', 'shortlink') or v is None:
                    continue

                friendly_key = neko.underscore_to_space(k)

                if k in ('updated_at', 'created_at', 'monitoring_at'):
                    incident[friendly_key] = parse_timestamp(v)
                elif k == 'incident_updates':
                    incident['updates'] = cls.__parse_incident_updates(v)
                elif k in ('impact', 'status'):
                    incident[friendly_key] = neko.underscore_to_space(v)

                else:
                    incident[friendly_key] = v

            target.append(incident)
        return {'resolved': resolved, 'unresolved': unresolved}

    @staticmethod
    def __parse_incident_updates(v):
        # Parse incident updates.
        updates = []

        if v is None:
            return updates

        for up in v:
            update = {}
            for up_k, up_v in up.items():
                up_f_k = neko.underscore_to_space(up_k)

                # Ignore custom_tweet and affected_components,
                # as we do not have any info on how these are
                # formatted...
                if up_k in ('id', 'incident_id', 'display_at',
                            'custom_tweet', 'affected_components',
                            'deliver_notifications') or up_v is None:
                    continue
                elif up_k in ('created_at', 'updated_at'):
                    if up_v is None:
                        continue
                    else:
                        update[up_f_k] = parse_timestamp(up_v)
                elif up_k == 'status':
                    update[up_f_k] = neko.underscore_to_space(up_v)
                else:
                    update[up_f_k] = up_v

            updates.append(update)
        return updates

    @staticmethod
    async def __get_active_and_scheduled_maintenances(res):
        """
        We do not care about maintenances that are done with, but this contains
        a lot of irrelevant information, so I guess we should skip what we
        don't need now.

        :param res: the response to use.
        """
        res = await res.json()
        res = res['scheduled_maintenances']

        return [r for r in res if r.get('status', None) != 'completed']
        # test: return res

    @classmethod
    async def get_scheduled_maintenances(cls, res) -> typing.List[typing.Dict]:
        """
        Gets a list of active and scheduled maintenance events.

        :param res: the response to use.
        """
        in_events = await cls.__get_active_and_scheduled_maintenances(res)

        out_events = []

        for event in in_events:
            event_obj = {}

            for k, v in event.items():
                if k in ('id', 'page_id', 'shortlink') or v is None:
                    continue

                friendly_key = neko.underscore_to_space(k)

                if k in ('created_at', 'monitoring_at',
                         'scheduled_for', 'scheduled_until',
                         'updated_at'):
                    event_obj[friendly_key] = parse_timestamp(v)
                elif k == 'incident_updates':
                    event_obj['updates'] = cls.__parse_incident_updates(v)
                elif k in ('status', 'impact'):
                    event_obj[friendly_key] = neko.underscore_to_space(v)
                else:
                    event_obj[friendly_key] = v
            out_events.append(event_obj)

        return out_events
