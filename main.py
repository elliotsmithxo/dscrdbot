import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from keep_alive import keep_alive  # ❤️ Heartbeat

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN_TEST")

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.guilds = True
intents.members = True  # Required if you're using on_member_join for autorole

bot = commands.Bot(command_prefix=",", intents=intents)

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"⚠️ Sync failed: {e}")
    print(f"✅ Logged in as {bot.user}")

async def load_extensions():
    await bot.load_extension("cogs.starboard")
    await bot.load_extension("cogs.welcome")
    await bot.load_extension("cogs.nuke")
    #await bot.load_extension("cogs.autorole")  # Only if you have it
    await bot.load_extension("cogs.moderation")
    # Add more cogs here if needed

async def main():
    keep_alive()  # 🔁 Keeps your bot alive on Replit
    await load_extensions()
    await bot.start(TOKEN)

asyncio.run(main())
