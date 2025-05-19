import discord
from discord.ext import commands
from discord import app_commands
from utils.configmanager import ConfigManager  # ✅ Centralized config

# === Welcome Embed Constants ===
EMBED_TITLE = "hi you,"
EMBED_DESCRIPTION = ("think of this place like the moment\n"
                     "right before the chorus hits\n"
                     "still, honest,,\n"
                     "a little sad\n"
                     "but somehow sweeter for it")
EMBED_IMAGE_URL = "https://i.pinimg.com/736x/c5/83/b6/c583b6f4ef35c73420ce15cbadb99250.jpg"
EMBED_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"
EMBED_COLOR = 0xb5a12c


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()

    def build_welcome_embed(self):
        embed = discord.Embed(title=EMBED_TITLE,
                              description=EMBED_DESCRIPTION,
                              color=EMBED_COLOR)
        embed.set_image(url=EMBED_IMAGE_URL)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    # === SEND EMBED ===

    @commands.command(name="welcome")
    async def legacy_welcome(self, ctx):
        channel_id = self.config.get("welcome_channel_id")
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Couldn't find the welcome channel.")
            return
        await channel.send(embed=self.build_welcome_embed())
        await ctx.send("✅ Sent the welcome embed.")

    @app_commands.command(
        name="welcome",
        description="Send the welcome embed to the welcome channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_welcome(self, interaction: discord.Interaction):
        channel_id = self.config.get("welcome_channel_id")
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Couldn't find the welcome channel.", ephemeral=True)
            return
        await channel.send(embed=self.build_welcome_embed())
        await interaction.response.send_message("✅ Welcome embed sent.",
                                                ephemeral=True)

    # === SET WELCOME CHANNEL ===

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome(self, ctx):
        self.config.set("welcome_channel_id", ctx.channel.id)
        await ctx.send(f"✅ {ctx.channel.mention} set as welcome channel.")

    @app_commands.command(
        name="setwelcome",
        description="Set this channel as the welcome channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome(self, interaction: discord.Interaction):
        self.config.set("welcome_channel_id", interaction.channel.id)
        await interaction.response.send_message(
            f"✅ {interaction.channel.mention} set as welcome channel.",
            ephemeral=True)


async def setup(bot):
    cog = Welcome(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_welcome)
        bot.tree.add_command(cog.slash_set_welcome)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
