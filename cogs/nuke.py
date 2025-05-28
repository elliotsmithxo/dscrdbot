from discord.ext import commands
from discord import app_commands
import discord
from .nukeview import NukeView  # assuming your NukeView is in another file

class Nuke(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ✅ LEGACY COMMAND with permission check
    @commands.command(name="nuke")
    @commands.has_permissions(manage_channels=True)
    async def legacy_nuke(self, ctx):
        view = NukeView(author=ctx.author, channel=ctx.channel)
        embed = discord.Embed(
            title="💣 Confirm Nuke",
            description="This will delete and recreate the channel.\nDo you want to continue?",
            color=discord.Color.orange()
        )
        await ctx.send(embed=embed, view=view)

    # ✅ SLASH COMMAND with permission check
    @app_commands.command(name="nuke", description="Nuke this channel (deletes and recreates it).")
    @app_commands.checks.has_permissions(manage_channels=True)
    async def slash_nuke(self, interaction: discord.Interaction):
        view = NukeView(author=interaction.user, channel=interaction.channel)
        embed = discord.Embed(
            title="💣 Confirm Nuke",
            description="This will delete and recreate the channel.\nDo you want to continue?",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed, view=view)

    # ✅ Handle errors gracefully
    @legacy_nuke.error
    async def legacy_nuke_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("🚫 You need the `Manage Channels` permission to use this command.")

    @slash_nuke.error
    async def slash_nuke_error(self, interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(
                "🚫 You need the `Manage Channels` permission to use this command.",
                ephemeral=True
            )

async def setup(bot):
    cog = Nuke(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_nuke)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
