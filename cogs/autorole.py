import discord
from discord.ext import commands
import json

CONFIG_PATH = "config.json"

class AutoRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def load_role_id(self):
        try:
            with open(CONFIG_PATH, "r") as f:
                raw = json.load(f).get("auto_role_id")
                return int(raw) if raw else None
        except Exception as e:
            print(f"[AutoRole] Failed to load role ID: {e}")
            return None

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.bot:
            return  # Skip bots

        role_id = self.load_role_id()
        if role_id is None:
            print("[AutoRole] No auto_role_id found in config.json.")
            return

        role = member.guild.get_role(role_id)
        if not role:
            print(f"[AutoRole] Role with ID {role_id} not found in guild.")
            return

        try:
            await member.add_roles(role, reason="Auto-role on join")
            print(f"[AutoRole] Assigned role {role.name} to {member}.")
        except discord.Forbidden:
            print("[AutoRole] Missing permissions to assign role.")
        except Exception as e:
            print(f"[AutoRole] Error assigning role: {e}")

async def setup(bot):
    await bot.add_cog(AutoRole(bot))
