# MoonFish Telegram Hype Bot

Copyright (c) 2025 BEDLAM520 Development

**MoonFish Hype Bot** is a Telegram bot designed to keep your Telegram groups lively and engaging. It automatically responds to keywords, reacts to mentions, and periodically sends hype messages when the chat is idle. It supports per-group runtime controls and persists settings to disk so changes survive restarts.

---

## Features

- Auto replies to keywords with multiple varied responses
- Idle prompts when a chat is quiet
- Per-group runtime commands:
  - `/start` : Activate the bot in the group
  - `/shutup` : Silence the bot in the group
  - `/hype` : Send an immediate hype message
  - `/calmdown` : Add +40s to the current cooldown window
  - `/status` : Show current state and overrides for the group
  - `/setidle X` : Set idle interval in minutes for the group
  - `/setkeyword X` : Set keyword reply probability (0.0–1.0)
  - `/setmention X` : Set mention reply probability (0.0–1.0)
  - `/setreply X` : Set general reply probability (0.0–1.0)
  - `/reloadidle` : Reload idle messages from `idle_messages.json`
  - `/reloadkeys` : Reload keyword responses from `keywords.json`

---

## Environment Variables

   > The bot configuration is managed through environment variables. You can use a `.env` file or set them directly in your hosting environment.

| Variable                 | Description                                              | Default                |
|--------------------------|----------------------------------------------------------|-----------------------|
| `BOT_TOKEN`              | Telegram bot token                                       | None (required)       |
| `IDLE_MINUTES`           | Default idle interval in minutes                         | 7                     |
| `MAX_MSG_PER_MIN`        | Reserved (not used currently)                            | 3                     |
| `KEYWORD_REPLY_PROB`     | Default keyword reply probability                        | 0.55                  |
| `MENTION_REPLY_PROB`     | Default mention reply probability                        | 0.90                  |
| `GENERAL_REPLY_PROB`     | Default general reply probability                        | 0.08                  |
| `COOLDOWN_SECONDS`       | Cooldown seconds after sending a message                | 25                    |
| `STATE_FILE`             | JSON file to store per-chat overrides and active flags  | `state.json`          |
| `KEYWORDS_FILE`          | JSON file for keyword-response mapping                  | `keywords.json`       |
| `IDLE_FILE`              | JSON file for idle messages                              | `idle_messages.json`  |

   > ***Note***: Railway and other cloud providers allow you to set these in the project environment settings.

---

## File Structure

moonfish-bot/
├── main.py # Main bot script
├── keywords.json # Keyword-response JSON file
├── idle_messages.json # Idle messages JSON file
├── state.json # Bot state JSON file
├── .env # Environment variables
├── requirements.txt # Python dependencies
└── README.md # Project documentation

- **main.py**: Contains all bot logic, message handling, and command handlers.
- **keywords.json**: Optional external file containing keywords and at least 10 responses per keyword.
- **idle_messages.json**: Optional external file containing at least 30 idle messages.
- **state.json**: External file containing a current state snapshot of the bot config.
- **requirements.txt**: Python dependencies (`python-telegram-bot`, `python-dotenv`, `httpx`, `nest_asyncio`).

---

## Installation & Setup

1. Clone the repository:

   ```bash

   git clone https://github.com/BEDLAM520Dev/moonfish-bot.git

   cd moonfish-bot

   ```

2. Create a virtual environment and install dependencies:

   ```bash

   python -m venv venv

   source venv/bin/activate   # Linux/macOS

   venv\Scripts\activate      # Windows

   pip install -r requirements.txt

   ```

3. Create a .env file with your bot token and settings:

   ```env

   BOT_TOKEN=your_telegram_bot_token
   IDLE_MINUTES=7
   MAX_MSG_PER_MIN=3
   KEYWORD_REPLY_PROB=0.55
   MENTION_REPLY_PROB=0.9
   GENERAL_REPLY_PROB=0.08
   COOLDOWN_SECONDS=25
   STATE_FILE=state.json
   KEYWORDS_FILE=keywords.json
   IDLE_FILE=idle_messages.json

   ```

4. Ensure your keywords.json and idle_messages.json exist or rely on built-in defaults.

---

## Running Locally

   ```bash

   python main.py

   ```

   > The bot will start and listen for messages.
   > Idle messages are sent every IDLE_MINUTES if the chat is quiet.
   > Use commands like /start and /hype in your group to interact.

---

## Deploying to Railway (Free Tier)

1. Sign up at Railway.

2. Create a new project → Deploy from GitHub → Select your repository.

3. Set environment variables in Railway settings.

4. Set Start Command to:

   ```bash

   python main.py

   ```

5. Deploy the project.

6. Monitor logs to ensure the bot starts:

   ```console

   MoonFish Hype Bot is running...

   ```

   > ***Note***: Free tier may sleep after inactivity. Use /reloadidle or /reloadkeys to refresh JSON content without redeploying.

---

## Updating Content

   ***To add more idle messages or keywords:***

   > Edit idle_messages.json or keywords.json.
   > In Telegram, run /reloadidle or /reloadkeys.
   > No bot restart required.

---

## Contributing

   ***Contributions are welcome!*** Suggested improvements:

   > More keyword-response pairs
   > New idle prompts
   > Feature requests for new commands or behaviors

---

## License

   **This project is maintained by BEDLAM520 Development and The MoonFish Community.**

   **All rights reserved 2025.**

---

## Notes & Best Practices

   > Keep COOLDOWN_SECONDS reasonable to avoid spam.
   > Avoid overly high idle intervals if the group is active.
   > Free-tier deployment may go idle if inactive for extended periods.
   > Make backups of state.json before modifying manually.

---

## Contact / Support

   ***Telegram Group***: <https://t.me/Moonfishsui>

   ***GitHub Issues***: <https://github.com/BEDLAM520Dev/moonfish-bot/issues>
