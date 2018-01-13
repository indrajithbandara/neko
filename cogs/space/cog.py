"""
Cog to hold commands.
"""
import datetime
import io

import discord
import PIL.Image

import neko

from . import coordinate


class SpaceCog(neko.Cog):
    async def plot(self, latitude, longitude, bytesio):
        """
        Plots a longitude and latitude on a given mercator projection.

        :param latitude: the latitude.
        :param longitude: the longitude.
        :param bytesio: the bytes IO to dump PNG data to.
        """
        def _plot():
            mercator = coordinate.MercatorProjection()

            x, y = mercator.swap_units(
                latitude,
                longitude,
                coordinate.MapCoordinate.long_lat
            )

            x, y = int(x), int(y)

            pen = mercator.pen()

            """
            pixels = [
                (x - 1, y - 1), (x - 1, y + 1),
                (x, y),
                (x + 1, y - 1), (x + 1, y + 1),
            ]

            pen.point([(x % mercator.width, y) for x, y in pixels], (255, 0, 0))
            """
            pen.ellipse([(x-4, y-4), (x+4, y+4)], (255, 0, 0))

            return mercator.image
        image: PIL.Image.Image = await neko.no_block(_plot)

        image.save(bytesio, 'PNG')

        # Seek back to the start
        bytesio.seek(0)

    @neko.command(name='iss', brief='Shows you where the ISS is.')
    @neko.cooldown(1, 5 * 60, neko.CooldownType.guild)
    async def find_the_iss(self, ctx):
        """
        A very crappy and slow command to show you the ISS current location.
        """

        with ctx.channel.typing():
            # Plot the first point
            with io.BytesIO() as b:
                res = await neko.request(
                    'GET',
                    'https://api.wheretheiss.at/v1/satellites/25544'
                )

                data = await res.json()
                image_fut = self.plot(data['latitude'], data['longitude'], b)

                assert isinstance(data, dict), 'I...I don\'t understand...'

                long = data['longitude']
                lat = data['latitude']
                time = datetime.datetime.fromtimestamp(data['timestamp'])
                altitude = data['altitude']
                velocity = data['velocity']

                is_day = data['visibility'] == 'daylight'

                desc = '\n'.join([
                    f'**Longitude**: {long:.3f} °E',
                    f'**Latitude**: {abs(lat):.3f} °{"N" if lat >= 0 else "S"}',
                    f'**Altitude**: {altitude:.3f} km',
                    f'**Velocity**: {velocity:.3f} km/h',
                    f'**Timestamp**: {time} UTC'
                ])

                embed = neko.Page(
                    title='International space station location',
                    description=desc,
                    color=0xFFFF00 if is_day else 0x0D293B,
                    url='http://www.esa.int/Our_Activities/Human_Spaceflight'
                        '/International_Space_Station'
                        '/Where_is_the_International_Space_Station '
                )

                embed.set_footer(text='Data provided by whereistheiss.at')

                await image_fut
                file = discord.File(b, 'iss.png')

                await ctx.send(file=file, embed=embed)
