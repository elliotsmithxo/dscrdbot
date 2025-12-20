import time
import discord
from discord.ext import commands
from discord import app_commands

from utils.configmanager import ConfigManager
from utils.embed_factory import themed_embed, DEFAULT_EMBED_FOOTER


class ProfileView(discord.ui.View):
    """Buttons to toggle between avatar / banner / profile."""
    def __init__(self, cog: "Avatar", invoker_id: int, guild_id: int, target_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.invoker_id = invoker_id
        self.guild_id = guild_id
        self.target_id = target_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.invoker_id:
            await interaction.response.send_message("❌ only the command invoker can use these buttons.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        # (4) polish: disable buttons when expired so it doesn’t look “broken”
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True

    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.secondary)
    async def show_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self.cog.fetch_user_cached(self.target_id)
        embed = self.cog.build_avatar_embed(self.guild_id, user)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.secondary)
    async def show_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self.cog.fetch_user_cached(self.target_id)
        embed = self.cog.build_banner_embed(self.guild_id, user)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Profile", style=discord.ButtonStyle.primary)
    async def show_profile(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = await self.cog.fetch_user_cached(self.target_id)
        embed = self.cog.build_profile_embed(self.guild_id, user)
        await interaction.response.edit_message(embed=embed, view=self)


class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigManager()

        # (7) simple cache for fetch_user (banner/accent needs fetching)
        # user_id -> (discord.User, expires_at_monotonic)
        self._user_cache: dict[int, tuple[discord.User, float]] = {}
        self._cache_ttl_seconds = 300  # 5 minutes

    async def fetch_user_cached(self, user_id: int) -> discord.User:
        now = time.monotonic()
        cached = self._user_cache.get(user_id)
        if cached and cached[1] > now:
            return cached[0]

        user = await self.bot.fetch_user(user_id)
        self._user_cache[user_id] = (user, now + self._cache_ttl_seconds)
        return user

    def _accent_color_int(self, user: discord.User) -> int | None:
        if getattr(user, "accent_color", None):
            return int(user.accent_color.value)
        return None

    # -------------------------
    # Embed builders (all themed)
    # -------------------------

    def build_avatar_embed(self, guild_id: int, user: discord.User) -> discord.Embed:
        avatar_url = user.display_avatar.replace(size=1024).url
        embed = themed_embed(
            config=self.config,
            guild_id=guild_id,
            title=f"{user.display_name}'s Avatar",
            footer=DEFAULT_EMBED_FOOTER,
        )
        embed.set_image(url=avatar_url)
        return embed

    def build_banner_embed(self, guild_id: int, user: discord.User) -> discord.Embed:
        banner = getattr(user, "banner", None)

        # (polish) If no banner: fall back to accent color if possible
        if not banner:
            accent = self._accent_color_int(user)
            embed = themed_embed(
                config=self.config,
                guild_id=guild_id,
                title=f"{user.display_name}'s Banner",
                description="no profile banner set.\nshowing their profile accent color instead.",
                footer=DEFAULT_EMBED_FOOTER,
                color=accent,  # if None, themed_embed uses global server color
            )
            embed.set_thumbnail(url=user.display_avatar.replace(size=256).url)
            if accent is not None:
                embed.add_field(name="Accent Color", value=f"`#{accent:06x}`", inline=True)
            else:
                embed.add_field(name="Accent Color", value="(none set)", inline=True)
            return embed

        banner_url = banner.replace(size=1024).url
        embed = themed_embed(
            config=self.config,
            guild_id=guild_id,
            title=f"{user.display_name}'s Banner",
            footer=DEFAULT_EMBED_FOOTER,
        )
        embed.set_image(url=banner_url)
        return embed

    def build_profile_embed(self, guild_id: int, user: discord.User) -> discord.Embed:
        banner = getattr(user, "banner", None)
        accent = self._accent_color_int(user)

        # If no banner, we allow the embed color to become accent (if present)
        color_override = accent if (not banner and accent is not None) else None

        embed = themed_embed(
            config=self.config,
            guild_id=guild_id,
            title=f"{user.display_name}'s Profile",
            footer=DEFAULT_EMBED_FOOTER,
            color=color_override,
        )

        embed.set_thumbnail(url=user.display_avatar.replace(size=256).url)

        if banner:
            embed.set_image(url=banner.replace(size=1024).url)
        else:
            embed.add_field(name="Banner", value="(none set)", inline=True)
            if accent is not None:
                embed.add_field(name="Accent Color", value=f"`#{accent:06x}`", inline=True)
            else:
                embed.add_field(name="Accent Color", value="(none set)", inline=True)

        return embed

    # -------------------------
    # SLASH: /av /banner /profile
    # -------------------------

    @app_commands.command(name="av", description="Get a user's avatar in full size.")
    @app_commands.describe(user="The user whose avatar you want to see")
    async def avatar_slash(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        embed = self.build_avatar_embed(interaction.guild.id, user)
        view = ProfileView(self, interaction.user.id, interaction.guild.id, user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="banner", description="Get a user's profile banner (or accent fallback).")
    @app_commands.describe(user="The user whose banner you want to see")
    async def banner_slash(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        fetched_user = await self.fetch_user_cached(user.id)
        embed = self.build_banner_embed(interaction.guild.id, fetched_user)
        view = ProfileView(self, interaction.user.id, interaction.guild.id, user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="profile", description="Show avatar + banner in one embed (with accent fallback).")
    @app_commands.describe(user="The user whose profile you want to see")
    async def profile_slash(self, interaction: discord.Interaction, user: discord.User = None):
        user = user or interaction.user
        fetched_user = await self.fetch_user_cached(user.id)
        embed = self.build_profile_embed(interaction.guild.id, fetched_user)
        view = ProfileView(self, interaction.user.id, interaction.guild.id, user.id)
        await interaction.response.send_message(embed=embed, view=view)

    # -------------------------
    # PREFIX: ,av ,banner ,profile
    # -------------------------

    @commands.command(name="av")
    async def avatar_prefix(self, ctx: commands.Context, user: discord.User = None):
        user = user or ctx.author
        embed = self.build_avatar_embed(ctx.guild.id, user)
        view = ProfileView(self, ctx.author.id, ctx.guild.id, user.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="banner")
    async def banner_prefix(self, ctx: commands.Context, user: discord.User = None):
        user = user or ctx.author
        fetched_user = await self.fetch_user_cached(user.id)
        embed = self.build_banner_embed(ctx.guild.id, fetched_user)
        view = ProfileView(self, ctx.author.id, ctx.guild.id, user.id)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="profile")
    async def profile_prefix(self, ctx: commands.Context, user: discord.User = None):
        user = user or ctx.author
        fetched_user = await self.fetch_user_cached(user.id)
        embed = self.build_profile_embed(ctx.guild.id, fetched_user)
        view = ProfileView(self, ctx.author.id, ctx.guild.id, user.id)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    cog = Avatar(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.avatar_slash)
        bot.tree.add_command(cog.banner_slash)
        bot.tree.add_command(cog.profile_slash)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
