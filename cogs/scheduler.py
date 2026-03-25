# cogs/scheduler.py
import discord
from datetime import datetime, timezone
from discord.ext import commands
import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


def _event_countdown(event_hour_utc: int, event_min_utc: int = 0) -> str:
    """Returns a Discord Unix timestamp line that renders in each user's local time."""
    now = datetime.now(timezone.utc)
    event_utc = now.replace(hour=event_hour_utc, minute=event_min_utc, second=0, microsecond=0)
    ts = int(event_utc.timestamp())
    return f"⏱️ Starts <t:{ts}:R> · <t:{ts}:t>"


load_dotenv()
TEST_CHANNEL_ID = int(os.getenv("TEST_CHANNEL_ID"))
GUILD_CHANNEL_ID = int(os.getenv("GUILD_CHANNEL_ID", "0"))
SPACE_ID = int(os.getenv("SPACE_ID", "0"))

class Scheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)
        self._scheduler_started = False

    @commands.Cog.listener()
    async def on_ready(self):
        if not self._scheduler_started:
            self.schedule_tasks()
            self.scheduler.start()
            self._scheduler_started = True
            print("✅ Scheduler started.")

    def cog_unload(self):
        print("🛑 Unloading scheduler... stopping all tasks.")
        self.scheduler.shutdown(wait=True)
        print("✅ APScheduler shut down.")


    def schedule_tasks(self):
        # Monday 09:00 UTC / 4:00 AM EST / 5:00 AM EDT
        self.scheduler.add_job(
            self.send_scheduled_message,
            CronTrigger(day_of_week='mon', hour=9, minute=0, timezone=timezone.utc),
            args=["🚀 Motivation:", "Motivation Monday", "New week, new goals! Let's get started!", discord.Color.blue(), "🚀"]
        )

        # Friday 15:30 UTC / 10:30 AM EST / 11:30 AM EDT
        self.scheduler.add_job(
            self.send_scheduled_message,
            CronTrigger(day_of_week='fri', hour=15, minute=30, timezone=timezone.utc),
            args=["🎉 Reminder:", "Weekend Countdown", "The weekend is almost here! Hang in there!", discord.Color.purple(), "🎉"]
        )

        # Saturday 09:00 UTC / 4:00 AM EST / 5:00 AM EDT
        self.scheduler.add_job(
            self.send_scheduled_message,
            CronTrigger(day_of_week='sat', hour=9, minute=0, timezone=timezone.utc),
            args=["🔥 Fun Reminder:", "Saturday Fun!", "Enjoy your weekend and take a break!", discord.Color.red(), "🔥"]
        )

        # Sunday 17:30 UTC / 12:30 PM EST / 1:30 PM EDT
        self.scheduler.add_job(
            self.send_scheduled_message,
            CronTrigger(day_of_week='sun', hour=17, minute=30, timezone=timezone.utc),
            args=["☀️ Reminder:", "Sunday Reminder", "Good Afternoon! It's Sunday afternoon, make sure to get rest for Monday!", discord.Color.gold(), "☀️"]
        )

        # Tuesday 06:00 UTC / 1:00 AM EST / 2:00 AM EDT  →  PvP at 19:00 UTC (13h away)
        self.scheduler.add_job(
            self.send_space_message,
            CronTrigger(day_of_week='tue', hour=6, minute=0, timezone=timezone.utc),
            args=["***Incoming Transmission from Squadron HQ, Crimson Hollow***", "Happy Chewsday Pilots!", "As a reminder, space PvP starts at 7PM UTC. Prepare to group up and head to Deep Space!", discord.Color.dark_red(), "<:TieDefender:682583044783341570>", "images/abyssal_squadron_banner.jpg", 19, 0]
        )

        # Tuesday 15:00 UTC / 10:00 AM EST / 11:00 AM EDT  →  PvP at 19:00 UTC (4h away)
        self.scheduler.add_job(
            self.send_space_message,
            CronTrigger(day_of_week='tue', hour=15, minute=0, timezone=timezone.utc),
            args=["***Incoming Transmission from Squadron HQ, Crimson Hollow***", "Chewsday Night PvP!", "We're about to launch! Group up and head to Deep Space!", discord.Color.dark_red(), "<:TieDefender:682583044783341570>", "images/abyssal_squadron_banner.jpg", 19, 0]
        )

        # Friday 10:00 UTC / 5:00 AM EST / 6:00 AM EDT  →  PvP at 19:00 UTC (9h away)
        self.scheduler.add_job(
            self.send_space_message,
            CronTrigger(day_of_week='fri', hour=10, minute=0, timezone=timezone.utc),
            args=["***Incoming Transmission from Squadron HQ, Crimson Hollow***", "Friday Night Fights Incoming!", "US pilots! PvP kicks off tonight at 7PM UTC — prepare for deployment!", discord.Color.dark_red(), "<:TieDefender:682583044783341570>", "images/abyssal_squadron_banner.jpg", 19, 0]
        )

        # Friday 19:00 UTC / 2:00 PM EST / 3:00 PM EDT  →  PvP starting NOW
        self.scheduler.add_job(
            self.send_space_message,
            CronTrigger(day_of_week='fri', hour=19, minute=0, timezone=timezone.utc),
            args=["***Incoming Transmission from Squadron HQ, Crimson Hollow***", "Weapons Hot!", "Friday Night Fights are about to begin — rally in Deep Space!", discord.Color.dark_red(), "<:TieDefender:682583044783341570>", "images/abyssal_squadron_banner.jpg", 19, 0]
        )

    async def send_scheduled_message(self, standard_message, title, message, color, emoji, event_hour_utc: int = None, event_min_utc: int = 0):
        countdown = _event_countdown(event_hour_utc, event_min_utc) if event_hour_utc is not None else None
        description = f"{message}\n\n{countdown}" if countdown else message
        for channel_id in [TEST_CHANNEL_ID, GUILD_CHANNEL_ID]:
            if not channel_id:
                continue
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(standard_message)
                embed = discord.Embed(title=title, description=description, color=color)
                embed.set_footer(text="📅 Scheduled Notification")
                sent_message = await channel.send(embed=embed)
                await sent_message.add_reaction(emoji)
            else:
                print(f"⚠️ Channel with ID {channel_id} not found!")

    async def send_space_message(self, standard_message, title, message, color, emoji, image_path, event_hour_utc: int, event_min_utc: int = 0):
        countdown_line = _event_countdown(event_hour_utc, event_min_utc)
        channel = self.bot.get_channel(SPACE_ID)
        if channel:
            filename = image_path.split('/')[-1]
            embed = discord.Embed(title=title, description=f"{message}\n\n{countdown_line}", color=color)
            embed.set_footer(text="📅 Scheduled Notification")
            embed.set_image(url=f"attachment://{filename}")
            file = discord.File(image_path, filename=filename)
            sent_message = await channel.send(content=standard_message, embed=embed, file=file)
            await sent_message.add_reaction(emoji)
        else:
            print(f"⚠️ Channel with ID {SPACE_ID} not found!")

async def setup(bot):
    await bot.add_cog(Scheduler(bot))
