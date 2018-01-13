import enum

import PIL.Image as image
import PIL.ImageDraw as draw

import neko


class MapCoordinate(enum.Enum):
    long_lat = enum.auto()
    xy = enum.auto()


class MercatorProjection:
    """
    Holds a PIL image and allows for manipulation using longitude-latitude
    locations.

    :param map_image: the image object to use for the projection.
    """
    def __init__(self, map_image: image.Image=None):
        """
        Creates a mercator projection from the given Image object.

        This assumes that 0E,0N is at the central pixel.

        If no image is given, the default mercator bitmap is used.
        """
        if map_image is None:
            # TODO: change.
            map_image: image.Image = image.open(
                neko.relative_to_here('res/mercator-small.png')
            )
            map_image.load()

        self.image = map_image
        self.ox, self.oy = map_image.width / 2, map_image.height / 2

        # Differential of X in pixels per degree
        self.dx = map_image.width / 360

        # Differential of Y in pixels per degree
        self.dy = map_image.height / 180

    @property
    def width(self):
        return self.image.width

    @property
    def height(self):
        return self.image.height

    def swap_units(self, vertical, horizontal, input_measurement):
        """
        Converts between X,Y and Lat,Long, depending on measurement.

        :return a tuple of (x,y) or (lat,long)
        """
        if input_measurement == MapCoordinate.long_lat:
            horizontal = (horizontal * self.dx) + self.ox
            vertical = self.oy - vertical * self.dy

            return (horizontal, vertical)
        elif input_measurement == MapCoordinate.xy:
            horizontal = (horizontal - self.ox) / self.dx
            vertical = (self.oy - vertical) / self.dy
            return (vertical, horizontal)
        else:
            raise TypeError('Unknown measurement')

    def duplicate(self):
        """Deep copy the projection."""
        return MercatorProjection(self.image.copy())

    def pen(self) -> draw.ImageDraw:
        """Gets an object capable of drawing over the projection."""
        return draw.ImageDraw(self.image)


if __name__ == '__main__':
    """
    Basic test.
    """
    earth = MercatorProjection()

    # Latitude and longitude of Beijing.
    in_lat = 39.913818
    in_long = 116.4074

    print((in_lat, in_long))

    xf, yf = earth.swap_units(in_lat, in_long, MapCoordinate.long_lat)
    x, y = int(xf), int(yf)

    print((x, y))
    pen = earth.pen()
    pen.point(
        [(px, py) for px in range(x-1, x+2) for py in range(y-1, y+2)],
        (255, 0, 0)
    )

    lat, long = earth.swap_units(yf, xf, MapCoordinate.xy)
    print((lat, long))
