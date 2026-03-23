# Nyx Phantom Discord Bot

A Discord bot for automated community messaging, scheduling, and interactive chat, designed for Star Wars Galaxies gaming guilds.

## Features

- 📅 **Automated Scheduling**: Send messages at specific times using UTC for DST-safe timing
- 👑 **Leadership Controls**: Role-based permissions for bot management
- 🤖 **AI Chatbot**: Respond to mentions or DMs with Star Wars Galaxies-themed advice and conversation
- 🎯 **Gaming Community Focus**: PvP event reminders, motivational messages, and SWG lore
- 🔄 **Hot Reload**: Reload scheduler without restarting the bot
- 📊 **Status Monitoring**: Check bot health and uptime

## Setup

### 1. Clone and Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Environment Configuration

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with your bot credentials:
- `DISCORD_TOKEN`: Your bot token from Discord Developer Portal
- `BOT_OWNER_ID`: Your Discord user ID
- `CHANNEL_ID`: Channel ID for general messages
- `SPACE_ID`: Channel ID for space/gaming messages

### 3. Run the Bot

```bash
python bot.py
```

**Note**: The chatbot uses a local AI model (DistilGPT-2) which downloads on first run (~1GB). Ensure you have a stable internet connection and sufficient disk space.

## Commands

### Admin Commands (Leadership Only)
- `/reload` - Reload the scheduler cog
- `/status` - Check bot status and uptime

### Chatbot
- Mention the bot (e.g., "@Nyx Phantom what's the best PvP ship?") or DM it for SWG-themed responses
- Powered by a local AI model (free, no API keys needed), responds with tips, lore, and fun interactions

### Scheduled Messages
The bot automatically sends messages at these UTC times:
- **Monday 09:00**: Motivation Monday
- **Friday 15:30**: Weekend countdown
- **Saturday 09:00**: Weekend fun reminder
- **Sunday 17:30**: Sunday reminder
- **Tuesday 06:00 & 15:00**: Chewsday PvP reminders
- **Friday 10:00 & 19:00**: Friday Night Fights reminders

## Development

### Project Structure
```
├── bot.py              # Main bot file
├── cogs/
│   ├── admin.py        # Admin commands
│   ├── scheduler.py    # Message scheduling
│   └── chatbot.py      # AI chatbot functionality
├── images/             # Message attachments
├── requirements.txt    # Python dependencies
└── .env.example        # Environment template
```

### Adding New Features
1. Create new cog files in the `cogs/` directory
2. Load them in `bot.py`'s `setup_hook()`
3. Use slash commands with `@app_commands.command()` or listeners for events

## Contributing

1. Test your changes locally
2. Ensure proper error handling
3. Follow the existing code style
4. Update this README if needed

## License

This project is open source. Feel free to use and modify as needed.