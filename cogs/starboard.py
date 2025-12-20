import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os

from utils.configmanager import ConfigManager
from utils.embed_factory import themed_embed

DEFAULT_FALLBACK_COLOR = 0xF1C40F  # fallback if server has no embed_color


class Starboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        self.star_emoji = "⭐"
        self.default_star_threshold = 1
        self.data_file = "starboard_data.json"

        if not os.path.exists(self.data_file):
            with open(self.data_file, "w") as f:
                json.dump({}, f)

        self._channel_health.start()  # (8)

    def cog_unload(self):
        self._channel_health.cancel()

    @tasks.loop(hours=6)
    async def _channel_health(self):
        for guild in self.bot.guilds:
            starboard_channel_id = self.config.get_guild(
                guild.id, "starboard_channel_id", None)
            if not starboard_channel_id:
                continue

            channel = guild.get_channel(int(starboard_channel_id))
            if not channel or not isinstance(channel, discord.TextChannel):
                self.config.set_guild(guild.id, "starboard_channel_id", None)
                continue

            perms = channel.permissions_for(guild.me)
            if not (perms.send_messages and perms.embed_links
                    and perms.read_message_history):
                self.config.set_guild(guild.id, "starboard_channel_id", None)

    @_channel_health.before_loop
    async def _before_channel_health(self):
        await self.bot.wait_until_ready()

    def load_data(self):
        with open(self.data_file, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=4)

    async def create_or_update_starboard_message(
            self, message: discord.Message, star_count: int,
            starboard_channel: discord.TextChannel):
        data = self.load_data()
        guild_id = str(message.guild.id)
        msg_id = str(message.id)

        embed = themed_embed(
            config=self.config,
            guild_id=message.guild.id,
            title=None,
            description=message.content or "",
            timestamp=message.created_at,
        )
        # if server has no embed_color, let fallback be starboard-gold-ish
        # (themed_embed will use embed_color if set; otherwise it falls back to embed_factory default)
        # If you prefer gold fallback, you can store embed_color or change embed_factory default.

        embed.set_author(name=message.author.display_name,
                         icon_url=message.author.display_avatar.url)
        embed.add_field(name="Jump to Message",
                        value=f"[Click Here]({message.jump_url})",
                        inline=False)

        if message.attachments:
            attachment = message.attachments[0]
            if attachment.content_type and attachment.content_type.startswith(
                    "image"):
                embed.set_image(url=attachment.url)

        if guild_id not in data:
            data[guild_id] = {}

        if msg_id in data[guild_id]:
            starboard_msg_id = int(data[guild_id][msg_id])
            try:
                starboard_msg = await starboard_channel.fetch_message(
                    starboard_msg_id)
                await starboard_msg.edit(
                    content=
                    f"{self.star_emoji} **{star_count}** | {message.channel.mention}",
                    embed=embed)
            except discord.NotFound:
                del data[guild_id][msg_id]
        else:
            starboard_msg = await starboard_channel.send(
                content=
                f"{self.star_emoji} **{star_count}** | {message.channel.mention}",
                embed=embed)
            data[guild_id][msg_id] = str(starboard_msg.id)

        self.save_data(data)

    async def scan_for_star_reactions(self,
                                      guild: discord.Guild,
                                      limit: int = 100):
        starboard_channel_id = self.config.get_guild(guild.id,
                                                     "starboard_channel_id",
                                                     None)
        if not starboard_channel_id:
            return

        starboard_channel = guild.get_channel(int(starboard_channel_id))
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        star_threshold = self.config.get_guild(guild.id, "star_threshold",
                                               self.default_star_threshold)

        for channel in guild.text_channels:
            if channel.id == starboard_channel.id:
                continue
            async for message in channel.history(limit=limit):
                for reaction in message.reactions:
                    if str(
                            reaction.emoji
                    ) == self.star_emoji and reaction.count >= star_threshold:
                        await self.create_or_update_starboard_message(
                            message, reaction.count, starboard_channel)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self,
                                  payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != self.star_emoji:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        starboard_channel_id = self.config.get_guild(guild.id,
                                                     "starboard_channel_id",
                                                     None)
        if not starboard_channel_id:
            return

        starboard_channel = guild.get_channel(int(starboard_channel_id))
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        star_threshold = self.config.get_guild(guild.id, "star_threshold",
                                               self.default_star_threshold)

        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        for reaction in message.reactions:
            if str(reaction.emoji
                   ) == self.star_emoji and reaction.count >= star_threshold:
                await self.create_or_update_starboard_message(
                    message, reaction.count, starboard_channel)
                break

    # ---------------------------
    # Admin commands
    # ---------------------------

    @commands.command(name="setstarboard")
    @commands.has_permissions(administrator=True)
    async def legacy_set_starboard(self, ctx, channel: discord.TextChannel):
        self.config.set_guild(ctx.guild.id, "starboard_channel_id", channel.id)
        await ctx.send(f"✅ starboard channel set to {channel.mention}")

    @app_commands.command(name="setstarboard",
                          description="Set the starboard channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_starboard(self, interaction: discord.Interaction,
                                  channel: discord.TextChannel):
        self.config.set_guild(interaction.guild.id, "starboard_channel_id",
                              channel.id)
        await interaction.response.send_message(
            f"✅ starboard channel set to {channel.mention}", ephemeral=True)

    @commands.command(name="setstarthreshold")
    @commands.has_permissions(administrator=True)
    async def legacy_set_star_threshold(self, ctx, threshold: int):
        self.config.set_guild(ctx.guild.id, "star_threshold", threshold)
        await ctx.send(f"✅ star threshold set to `{threshold}`")

    @app_commands.command(name="setstarthreshold",
                          description="Set the star threshold")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_star_threshold(self, interaction: discord.Interaction,
                                       threshold: int):
        self.config.set_guild(interaction.guild.id, "star_threshold",
                              threshold)
        await interaction.response.send_message(
            f"✅ star threshold set to `{threshold}`", ephemeral=True)

    @commands.command(name="scanstars")
    @commands.has_permissions(administrator=True)
    async def legacy_scan_stars(self, ctx, limit: int = 100):
        await self.scan_for_star_reactions(ctx.guild, limit=limit)
        await ctx.send("✅ star scan complete.")

    @app_commands.command(
        name="scanstars",
        description="Scan recent messages for star reactions")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_scan_stars(self,
                               interaction: discord.Interaction,
                               limit: int = 100):
        await self.scan_for_star_reactions(interaction.guild, limit=limit)
        await interaction.response.send_message("✅ star scan complete.",
                                                ephemeral=True)


async def setup(bot):
    cog = Starboard(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_set_starboard)
        bot.tree.add_command(cog.slash_set_star_threshold)
        bot.tree.add_command(cog.slash_scan_stars)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
