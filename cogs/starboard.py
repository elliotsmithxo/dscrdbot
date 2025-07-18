import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from utils.configmanager import ConfigManager


class Starboard(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()
        self.star_emoji = "⭐"
        self.default_star_threshold = 1
        self.data_file = "starboard_data.json"
        self.starboard_data = self.load_data()

    async def create_starboard_entry(self, message: discord.Message, valid_count: int, starboard_channel: discord.TextChannel):
        embed = discord.Embed(
            description=message.content or "",
            color=discord.Color.gold(),
            timestamp=message.created_at,
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(
            name="Source",
            value=f"[Jump to message]({message.jump_url})",
            inline=False,
        )

        if message.attachments:
            for attachment in message.attachments:
                if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                    embed.set_image(url=attachment.url)
                    break

        if message.embeds:
            for e in message.embeds:
                if e.type in ("gifv", "image") and hasattr(e, "url"):
                    embed.set_image(url=e.url)
                    break

        embed.set_footer(text=f"{self.star_emoji} {valid_count} | #{message.channel.name}")
        starboard_message = await starboard_channel.send(embed=embed)
        self.starboard_data[str(message.id)] = {
            "starboard_message_id": starboard_message.id,
            "original_channel_id": message.channel.id,
        }
        self.save_data()

    async def scan_for_star_reactions(self, guild: discord.Guild, limit: int = 100):
        starboard_channel_id = self.config.get_guild(guild.id, "starboard_channel_id")
        if not starboard_channel_id:
            return

        starboard_channel = self.bot.get_channel(int(starboard_channel_id))
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        star_threshold = self.config.get_guild(guild.id, "star_threshold", self.default_star_threshold)

        for channel in guild.text_channels:
            if channel.id == starboard_channel.id:
                continue
            async for message in channel.history(limit=limit):
                if message.stickers and not message.content and not message.attachments:
                    continue
                reaction = discord.utils.get(message.reactions, emoji=self.star_emoji)
                if not reaction:
                    continue
                valid_count = await self.count_valid_reactors(reaction, message.author.id)
                if valid_count < star_threshold:
                    continue

                message_id = str(message.id)
                if message_id in self.starboard_data:
                    try:
                        starboard_message = await starboard_channel.fetch_message(
                            self.starboard_data[message_id]["starboard_message_id"]
                        )
                        embed = starboard_message.embeds[0]
                        embed.set_footer(text=f"{self.star_emoji} {valid_count} | #{message.channel.name}")
                        await starboard_message.edit(embed=embed)
                    except discord.NotFound:
                        await self.create_starboard_entry(message, valid_count, starboard_channel)
                else:
                    await self.create_starboard_entry(message, valid_count, starboard_channel)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

    def save_data(self):
        try:
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.starboard_data, f, indent=4)
        except:
            pass

    async def count_valid_reactors(self, reaction, author_id):
        count = 0
        async for user in reaction.users():
            if not user.bot and user.id != author_id:
                count += 1
        return count

    async def ensure_full_message(self, message):
        if isinstance(message, discord.PartialMessage) or message.partial:
            try:
                message = await message.fetch()
            except:
                return None
        try:
            return await message.channel.fetch_message(message.id)
        except:
            return None

    @commands.command(name="setstarboard")
    @commands.has_permissions(administrator=True)
    async def set_starboard_legacy(self, ctx):
        self.config.set_guild(ctx.guild.id, "starboard_channel_id", ctx.channel.id)
        await ctx.send(f"✅ {ctx.channel.mention} set as starboard channel.")

    @app_commands.command(name="setstarboard",
                          description="Set this channel as the starboard.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_starboard_slash(self, interaction: discord.Interaction):
        self.config.set_guild(interaction.guild.id, "starboard_channel_id", interaction.channel.id)
        await interaction.response.send_message(
            f"✅ {interaction.channel.mention} set as starboard channel.",
            ephemeral=True)

    @commands.command(name="setstarthreshold")
    @commands.has_permissions(administrator=True)
    async def set_star_threshold_legacy(self, ctx, threshold: int):
        self.config.set_guild(ctx.guild.id, "star_threshold", threshold)
        await ctx.send(f"✅ Star threshold set to {threshold}.")

    @app_commands.command(name="setstarthreshold", description="Set the star threshold for this guild")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_star_threshold_slash(self, interaction: discord.Interaction, threshold: int):
        self.config.set_guild(interaction.guild.id, "star_threshold", threshold)
        await interaction.response.send_message(
            f"✅ Star threshold set to {threshold}.", ephemeral=True)

    @commands.command(name="scanstarboard")
    @commands.has_permissions(administrator=True)
    async def scan_starboard_legacy(self, ctx, limit: int = 100):
        await ctx.send("🔍 Scanning recent messages for stars...")
        await self.scan_for_star_reactions(ctx.guild, limit)
        await ctx.send("✅ Scan complete.")

    @app_commands.command(name="scanstarboard", description="Scan recent messages for star reactions")
    @app_commands.checks.has_permissions(administrator=True)
    async def scan_starboard_slash(self, interaction: discord.Interaction, limit: int = 100):
        await interaction.response.defer(ephemeral=True)
        await self.scan_for_star_reactions(interaction.guild, limit)
        await interaction.followup.send("✅ Scan complete.", ephemeral=True)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot or not reaction.message.guild:
            return

        if str(reaction.emoji) != self.star_emoji:
            return

        message = await self.ensure_full_message(reaction.message)
        if message is None or user.id == message.author.id:
            return

        message_id = str(message.id)
        starboard_channel_id = self.config.get_guild(message.guild.id, "starboard_channel_id")
        if not starboard_channel_id:
            return

        starboard_channel = self.bot.get_channel(int(starboard_channel_id))
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        if message.channel.id == starboard_channel.id:
            return

        if message.stickers and not message.content and not message.attachments:
            return

        valid_count = await self.count_valid_reactors(reaction, message.author.id)
        star_threshold = self.config.get_guild(message.guild.id, "star_threshold", self.default_star_threshold)
        if valid_count < star_threshold:
            return

        if message_id in self.starboard_data:
            try:
                starboard_message = await starboard_channel.fetch_message(
                    self.starboard_data[message_id]["starboard_message_id"])
                embed = starboard_message.embeds[0]
                embed.set_footer(text=f"{self.star_emoji} {valid_count} | #{message.channel.name}")
                await starboard_message.edit(embed=embed)
            except discord.NotFound:
                pass
        else:
            embed = discord.Embed(description=message.content or "",
                                  color=discord.Color.gold(),
                                  timestamp=message.created_at)
            embed.set_author(name=message.author.display_name,
                             icon_url=message.author.display_avatar.url)
            embed.add_field(name="Source",
                            value=f"[Jump to message]({message.jump_url})",
                            inline=False)

            if message.attachments:
                for attachment in message.attachments:
                    if attachment.filename.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        embed.set_image(url=attachment.url)
                        break

            if message.embeds:
                for e in message.embeds:
                    if e.type in ("gifv", "image") and hasattr(e, "url"):
                        embed.set_image(url=e.url)
                        break

            embed.set_footer(text=f"{self.star_emoji} {valid_count} | #{message.channel.name}")
            starboard_message = await starboard_channel.send(embed=embed)

            self.starboard_data[message_id] = {
                "starboard_message_id": starboard_message.id,
                "original_channel_id": message.channel.id
            }
            self.save_data()

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        if user.bot or not reaction.message.guild:
            return

        if str(reaction.emoji) != self.star_emoji:
            return

        message = await self.ensure_full_message(reaction.message)
        if message is None:
            return

        message_id = str(message.id)
        starboard_channel_id = self.config.get_guild(message.guild.id, "starboard_channel_id")
        if not starboard_channel_id or message_id not in self.starboard_data:
            return

        starboard_channel = self.bot.get_channel(int(starboard_channel_id))
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        try:
            starboard_message = await starboard_channel.fetch_message(
                self.starboard_data[message_id]["starboard_message_id"])
        except discord.NotFound:
            return

        valid_count = await self.count_valid_reactors(reaction, message.author.id)
        star_threshold = self.config.get_guild(message.guild.id, "star_threshold", self.default_star_threshold)
        if valid_count < star_threshold:
            await starboard_message.delete()
            del self.starboard_data[message_id]
            self.save_data()
        else:
            embed = starboard_message.embeds[0]
            embed.set_footer(text=f"{self.star_emoji} {valid_count} | #{message.channel.name}")
            await starboard_message.edit(embed=embed)


async def setup(bot):
    cog = Starboard(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.set_starboard_slash)
        bot.tree.add_command(cog.set_star_threshold_slash)
        bot.tree.add_command(cog.scan_starboard_slash)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
