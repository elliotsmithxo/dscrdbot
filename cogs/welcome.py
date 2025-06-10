import discord
from discord.ext import commands
from discord import app_commands
from utils.configmanager import ConfigManager  # ✅ Centralized config

# === Default Welcome Embed Values ===
DEFAULT_EMBED_TITLE = "hi you,"
DEFAULT_EMBED_DESCRIPTION = ("think of this place like the moment\n"
                            "right before the chorus hits\n"
                            "still, honest,,\n"
                            "a little sad\n"
                            "but somehow sweeter for it")
DEFAULT_EMBED_IMAGE_URL = (
    "https://i.pinimg.com/736x/c5/83/b6/c583b6f4ef35c73420ce15cbadb99250.jpg"
)
DEFAULT_EMBED_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"
EMBED_COLOR = 0xb5a12c


class Welcome(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()

    def build_welcome_embed(self):
        title = self.config.get("welcome_embed_title", DEFAULT_EMBED_TITLE)
        description = self.config.get(
            "welcome_embed_description", DEFAULT_EMBED_DESCRIPTION
        )
        image_url = self.config.get(
            "welcome_embed_image_url", DEFAULT_EMBED_IMAGE_URL
        )
        footer = self.config.get("welcome_embed_footer", DEFAULT_EMBED_FOOTER)

        embed = discord.Embed(
            title=title,
            description=description,
            color=EMBED_COLOR,
        )
        embed.set_image(url=image_url)
        embed.set_footer(text=footer)
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

    # === SET WELCOME EMBED FIELDS ===

    @commands.command(name="setwelcomeembed")
    @commands.has_permissions(administrator=True)
    async def legacy_set_welcome_embed(self, ctx, *, args: str = ""):
        """Update welcome embed configuration via a legacy command."""
        updates = self.parse_embed_args(args)
        for key, value in updates.items():
            self.config.set(key, value)
        if updates:
            await ctx.send("✅ Updated welcome embed.")
        else:
            await ctx.send("❌ No valid fields provided.")

    @app_commands.command(
        name="setwelcomeembed",
        description="Update the welcome embed settings.",
    )
    @app_commands.describe(
        title="Embed title",
        description="Embed description",
        image="Image URL",
        footer="Footer text",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def slash_set_welcome_embed(
        self,
        interaction: discord.Interaction,
        title: str | None = None,
        description: str | None = None,
        image: str | None = None,
        footer: str | None = None,
    ):
        updates = {}
        if title is not None:
            updates["welcome_embed_title"] = title
        if description is not None:
            updates["welcome_embed_description"] = description
        if image is not None:
            updates["welcome_embed_image_url"] = image
        if footer is not None:
            updates["welcome_embed_footer"] = footer
        for key, value in updates.items():
            self.config.set(key, value)

        if updates:
            await interaction.response.send_message(
                "✅ Updated welcome embed.", ephemeral=True
            )
        else:
            await interaction.response.send_message(
                "❌ No changes provided.", ephemeral=True
            )

    # === UTILITIES ===

    def parse_embed_args(self, arg_str: str) -> dict:
        """Parse key:value pairs from a command string."""
        import shlex

        tokens = shlex.split(arg_str)
        updates = {}
        for token in tokens:
            if token.startswith("title:"):
                updates["welcome_embed_title"] = token.split("title:", 1)[1]
            elif token.startswith("description:"):
                updates["welcome_embed_description"] = token.split(
                    "description:", 1
                )[1]
            elif token.startswith("image:"):
                updates["welcome_embed_image_url"] = token.split("image:", 1)[1]
            elif token.startswith("footer:"):
                updates["welcome_embed_footer"] = token.split("footer:", 1)[1]
        return updates


async def setup(bot):
    cog = Welcome(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.slash_welcome)
        bot.tree.add_command(cog.slash_set_welcome)
        bot.tree.add_command(cog.slash_set_welcome_embed)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
