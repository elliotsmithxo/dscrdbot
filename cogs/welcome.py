import discord
from discord.ext import commands
from discord import app_commands

from utils.configmanager import ConfigManager
from utils.embed_factory import themed_embed, DEFAULT_EMBED_FOOTER, get_embed_color

# -------------------------
# Defaults
# -------------------------

DEFAULT_EMBED_TITLE = "hi you,"
DEFAULT_EMBED_DESCRIPTION = ("think of this place like the moment\n"
                             "right before the chorus hits\n"
                             "still, honest,,\n"
                             "a little sad\n"
                             "but somehow sweeter for it")
DEFAULT_EMBED_IMAGE_URL = "https://i.pinimg.com/736x/c5/83/b6/c583b6f4ef35c73420ce15cbadb99250.jpg"

DEFAULT_WELCOME_MODE = "static"  # "static" or "auto"


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()

    # -------------------------
    # Helpers
    # -------------------------

    def _get_mode(self, guild_id: int) -> str:
        mode = self.config.get_guild(guild_id, "welcome_mode",
                                     DEFAULT_WELCOME_MODE)
        return mode if mode in ("static", "auto") else DEFAULT_WELCOME_MODE

    def _set_mode(self, guild_id: int, mode: str):
        self.config.set_guild(guild_id, "welcome_mode", mode)

    def _get_welcome_channel(
            self, guild: discord.Guild) -> discord.TextChannel | None:
        channel_id = self.config.get_guild(guild.id, "welcome_channel_id",
                                           None)
        if not channel_id:
            return None
        channel = guild.get_channel(int(channel_id))
        return channel if isinstance(channel, discord.TextChannel) else None

    def _ensure_auto_ready_message(self, guild: discord.Guild) -> str | None:
        """
        Returns a warning string if auto mode is not ready to function (no channel set).
        Returns None if all good.
        """
        if self._get_welcome_channel(guild) is None:
            return (
                "⚠️ welcome mode is set to **auto**, but no welcome channel is configured.\n"
                "set one with `,setwelcomechannel #channel` or `/setwelcomechannel` so auto-send works."
            )
        return None

    # -------------------------
    # Embed builder
    # -------------------------

    def build_welcome_embed(self, guild_id: int) -> discord.Embed:
        title = self.config.get_guild(guild_id, "welcome_title",
                                      DEFAULT_EMBED_TITLE)
        description = self.config.get_guild(guild_id, "welcome_description",
                                            DEFAULT_EMBED_DESCRIPTION)
        image = self.config.get_guild(guild_id, "welcome_image",
                                      DEFAULT_EMBED_IMAGE_URL)
        footer = self.config.get_guild(guild_id, "welcome_footer",
                                       DEFAULT_EMBED_FOOTER)

        embed = themed_embed(
            config=self.config,
            guild_id=guild_id,
            title=title,
            description=description,
            footer=footer,
            legacy_keys=("welcome_color", ),
        )
        embed.set_image(url=image)
        return embed

    # -------------------------
    # Auto mode behavior (only if enabled)
    # -------------------------

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self._get_mode(member.guild.id) != "auto":
            return

        channel = self._get_welcome_channel(member.guild)
        if not channel:
            return

        embed = self.build_welcome_embed(member.guild.id)
        try:
            await channel.send(content=f"welcome,, {member.mention}",
                               embed=embed)
        except discord.Forbidden:
            pass

    # -------------------------
    # Global embed color
    # -------------------------

    def _parse_hex_color(self, raw: str) -> int:
        raw = (raw or "").strip()
        if raw.startswith("#"):
            raw = raw[1:]
        if len(raw) != 6:
            raise ValueError
        return int(raw, 16)

    @commands.command(name="setembedcolor")
    @commands.has_permissions(administrator=True)
    async def legacy_set_embed_color(self, ctx, color: str):
        try:
            value = self._parse_hex_color(color)
        except ValueError:
            return await ctx.send(
                "❌ that hex doesn’t look right. try `#ff00ff`.")

        self.config.set_guild(ctx.guild.id, "embed_color", value)
        await ctx.send(f"✅ global embed color set to `#{value:06x}`")

    @app_commands.command(
        name="setembedcolor",
        description="Set the global embed color for this server (hex)")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_embed_color(self, interaction: discord.Interaction,
                                    color: str):
        try:
            value = self._parse_hex_color(color)
        except ValueError:
            return await interaction.response.send_message(
                "❌ try `#ff00ff` (6-digit hex).", ephemeral=True)

        self.config.set_guild(interaction.guild.id, "embed_color", value)
        await interaction.response.send_message(
            f"✅ global embed color set to `#{value:06x}`", ephemeral=True)

    # -------------------------
    # Welcome mode toggle (with warning polish)
    # -------------------------

    @commands.command(name="welcomemode")
    @commands.has_permissions(administrator=True)
    async def legacy_welcome_mode(self, ctx, mode: str):
        mode = (mode or "").lower().strip()
        if mode not in ("static", "auto"):
            return await ctx.send("❌ mode must be `static` or `auto`.")

        self._set_mode(ctx.guild.id, mode)

        if mode == "auto":
            warning = self._ensure_auto_ready_message(ctx.guild)
            if warning:
                return await ctx.send(
                    "✅ welcome mode set to **auto** (will post on join)\n\n" +
                    warning)
            return await ctx.send(
                "✅ welcome mode set to **auto** (will post on join).")

        await ctx.send(
            "✅ welcome mode set to **static** (manual posting only).")

    @app_commands.command(
        name="welcomemode",
        description=
        "Toggle welcome behavior: auto on join or static manual post")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(mode="auto (post on join) or static (manual only)")
    async def slash_welcome_mode(self, interaction: discord.Interaction,
                                 mode: str):
        mode = (mode or "").lower().strip()
        if mode not in ("static", "auto"):
            return await interaction.response.send_message(
                "❌ mode must be `static` or `auto`.", ephemeral=True)

        self._set_mode(interaction.guild.id, mode)

        if mode == "auto":
            warning = self._ensure_auto_ready_message(interaction.guild)
            msg = "✅ welcome mode set to **auto** (will post on join)."
            if warning:
                msg = msg + "\n\n" + warning
            return await interaction.response.send_message(msg, ephemeral=True)

        await interaction.response.send_message(
            "✅ welcome mode set to **static** (manual posting only).",
            ephemeral=True)

    # -------------------------
    # Welcome channel setter (used for auto mode)
    # -------------------------

    @commands.command(name="setwelcomechannel")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_channel(self, ctx,
                                         channel: discord.TextChannel):
        self.config.set_guild(ctx.guild.id, "welcome_channel_id", channel.id)
        msg = f"✅ welcome channel set to {channel.mention}"

        # extra polish: if you're already in auto mode, confirm it's now ready
        if self._get_mode(ctx.guild.id) == "auto":
            msg += "\n✅ auto mode is now ready."

        await ctx.send(msg)

    @app_commands.command(
        name="setwelcomechannel",
        description="Set the channel used for welcome auto-posting")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_channel(self, interaction: discord.Interaction,
                                        channel: discord.TextChannel):
        self.config.set_guild(interaction.guild.id, "welcome_channel_id",
                              channel.id)
        msg = f"✅ welcome channel set to {channel.mention}"

        if self._get_mode(interaction.guild.id) == "auto":
            msg += "\n✅ auto mode is now ready."

        await interaction.response.send_message(msg, ephemeral=True)

    # -------------------------
    # Welcome content setters
    # -------------------------

    @commands.command(name="setwelcometitle")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_title(self, ctx, *, title: str):
        self.config.set_guild(ctx.guild.id, "welcome_title", title)
        await ctx.send("✅ welcome title updated.")

    @app_commands.command(name="setwelcometitle",
                          description="Set the welcome embed title")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_title(self, interaction: discord.Interaction,
                                      title: str):
        self.config.set_guild(interaction.guild.id, "welcome_title", title)
        await interaction.response.send_message("✅ welcome title updated.",
                                                ephemeral=True)

    @commands.command(name="setwelcomedesc")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_desc(self, ctx, *, description: str):
        self.config.set_guild(ctx.guild.id, "welcome_description", description)
        await ctx.send("✅ welcome description updated.")

    @app_commands.command(name="setwelcomedesc",
                          description="Set the welcome embed description")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_desc(self, interaction: discord.Interaction,
                                     description: str):
        self.config.set_guild(interaction.guild.id, "welcome_description",
                              description)
        await interaction.response.send_message(
            "✅ welcome description updated.", ephemeral=True)

    @commands.command(name="setwelcomeimage")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_image(self, ctx, url: str):
        self.config.set_guild(ctx.guild.id, "welcome_image", url)
        await ctx.send("✅ welcome image updated.")

    @app_commands.command(name="setwelcomeimage",
                          description="Set the welcome embed image URL")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_image(self, interaction: discord.Interaction,
                                      url: str):
        self.config.set_guild(interaction.guild.id, "welcome_image", url)
        await interaction.response.send_message("✅ welcome image updated.",
                                                ephemeral=True)

    @commands.command(name="setwelcomefooter")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_footer(self, ctx, *, footer: str):
        self.config.set_guild(ctx.guild.id, "welcome_footer", footer)
        await ctx.send("✅ welcome footer updated.")

    @app_commands.command(name="setwelcomefooter",
                          description="Set the welcome embed footer")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_footer(self, interaction: discord.Interaction,
                                       footer: str):
        self.config.set_guild(interaction.guild.id, "welcome_footer", footer)
        await interaction.response.send_message("✅ welcome footer updated.",
                                                ephemeral=True)

    # -------------------------
    # Send / Preview welcome embed (works in both modes)
    # -------------------------

    @commands.command(name="welcome")
    @commands.has_permissions(administrator=True)
    async def legacy_send_welcome(self,
                                  ctx,
                                  channel: discord.TextChannel | None = None):
        target = channel or ctx.channel
        embed = self.build_welcome_embed(ctx.guild.id)
        await target.send(embed=embed)

        # If you're in auto mode but missing channel, mention it once (nice UX)
        warning = self._ensure_auto_ready_message(ctx.guild)
        if warning and self._get_mode(ctx.guild.id) == "auto":
            await ctx.send(warning)

    @app_commands.command(name="welcome",
                          description="Send or preview the welcome embed")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(mode="preview (ephemeral) or send",
                           channel="Where to send it (optional)")
    async def slash_welcome(self,
                            interaction: discord.Interaction,
                            mode: str = "preview",
                            channel: discord.TextChannel | None = None):
        embed = self.build_welcome_embed(interaction.guild.id)

        if mode.lower() == "send":
            target = channel or interaction.channel
            await target.send(embed=embed)

            msg = "✅ welcome embed sent."
            warning = self._ensure_auto_ready_message(interaction.guild)
            if warning and self._get_mode(interaction.guild.id) == "auto":
                msg += "\n\n" + warning

            return await interaction.response.send_message(msg, ephemeral=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------
    # Settings overview (now explicitly shows welcome type)
    # -------------------------

    def _settings_embed(self, guild: discord.Guild) -> discord.Embed:
        gid = guild.id
        embed_color = get_embed_color(self.config, gid)
        mode = self._get_mode(gid)

        welcome_channel = self._get_welcome_channel(guild)
        welcome_channel_display = welcome_channel.mention if welcome_channel else "(not set)"

        title = self.config.get_guild(gid, "welcome_title",
                                      DEFAULT_EMBED_TITLE)
        image = self.config.get_guild(gid, "welcome_image",
                                      DEFAULT_EMBED_IMAGE_URL)

        e = themed_embed(config=self.config,
                         guild_id=gid,
                         title="Settings",
                         description="current server configuration",
                         footer=DEFAULT_EMBED_FOOTER)

        # ✅ clearer naming (welcome type)
        e.add_field(name="Welcome Type", value=f"`{mode}`", inline=True)
        e.add_field(name="Welcome Channel",
                    value=welcome_channel_display,
                    inline=True)
        e.add_field(name="Embed Color",
                    value=f"`#{embed_color:06x}`",
                    inline=True)

        # optional clarity: if auto but not ready, show it right in settings
        if mode == "auto" and welcome_channel is None:
            e.add_field(
                name="Auto Mode Status",
                value="⚠️ not ready (set a channel with `setwelcomechannel`)",
                inline=False)

        e.add_field(name="Welcome Title",
                    value=(title[:100] + "…" if len(title) > 100 else title),
                    inline=False)
        e.add_field(name="Welcome Image", value=image, inline=False)
        return e

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def legacy_settings(self, ctx):
        await ctx.send(embed=self._settings_embed(ctx.guild))

    @app_commands.command(name="settings",
                          description="View this server's bot settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_settings(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self._settings_embed(
            interaction.guild),
                                                ephemeral=True)


async def setup(bot):
    cog = Welcome(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_set_embed_color)
        bot.tree.add_command(cog.slash_welcome_mode)
        bot.tree.add_command(cog.slash_set_welcome_channel)

        bot.tree.add_command(cog.slash_set_welcome_title)
        bot.tree.add_command(cog.slash_set_welcome_desc)
        bot.tree.add_command(cog.slash_set_welcome_image)
        bot.tree.add_command(cog.slash_set_welcome_footer)

        bot.tree.add_command(cog.slash_welcome)
        bot.tree.add_command(cog.slash_settings)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
