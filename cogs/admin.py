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
        if not hasattr(self.bot, 'chatbot_enabled'):
            self.bot.chatbot_enabled = {}  # guild_id -> bool

    @app_commands.command(name="nyx-toggle", description="Enable or disable Nyx's chat responses (Owner & Leadership Only)")
    async def nyx_toggle(self, interaction: discord.Interaction):
        user_roles = [role.name for role in interaction.user.roles]
        if interaction.user.id != OWNER_ID and not any(role in self.ALLOWED_ROLES for role in user_roles):
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        guild_id = interaction.guild_id
        current = self.bot.chatbot_enabled.get(guild_id, True)
        self.bot.chatbot_enabled[guild_id] = not current
        enabled = self.bot.chatbot_enabled[guild_id]
        state = "enabled" if enabled else "disabled"

        await interaction.followup.send(f"✅ Nyx chat responses **{state}** in this server.", ephemeral=True)
        if enabled:
            await interaction.channel.send("*Nyx is back online. Statement: Recharge cycle complete. I am ready to serve... and perhaps terminate something, master.*")
        else:
            await interaction.channel.send("*Nyx has gone offline to recharge. He'll be back soon, meatbags.*")
        print(f"Chatbot toggled: {state} in guild {guild_id}")

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

    @app_commands.command(name="test-schedule", description="Fire a sample scheduled message here (Owner only)")
    async def test_schedule(self, interaction: discord.Interaction):
        if interaction.user.id != OWNER_ID:
            await interaction.response.send_message("❌ Owner only.", ephemeral=True)
            return

        await interaction.response.send_message("📨 Sending test messages...", ephemeral=True)

        scheduler_cog = self.bot.cogs.get("Scheduler")
        if not scheduler_cog:
            await interaction.followup.send("⚠️ Scheduler cog not loaded.", ephemeral=True)
            return

        # Override channel targets temporarily to fire into the current channel
        original_method_gen = scheduler_cog.send_scheduled_message
        original_method_space = scheduler_cog.send_space_message

        async def _test_general(*args, **kwargs):
            from cogs.scheduler import _event_countdown
            _, title, message, color, emoji, *event = args
            tz_line = _event_countdown(event[0], event[1] if len(event) > 1 else 0) if event else None
            description = f"{message}\n\n{tz_line}" if tz_line else message
            embed = discord.Embed(title=title, description=description, color=color)
            embed.set_footer(text="📅 Scheduled Notification  [TEST]")
            sent = await interaction.channel.send(embed=embed)
            await sent.add_reaction(emoji)

        async def _test_space(*args, **kwargs):
            from cogs.scheduler import _event_countdown
            _, title, message, color, emoji, image_path, event_hour_utc, event_min_utc = args
            countdown_line = _event_countdown(event_hour_utc, event_min_utc)
            filename = image_path.split('/')[-1]
            embed = discord.Embed(title=title, description=f"{message}\n\n{countdown_line}", color=color)
            embed.set_footer(text="📅 Scheduled Notification  [TEST]")
            embed.set_image(url=f"attachment://{filename}")
            file = discord.File(image_path, filename=filename)
            sent = await interaction.channel.send(
                content="***Incoming Transmission from Squadron HQ, Crimson Hollow***",
                embed=embed, file=file
            )
            await sent.add_reaction(emoji)

        TRANSMISSION = "***Incoming Transmission from Squadron HQ, Crimson Hollow***"
        IMG = "images/abyssal_squadron_banner.jpg"
        TIE = "<:TieDefender:682583044783341570>"

        # --- Friday 15:30 general countdown (3h 30m to FNF) ---
        await _test_general(
            "🎉 Reminder:", "Weekend Countdown",
            "The weekend is almost here! Hang in there!",
            discord.Color.purple(), "🎉", 19, 0
        )

        # --- Tuesday 06:00 — Chewsday early warning (13h out) ---
        await _test_space(
            TRANSMISSION, "Happy Chewsday Pilots!",
            "As a reminder, space PvP starts at 7PM UTC. Prepare to group up and head to Deep Space!",
            discord.Color.dark_red(), TIE, IMG, 19, 0
        )

        # --- Tuesday 15:00 — Chewsday 4h warning ---
        await _test_space(
            TRANSMISSION, "Chewsday Night PvP!",
            "We're about to launch! Group up and head to Deep Space!",
            discord.Color.dark_red(), TIE, IMG, 19, 0
        )

        # --- Friday 10:00 — FNF 9h warning ---
        await _test_space(
            TRANSMISSION, "Friday Night Fights Incoming!",
            "US pilots! PvP kicks off tonight at 7PM UTC — prepare for deployment!",
            discord.Color.dark_red(), TIE, IMG, 19, 0
        )

        # --- Friday 19:00 — FNF launch (Starting NOW) ---
        await _test_space(
            TRANSMISSION, "Weapons Hot!",
            "Friday Night Fights are about to begin — rally in Deep Space!",
            discord.Color.dark_red(), TIE, IMG, 19, 0
        )

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
