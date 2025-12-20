import discord
from discord.ext import commands
from discord import app_commands

from utils.configmanager import ConfigManager
from utils.embed_factory import themed_embed


class NukeView(discord.ui.View):

    def __init__(self, author, channel):
        super().__init__(timeout=15)
        self.author = author
        self.channel = channel
        self.config = ConfigManager()

    async def on_timeout(self):
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True

    async def update_config(self, new_channel):
        config_key = self.config.get_key_by_value(self.channel.id)
        if not config_key:
            config_key = self.config.generate_key_from_name(self.channel.name)

        try:
            self.config.set(config_key, new_channel.id)
        except Exception:
            pass

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction,
                      button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ you can’t confirm this.", ephemeral=True)

        guild = self.channel.guild
        position = self.channel.position
        category = self.channel.category
        overwrites = self.channel.overwrites

        await self.channel.delete(reason=f"Nuked by {self.author}")

        new_channel = await guild.create_text_channel(
            name=self.channel.name,
            category=category,
            overwrites=overwrites,
            position=position,
            reason=f"Nuked by {self.author}")

        await self.update_config(new_channel)

        embed = themed_embed(
            config=self.config,
            guild_id=guild.id,
            title="☢️ Channel Nuked",
            description=
            f"{new_channel.mention} was recreated.\nNuked by: {self.author.mention}",
        )
        await new_channel.send(embed=embed)
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction,
                     button: discord.ui.Button):
        if interaction.user != self.author:
            return await interaction.response.send_message(
                "❌ you can’t cancel this.", ephemeral=True)

        await interaction.response.send_message("✅ nuke cancelled.",
                                                ephemeral=True)
        self.stop()


class Nuke(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()

    @app_commands.command(
        name="nuke",
        description=
        "Delete and recreate the current channel (confirmation required).")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_nuke(self, interaction: discord.Interaction):
        if not isinstance(interaction.channel, discord.TextChannel):
            return await interaction.response.send_message(
                "❌ this only works in text channels.", ephemeral=True)

        view = NukeView(interaction.user, interaction.channel)

        embed = themed_embed(
            config=self.config,
            guild_id=interaction.guild.id,
            title="💣 Confirm Nuke",
            description=
            "this will delete and recreate the channel.\ndo you want to continue?",
        )
        await interaction.response.send_message(embed=embed,
                                                view=view,
                                                ephemeral=True)


async def setup(bot):
    cog = Nuke(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_nuke)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
