import discord
from discord.ext import commands
from discord import app_commands

EMBED_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"
EMBED_COLOR = 0xb5a12c  # gold-toned

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # SLASH COMMAND
    @app_commands.command(name="av", description="Get a user's avatar in full size.")
    @app_commands.describe(user="The user whose avatar you want to see")
    async def avatar_slash(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        await self.send_avatar(interaction, user)

    # LEGACY COMMAND
    @commands.command(name="av")
    async def avatar_legacy(self, ctx, user: discord.User = None):
        user = user or ctx.author
        embed = self.build_avatar_embed(user)
        await ctx.send(embed=embed)

    def build_avatar_embed(self, user: discord.User):
        avatar_url = user.display_avatar.replace(size=1024).url
        embed = discord.Embed(
            title=f"{user.display_name}'s Avatar",
            color=EMBED_COLOR
        )
        embed.set_image(url=avatar_url)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    async def send_avatar(self, interaction: discord.Interaction, user: discord.User):
        embed = self.build_avatar_embed(user)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = Avatar(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.avatar_slash)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
