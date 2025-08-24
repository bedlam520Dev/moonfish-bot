# Copyright (c) 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""MoonFish Telegram Hype Bot.

This bot keeps Telegram groups lively with keyword-based replies, mention
reactions, and periodic hype prompts. It supports per-group runtime controls
and persists settings to disk so changes survive restarts.

Features:
- Auto replies to keywords with varied responses
- Idle prompts when a chat is quiet
- Per-group commands:
  - /start        : Activate the bot in the group
  - /shutup       : Silence the bot in the group
  - /hype         : Send an immediate hype message
  - /calmdown     : Add +40s to the current cooldown window
  - /status       : Show current state and overrides for this group
  - /setidle X    : Set idle interval in minutes for this group
  - /setkeyword X : Set keyword reply probability (0.0-1.0) for this group
  - /setmention X : Set mention reply probability (0.0-1.0) for this group
  - /setreply X   : Set general reply probability (0.0-1.0) for this group
  - /reloadidle   : Reload idle messages from idle_messages.json
  - /reloadkeys   : Reload keyword responses from keywords.json

Environment:
- BOT_TOKEN              : Telegram bot token
- IDLE_MINUTES           : Default idle minutes (int, default 5)
- MAX_MSG_PER_MIN        : Reserved (int, default 6)
- KEYWORD_REPLY_PROB     : Default keyword reply probability (float, default 1)
- MENTION_REPLY_PROB     : Default mention reply probability (float, default 0.90)
- GENERAL_REPLY_PROB     : Default general reply probability (float, default 0.75)
- COOLDOWN_SECONDS       : Cooldown seconds after a reply (int, default 10)
- STATE_FILE             : JSON state path (default: ./state.json)
- KEYWORDS_FILE          : JSON file for keywords (default: ./keywords.json)
- IDLE_FILE              : JSON file for idle messages (default: ./idle_messages.json)

Notes:
- The bot will attempt to load external JSON files (keywords.json and
  idle_messages.json) at startup and when you invoke reload commands.
- If external files are missing or invalid, built-in defaults are used.
- State overrides (per-chat probabilities and idle minutes) are persisted
  to STATE_FILE so they survive restarts.

Ruff notes:
- Line length ≤ 88
- Full module and function docstrings
- Type hints included
"""

import asyncio
import json
import os
import random
import re
import nest_asyncio
from pathlib import Path
from typing import Dict, Tuple

from dotenv import load_dotenv
from telegram import (
    Update,
    MessageEntity
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ---- Environment ----------------------------------------------------------------

print("Bot is starting...")

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")

IDLE_MINUTES: int = int(os.getenv("IDLE_MINUTES", 5))
MAX_MSG_PER_MIN: int = int(os.getenv("MAX_MSG_PER_MIN", 6))
KEYWORD_REPLY_PROB: float = float(os.getenv("KEYWORD_REPLY_PROB", 1))
MENTION_REPLY_PROB: float = float(os.getenv("MENTION_REPLY_PROB", 0.90))
GENERAL_REPLY_PROB: float = float(os.getenv("GENERAL_REPLY_PROB", 0.75))
COOLDOWN_SECONDS: int = int(os.getenv("COOLDOWN_SECONDS", 10))
STATE_FILE: Path = Path(os.getenv("STATE_FILE", "state.json"))
KEYWORDS_FILE: Path = Path(os.getenv("KEYWORDS_FILE", "keywords.json"))
IDLE_FILE: Path = Path(os.getenv("IDLE_FILE", "idle_messages.json"))

# ---- Built-in defaults (used as fallback if JSON files missing) ------------------

DEFAULT_KEYWORDS: Dict[str, list[str]] = {
    "moon": [
        "🌕 To the moon, fam!",
        "MoonFish gonna fly past Valhalla 🚀🐟",
        "Moon mode engaged — strap in! 🚀🌕",
    ],
    "moonfish": [
        "MoonFish strong 💎🙌",
        "MoonFish community never sleeps 🌊",
        "School of MoonFish > everything 🐟🚀",
    ],
    "hodl": [
        "HODL strong 💎✊",
        "Diamond hands only here 🚀🐟",
        "HODL till Valhalla, frens ⚔️",
    ],
    "diamond": [
        "💎💎💎 Diamond Hand Gang 💎💎💎",
        "Nothing cuts diamond hands 💪💎",
        "Shine bright, holders 💎",
    ],
    "fish": [
        "Just keep swimming… to the moon! 🐠🚀",
        "School of Fish = strongest community 🌊",
        "One fish, two fish, MOONFISH 🚀🐟",
    ],
    "valhalla": [
        "We sail to Valhalla with MoonFish 🛡️⚔️🐟",
        "Valhalla doors open for diamond hands ⚔️💎",
    ],
    "lfg": [
        "LFG 🚀🌊 MoonFish unstoppable!",
        "Let’s f***ing gooo MoonFish fam 💎🐟",
        "LFG, riders of the moon tide 🌊🌕",
    ],
}

DEFAULT_STARTERS: list[str] = [
    "What’s everyone HODLing today? 💎🐟",
    "If MoonFish hits 10x, what’s your first move? 🚀",
    "Drop a 🐟 if you’re diamond hands till Valhalla!",
    "Who here was early to MoonFish? 🌊🙌",
    "What’s stronger: tides 🌊 or diamond hands 💎?",
]

# ---- Active working variables ----------------------------------------------------

KEYWORDS: Dict[str, list[str]] = dict(DEFAULT_KEYWORDS)
STARTERS: list[str] = list(DEFAULT_STARTERS)

# ---- State (in-memory) -----------------------------------------------------------

last_msg_time: Dict[int, float] = {}
cooldowns_until: Dict[int, float] = {}
active_chats: Dict[int, bool] = {}
idle_minutes_override: Dict[int, int] = {}
keyword_prob_override: Dict[int, float] = {}
mention_prob_override: Dict[int, float] = {}
general_prob_override: Dict[int, float] = {}

# ---- Persistence ----------------------------------------------------------------


def _chat_key(chat_id: int) -> str:
    """Convert an int chat_id to a JSON-safe string key."""
    return str(chat_id)


def _parse_prob(value: float) -> float:
    """Clamp a probability to [0.0, 1.0]."""
    return max(0.0, min(1.0, float(value)))


def load_state() -> None:
    """Load persisted state from STATE_FILE into in-memory dicts."""
    if not STATE_FILE.exists():
        return
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return

    active = data.get("active_chats", {})
    idle = data.get("idle_minutes_override", {})
    kprob = data.get("keyword_prob_override", {})
    mprob = data.get("mention_prob_override", {})
    gprob = data.get("general_prob_override", {})

    active_chats.clear()
    idle_minutes_override.clear()
    keyword_prob_override.clear()
    mention_prob_override.clear()
    general_prob_override.clear()

    for k, v in active.items():
        active_chats[int(k)] = bool(v)
    for k, v in idle.items():
        try:
            idle_minutes_override[int(k)] = int(v)
        except Exception:
            continue
    for k, v in kprob.items():
        try:
            keyword_prob_override[int(k)] = _parse_prob(float(v))
        except Exception:
            continue
    for k, v in mprob.items():
        try:
            mention_prob_override[int(k)] = _parse_prob(float(v))
        except Exception:
            continue
    for k, v in gprob.items():
        try:
            general_prob_override[int(k)] = _parse_prob(float(v))
        except Exception:
            continue


def save_state() -> None:
    """Persist current overrides and active flags to STATE_FILE."""
    data = {
        "active_chats": {str(k): v for k, v in active_chats.items()},
        "idle_minutes_override": {str(k): v for k, v in idle_minutes_override.items()},
        "keyword_prob_override": {str(k): v for k, v in keyword_prob_override.items()},
        "mention_prob_override": {str(k): v for k, v in mention_prob_override.items()},
        "general_prob_override": {str(k): v for k, v in general_prob_override.items()},
    }
    tmp = STATE_FILE.with_suffix(".json.tmp")
    try:
        tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        tmp.replace(STATE_FILE)
    except Exception:
        # Best-effort; avoid crashing on I/O failures.
        pass


# ---- External lists load/reload --------------------------------------------------


def _load_keywords_file(path: Path) -> Dict[str, list[str]]:
    """Load keywords mapping from JSON file, with basic validation."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            parsed: Dict[str, list[str]] = {}
            for k, v in raw.items():
                if isinstance(k, str) and isinstance(v, list):
                    parsed[k] = [str(x) for x in v if isinstance(x, (str,))]
            return parsed
    except Exception:
        pass
    return dict(DEFAULT_KEYWORDS)


def _load_idle_file(path: Path) -> list[str]:
    """Load idle messages list from JSON file, with basic validation."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [str(x) for x in raw if isinstance(x, (str,))]
    except Exception:
        pass
    return list(DEFAULT_STARTERS)


def load_external_lists() -> None:
    """Load external keywords and idle messages if JSON files exist.

    This updates the global KEYWORDS and STARTERS variables. If the external
    files are missing or invalid, the function leaves the defaults intact.
    """
    global KEYWORDS, STARTERS
    if KEYWORDS_FILE.exists():
        kws = _load_keywords_file(KEYWORDS_FILE)
        if kws:
            KEYWORDS = kws
    if IDLE_FILE.exists():
        ids = _load_idle_file(IDLE_FILE)
        if ids:
            STARTERS = ids


# ---- Helpers --------------------------------------------------------------------


def should_reply(prob: float) -> bool:
    """Return True if a random draw is below the given probability."""
    return random.random() < prob


def chat_probs(chat_id: int) -> Tuple[float, float, float]:
    """Return per-chat probabilities with env defaults as fallback."""
    k = keyword_prob_override.get(chat_id, KEYWORD_REPLY_PROB)
    m = mention_prob_override.get(chat_id, MENTION_REPLY_PROB)
    g = general_prob_override.get(chat_id, GENERAL_REPLY_PROB)
    return k, m, g


# ---- Handlers: messages ----------------------------------------------------------


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to group messages using keyword/mention/general logic."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message or not message.text:
        print("No chat or message or text, exiting handle_message")
        return

    chat_id = chat.id
    if not active_chats.get(chat_id, True):
        print(f"Chat {chat_id} is inactive, skipping")
        return

    text = message.text
    text_lower = text.lower()
    print(f"Received message in chat {chat_id}: {text}")

    now = asyncio.get_event_loop().time()
    if now < cooldowns_until.get(chat_id, 0.0):
        remaining = int(cooldowns_until.get(chat_id, 0.0) - now)
        print(f"Chat {chat_id} is in cooldown ({remaining}s remaining), skipping")
        return

    kprob, mprob, gprob = chat_probs(chat_id)
    print(f"Chat probabilities: k={kprob}, m={mprob}, g={gprob}")

    # ---- Collect actual @mentions from message entities (case-insensitive) ----
    mentioned_usernames = set()
    if message.entities:
        for ent in message.entities:
            if ent.type == "mention":
                # This slice includes the '@', e.g. '@Founder'
                uname = text[ent.offset : ent.offset + ent.length]
                mentioned_usernames.add(uname.lower())
    if mentioned_usernames:
        print(f"Detected mentions in message: {mentioned_usernames}")

    # ---- 1) Selective @username triggers from KEYWORDS ------------------------
    # Only trigger if the message actually @mentions a username that exists as a KEYWORDS key.
    # Example KEYWORDS keys: "@founder", "@marketer", "@me"
    username_keys_lower = {k.lower() for k in KEYWORDS.keys() if k.startswith("@")}
    hits = mentioned_usernames.intersection(username_keys_lower)
    if hits:
        # If multiple usernames are mentioned, pick the first matching key
        hit_key_lower = next(iter(hits))
        # Find the original-cased key so we keep the replies mapped correctly
        for original_key, responses in KEYWORDS.items():
            if original_key.lower() == hit_key_lower:
                print(f"Username trigger matched: {original_key}")
                if should_reply(kprob):
                    reply = random.choice(responses)
                    print(f"Replying to username trigger {original_key}: {reply}")
                    await message.reply_text(reply)
                    cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
                    last_msg_time[chat_id] = now
                    return
                else:
                    print(f"Username trigger {original_key} did not pass probability check")
                break  # matched the key; no need to continue

    # ---- 2) Keyword replies (non-@ keys), case-insensitive --------------------
    for key, responses in KEYWORDS.items():
        if key.startswith("@"):
            continue  # handled above
        if key.lower() in text_lower:
            print(f"Keyword match found: {key}")
            if should_reply(kprob):
                reply = random.choice(responses)
                print(f"Replying to keyword {key}: {reply}")
                await message.reply_text(reply)
                cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
                last_msg_time[chat_id] = now
                return
            else:
                print(f"Keyword {key} detected but did not pass probability check")

    # ---- 3) Bot mention (e.g. @YourBot), case-insensitive ---------------------
    mention_token = f"@{context.bot.username.lower()}"
    if mention_token in text_lower:
        print(f"Bot mention detected: {mention_token}")
        if should_reply(mprob):
            flat = [r for rs in KEYWORDS.values() for r in rs]
            reply = random.choice(flat)
            print(f"Replying to bot mention: {reply}")
            await message.reply_text(reply)
            cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
            last_msg_time[chat_id] = now
            return
        else:
            print("Bot mention did not pass probability check")

    # ---- 4) General replies ---------------------------------------------------
    if should_reply(gprob):
        flat = [r for rs in KEYWORDS.values() for r in rs]
        reply = random.choice(flat)
        print(f"Replying with general reply: {reply}")
        await message.reply_text(reply)
        cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
        last_msg_time[chat_id] = now
    else:
        print("No reply chosen by probability")


async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update last activity time for idle detection."""
    chat = update.effective_chat
    if not chat:
        print("track_activity: no chat")
        return
    last_msg_time[chat.id] = asyncio.get_event_loop().time()
    print(f"Updated last activity for chat {chat.id}")


# ---- Handlers: idle task ---------------------------------------------------------


async def idle_task(application: Application) -> None:
    """Periodically post a starter prompt if the chat is idle."""
    while True:
        await asyncio.sleep(60)
        now = asyncio.get_event_loop().time()
        for chat_id, last in list(last_msg_time.items()):
            if not active_chats.get(chat_id, True):
                continue
            minutes = idle_minutes_override.get(chat_id, IDLE_MINUTES)
            if now - last >= minutes * 60:
                try:
                    await application.bot.send_message(
                        chat_id=chat_id,
                        text=random.choice(STARTERS),
                    )
                except Exception:
                    pass
                last_msg_time[chat_id] = now


# ---- Handlers: commands ----------------------------------------------------------


async def hype_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send an immediate hype message."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    if not active_chats.get(chat.id, True):
        return
    flat = [r for rs in KEYWORDS.values() for r in rs]
    await message.reply_text(random.choice(flat))


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activate the bot in this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    active_chats[chat.id] = True
    save_state()
    await message.reply_text("MoonFish bot activated 🚀🐟")


async def shutup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Silence the bot in this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    active_chats[chat.id] = False
    save_state()
    await message.reply_text("MoonFish bot silenced 🤐")


async def calmdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add +40 seconds to the current cooldown window."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    now = asyncio.get_event_loop().time()
    cooldowns_until[chat.id] = max(
        cooldowns_until.get(chat.id, now),
        now,
    ) + 40.0
    await message.reply_text("Calm down mode: +40s cooldown 🐟⏳")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report current state and overrides for this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    kprob, mprob, gprob = chat_probs(chat.id)
    active = active_chats.get(chat.id, True)
    minutes = idle_minutes_override.get(chat.id, IDLE_MINUTES)
    now = asyncio.get_event_loop().time()
    remaining = max(0, int(cooldowns_until.get(chat.id, 0.0) - now))
    await message.reply_text(
        f"Active: {active}\n"
        f"Idle minutes: {minutes}\n"
        f"Keyword prob: {kprob:.2f}\n"
        f"Mention prob: {mprob:.2f}\n"
        f"General prob: {gprob:.2f}\n"
        f"Cooldown remaining: {remaining}s",
    )


async def setidle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set idle interval in minutes for this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        minutes = int(context.args[0])
        minutes = max(1, minutes)
        idle_minutes_override[chat.id] = minutes
        save_state()
        await message.reply_text(f"Idle interval set to {minutes} minutes ⏱️")
    except (IndexError, ValueError):
        await message.reply_text("Usage: /setidle <minutes>")


async def setkeyword_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set keyword reply probability for this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        prob = _parse_prob(float(context.args[0]))
        keyword_prob_override[chat.id] = prob
        save_state()
        await message.reply_text(f"Keyword reply probability set to {prob:.2f}")
    except (IndexError, ValueError):
        await message.reply_text("Usage: /setkeyword <probability>")


async def setmention_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set mention reply probability for this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        prob = _parse_prob(float(context.args[0]))
        mention_prob_override[chat.id] = prob
        save_state()
        await message.reply_text(f"Mention reply probability set to {prob:.2f}")
    except (IndexError, ValueError):
        await message.reply_text("Usage: /setmention <probability>")


async def setreply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set general reply probability for this group."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        prob = _parse_prob(float(context.args[0]))
        general_prob_override[chat.id] = prob
        save_state()
        await message.reply_text(f"General reply probability set to {prob:.2f}")
    except (IndexError, ValueError):
        await message.reply_text("Usage: /setreply <probability>")


async def reloadidle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reload idle messages from the configured IDLE_FILE."""
    try:
        global STARTERS
        STARTERS = _load_idle_file(IDLE_FILE) if IDLE_FILE.exists() else list(DEFAULT_STARTERS)
        await update.message.reply_text(f"Reloaded {len(STARTERS)} idle messages.")
        print(f"[Console] Reloaded {len(STARTERS)} idle messages from {IDLE_FILE}")
    except Exception as exc:
        await update.message.reply_text(f"Failed to reload idle messages: {exc}")
        print(f"[Console] Failed to reload idle messages: {exc}")


async def reloadkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reload keyword responses from the configured KEYWORDS_FILE."""
    try:
        global KEYWORDS
        KEYWORDS = _load_keywords_file(KEYWORDS_FILE) if KEYWORDS_FILE.exists() else dict(DEFAULT_KEYWORDS)
        await update.message.reply_text(f"Reloaded {len(KEYWORDS)} keyword sets.")
        print(f"[Console] Reloaded {len(KEYWORDS)} keyword sets from {KEYWORDS_FILE}")
    except Exception as exc:
        await update.message.reply_text(f"Failed to reload keyword responses: {exc}")
        print(f"[Console] Failed to reload keyword responses: {exc}")


# ---- App lifecycle ---------------------------------------------------------------


async def main() -> None:
    """Create the app, register handlers, and start polling."""
    load_external_lists()
    load_state()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message), group=0)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_activity), group=1)

    app.add_handler(CommandHandler("hype", hype_command))
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("shutup", shutup_command))
    app.add_handler(CommandHandler("calmdown", calmdown_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("setidle", setidle_command))
    app.add_handler(CommandHandler("setkeyword", setkeyword_command))
    app.add_handler(CommandHandler("setmention", setmention_command))
    app.add_handler(CommandHandler("setreply", setreply_command))
    app.add_handler(CommandHandler("reloadidle", reloadidle_command))
    app.add_handler(CommandHandler("reloadkeys", reloadkeys_command))

    # schedule idle_task
    asyncio.create_task(idle_task(app))

    print("MoonFish Hype Bot is running...")

    await app.run_polling()  # run_polling manages the loop itself


if __name__ == "__main__":
    import nest_asyncio
    import asyncio

    nest_asyncio.apply()  # <-- only here, top-level, before any loop creation
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
