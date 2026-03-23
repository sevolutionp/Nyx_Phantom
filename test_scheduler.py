#!/usr/bin/env python3
"""
Test script for Nyx Phantom scheduler logic
Run this to test the scheduling without needing a Discord bot token
"""

import asyncio
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class MockBot:
    """Mock bot for testing"""
    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone=timezone.utc)

    async def send_scheduled_message(self, standard_message, title, message, color, emoji):
        """Mock message sender"""
        print(f"📅 [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] {standard_message}")
        print(f"   📌 {title}")
        print(f"   💬 {message}")
        print(f"   🎨 Color: {color}")
        print(f"   😀 Reaction: {emoji}")
        print("-" * 50)

    async def send_space_message(self, standard_message, title, message, color, emoji, image_path):
        """Mock space message sender"""
        print(f"🚀 [{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}] {standard_message}")
        print(f"   📌 {title}")
        print(f"   💬 {message}")
        print(f"   🎨 Color: {color}")
        print(f"   😀 Reaction: {emoji}")
        print(f"   🖼️  Image: {image_path}")
        print("-" * 50)

    def schedule_test_messages(self):
        """Schedule test messages for the next few minutes"""
        now = datetime.now(timezone.utc)

        # Schedule a test message in 1 minute
        test_time_1 = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        self.scheduler.add_job(
            self.send_scheduled_message,
            'date',
            run_date=test_time_1,
            args=["🧪 TEST:", "Scheduler Test", "This is a test message!", "blue", "✅"]
        )
        print(f"✅ Scheduled test message for: {test_time_1.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Schedule another test in 2 minutes
        test_time_2 = now.replace(second=0, microsecond=0) + timedelta(minutes=2)
        self.scheduler.add_job(
            self.send_space_message,
            'date',
            run_date=test_time_2,
            args=["🧪 TEST TRANSMISSION:", "Space Test", "Testing space message system!", "red", "🚀", "images/abyssal_squadron_banner.jpg"]
        )
        print(f"✅ Scheduled space test message for: {test_time_2.strftime('%Y-%m-%d %H:%M:%S UTC')}")

    async def run_test(self):
        """Run the test scheduler"""
        print("🧪 Starting Nyx Phantom Scheduler Test")
        print("=" * 50)

        self.schedule_test_messages()
        self.scheduler.start()

        print("⏰ Waiting for scheduled messages... (Press Ctrl+C to stop)")
        try:
            while True:
                await asyncio.sleep(10)
                print(f"⏰ Still running... Next check in 10 seconds")
        except KeyboardInterrupt:
            print("\n🛑 Test stopped by user")
        finally:
            self.scheduler.shutdown()
            print("✅ Test completed")

if __name__ == "__main__":
    bot = MockBot()
    asyncio.run(bot.run_test())