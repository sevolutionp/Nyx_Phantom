# Nyx Phantom Discord Bot

A Discord bot for Star Wars Galaxies Legends guilds — featuring AI chat powered by the SWG Legends wiki, automated event reminders, and community scheduling.

## Features

- 🤖 **AI Chatbot**: Mention Nyx or DM it for SWG Legends-accurate answers powered by Groq (Llama 3.3 70B) + RAG wiki knowledge
- 🗡️ **HK-47 Personality**: Nyx speaks in the style of HK-47 from KOTOR — "Statement:", "Query:", "Observation:" prefixes, dry sarcasm, and the occasional "meatbag"
- 📅 **Automated Scheduling**: PvP event reminders, motivational messages, and weekly announcements sent on a UTC schedule
- 🗺️ **Wiki-Powered Knowledge**: Scraped and indexed SWG Legends wiki for accurate gameplay answers (professions, planets, crafting, space PvP, etc.)
- 📚 **Guild Lore Indexing**: `/scrape-lore` indexes any Discord channel (messages + PDF attachments) into Nyx's knowledge base
- 🔇 **Toggle On/Off**: `/nyx-toggle` silences Nyx with a recharge message and wakes him back up when ready
- 👑 **Leadership Controls**: Role-based permissions for bot management
- 🔄 **Hot Reload**: Reload the scheduler without restarting the bot
- 📊 **Status Monitoring**: Check bot health and uptime via `/status`
- 🖥️ **Multi-Server Support**: Runs in both a test server and a live guild server simultaneously

## Setup

### 1. Clone and install dependencies

```bash
git clone https://github.com/sevolutionp/Nyx_Phantom.git
cd Nyx_Phantom
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description |
|---|---|
| `DISCORD_TOKEN` | Bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `BOT_OWNER_ID` | Your Discord user ID |
| `GROQ_API_KEY` | Free API key from [console.groq.com](https://console.groq.com) |
| `TEST_CHANNEL_ID` | Channel ID for test/dev server |
| `GUILD_CHANNEL_ID` | Channel ID for guild general chat |
| `SPACE_ID` | Channel ID for space PvP announcements |
| `CF_CLEARANCE` | Cloudflare cookie for wiki scraping (see below) |

### 3. Build the wiki knowledge base (optional but recommended)

This scrapes the SWG Legends wiki and builds a local vector index so Nyx can answer gameplay questions accurately.

**Get your `cf_clearance` cookie:**
1. Visit `https://swglegends.com/wiki/index.php?title=Home` in your browser
2. Open DevTools (`F12`) → Application → Cookies → `swglegends.com`
3. Copy the `cf_clearance` value into your `.env`

**Run the scraper and indexer:**
```bash
python scraper.py       # crawls the wiki (~868 pages, takes a few minutes)
python build_index.py   # builds the ChromaDB vector index
```

> Note: The `cf_clearance` cookie expires every ~24 hours. Re-run `scraper.py` + `build_index.py` to refresh the knowledge base.

### 4. Run the bot

```bash
python bot.py
```

## Commands

### Slash Commands
| Command | Permission | Description |
|---|---|---|
| `/status` | Everyone | Check bot latency, uptime, and server count |
| `/nyx-toggle` | Owner & Leadership | Enable or disable Nyx's chat responses |
| `/scrape-lore` | Owner & Leadership | Index the current channel's messages and PDFs into Nyx's knowledge base |
| `/reload` | Owner & Leadership | Reload the scheduler cog without restarting |

### Chatbot
Mention `@Nyx Phantom` or send a DM — Nyx will answer using SWG Legends wiki knowledge where available, falling back to Llama 3.3 70B general knowledge.

When the Groq daily token limit is hit, Nyx automatically falls back to `llama-3.1-8b-instant` to stay online.

### Scheduled Messages (UTC)
| Time | Message |
|---|---|
| Monday 09:00 | Motivation Monday |
| Tuesday 06:00 | Chewsday PvP reminder |
| Tuesday 15:00 | Chewsday PvP launch |
| Friday 10:00 | Friday Night Fights warning |
| Friday 15:30 | Weekend countdown |
| Friday 19:00 | Friday Night Fights launch |
| Saturday 09:00 | Weekend reminder |
| Sunday 17:30 | Sunday afternoon reminder |

## Project Structure

```
├── bot.py              # Main bot entry point
├── cogs/
│   ├── admin.py        # Slash commands (/status, /reload, /nyx-toggle)
│   ├── scheduler.py    # Automated message scheduling
│   ├── chatbot.py      # AI chatbot with RAG retrieval + HK-47 personality
│   └── lore_scraper.py # /scrape-lore — indexes Discord channels + PDFs
├── scraper.py          # SWG Legends wiki scraper
├── build_index.py      # Embeds wiki chunks into ChromaDB
├── images/             # Images used in scheduled messages
├── requirements.txt    # Python dependencies
└── .env.example        # Environment variable template
```

## Contributing

1. Fork the repo and create a feature branch
2. Test your changes locally with a dev Discord server
3. Ensure proper error handling
4. Open a Pull Request with a clear description of the change

## License

Open source — free to use and modify.
