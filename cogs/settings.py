import discord
from discord.ext import commands
from discord import app_commands

from utils.configmanager import ConfigManager

DEFAULT_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"
DEFAULT_COLOR = 0xb5a12c


class Settings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # NOTE: we intentionally do NOT rely on a long-lived cached config for reads
        self.config = ConfigManager()

    # -------------------------
    # Helpers
    # -------------------------

    def _get_embed_color(self, cfg: ConfigManager, guild_id: int) -> int:
        color = cfg.get_guild(guild_id, "embed_color", None)
        if isinstance(color, int):
            return color

        legacy = cfg.get_guild(guild_id, "welcome_color", None)
        if isinstance(legacy, int):
            return legacy

        return DEFAULT_COLOR

    def _get_channel_mention(self, guild: discord.Guild, channel_id) -> str:
        if not channel_id:
            return "(not set)"
        try:
            channel = guild.get_channel(int(channel_id))
        except (TypeError, ValueError):
            return "(not set)"
        return channel.mention if isinstance(channel, discord.abc.GuildChannel) else "(not set)"

    def _get_welcome_type(self, cfg: ConfigManager, guild_id: int) -> str:
        mode = cfg.get_guild(guild_id, "welcome_mode", "static")
        return mode if mode in ("static", "auto") else "static"

    def _admin_roles(self, guild: discord.Guild) -> list[discord.Role]:
        return [r for r in guild.roles if r.permissions.administrator and not r.is_default()]

    def _admin_members(self, guild: discord.Guild) -> list[discord.Member]:
        return [m for m in guild.members if m.guild_permissions.administrator and not m.bot]

    def _format_mentions_list(self, items: list[str], *, empty_text="(none)", limit=15) -> str:
        if not items:
            return empty_text
        shown = items[:limit]
        more = len(items) - len(shown)
        if more > 0:
            return " ".join(shown) + f"\n…and {more} more"
        return " ".join(shown)

    def _settings_embed(self, guild: discord.Guild) -> discord.Embed:
        # ✅ Fresh read every time (fixes stale cache across cogs)
        cfg = ConfigManager()

        gid = guild.id
        color = self._get_embed_color(cfg, gid)

        welcome_type = self._get_welcome_type(cfg, gid)

        welcome_channel_id = cfg.get_guild(gid, "welcome_channel_id", None)
        starboard_channel_id = cfg.get_guild(gid, "starboard_channel_id", None)
        star_threshold = cfg.get_guild(gid, "star_threshold", 1)

        welcome_channel = self._get_channel_mention(guild, welcome_channel_id)
        starboard_channel = self._get_channel_mention(guild, starboard_channel_id)

        roles = self._admin_roles(guild)
        members = self._admin_members(guild)

        role_mentions = [r.mention for r in roles]
        member_mentions = [m.mention for m in members]

        embed = discord.Embed(
            title="Settings",
            description="current server configuration",
            color=color
        )

        embed.add_field(name="Embed Color", value=f"`#{color:06x}`", inline=True)
        embed.add_field(name="Welcome Type", value=f"`{welcome_type}`", inline=True)
        embed.add_field(name="Welcome Channel", value=welcome_channel, inline=True)

        embed.add_field(name="Starboard Channel", value=starboard_channel, inline=True)
        embed.add_field(name="Star Threshold", value=f"`{star_threshold}`", inline=True)

        if welcome_type == "auto" and not welcome_channel_id:
            embed.add_field(
                name="Auto Welcome Status",
                value="⚠️ `auto` is enabled, but no welcome channel is set.\nUse `setwelcomechannel`.",
                inline=False
            )

        embed.add_field(
            name=f"Admin Roles ({len(roles)})",
            value=self._format_mentions_list(role_mentions, empty_text="(none)", limit=12),
            inline=False
        )
        embed.add_field(
            name=f"Admin Members ({len(members)})",
            value=self._format_mentions_list(member_mentions, empty_text="(none)", limit=12),
            inline=False
        )

        embed.set_footer(text=DEFAULT_FOOTER)
        return embed

    # -------------------------
    # Commands
    # -------------------------

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def legacy_settings(self, ctx: commands.Context):
        await ctx.send(embed=self._settings_embed(ctx.guild))

    @app_commands.command(name="settings", description="View server settings (welcome + starboard + admins)")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_settings(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=self._settings_embed(interaction.guild),
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    cog = Settings(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_settings)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
