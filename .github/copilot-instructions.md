# Copilot Instructions for MoonFishHypeBot

## Project Overview

MoonFishHypeBot is a Telegram bot for group engagement, written in Python using `python-telegram-bot`, with configuration via environment variables and persistent state in JSON files. The bot responds to keywords, mentions, and idle chat, and supports runtime controls via Telegram commands.

## Architecture & Major Components

- **main.py**: Core bot logic, command handlers, configuration, and runtime controls. All bot features are implemented here.
- **JSON Configs**: `keywords.json`, `idle_messages.json`, `general_replies.json` provide reply content. If missing, built-in defaults are used.
- **State Persistence**: `state.json` stores per-chat overrides and bot activity. Changes survive restarts.
- **Environment**: `.env` file for secrets and config. See README for variable details.

## Developer Workflows

- **Run Bot**: Execute `main.py` directly. Railway and local environments supported.
- **Testing**: Unit tests are in the `tests/` directory (if present). Use Python's `unittest` to run tests. See `INSTRUCTIONS.md` for details.
- **Debugging**: Logging is set up via Python's logging module. Logs output to console at INFO level.
- **Reloading Configs**: Use `/reloadkeys`, `/reloadidle`, `/reloadgeneral` commands in Telegram to reload JSON config files at runtime.

## Project-Specific Patterns

- **Command Handlers**: All bot commands are async functions in `main.py`, registered via `CommandHandler`.
- **Reply Logic**: Keyword, mention, and general replies use probability checks. Mention replies have anti-spam logic (30s window).
- **Admin Controls**: Some commands (e.g., `/help`) are admin-only and attempt to reply privately.
- **State Management**: Per-chat overrides for probabilities and idle timeout are persisted in `state.json`.
- **Fallbacks**: If config files are missing or invalid, built-in defaults are used.

## Integration Points

- **python-telegram-bot**: Main dependency for Telegram API.
- **python-dotenv**: Loads environment variables.
- **nest_asyncio**: Enables async event loop compatibility.

## Examples

- To add a new command, define an async function in `main.py` and register it with `CommandHandler`.
- To change reply content, edit the relevant JSON file and use the reload command in Telegram.
- To persist new state, update the `state` dict and call `save_state()`.

## Key Files

- `main.py`: All bot logic and command handlers.
- `keywords.json`, `idle_messages.json`, `general_replies.json`: Reply content.
- `state.json`: Persistent state.
- `.env`: Environment config.
- `README.md`: Project documentation.

---

For more details, see `README.md` and in-code docstrings. If any section is unclear or missing, please provide feedback for improvement.
