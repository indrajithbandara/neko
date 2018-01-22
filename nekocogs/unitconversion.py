"""
Listens for various units of measurements in messages and outputs the
conversions applicable to that measurement where applicable.

This isn't coded that well... but I cannot be arsed to re-implement this, and
it was a complete and utter bastard to get working the way I wanted...
"""
import asyncio
import collections
import copy
import enum
import re
import time
import typing

import discord

import neko
import neko.other.perms as perms


unit_pattern = \
    r'(?:\s|^)([-+]?(?:(?:\d+)\.\d+|\d+)(?:[eE][-+]?\d+)?) ?([-°^"/\w]+)(?:\b)'
unit_pattern = re.compile(unit_pattern, re.I | re.U)

ConversionToken = collections.namedtuple('ConversionToken', [
    'magnitude',
    'unit'
])


def _find_tokens(input_str: str):
    """
    Yields any substrings that are potential unit measures as
    a generator of ConversionToken tuples. Each holds
    a measure of magnitude, and a unit.

    :returns: a generator iterator.
    """
    return [
        ConversionToken(
            magnitude=float(match.group(1).replace(',', '')),
            unit=match.group(2)
        )
        for match in unit_pattern.finditer(input_str)
    ]


def _reverse_map(dictionary) -> dict:
    """
    Inverts a map of single or iterable value types.

    { a: b, c: d, } will become { b: a, d: c, }
    { a: [b, c], d: [e, f], } will become { b: a, c: a, e: d, f: d, }

    etc...
    """
    result = {}
    for k in dictionary.keys():
        v = dictionary[k]
        if isinstance(v, (list, set, frozenset, tuple)):
            for _v in v:
                result[_v] = k
        else:
            result[v] = k
    return result


@enum.unique
class Dim(enum.IntEnum):
    """Represents dimensions of measurement."""
    distance = enum.auto()
    # time = enum.auto()
    speed = enum.auto()
    force = enum.auto()
    volume = enum.auto()
    mass = enum.auto()
    temperature = enum.auto()


@enum.unique
class Unit(enum.IntEnum):
    """Represents valid units of measurement to parse."""

    # Short distances
    meter = enum.auto()
    yard = enum.auto()
    inch = enum.auto()
    foot = enum.auto()
    centimeter = enum.auto()
    millimeter = enum.auto()

    # Long distances
    kilometer = enum.auto()
    mile = enum.auto()
    nautical_mile = enum.auto()

    # Time
    # second = enum.auto()
    # minute = enum.auto()
    # hour = enum.auto()
    # day = enum.auto()
    # week = enum.auto()
    # month = enum.auto()
    # year = enum.auto()

    # Speed
    meters_per_second = enum.auto()
    kilometers_per_hour = enum.auto()
    miles_per_hour = enum.auto()
    knots = enum.auto()

    # Force
    newton = enum.auto()
    pound_force = enum.auto()

    # Volume
    meters3 = enum.auto()
    cubic_centimeters = enum.auto()
    liters = enum.auto()
    pint = enum.auto()
    uk_gal = enum.auto()
    us_gal = enum.auto()
    teaspoon = enum.auto()
    tablespoon = enum.auto()

    # Mass
    kilogram = enum.auto()
    gram = enum.auto()
    stone = enum.auto()
    pound_mass = enum.auto()
    ounce = enum.auto()
    tonne = enum.auto()
    ton = enum.auto()

    # Temperature
    kelvin = enum.auto()
    celcius = enum.auto()
    fahrenheit = enum.auto()


# Maps dimensions to their SI units.
dim2si = {
    Dim.distance: Unit.meter,
    # Dim.time: Unit.second,
    Dim.speed: Unit.meters_per_second,
    Dim.force: Unit.newton,
    Dim.volume: Unit.meters3,
    Dim.mass: Unit.kilogram,
    Dim.temperature: Unit.kelvin,
}

# Maps SI units to their dimension.
si2dim = _reverse_map(dim2si)

# Bind units to their dimensionality
dim2unit = {
    Dim.distance: [
        Unit.meter,
        Unit.yard,
        Unit.inch,
        Unit.foot,
        Unit.mile,
        Unit.kilometer,
        Unit.nautical_mile,
        Unit.centimeter,
        Unit.millimeter
    ],
    # Dim.time: [
    #     Unit.second,
    #     Unit.minute,
    #     Unit.hour,
    #     Unit.day,
    #     Unit.week,
    #     Unit.month,
    #     Unit.year,
    # ],
    Dim.speed: [
        Unit.meters_per_second,
        Unit.kilometers_per_hour,
        Unit.miles_per_hour,
        Unit.knots,
    ],
    Dim.force: [
        Unit.newton,
        Unit.pound_force,
    ],
    Dim.volume: [
        Unit.meters3,
        Unit.cubic_centimeters,
        Unit.liters,
        Unit.pint,
        Unit.uk_gal,
        Unit.us_gal,
        Unit.teaspoon,
        Unit.tablespoon,
    ],
    Dim.mass: [
        Unit.kilogram,
        Unit.gram,
        Unit.stone,
        Unit.pound_mass,
        Unit.ounce,
        Unit.tonne,
        Unit.ton,
    ],
    Dim.temperature: [
        Unit.kelvin,
        Unit.celcius,
        Unit.fahrenheit,
    ]
}

# Create a reverse mapping of each unit to their dimensionality.
unit2dim = _reverse_map(dim2unit)


# Returns the input value. Used for SI unit conversions to themselves.
def __si_u(x): return x


def __k_chk(k):
    """
    Ensures a kelvin value is not below absolute zero. If it is
    not, we raise a ValueError instead. If it is valid, we return it.
    """
    if k < 0:
        if k % 1 == 0:
            k = int(k)
        raise ValueError(f'{k}K is below absolute zero, and is invalid.')
    return k


# Converts any SI quantity to the unit.
# Input = Si; Output = Unit.
si2unit_conversion = {
    Unit.meter: __si_u,
    Unit.yard: lambda v: v * 1.09361,
    Unit.inch: lambda v: v * 39.3701,
    Unit.foot: lambda v: v * 3.28084,
    Unit.kilometer: lambda v: v * 0.001,
    Unit.mile: lambda v: v * 0.000621371,
    Unit.nautical_mile: lambda v: v * 0.000539957,
    Unit.centimeter: lambda v: v * 100,
    Unit.millimeter: lambda v: v * 1000,

    # Unit.second: __si_u,
    # Unit.minute: lambda v: v / 60,
    # Unit.hour: lambda v: v / (60 ** 2),
    # Unit.day: lambda v: v / (24 * 60 ** 2),
    # Unit.week: lambda v: v / (7 * 24 * 60 ** 2),
    # Unit.month: lambda v: v / (30 * 24 * 60 ** 2),
    # Unit.year: lambda v: v / (365 * 24 * 60 ** 2),

    Unit.meters_per_second: __si_u,
    Unit.kilometers_per_hour: lambda v: v * 3.6,
    Unit.miles_per_hour: lambda v: v * 2.23694,
    Unit.knots: lambda v: v * 1.94384,

    Unit.newton: __si_u,
    Unit.pound_force: lambda v: v * 0.224809,

    Unit.meters3: __si_u,
    Unit.cubic_centimeters: lambda v: v * 1e6,
    Unit.liters: lambda v: v * 1000,
    Unit.pint: lambda v: v * 1759.75,
    Unit.uk_gal: lambda v: v * 219.969,
    Unit.us_gal: lambda v: v * 264.172,
    Unit.teaspoon: lambda v: v * 168936,
    Unit.tablespoon: lambda v: v * 56312.1,

    Unit.gram: __si_u,
    Unit.kilogram: lambda v: v * 0.001,
    Unit.stone: lambda v: v * 0.000157473,
    Unit.pound_mass: lambda v: v * 0.00220462,
    Unit.ounce: lambda v: v * 0.035274,
    Unit.tonne: lambda v: v * 1e-6,
    Unit.ton: lambda v: v * 1.10231e-6,

    Unit.kelvin: __k_chk,
    Unit.celcius: lambda v: __k_chk(v) - 273.15,
    Unit.fahrenheit: lambda v: 9 / 5 * __k_chk(v) - 459.67,
}

# Converts unit measurements to Si measurements.
# Input = Unit; Output = Si;
unit2si_conversion = {
    Unit.meter: __si_u,
    Unit.yard: lambda v: v * 0.9144,
    Unit.inch: lambda v: v * 0.0254,
    Unit.foot: lambda v: v * 0.3048,
    Unit.kilometer: lambda v: v * 1000,
    Unit.mile: lambda v: v * 1609.34,
    Unit.nautical_mile: lambda v: v * 1852,
    Unit.centimeter: lambda v: v / 100,
    Unit.millimeter: lambda v: v / 1000,
    # Unit.second: __si_u,
    # Unit.minute: lambda v: v * 60,
    # Unit.hour: lambda v: v * 60 ** 2,
    # Unit.day: lambda v: v * 24 * 60 ** 2,
    # Unit.week: lambda v: v * 7 * 24 * 60 ** 2,
    # Unit.month: lambda v: v * 30 * 24 * 60 ** 2,
    # Unit.year: lambda v: v * 365 * 24 * 60 ** 2,
    Unit.meters_per_second: __si_u,
    Unit.kilometers_per_hour: lambda v: v * 10/36,
    Unit.miles_per_hour: lambda v: v * 0.44704,
    Unit.knots: lambda v: v * 0.514444,
    Unit.newton: __si_u,
    Unit.pound_force: lambda v: v * 4.44822,
    Unit.meters3: __si_u,
    Unit.cubic_centimeters: lambda v: v * 1e-6,
    Unit.liters: lambda v: v * 0.001,
    Unit.pint: lambda v: v * 0.000568261,
    Unit.uk_gal: lambda v: v * 0.00454609,
    Unit.us_gal: lambda v: v * 0.00378541,
    Unit.teaspoon: lambda v: v * 5.91939e-6,
    Unit.tablespoon: lambda v: v * 1.77582e-5,
    Unit.gram: __si_u,
    Unit.kilogram: lambda v: v * 1000,
    Unit.stone: lambda v: v * 6350.29,
    Unit.pound_mass: lambda v: v * 453.592,
    Unit.ounce: lambda v: v * 28.3495,
    Unit.tonne: lambda v: v * 1000000,
    Unit.ton: lambda v: v * 907185,
    Unit.kelvin: __k_chk,
    Unit.celcius: lambda v: __k_chk(v + 273.15),
    Unit.fahrenheit: lambda v: __k_chk((v + 459.67) * 5 / 9),
}

# Aliases for measurement names
# The first in this list is always used when printing out the
# value in a readable format, and should be an abbreviated value.
unit2alias = {
    Unit.meter: ['m', 'meter', 'meters'],
    Unit.centimeter: ['cm', 'centimeter', 'centimeters'],
    Unit.millimeter: ['mm', 'millimeter', 'millimeters'],
    Unit.yard: ['yd', 'yard', 'yards'],
    Unit.inch: ['inch', 'inches'],
    Unit.foot: ['ft', 'foots', 'feet', 'feets', 'foot'],
    Unit.kilometer: ['km', 'kilometer', 'kilometers'],
    Unit.mile: ['mi', 'mile', 'miles'],
    Unit.nautical_mile: ['NMI',
                         'nauticalmile',
                         'nauticalmiles',
                         'NM',
                         'NAUTIMI'
                         ],
    # Unit.second: ['second', 'seconds', 'sec', 'secs'],
    # Unit.minute: ['min', 'minute', 'minutes', 'mins'],
    # Unit.hour: ['hr', 'hour', 'hours', 'hrs'],
    # Unit.day: ['dy', 'day', 'dys', 'days'],
    # Unit.week: ['wk', 'week', 'wks', 'weeks'],
    # Unit.month: ['mon', 'mons', 'month', 'months'],
    # Unit.year: ['yr', 'yrs', 'year', 'years'],
    Unit.meters_per_second: ['m/s', 'mps', 'ms^-1'],
    Unit.kilometers_per_hour: ['km/h', 'kph', 'km/hr', 'km/hour', 'km/hours',
                               'kmph'
                               ],
    Unit.miles_per_hour: ['mph', 'mi/h'],
    Unit.knots: ['KN', 'kt', 'knot', 'knots'],
    Unit.newton: ['newton', 'newtons'],
    Unit.pound_force: ['lbf', 'poundforce', 'pound-force',
                       'pounds-force', 'poundsforce'
                       ],
    Unit.meters3: ['m³', 'm3', 'meters3'],
    Unit.cubic_centimeters: ['cm³', 'cc', 'ccs'],
    Unit.liters: ['L', 'li', 'litre', 'liter', 'litres', 'liters'],
    Unit.pint: ['pnt', 'pt', 'pnt.', 'pint', 'pints'],
    Unit.uk_gal: ['gal (imperial)', 'gal', 'ukgal', 'gallon', 'gallons'],
    Unit.us_gal: ['gal (US)', 'usgal', 'US-gallon', 'US-gallons'],
    Unit.teaspoon: ['tsp', 'tspn', 'tsp.', 'teaspoon', 'teaspoons'],
    Unit.tablespoon: ['Tbsp', 'tblsp', 'tablespoon', 'tablespoons'],
    Unit.kilogram: ['kg', 'kilogram', 'kilo', 'kilograms', 'kilogramme',
                    'kilogrammes', 'kilos'],
    Unit.gram: ['gram', 'gramme', 'grams', 'grammes'],
    Unit.stone: ['st', 'stone', 'stones'],
    Unit.pound_mass: ['lbs', 'lb', 'pound', 'pounds'],
    Unit.ounce: ['oz', 'ounce', 'ounces'],
    Unit.tonne: ['tonne', 'tonnes'],
    Unit.ton: ['ton (US)', 'ton', 'tons'],
    Unit.kelvin: ['kelvin', '°K', 'degK', 'degreesK'],
    Unit.celcius: ['°C', 'degC', 'degreeC', 'degreesC', 'Celcius', 'centigrade',
                   'C'],
    Unit.fahrenheit: ['°F', 'degF', 'degreeF', 'degreesF', 'fahrenheit', 'F'],
}

# Create a reverse mapping
alias2unit = _reverse_map(unit2alias)

"""
Holds a unit of measurement.
"""
Measurement = collections.namedtuple('Measurement', [
    'dimension', 'magnitude', 'unit', 'alias'
])


def _find_unit_token(string_value):
    """
    Attempt to find the correct token for the unit string.
    If nothing is found, we return None.
    """
    # Get the unit type
    available_units = alias2unit.keys()
    matched_unit_alias = None

    for available_unit in available_units:
        if string_value.strip() == available_unit.lower().strip():
            matched_unit_alias = available_unit
            break

    if not matched_unit_alias:
        # We didn't find a result.
        return None

    # Get the unit enum.
    return alias2unit[matched_unit_alias]


def _to_si(magnitude, unit):
    """
    Attempts to get the SI value for a given magnitude and unit.
    If nothing compatible is found, we return None, otherwise we
    return a Measurement namedtuple.
    """
    assert isinstance(unit, Unit), \
        f'Incorrect type for Unit {unit} passed.'

    magnitude_float = float(magnitude)

    # Get the SI conversion
    conv = unit2si_conversion[unit]

    # Perform the conversion
    conv_mag = conv(magnitude_float)

    # Get the dimension type
    dimension = unit2dim[unit]

    # Get the SI unit
    si_unit = dim2si[dimension]

    return Measurement(
        dimension=dimension,
        magnitude=conv_mag if conv_mag % 1 != 0 else int(conv_mag),
        unit=si_unit,
        alias=copy.deepcopy(unit2alias[si_unit][0]),
    )


def _find_suitable_conversions(si_unit: Measurement):
    """
    Given a measurement tuple of SI units, yield all
    available conversions.

    :param si_unit: the SI measurement to convert.
    :return: a generator of conversions.
    """

    # Ensure the passed unit is an SI unit in a Measurement tuple.
    assert isinstance(si_unit, Measurement), \
        f'Incorrect type for Unit {si_unit} passed.'
    assert si_unit.unit in si2dim.keys(), \
        f'{si_unit} is not an SI unit.'

    for unit in dim2unit[si_unit.dimension]:
        conv_mag = si2unit_conversion[unit](si_unit.magnitude)

        yield Measurement(
            dimension=si_unit.dimension,
            magnitude=conv_mag,
            unit=unit,
            alias=unit2alias[unit][0]
        )


def _find_conversions(token: ConversionToken) \
        -> typing.Optional[
            typing.Tuple[
                Measurement,
                typing.List[Measurement]
            ]
        ]:
    """
    Given a conversion token, return a tuple:

    (Input, [Conversions])

    Where Unit is the parsed unit that was input as a
    conversion value, and Conversions is a list across
    each valid conversion Measurement tuple (members
    dimension, magnitude, unit).

    The list will not include the original unit, as this is
    returned as the first value anyway.

    If no match can be made, we return None.
    """
    if not isinstance(token, ConversionToken):
        raise TypeError(f'Expected conversion token, got {token}.')

    unit: Unit = _find_unit_token(token.unit.lower())

    if unit is None:
        # No match in the parser.
        return None

    # Get the SI conversion
    si = _to_si(token.magnitude, unit)

    unit = Measurement(
        dimension=unit2dim[unit],
        magnitude=token.magnitude,
        unit=unit,
        alias=unit2alias[unit][0]
    )

    # Get all suitable conversions
    gen = _find_suitable_conversions(si)

    results = list(gen)

    # Remove the original unit from the results.
    i = 0
    while i < len(results):
        if results[i].unit == unit.unit:
            results.pop(i)
        i += 1

    return unit, results


def _find_any_conversions(string) -> \
        typing.Iterator[
            typing.Union[
                typing.Tuple[Measurement, typing.List[Measurement]],
                typing.Tuple[str, ValueError]
            ]
        ]:
    """
    Returns an iterator across all unit matches in the input string, if any.

    Each conversion is a tuple of the input conversion and any equivalent
    conversions as a list.

    If any are valid conversions that have domain/range errors, then a TypeError
    is returned instead.

    :param string: the string to query.
    :return: generator of each result tuple.
    """

    for token in _find_tokens(string):
        try:
            result = _find_conversions(token)
            if result is None:
                continue

            input_conv, other_conv = result

            if input_conv in other_conv:
                other_conv.remove(input_conv)

        except ValueError as err:
            m = token.magnitude
            yield f'{m}{token.unit}', err
        else:
            yield (input_conv, other_conv)


def _measurement_to_string(measurement, should_round=True):
    """Produces a friendly string from a measurement."""
    rounded = round(measurement.magnitude, 2) \
        if should_round else measurement.magnitude

    return f'{rounded:g} {measurement.alias}'


@neko.inject_setup
class AutoUnitConversionCog(neko.Cog):
    """
    A cog that listens to incoming messages and spits out any applicable
    conversions that might exist.
    """
    permissions = (perms.Permissions.SEND_MESSAGES |
                   perms.Permissions.READ_MESSAGES |
                   perms.Permissions.ADD_REACTIONS)

    def __init__(self, bot: neko.NekoBot):
        self.bot = bot

    async def on_message(self, message):
        """
        Listens to any incoming messages and performs a conversion if it
        detects one in the message.
        """

        # Prevent responding in DMs, prevent responding to bots.
        if message.guild is None or message.author.bot:
            return

        start_time = time.time()
        results = await self.bot.do_job_in_pool(
            _find_any_conversions, message.content)
        results = list(results)

        # Measure runtime in microseconds
        runtime = (time.time() - start_time) * 1e4

        if not results:
            return
        else:
            self.logger.debug(f'Found {len(results)} potential conversions.')
            self.logger.debug(', '.join(map(str, results)))

        embed = discord.Embed(color=neko.random_color())

        for tup in results:
            input_val = tup[0]
            # Sort in ascending order of magnitude
            conversions = sorted(list(tup[1]),
                                 key=lambda x: abs(-x.magnitude),
                                 reverse=True)

            should_round = abs(input_val.magnitude) > 1e-5

            if isinstance(conversions, ValueError):
                conversions_str = str(conversions)
                fw = input_val
            else:
                conversions_str = ''
                for c in conversions:
                    # If magnitude is less than 10^-6 or greater
                    # than 10^7, put it in standard form.
                    line = _measurement_to_string(c, should_round)
                    if not line.startswith('0 '):
                        conversions_str += f'{line}\n'

                fw = _measurement_to_string(input_val, False)

            if conversions_str:
                embed.add_field(name=fw, value=conversions_str)

        t = f'Matching and all conversions took about {round(runtime, 3)} ms'

        embed.set_footer(
            text=t
        )

        message = await message.channel.send(embed=embed)
        asyncio.ensure_future(self.close_button_listener(message))

    async def close_button_listener(self, msg: discord.Message):
        """
        Listens on a message for an 'X' button to be reacted by ANYONE.
        If this happens, the message is deleted. This lasts for 5 minutes.

        :param msg: the message to listen to.
        """
        delete_rct = '\N{PUT LITTER IN ITS PLACE SYMBOL}'
        close_rct = '\N{SQUARED OK}'

        await msg.add_reaction(close_rct)
        await msg.add_reaction(delete_rct)
        self.logger.debug('Created pagination reacts.')

        def predicate(r, u):
            return (
                u.id != self.bot.user.id and
                r.message.id == msg.id and
                (r.emoji == delete_rct or r.emoji == close_rct)
            )

        try:
            react, _ = await self.bot.wait_for(
                'reaction_add',
                check=predicate,
                # Timeout is 5 minutes.
                timeout=5*60
            )

            # If we get here, someone requested to close the conversion.
            if react.emoji == delete_rct:
                await msg.delete()
            else:
                await msg.clear_reactions()
        except asyncio.TimeoutError:
            # If we timeout, we just clear the reactions.
            await msg.clear_reactions()
        finally:
            self.logger.debug('Finished pagination element.')
