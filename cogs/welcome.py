import discord
from discord.ext import commands, tasks
from discord import app_commands

from utils.configmanager import ConfigManager
from utils.embed_factory import themed_embed, DEFAULT_EMBED_FOOTER, get_embed_color

DEFAULT_EMBED_TITLE = "hi you,"
DEFAULT_EMBED_DESCRIPTION = (
    "think of this place like the moment\n"
    "right before the chorus hits\n"
    "still, honest,,\n"
    "a little sad\n"
    "but somehow sweeter for it"
)
DEFAULT_EMBED_IMAGE_URL = "https://i.pinimg.com/736x/c5/83/b6/c583b6f4ef35c73420ce15cbadb99250.jpg"


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        self._channel_health.start()  # (8) background cleanup

    def cog_unload(self):
        self._channel_health.cancel()

    # (8) Validate channels periodically, clear config if channel deleted or bot cannot send
    @tasks.loop(hours=6)
    async def _channel_health(self):
        for guild in self.bot.guilds:
            welcome_channel_id = self.config.get_guild(guild.id, "welcome_channel", None)
            if not welcome_channel_id:
                continue

            channel = guild.get_channel(int(welcome_channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                self.config.set_guild(guild.id, "welcome_channel", None)
                continue

            perms = channel.permissions_for(guild.me)
            if not (perms.send_messages and perms.embed_links):
                # keep it simple: clear so it fails gracefully instead of spamming errors
                self.config.set_guild(guild.id, "welcome_channel", None)

    @_channel_health.before_loop
    async def _before_channel_health(self):
        await self.bot.wait_until_ready()

    def build_welcome_embed(self, guild_id: int) -> discord.Embed:
        title = self.config.get_guild(guild_id, "welcome_title", DEFAULT_EMBED_TITLE)
        description = self.config.get_guild(guild_id, "welcome_description", DEFAULT_EMBED_DESCRIPTION)
        image = self.config.get_guild(guild_id, "welcome_image", DEFAULT_EMBED_IMAGE_URL)
        footer = self.config.get_guild(guild_id, "welcome_footer", DEFAULT_EMBED_FOOTER)

        embed = themed_embed(
            config=self.config,
            guild_id=guild_id,
            title=title,
            description=description,
            footer=footer,
            legacy_keys=("welcome_color",),
        )
        embed.set_image(url=image)
        return embed

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        channel_id = self.config.get_guild(guild_id, "welcome_channel", None)
        if not channel_id:
            return

        channel = member.guild.get_channel(int(channel_id))
        if not channel:
            return

        embed = self.build_welcome_embed(guild_id)
        try:
            await channel.send(content=f"welcome,, {member.mention}", embed=embed)
        except discord.Forbidden:
            # (6) gentle failure: clear invalid config
            self.config.set_guild(guild_id, "welcome_channel", None)

    # ---------------------------
    # Admin: setwelcome
    # ---------------------------

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome(self, ctx, channel: discord.TextChannel):
        self.config.set_guild(ctx.guild.id, "welcome_channel", channel.id)
        await ctx.send(f"✅ welcome channel set to {channel.mention}")

    @app_commands.command(name="setwelcome", description="Set the welcome channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.config.set_guild(interaction.guild.id, "welcome_channel", channel.id)
        await interaction.response.send_message(f"✅ welcome channel set to {channel.mention}", ephemeral=True)

    # ---------------------------
    # Global embed color (server)
    # ---------------------------

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
            return await ctx.send("❌ that hex doesn’t look right. try something like `#ff00ff`.")

        self.config.set_guild(ctx.guild.id, "embed_color", value)
        await ctx.send(f"✅ global embed color set to `#{value:06x}`")

    @app_commands.command(name="setembedcolor", description="Set the global embed color for this server (hex)")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_embed_color(self, interaction: discord.Interaction, color: str):
        try:
            value = self._parse_hex_color(color)
        except ValueError:
            return await interaction.response.send_message(
                "❌ that hex doesn’t look right. try something like `#ff00ff`.",
                ephemeral=True,
            )

        self.config.set_guild(interaction.guild.id, "embed_color", value)
        await interaction.response.send_message(f"✅ global embed color set to `#{value:06x}`", ephemeral=True)

    # Optional deprecated alias (keeps older muscle memory working)
    @commands.command(name="setwelcomecolor")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_color(self, ctx, color: str):
        try:
            value = self._parse_hex_color(color)
        except ValueError:
            return await ctx.send("❌ try `,setembedcolor #ff00ff` instead (6-digit hex).")

        self.config.set_guild(ctx.guild.id, "embed_color", value)
        self.config.set_guild(ctx.guild.id, "welcome_color", value)
        await ctx.send("✅ updated. (use `setembedcolor` next time.)")

    # ---------------------------
    # (2) Settings readout
    # ---------------------------

    def _settings_embed(self, guild: discord.Guild) -> discord.Embed:
        gid = guild.id

        embed_color = get_embed_color(self.config, gid)
        welcome_channel_id = self.config.get_guild(gid, "welcome_channel", None)
        starboard_channel_id = self.config.get_guild(gid, "starboard_channel_id", None)
        star_threshold = self.config.get_guild(gid, "star_threshold", 1)

        welcome_channel = guild.get_channel(int(welcome_channel_id)) if welcome_channel_id else None
        starboard_channel = guild.get_channel(int(starboard_channel_id)) if starboard_channel_id else None

        e = themed_embed(
            config=self.config,
            guild_id=gid,
            title="Settings",
            description="current server configuration",
            footer=DEFAULT_EMBED_FOOTER
        )

        e.add_field(name="Embed Color", value=f"`#{embed_color:06x}`", inline=True)
        e.add_field(name="Welcome Channel", value=(welcome_channel.mention if welcome_channel else "(not set)"), inline=True)
        e.add_field(name="Starboard Channel", value=(starboard_channel.mention if starboard_channel else "(not set)"), inline=True)
        e.add_field(name="Star Threshold", value=f"`{star_threshold}`", inline=True)
        return e

    @commands.command(name="settings")
    @commands.has_permissions(administrator=True)
    async def legacy_settings(self, ctx):
        await ctx.send(embed=self._settings_embed(ctx.guild))

    @app_commands.command(name="settings", description="View this server's bot settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_settings(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=self._settings_embed(interaction.guild), ephemeral=True)


async def setup(bot):
    cog = Welcome(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_set_welcome)
        bot.tree.add_command(cog.slash_set_embed_color)
        bot.tree.add_command(cog.slash_settings)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
