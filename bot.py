# bot.py
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Validate required environment variables
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN not found in .env file!")
    print("Please create a .env file with your bot token.")
    print("See .env.example for the required format.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for role checks

class NyxBot(commands.Bot):
    async def setup_hook(self):
        try:
            await self.load_extension("cogs.admin")
            await self.load_extension("cogs.scheduler")
            await self.load_extension("cogs.chatbot")
            await self.load_extension("cogs.lore_scraper")
            print("✅ All cogs loaded successfully.")
        except Exception as e:
            print(f"❌ Failed to load cogs: {e}")
            sys.exit(1)

bot = NyxBot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"🤖 Bot is ready! Connected to {len(bot.guilds)} server(s)")
    try:
        # Sync per-guild for instant propagation
        for guild in bot.guilds:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"  Synced to {guild.name}")
        print(f"✅ Slash commands synced to {len(bot.guilds)} guild(s)")
    except Exception as e:
        print(f"⚠️ Failed to sync slash commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    else:
        await ctx.send(f"⚠️ An error occurred: {error}")
        print(f"Command error: {error}")
@bot.event
async def on_message(message):
    # Process commands (for any prefix-based commands, though currently using slash)
    await bot.process_commands(message)
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Invalid bot token! Please check your DISCORD_TOKEN in .env")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        sys.exit(1)
