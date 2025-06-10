import discord
from discord.ext import commands
from discord import app_commands
from utils.configmanager import ConfigManager  # ✅ Centralized config

# === Welcome Embed Defaults ===
DEFAULT_EMBED_TITLE = "hi you,"
DEFAULT_EMBED_DESCRIPTION = (
    "think of this place like the moment\n"
    "right before the chorus hits\n"
    "still, honest,,\n"
    "a little sad\n"
    "but somehow sweeter for it"
)
DEFAULT_EMBED_IMAGE_URL = (
    "https://i.pinimg.com/736x/c5/83/b6/c583b6f4ef35c73420ce15cbadb99250.jpg"
)
DEFAULT_EMBED_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"
DEFAULT_EMBED_COLOR = 0xb5a12c


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()

    def build_welcome_embed(self, guild_id: int):
        title = self.config.get_guild(guild_id, "welcome_title", DEFAULT_EMBED_TITLE)
        description = self.config.get_guild(
            guild_id, "welcome_description", DEFAULT_EMBED_DESCRIPTION
        )
        image = self.config.get_guild(guild_id, "welcome_image", DEFAULT_EMBED_IMAGE_URL)
        footer = self.config.get_guild(guild_id, "welcome_footer", DEFAULT_EMBED_FOOTER)
        color = self.config.get_guild(guild_id, "welcome_color", DEFAULT_EMBED_COLOR)
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_image(url=image)
        embed.set_footer(text=footer)
        return embed

    # === SEND EMBED ===

    @commands.command(name="welcome")
    async def legacy_welcome(self, ctx):
        channel_id = self.config.get_guild(ctx.guild.id, "welcome_channel_id")
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Couldn't find the welcome channel.")
            return
        await channel.send(embed=self.build_welcome_embed(ctx.guild.id))
        await ctx.send("✅ Sent the welcome embed.")

    @app_commands.command(
        name="welcome",
        description="Send the welcome embed to the welcome channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_welcome(self, interaction: discord.Interaction):
        channel_id = self.config.get_guild(interaction.guild.id, "welcome_channel_id")
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ Couldn't find the welcome channel.", ephemeral=True)
            return
        await channel.send(embed=self.build_welcome_embed(interaction.guild.id))
        await interaction.response.send_message("✅ Welcome embed sent.",
                                                ephemeral=True)

    # === SET WELCOME CHANNEL ===

    @commands.command(name="setwelcome")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome(self, ctx):
        self.config.set_guild(ctx.guild.id, "welcome_channel_id", ctx.channel.id)
        await ctx.send(f"✅ {ctx.channel.mention} set as welcome channel.")

    @app_commands.command(
        name="setwelcome",
        description="Set this channel as the welcome channel.")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome(self, interaction: discord.Interaction):
        self.config.set_guild(interaction.guild.id, "welcome_channel_id", interaction.channel.id)
        await interaction.response.send_message(
            f"✅ {interaction.channel.mention} set as welcome channel.",
            ephemeral=True)

    # === CUSTOMIZATION COMMANDS ===

    @commands.command(name="setwelcometitle")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_title(self, ctx, *, title: str):
        self.config.set_guild(ctx.guild.id, "welcome_title", title)
        await ctx.send("✅ Welcome title updated.")

    @app_commands.command(name="setwelcometitle", description="Set the welcome embed title")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_title(self, interaction: discord.Interaction, title: str):
        self.config.set_guild(interaction.guild.id, "welcome_title", title)
        await interaction.response.send_message("✅ Welcome title updated.", ephemeral=True)

    @commands.command(name="setwelcomedescription")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_description(self, ctx, *, description: str):
        self.config.set_guild(ctx.guild.id, "welcome_description", description)
        await ctx.send("✅ Welcome description updated.")

    @app_commands.command(name="setwelcomedescription", description="Set the welcome embed description")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_description(self, interaction: discord.Interaction, description: str):
        self.config.set_guild(interaction.guild.id, "welcome_description", description)
        await interaction.response.send_message("✅ Welcome description updated.", ephemeral=True)

    @commands.command(name="setwelcomeimage")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_image(self, ctx, image_url: str):
        self.config.set_guild(ctx.guild.id, "welcome_image", image_url)
        await ctx.send("✅ Welcome image updated.")

    @app_commands.command(name="setwelcomeimage", description="Set the welcome embed image URL")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_image(self, interaction: discord.Interaction, image_url: str):
        self.config.set_guild(interaction.guild.id, "welcome_image", image_url)
        await interaction.response.send_message("✅ Welcome image updated.", ephemeral=True)

    @commands.command(name="setwelcomefooter")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_footer(self, ctx, *, footer: str):
        self.config.set_guild(ctx.guild.id, "welcome_footer", footer)
        await ctx.send("✅ Welcome footer updated.")

    @app_commands.command(name="setwelcomefooter", description="Set the welcome embed footer")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_footer(self, interaction: discord.Interaction, footer: str):
        self.config.set_guild(interaction.guild.id, "welcome_footer", footer)
        await interaction.response.send_message("✅ Welcome footer updated.", ephemeral=True)

    @commands.command(name="setwelcomecolor")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_color(self, ctx, color: str):
        value = int(color.lstrip('#'), 16)
        self.config.set_guild(ctx.guild.id, "welcome_color", value)
        await ctx.send("✅ Welcome color updated.")

    @app_commands.command(name="setwelcomecolor", description="Set the welcome embed color (hex)")
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_color(self, interaction: discord.Interaction, color: str):
        value = int(color.lstrip('#'), 16)
        self.config.set_guild(interaction.guild.id, "welcome_color", value)
        await interaction.response.send_message("✅ Welcome color updated.", ephemeral=True)


async def setup(bot):
    cog = Welcome(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_welcome)
        bot.tree.add_command(cog.slash_set_welcome)
        bot.tree.add_command(cog.slash_set_welcome_title)
        bot.tree.add_command(cog.slash_set_welcome_description)
        bot.tree.add_command(cog.slash_set_welcome_image)
        bot.tree.add_command(cog.slash_set_welcome_footer)
        bot.tree.add_command(cog.slash_set_welcome_color)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
