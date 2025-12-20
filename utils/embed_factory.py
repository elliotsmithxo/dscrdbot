import discord
from utils.configmanager import ConfigManager

DEFAULT_EMBED_COLOR = 0xb5a12c
DEFAULT_EMBED_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"


def get_embed_color(
    config: ConfigManager,
    guild_id: int,
    default: int = DEFAULT_EMBED_COLOR,
    legacy_keys: tuple[str, ...] = ("welcome_color",),
) -> int:
    """Get a server-wide embed color, with optional legacy fallbacks."""
    color = config.get_guild(guild_id, "embed_color", None)
    if isinstance(color, int):
        return color

    # legacy fallback keys (keeps older servers working without migration steps)
    for key in legacy_keys:
        legacy = config.get_guild(guild_id, key, None)
        if isinstance(legacy, int):
            return legacy

    return default


def themed_embed(
    *,
    config: ConfigManager,
    guild_id: int,
    title: str | None = None,
    description: str | None = None,
    footer: str | None = DEFAULT_EMBED_FOOTER,
    timestamp=None,
    color: int | None = None,
    legacy_keys: tuple[str, ...] = ("welcome_color",),
) -> discord.Embed:
    """Create a consistently themed embed for the whole bot."""
    final_color = color if isinstance(color, int) else get_embed_color(
        config=config,
        guild_id=guild_id,
        legacy_keys=legacy_keys
    )

    embed = discord.Embed(title=title, description=description, color=final_color, timestamp=timestamp)
    if footer:
        embed.set_footer(text=footer)
    return embed
