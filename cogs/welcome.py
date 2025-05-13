import discord
from discord.ext import commands
import json

EMBED_TITLE = "hi,"
EMBED_DESCRIPTION = (
    "for those who aimlessly wander\n"
    "in search of something,,\n"
    "a final resting place\n"
    "for lost memories..."
)
EMBED_IMAGE_URL = "https://i.pinimg.com/736x/97/4c/0f/974c0f19f6b394b0f610f162d8a2057d.jpg"
EMBED_FOOTER = "⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺"
EMBED_COLOR = 0xE3E5E8
CONFIG_PATH = "config.json"

class Welcome(commands.Cog):
    def build_welcome_embed(self):
        embed = discord.Embed(
            title=EMBED_TITLE,
            description=EMBED_DESCRIPTION,
            color=EMBED_COLOR
        )
        embed.set_image(url=EMBED_IMAGE_URL)
        embed.set_footer(text=EMBED_FOOTER)
        return embed

    def load_channel_id(self, key):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f).get(key)
        except Exception:
            return None

    @commands.command(name="welcome")
    async def legacy_welcome(self, ctx):
        channel_id = self.load_channel_id("welcome_channel_id")
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await ctx.send("❌ Couldn't find the welcome channel.")
            return
        await channel.send(embed=self.build_welcome_embed())
        await ctx.send("✅ Sent the welcome embed.")

    @discord.app_commands.command(
        name="welcome",
        description="Send the poetic welcome embed to the welcome channel"
    )
    @discord.app_commands.checks.has_permissions(administrator=True)
    async def slash_welcome(self, interaction: discord.Interaction):
        channel_id = self.load_channel_id("welcome_channel_id")
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("❌ Couldn't find the welcome channel.", ephemeral=True)
            return
        await channel.send(embed=self.build_welcome_embed())
        await interaction.response.send_message("✅ Welcome embed sent.", ephemeral=True)

async def setup(bot):
    if not bot.get_cog("Welcome"):
        await bot.add_cog(Welcome())
