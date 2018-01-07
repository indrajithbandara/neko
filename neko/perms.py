"""
Enum-type definition for permissions, as I prefer the syntax.
"""
import enum
import discord

__all__ = ['Permissions']


class Permissions(enum.IntFlag):
    """
    Danny's Permissions class does not define these as integer constants. We
    can define these as follows which allows for bitwise or-ing the values
    to combine permissions.

    There is an additional utility method to convert to the Discord.py variant
    included here for ease of use.
    """
    NONE = 0x00000000
    CREATE_INSTANT_INVITE = 0x00000001
    KICK_MEMBERS = 0x00000002
    BAN_MEMBERS = 0x00000004
    ADMINISTRATOR = 0x00000008
    MANAGE_CHANNELS = 0x00000010
    MANAGE_GUILD = 0x00000020
    ADD_REACTIONS = 0x00000040
    VIEW_AUDIT_LOG = 0x00000080
    # Deprecated 1 = 0x00000100
    # Deprecated 2 = 0x00000200
    READ_MESSAGES = 0x00000400
    SEND_MESSAGES = 0x00000800
    SEND_TTS_MESSAGES = 0x00001000
    MANAGE_MESSAGES = 0x00002000
    EMBED_LINKS = 0x00004000
    ATTACH_FILES = 0x00008000
    READ_MESSAGE_HISTORY = 0x00010000
    MENTION_EVERYONE = 0x00020000
    USE_EXTERNAL_EMOJIS = 0x00040000
    # Deprecated 3 = 0x00080000
    CONNECT = 0x00100000
    SPEAK = 0x00200000
    MUTE_MEMBERS = 0x00400000
    DEAFEN_MEMBERS = 0x00800000
    MOVE_MEMBERS = 0x01000000
    USE_VAD = 0x02000000
    CHANGE_NICKNAME = 0x04000000
    MANAGE_NICKNAMES = 0x08000000
    MANAGE_ROLES = 0x10000000
    MANAGE_WEBHOOKS = 0x20000000
    MANAGE_EMOJIS = 0x40000000

    def to_discord_type(self):
        """
        Converts the permissions bits to the corresponding Discord.py
        implementation.
        """
        return discord.Permissions(self.value)

    @classmethod
    def from_discord_type(cls, discord_perms: discord.Permissions):
        """
        Converts the given Discord.py permissions implementation to a member
        of this enum.
        """
        return cls(discord_perms.value)
