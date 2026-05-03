# AntiAIFlex

A self-hosted Discord bot that uses NVIDIA's vision AI to detect scam images — fake celebrity giveaways, crypto casino promotions, and similar fraud commonly shared in Discord servers.

## How it works

When a user posts an image (optionally prefixed with "bro"), the bot sends it to [NVIDIA NIM](https://integrate.api.nvidia.com) using the `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` vision model. The model analyzes the image for scam indicators and returns a confidence score. If the score meets the guild's threshold, the bot takes the configured actions and logs the result to a designated channel.

GIFs and videos are ignored. Only static images (PNG, JPG, WEBP, etc.) are analyzed.

## Features

- Vision AI analysis via NVIDIA NIM (OpenAI-compatible API)
- Per-guild configuration stored in MongoDB
- Configurable scan trigger: messages starting with "bro", or all images
- Configurable confidence threshold (default: 85%)
- Configurable actions per guild: DM warning, delete message, timeout, ban
- Embed log channel with scam details, confidence, reason, and jump link
- Slash commands for all configuration
- Self-hostable — bring your own keys

## Requirements

- Python 3.11+
- MongoDB (local or remote)
- [NVIDIA NIM API key](https://build.nvidia.com) (free tier available)
- Discord bot token with Message Content Intent enabled

## Setup

### 1. Clone and install

```bash
git clone https://github.com/hxgohxrr/AntiAIFlex.git
cd AntiAIFlex
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
DISCORD_TOKEN=your_discord_bot_token
NVIDIA_API_KEY=your_nvidia_nim_api_key
MONGO_URI=mongodb://localhost:27017
```

### 3. Discord bot settings

In the [Discord Developer Portal](https://discord.com/developers/applications):

- Enable **Message Content Intent** under Bot → Privileged Gateway Intents
- Required permissions: `Read Messages`, `Send Messages`, `Embed Links`, `Manage Messages`, `Moderate Members`, `Ban Members`

### 4. Run

```bash
python bot.py
```

### Docker

```bash
docker compose up -d
```

MongoDB is included in the compose file. Only `DISCORD_TOKEN` and `NVIDIA_API_KEY` are required in the environment.

## Configuration (slash commands)

All commands require the **Manage Server** permission.

| Command | Description |
|---|---|
| `/antiscam setup #channel` | Set the log channel and enable the bot |
| `/antiscam mode bro_only` | Only scan images in messages starting with "bro" |
| `/antiscam mode all_images` | Scan every image posted |
| `/antiscam threshold <0-100>` | Set confidence threshold (default: 85) |
| `/antiscam status` | Show current configuration |
| `/antiscam action warn on/off` | DM the user with a warning |
| `/antiscam action delete on/off` | Delete the message |
| `/antiscam action timeout <minutes>` | Timeout the user (0 = disabled) |
| `/antiscam action ban on/off` | Ban the user |
| `/antiscam action log_clean on/off` | Also log non-scam results |

## Project structure

```
bot.py                  # Entry point
cogs/
  scanner.py            # on_message listener, scan trigger logic
  commands.py           # Slash commands
services/
  analyzer.py           # NVIDIA NIM API call and JSON extraction
  actions.py            # warn / delete / timeout / ban
  logger.py             # Discord embed log
db/
  client.py             # Motor singleton
  guild_config.py       # get/upsert guild config
config/
  defaults.py           # Default thresholds and AI prompts
models.py               # ScamResult, GuildConfig, GuildActions
```

## Running tests

```bash
pip install -r requirements-dev.txt
pytest
```

Tests use `mongomock-motor` — no real MongoDB needed.

## License

MIT
