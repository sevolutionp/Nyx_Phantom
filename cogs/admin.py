# cogs/admin.py
import discord
from discord import app_commands
from discord.ext import commands
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
OWNER_ID = int(os.getenv("BOT_OWNER_ID"))

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    ALLOWED_ROLES = ["Leader", "Militia", "Officer", "Senior Officer", "Council Member"]

    @app_commands.command(name="status", description="Check bot status and uptime")
    async def status(self, interaction: discord.Interaction):
        """Check the bot's current status and uptime"""
        await interaction.response.defer()

        # Calculate uptime
        uptime_seconds = time.time() - self.start_time
        uptime_str = self.format_uptime(uptime_seconds)

        # Create status embed
        embed = discord.Embed(title="🤖 Nyx Phantom Status", color=discord.Color.blue())
        embed.add_field(name="📊 Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="🏠 Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="👥 Users", value=sum(guild.member_count for guild in self.bot.guilds), inline=True)
        embed.add_field(name="⚙️ Cogs Loaded", value=len(self.bot.cogs), inline=True)
        embed.add_field(name="📅 Scheduled Jobs", value="Active" if hasattr(self.bot, 'cogs') and 'Scheduler' in self.bot.cogs else "Inactive", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")

        await interaction.followup.send(embed=embed)

    @app_commands.command(name="reload", description="Reload scheduler cog (Owner & Leadership Roles Only)")
    async def reload(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)  # ✅ Correct way to defer

        async def do_reload():
            user_roles = [role.name for role in interaction.user.roles]
            print(f"👤 {interaction.user} roles: {user_roles}")

            if interaction.user.id == OWNER_ID or any(role in self.ALLOWED_ROLES for role in user_roles):
                try:
                    await self.bot.unload_extension("cogs.scheduler")  # ✅ Unload first
                    await self.bot.load_extension("cogs.scheduler")  # ✅ Reload fresh
                    await interaction.followup.send("♻️ Scheduler reloaded successfully!", ephemeral=True)  # ✅ Respond AFTER reload
                    print("✅ Scheduler fully reloaded.")
                except Exception as e:
                    await interaction.followup.send(f"⚠️ Reload failed: {e}", ephemeral=True)
                    print(f"❌ Reload failed: {e}")
            else:
                await interaction.followup.send("❌ You do not have permission to use this command.", ephemeral=True)

        self.bot.loop.create_task(do_reload())  # ✅ Now correctly inside `reload()`

    def format_uptime(self, seconds):
        """Format uptime seconds into a readable string"""
        days, remainder = divmod(int(seconds), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)

# Function to add the cog
async def setup(bot):
    await bot.add_cog(Admin(bot))
