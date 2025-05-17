from discord.ext import commands
from discord import app_commands, Interaction
import discord
import json
import os

BANLOG_FILE = "banlog.json"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.banlog = self.load_banlog()

    def load_banlog(self):
        if os.path.exists(BANLOG_FILE):
            with open(BANLOG_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_banlog(self):
        with open(BANLOG_FILE, "w") as f:
            json.dump(self.banlog, f, indent=4)

    # --- BAN ---

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_legacy(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        self.banlog[str(member.id)] = reason
        self.save_banlog()
        await ctx.send(f"✅ Banned {member.mention} for: {reason}")

    @app_commands.command(name="ban", description="Ban a member or user ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    @app_commands.describe(member="Select a server member to ban", user_id="Or provide a user ID", reason="Reason for the ban")
    async def ban_slash(self, interaction: Interaction, member: discord.Member = None, user_id: str = None, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)

        if member:
            await member.ban(reason=reason)
            self.banlog[str(member.id)] = reason
            self.save_banlog()
            await interaction.followup.send(f"✅ Banned {member.mention} for: {reason}")
        elif user_id:
            try:
                user = await self.bot.fetch_user(int(user_id))
                await interaction.guild.ban(user, reason=reason)
                self.banlog[str(user.id)] = reason
                self.save_banlog()
                await interaction.followup.send(f"✅ Banned `{user}` (ID: {user.id}) for: {reason}")
            except Exception as e:
                await interaction.followup.send(f"❌ Failed to ban user ID {user_id}: {e}")
        else:
            await interaction.followup.send("⚠️ Please specify either a member or a user ID.")

    # --- KICK ---

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_legacy(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 Kicked {member.mention} for: {reason}")

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick_slash(self, interaction: Interaction, member: discord.Member, reason: str = "No reason provided"):
        await interaction.response.defer(ephemeral=True)
        await member.kick(reason=reason)
        await interaction.followup.send(f"👢 Kicked {member.mention} for: {reason}")

    # --- UNBAN ---

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban_legacy(self, ctx, user_id: int):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        self.banlog.pop(str(user_id), None)
        self.save_banlog()
        await ctx.send(f"🔓 Unbanned {user.name}")

    @app_commands.command(name="unban", description="Unban a user by their ID.")
    @app_commands.checks.has_permissions(ban_members=True)
    async def unban_slash(self, interaction: Interaction, user_id: str):
        await interaction.response.defer(ephemeral=True)
        user = await self.bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)
        self.banlog.pop(user_id, None)
        self.save_banlog()
        await interaction.followup.send(f"🔓 Unbanned {user.name}")

    # --- PURGE ---

    @commands.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge_legacy(self, ctx, amount: int):
        if 1 <= amount <= 1000:
            deleted = await ctx.channel.purge(limit=amount)
            await ctx.send(f"🧹 Deleted {len(deleted)} messages.", delete_after=5)
        else:
            await ctx.send("⚠️ Amount must be between 1 and 1000.")

    @app_commands.command(name="purge", description="Delete a number of messages (1–1000).")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purge_slash(self, interaction: Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        if 1 <= amount <= 1000:
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"🧹 Deleted {len(deleted)} messages.", ephemeral=True)
        else:
            await interaction.followup.send("⚠️ Amount must be between 1 and 1000.", ephemeral=True)

async def setup(bot):
    cog = Moderation(bot)
    await bot.add_cog(cog)
    try:
        bot.tree.add_command(cog.ban_slash)
        bot.tree.add_command(cog.kick_slash)
        bot.tree.add_command(cog.unban_slash)
        bot.tree.add_command(cog.purge_slash)
    except discord.app_commands.errors.CommandAlreadyRegistered:
        pass
