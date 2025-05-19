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
        self.star_threshold = 2
        self.data_file = "starboard_data.json"
        self.starboard_data = self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r") as f:
                return json.load(f)
        return {}

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.starboard_data, f, indent=4)

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

    async def count_valid_reactors(self, reaction, author_id):
        count = 0
        async for user in reaction.users():
            if user.id != author_id and not user.bot:
                count += 1
        return count

    @commands.command(name="setstarboard")
    @commands.has_permissions(administrator=True)
    async def set_starboard_legacy(self, ctx):
        self.config.set("starboard_channel_id", ctx.channel.id)
        await ctx.send(f"✅ {ctx.channel.mention} set as starboard channel.")

    @app_commands.command(name="setstarboard",
                          description="Set this channel as the starboard.")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_starboard_slash(self, interaction: discord.Interaction):
        self.config.set("starboard_channel_id", interaction.channel.id)
        await interaction.response.send_message(
            f"✅ {interaction.channel.mention} set as starboard channel.",
            ephemeral=True)

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
        starboard_channel_id = self.config.get("starboard_channel_id")
        if not starboard_channel_id:
            return

        starboard_channel = self.bot.get_channel(int(starboard_channel_id))
        if not isinstance(starboard_channel, discord.TextChannel):
            return

        if message.channel.id == starboard_channel.id:
            return

        if message.stickers and not message.content and not message.attachments:
            return

        for r in message.reactions:
            if str(r.emoji) == self.star_emoji:
                valid_count = await self.count_valid_reactors(
                    r, message.author.id)
                break
        else:
            return

        if message_id in self.starboard_data:
            if valid_count >= self.star_threshold:
                try:
                    starboard_message = await starboard_channel.fetch_message(
                        self.starboard_data[message_id]["starboard_message_id"]
                    )
                    embed = starboard_message.embeds[0]
                    embed.set_footer(
                        text=
                        f"{self.star_emoji} {valid_count} | #{message.channel.name}"
                    )
                    await starboard_message.edit(embed=embed)
                except discord.NotFound:
                    pass
        elif valid_count >= self.star_threshold:
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
                    if attachment.filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".webp")):
                        embed.set_image(url=attachment.url)
                        break

            if message.embeds:
                for e in message.embeds:
                    if e.type in ("gifv", "image") and hasattr(e, "url"):
                        embed.set_image(url=e.url)
                        break

            embed.set_footer(
                text=
                f"{self.star_emoji} {valid_count} | #{message.channel.name}")
            starboard_message = await starboard_channel.send(embed=embed)
            await starboard_message.add_reaction(self.star_emoji)

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
        starboard_channel_id = self.config.get("starboard_channel_id")
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

        for r in message.reactions:
            if str(r.emoji) == self.star_emoji:
                valid_count = await self.count_valid_reactors(
                    r, message.author.id)
                break
        else:
            valid_count = 0

        if valid_count < self.star_threshold:
            await starboard_message.delete()
            del self.starboard_data[message_id]
            self.save_data()
        else:
            embed = starboard_message.embeds[0]
            embed.set_footer(
                text=
                f"{self.star_emoji} {valid_count} | #{message.channel.name}")
            await starboard_message.edit(embed=embed)


async def setup(bot):
    cog = Starboard(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.set_starboard_slash)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
