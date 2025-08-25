# MoonFishHypeBot Telegram Group Hype Bot

Copyright © 2025 BEDLAM520 Development

**MoonFishHypeBot** is a Telegram bot designed to keep your Telegram groups lively and engaging. It automatically responds to keywords, reacts to mentions, and periodically sends hype messages when the chat is idle. It supports runtime controls and persists settings to state file so changes survive restarts.

---

## Features

- Scheduled hype messages sent at 8am, 12pm, and 8pm EST (Good Morning, Afternoon, Good Night)

## Command Reference

| `/activatehype`      | Activate scheduled hype messages. |
| `/deactivatehype`    | Deactivate scheduled hype messages. |

| Command           | Description |
|-------------------|-------------|
| `/start`          | Activate the bot in the current group. |
| `/shutup`         | Deactivate the bot in the current group. |
| `/status`         | Show current global configuration, state, and bot statistics. |
| `/hype`           | Force send a hype message to the group. |
| `/setidle X`      | Set idle timeout in minutes (persistent, 1-1440). |
| `/setkeyword X`   | Set keyword reply probability (persistent, 0-100). |
| `/setmention X`   | Set mention reply probability (persistent, 0-100). |
| `/setreply X`     | Set general reply probability (persistent, 0-100). |
| `/setcooldown X`  | Set global cooldown in seconds (persistent, 1-3600). |
| `/calmdown`       | Temporarily increase cooldown by +40s (non-persistent). |
| `/reloadidle`     | Reload idle messages from idle_messages.json. |
| `/reloadkeys`     | Reload keyword responses from keywords.json. |
| `/reloadgeneral`  | Reload general replies from general_replies.json. |
| `/help`           | Show help message with command descriptions (admin only, sent privately if possible). |
| `/reloadscheduled`| Reload scheduled hype messages from scheduled_hype.json. |

All commands must be run in a group where the bot is active. Some commands may require admin privileges depending on your group settings.

---

## Environment Variables

   > The bot configuration is managed through environment variables. You can use a `.env` file or set them directly in your hosting environment.

| Variable                 | Description                                              | Default                |
|--------------------------|----------------------------------------------------------|-----------------------|
| `BOT_TOKEN`              | Telegram bot token                              | None (required)        |
| `IDLE_MINUTES`           | Default idle interval in minutes                            | 10                     |
| `MAX_MSG_PER_MIN`        | Reserved (not used currently)                         | 6                      |
| `KEYWORD_REPLY_PROB`     | Default keyword reply probability                        | 55                     |
| `MENTION_REPLY_PROB`     | Default mention reply probability                        | 90                     |
| `GENERAL_REPLY_PROB`     | Default general reply probability                        | 8                      |
| `COOLDOWN_SECONDS`       | Cooldown seconds after sending a message                            | 10                     |
| `STATE_FILE`             | JSON file to store per-chat overrides and active flags                       | `state.json`           |
| `KEYWORDS_FILE`          | JSON file for keyword-response mapping                            | `keywords.json`        |
| `IDLE_FILE`              | JSON file for idle messages                           | `idle_messages.json`   |
| `GENERAL_FILE`           | JSON file for general replies                            | `general_replies.json` |
| `SCHEDULED_HYPE_FILE`    | JSON file for scheduled replies                            | `scheduled_hype.json`  |

   > ***Note***: Railway and other cloud providers allow you to set these in the project environment settings.

---

## File Structure

moonfish-bot/
├── .env                  # Your environment variables, ***not in repo***
├── .env.example          # Environment variables example
├── .gitignore            # Your gitignore, ***not in repo***
├── general_replies.json  # General replies JSON file, ***prefilled, please update with your own***
├── idle_messages.json    # Idle messages JSON file, ***prefilled, please update with your own***
├── keywords.json         # Keyword-response JSON file, ***prefilled, please update with your own***
├── LICENSE               # License file
├── main.py               # Main bot script
├── README.md             # Project documentation
├── requirements.txt      # Python dependencies
├── scheduled_hype.json   # Scheduled messages JSON file, ***prefilled, please update with your own***
├── state_example.json    # Bot state JSON file example, ***instructions within***
├── state.json            # Your bot state JSON file, ***not in repo***
├── tests/                # Unit tests for all functions
   ├── INSTRUCTIONS.md    # How to run and maintain tests
   ├── test_load_keywords_file.py
   ├── test_load_idle_file.py
   ├── test_load_general_file.py
   ├── test_chat_probs.py
   ├── test_should_reply.py
   ├── test_load_scheduled_hype_file.py   # Tests loading scheduled hype messages
   ├── test_activatehype_command.py       # Tests /activatehype command logic
   ├── test_deactivatehype_command.py     # Tests /deactivatehype command logic
   ├── test_reloadscheduled_command.py    # Tests /reloadscheduled command logic

- **main.py**: Contains all bot logic, defaults, helpers, message handling, and command handlers.
- **keywords.json**: Optional external file containing keywords and corresponding replies.
- **idle_messages.json**: Optional external file containing idle messages.
- **general_replies.json**: Optional external file containing general reply messages.
- **scheduled_hype.json**: Optional external file containing scheduled hype messages (' gm ', ' noon ', ' gn ').
- **state.json**: External file containing a current state snapshot of the bot config.
- **requirements.txt**: Python dependencies (`python-telegram-bot`, `python-dotenv`, `httpx`, `nest_asyncio`, `pytz`).
- **tests/**: Contains individual unit test scripts for each function in main.py for robust testing and maintainability. See `tests/INSTRUCTIONS.md` for details on running and maintaining tests.

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
   IDLE_MINUTES=10
   MAX_MSG_PER_MIN=6
   KEYWORD_REPLY_PROB=55
   MENTION_REPLY_PROB=90
   GENERAL_REPLY_PROB=8
   COOLDOWN_SECONDS=10
   STATE_FILE=state.json
   KEYWORDS_FILE=keywords.json
   IDLE_FILE=idle_messages.json
   GENERAL_FILE=general_replies.json
   SCHEDULED_HYPE_FILE=scheduled_hype.json

   ```

4. Ensure your keywords.json, idle_messages.json, general_replies.json, and scheduled_hype.json exist, or rely on built-in defaults located in main.py.

---

## Running Locally

   ```bash

   python main.py

   ```

   > The bot will start and listen for messages.
   > Idle messages are sent every IDLE_MINUTES if the chat is quiet.
   > Use commands like /start, /status, and /hype in your group to interact.
   > Use commands /setidle, /setmention, /setreply, and /setcooldown in your group to adjust the current bot state with persistence.
   > Use the command /calmdown to add a non-persistent 40 second extension to cooldown.
   > Use commands /reloadkeys, /reloadidle, and /reloadgeneral to hot reload the JSON files without the need to stop and restart the bot.
   > Use the command /reloadscheduled to hot reload scheduled hype messages from scheduled_hype.json.
   > Use /activatehype and /deactivatehype to control scheduled hype messages per chat.

---

## Deploying to Railway (Free Tier)

   > ***Note***: This is merely one example of a method to deploy the bot for production and is in no way intended to be a necessity, please feel free to deploy local, or to whatever host platform you prefer.

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

   Bot is starting...
   MoonFish Hype Bot is running...

   ```

   > ***Note***: Free tier may sleep after inactivity. Use /reloadidle, /reloadkeys , and /reloadgeneral to refresh JSON content without redeploying.

---

## Updating Content

   ***To add more keywords, idle messages, or general replies:***

   > Edit keywords.json, idle_messages.json, or general_replies.json.
   > In Telegram, run /reloadkeys, /reloadidle, or /reloadgeneral.
   > No bot restart required.

---

## Contributing

   ***Contributions are welcome!***

### Suggested improvements

   > More or updated keyword-response pairs
   > More or updated idle messages
   > More or updated general replies
   > Feature requests for new commands or behaviors
   > ***PLEASE*** reach out before commiting ***ANYTHING*** to main!!!

---

## License

   ***This project is licensed under the MIT license.***

---

## Notes & Best Practices

   > Keep COOLDOWN_SECONDS reasonable to avoid spam.
   > Avoid overly high idle intervals if the group is active.
   > Free-tier deployment on Railway may go idle if inactive for extended periods.
   > Make backups of state.json before modifying manually.

---

## Contact / Support

   ***Telegram Group***: <https://t.me/Moonfishsui>

   ***GitHub Issues***: <https://github.com/BEDLAM520Dev/moonfish-bot/issues>

---

***This project is maintained by BEDLAM520 Development and The MoonFishSui Community.***
