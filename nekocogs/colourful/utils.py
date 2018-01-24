import collections
import io
import typing

import neko
import neko.other.singleton as singleton

import PIL.Image as pil_image

_pheight = 25
_pwidth = 25


_rgb = typing.Tuple[int, int, int]
_rgba = typing.Tuple[int, int, int, int]


def generate_preview(bytes_io: io.BytesIO,
                     red: int,
                     green: int,
                     blue: int,
                     alpha: int):
    """Generates a 25x25 pixel colour preview as a PNG."""
    if not all(0 <= rgba <= 255 for rgba in (red, green, blue, alpha)):
        raise ValueError(
            f'Invalid colour channel in ({red},{green},{blue},{alpha}).')

    img = pil_image.new(
        'RGBA',
        color=(red, green, blue, alpha),
        size=(_pwidth, _pheight))

    bytes_io.seek(0)
    img.save(bytes_io, 'PNG')
    bytes_io.seek(0)


def is_web_safe(r: int, g: int, b: int, a: int):
    """
    True if the rgba value is websafe.

    Cite: https://www.rapidtables.com/web/color/Web_Safe.html
    """
    if a != 255:
        return False
    else:
        return all(x in (0, 0x33, 0x66, 0x99, 0xCC, 0xFF) for x in (r, g, b))


def to_float(r: int, g: int, b: int, a: int = None):
    """Converts RGBA or RGB to float."""
    if not all(0 <= x < 256 for x in (r, g, b, a if a is not None else 255)):
        raise ValueError('Expected values in the range [0,256)')

    r = round(r / 255., 2)
    g = round(g / 255., 2)
    b = round(b / 255., 2)
    a = round(a / 255., 2) if a else None

    if a is None:
        return (r, g, b)
    else:
        return (r, g, b, a)


def from_float(r: float, g: float, b: float, a: float=None):
    """Parses from float to int values."""
    # Validates and parses the inputs to the correct type.
    r, g, b = float(r), float(g), float(b)
    if a is not None:
        a = float(a)

    if not all(0 <= x <= 1 for x in (r, g, b, a if a is not None else 1)):
        raise ValueError('Expected values in the range [0,1]')

    else:
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        a = int(a * 255) if a is not None else a

        if a is not None:
            return (r, g, b, a)
        else:
            return (r, g, b)


def to_hex(r: int, g: int, b: int, _a: int=None, *, prefix='#'):
    """
    Takes RGBA colour values from 0 to 255, and generates a hex
    representation. Note the alpha channel is ignored, and is optional.
    :param r: red channel
    :param g: green channel
    :param b: blue channel
    :param _a: the alpha channel. Optional, and isn't used.
    :param prefix: what to prefix to the start. Defaults to '#'
    :return: the string generated.
    """
    r = hex(r)[2:]
    if len(r) == 1:
        r = f'0{r}'
    g = hex(g)[2:]
    if len(g) == 1:
        g = f'0{g}'
    b = hex(b)[2:]
    if len(b) == 1:
        b = f'0{b}'

    return prefix + ''.join((r, g, b))


def from_hex(cc: str) -> _rgb:
    """
    Takes a three or six digit hexadecimal RGB value and returns the value as
    a tuple of red, green and blue byte-sized ints. Each can range between 0
    and 255 inclusive.

    If a 0x or a # is on the start of the string, we ignore it, so you do not
    need to sanitise input for those.

    :param cc: the input
    :return: tuple of red, green and blue.
    """
    cc = cc.upper()
    for x in ('0x', '0X', '#'):
        cc = cc.replace(x, '')

    if len(cc) not in (3, 6) or not all(d in '0123456789ABCDEF' for d in cc):
        raise ValueError('Expected either 3 or 6 hexadecimal digits only.')
    elif len(cc) == 3:
        # FAB -> FFAABB
        cc = ''.join(2 * d for d in cc)

    # noinspection PyTypeChecker
    return tuple(int(d, 16) for d in (cc[0:2], cc[2:4], cc[4:6]))


@singleton.singleton
class HtmlNames(collections.Mapping):

    def __init__(self):
        path = neko.relative_to_here('htmlcolours.json')
        obj = neko.load_or_make_json(path, default={})
        assert isinstance(obj, dict)

        # Do this to remove case sensitivity.
        self.__data = dict()

        for name, colour in obj.items():
            assert isinstance(name, str)
            assert isinstance(colour, str)
            self.__data[name.lower()] = from_hex(colour)

        # Reverse the list for reverse lookups.
        self.__reversed = {v: k for k, v in self.items()}

    def __iter__(self):
        return iter(self.__data)

    def __len__(self) -> int:
        return len(self.__data)

    def __getitem__(self, item) -> _rgb:
        return self.__data[item.lower()]

    def __contains__(self, item) -> bool:
        return item.lower() in self.__data

    def get(self, name, default=None) -> _rgb:
        return self[name] if name in self else default

    def items(self) -> typing.Iterable[typing.Tuple[str, _rgb]]:
        return self.__data.items()

    def keys(self) -> typing.Iterable[str]:
        return self.__data.keys()

    def values(self) -> typing.Iterable[_rgb]:
        return self.__data.values()

    def from_value(self, value: (int, int, int), default=None):
        """Reverse lookup."""
        return self.__reversed.get(value, default)


# Suppresses incorrect inspections.
HtmlNames: HtmlNames = HtmlNames
