"""
Defines an embed type for discord.py
that will automatically trim fields if
they get too long.
"""
import discord
import discord.embeds as embeds

import neko


__all__ = ('SafeEmbed', 'FullEmbedError')


EmptyEmbed = embeds.EmptyEmbed

# https://discordapp.com/developers/docs/resources/channel#embed-limits
_max_title = 256
_max_desc = 2048
_max_field_name = 256
_max_field_cont = 1024
_max_footer = 2048
_max_auth_name = 256
_max_fields = 25


class FullEmbedError(discord.ClientException):
    def __str__(self):
        return f'This embed has maximum number of fields {_max_fields} already.'

    __repr__ = __str__


class SafeEmbed(embeds.Embed):
    """
    Encapsulates the setters for properties and attributes
    by adding length checks to them. If they are too long,
    text is truncated and ellipses are added as the last
    three characters. If it is a field, a ValueError is
    raised to tell you that you already have the maximum
    number of fields available.

    Due to how embed is implemented, it was more complicated
    to derive this class from it, than it was to just write
    a wrapper, and this is a very hacky work around. I cant
    seem to alter internal values for whatever reason as we
    set them, so the validation unfortunately is done each
    time we access a field that is limited. This was the only
    way I could get this to work. This limitation seems to
    be regarding the fields that are not encapsulated with
    setter methods, such as title and description.

    The bits that have overridable methods will set the values
    at the appropriate time. This is a very messed up solution
    and if it causes too many issues, I may well remove it in
    the near future.
    """
    def __init__(self, *,
                 title: str=EmptyEmbed,
                 description: str=EmptyEmbed,
                 **kwargs):
        if title != EmptyEmbed:
            title = neko.ellipses(title, _max_title)
        if description != EmptyEmbed:
            description = neko.ellipses(description, _max_desc)
        kwargs['title'] = title
        kwargs['description'] = description
        super().__init__(**kwargs)

    def __getattribute__(self, item):
        # Unless we do this in this way
        if item == 'title':
            return neko.ellipses(super().title, _max_title)
        elif item == 'description':
            return neko.ellipses(super().description, _max_desc)
        else:
            return getattr(super(), item)

    # Some things are better left unsaid.
    __getattr__ = __getattribute__

    def set_author(self, *, name, url=EmptyEmbed, icon_url=EmptyEmbed):
        name = neko.ellipses(name, _max_auth_name)
        super().set_author(name=name, url=url, icon_url=icon_url)

    def set_field_at(self, index, *, name, value, inline=True):
        name = neko.ellipses(name, _max_field_name)
        value = neko.ellipses(value, _max_field_cont)
        super().set_field_at(index=index, name=name, value=value, inline=inline)

    def set_footer(self, *, text=EmptyEmbed, icon_url=EmptyEmbed):
        text = neko.ellipses(text, _max_footer)
        super().set_footer(text=text, icon_url=icon_url)

    def add_field(self, *, name, value, inline=True):
        if len(super().fields) < _max_fields:
            name = neko.ellipses(name, _max_field_name)
            value = neko.ellipses(value, _max_field_cont)
            super().add_field(name=name, value=value, inline=inline)
        else:
            raise FullEmbedError

    def __str__(self):
        return (f'SafeEmbed with title {self.title} '
                f'and {neko.pluralise(len(self.fields), "field")}.')

    def __repr__(self):
        strings = []
        for f in ('title', 'description', 'colour', 'fields', 'author', 'url',
                  'timestamp', 'footer'):
            strings.append(f'{f}={getattr(self, f)!r}')

        return f'<SafeEmbed' + (', '.join(strings) if strings else '') + '>'

