import discord
from discord.ext import commands
from discord import app_commands
from utils.configmanager import ConfigManager

class NukeView(discord.ui.View):
    def __init__(self, author, channel):
        super().__init__(timeout=15)
        self.author = author
        self.channel = channel
        self.config = ConfigManager()

    async def update_config(self, new_channel):
        config_key = self.config.get_key_by_value(self.channel.id)
        if not config_key:
            config_key = self.config.generate_key_from_name(self.channel.name)
        try:
            self.config.set(config_key, new_channel.id)
        except Exception:
            pass

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
        overwrites = old_channel.overwrites

        # Check if old_channel was the system channel
        was_system_channel = guild.system_channel and (guild.system_channel.id == old_channel.id)

        await old_channel.delete()
        new_channel = await guild.create_text_channel(
            name=name,
            category=category,
            position=position,
            overwrites=overwrites
        )

        # If it was the system channel, restore the setting
        if was_system_channel:
            try:
                await guild.edit(system_channel=new_channel)
            except discord.Forbidden:
                await new_channel.send("⚠️ I couldn't set this as the system messages channel. Make sure I have the 'Manage Server' permission.")
            except Exception as e:
                await new_channel.send(f"⚠️ Unexpected error while setting system channel: `{e}`")

        await self.update_config(new_channel)

        embed = discord.Embed(
            title="☢️ Channel Nuked",
            description=f"{new_channel.mention} was recreated.\nNuked by: {self.author.mention}",
            color=discord.Color.red()
        )
        await new_channel.send(embed=embed)
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("You can't cancel someone else's nuke!", ephemeral=True)
            return

        # Delete the message containing the view
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            await interaction.response.send_message("❎ I don't have permission to delete this message.", ephemeral=True)
            return

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
    cog = Nuke(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_nuke)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
