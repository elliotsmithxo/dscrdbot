import discord
from discord.ext import commands
from discord import app_commands
import json

CONFIG_PATH = "config.json"

SPECIAL_NAME_KEYS = {
    "έναστρος-ουρανός": "starboard_channel_id",
    "welcome": "welcome_channel_id"
}

class NukeView(discord.ui.View):
    def __init__(self, author, channel):
        super().__init__(timeout=15)
        self.author = author
        self.channel = channel

    async def update_config(self, new_channel):
        config_key = None
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            for key, value in config.items():
                if str(value) == str(self.channel.id):
                    config_key = key
                    break
            if config_key:
                config[config_key] = new_channel.id
                with open(CONFIG_PATH, "w") as f:
                    json.dump(config, f, indent=4)
                print(f"[Nuke] Updated {config_key} to {new_channel.id}")
        except Exception as e:
            print(f"[ERROR] Failed to update config.json: {e}")


    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't confirm someone else's nuke!", ephemeral=True)
            return

        guild = interaction.guild
        old_channel = self.channel
        position = old_channel.position
        name = old_channel.name
        category = old_channel.category

        await old_channel.delete()
        new_channel = await guild.create_text_channel(name=name, category=category, position=position)

        await self.update_config(new_channel)

        embed = discord.Embed(
            title="☢️ Channel Nuked",
            description=f"{new_channel.mention} was recreated.\nNuked by: {self.author.mention}",
            color=discord.Color.red()
        )
        await new_channel.send(embed=embed)
        await interaction.response.defer()  # Cleanly closes the view

        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't cancel someone else's nuke!", ephemeral=True)
            return

        await interaction.response.send_message("❎ Nuke canceled.", ephemeral=True)
        self.stop()

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="nuke")
    async def legacy_nuke(self, ctx):
        view = NukeView(author=ctx.author, channel=ctx.channel)
        embed = discord.Embed(
            title="💣 Confirm Nuke",
            description="This will delete and recreate the channel.\nDo you want to continue?",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, view=view)

    @app_commands.command(name="nuke", description="Nuke this channel (deletes and recreates it).")
    async def slash_nuke(self, interaction: discord.Interaction):
        view = NukeView(author=interaction.user, channel=interaction.channel)
        embed = discord.Embed(
            title="💣 Confirm Nuke",
            description="This will delete and recreate the channel.\nDo you want to continue?",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    if not bot.get_cog("Nuke"):
        await bot.add_cog(Nuke(bot))
