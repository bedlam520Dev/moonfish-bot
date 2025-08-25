# Copyright © 2025 BEDLAM520 Development
# -*- coding: utf-8 -*-

"""MoonFishHypeBot Telegram Group Hype Bot.

This bot keeps Telegram groups lively with keyword-based replies, mention
reactions, and periodic hype prompts. It supports per-group runtime controls
and persists settings to disk so changes survive restarts.

Features include:
- Idle chat replies loaded from idle_messages.json
- Keyword-triggered replies loaded from keywords.json
- General replies loaded from general_replies.json
- Idle detection and idle replies
- Configurable probabilities for keyword/mention/general replies
- Cooldown system with persistent global overrides via /set commands
- Commands to control activity, cooldown, probabilities, and states
- Persistent state saving/loading for overrides and activity
- Support for @username keyword triggers
- Separation of reply types: keyword, general, and idle

Commands:
    /start             - Activate the bot in the current group
    /shutup            - Deactivate the bot in the current group
    /status            - Show current global configuration and state
    /hype              - Force send a hype message
    /setidle X         - Set idle timeout in seconds (persistent)
    /setkeyword X      - Set keyword reply probability 0-100 (persistent)
    /setmention X      - Set mention reply probability 0-100 (persistent)
    /setreply X        - Set general reply probability 0-100 (persistent)
    /setcooldown X     - Set global cooldown in seconds (persistent)
    /calmdown          - Temporarily increase cooldown by +40s (non-persistent)
    /reloadidle        - Reload idle list from idle_messages.json
    /reloadkeys        - Reload keyword list from keywords.json
    /reloadgeneral     - Reload general replies from general_replies.json
    /reloadscheduled   - Reload scheduled hype messages from scheduled_hype.json
    /activatehype      - Activate scheduled hype messages for this chat
    /deactivatehype    - Deactivate scheduled hype messages for this chat
    /help              - Show help message with command descriptions (admin only, sent privately if possible)

Environment:
- BOT_TOKEN              : Telegram bot token
- IDLE_MINUTES           : Default idle minutes (int, default 10)
- MAX_MSG_PER_MIN        : Reserved (int, default 6)
- KEYWORD_REPLY_PROB     : Default keyword reply probability (float, default 55)
- MENTION_REPLY_PROB     : Default mention reply probability (float, default 90)
- GENERAL_REPLY_PROB     : Default general reply probability (float, default 8)
- COOLDOWN_SECONDS       : Cooldown seconds after a reply (int, default 10)
- STATE_FILE             : JSON state path (default: ./state.json)
- KEYWORDS_FILE          : JSON file for keywords (default: ./keywords.json)
- IDLE_FILE              : JSON file for idle messages (default: ./idle_messages.json)
- GENERAL_FILE           : JSON file for general replies (default: ./general_replies.json)
- SCHEDULED_HYPE_FILE    : JSON file for scheduled hype messages (default: ./scheduled_hype.json)

Notes:
- The bot will attempt to load external JSON files (keywords.json, idle_messages.json, and general_replies.json) at startup and when you invoke reload commands.
- If external files are missing or invalid, built-in defaults are used.
- State overrides (per-chat probabilities and idle minutes) are persisted
    to STATE_FILE so they survive restarts.

Ruff notes: (IF USING RUFF)
- Line length ≤ 88
- Full module and function docstrings
- Type hints included
- Imports sorted
- Lines and whitespace normalized

Author: BEDLAM520 Development
License: MIT
Version: 1.3.0
Last Updated: August 25, 2025
"""

import asyncio
import json
import os
import random
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import nest_asyncio
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


# ---- Logging Setup -------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("moonfish_bot")

logger.info("Bot is starting...")


# ---- Environment ----------------------------------------------------------------


load_dotenv()


BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")
IDLE_MINUTES: int = int(os.getenv("IDLE_MINUTES", 10))
MAX_MSG_PER_MIN: int = int(os.getenv("MAX_MSG_PER_MIN", 6))
KEYWORD_REPLY_PROB: float = float(os.getenv("KEYWORD_REPLY_PROB", 55))
MENTION_REPLY_PROB: float = float(os.getenv("MENTION_REPLY_PROB", 90))
GENERAL_REPLY_PROB: float = float(os.getenv("GENERAL_REPLY_PROB", 8))
COOLDOWN_SECONDS: int = int(os.getenv("COOLDOWN_SECONDS", 10))
STATE_FILE: Path = Path(os.getenv("STATE_FILE", "state.json"))
KEYWORDS_FILE: Path = Path(os.getenv("KEYWORDS_FILE", "keywords.json"))
IDLE_FILE: Path = Path(os.getenv("IDLE_FILE", "idle_messages.json"))
GENERAL_FILE: Path = Path(os.getenv("GENERAL_FILE", "general_replies.json"))
SCHEDULED_HYPE_FILE: Path = Path(os.getenv("SCHEDULED_HYPE_FILE", "scheduled_hype.json"))


# ---- Built-in defaults (used as fallback if JSON files missing) -----------------
DEFAULT_SCHEDULED_HYPE: Dict[str, list[str]] = {
    "gm": [
        "GM fam! Carpe Diem — seize the day and grab your coffee ☕!",
        "Good morning! Let's make today count. Carpe Diem!",
        "Rise and shine! Coffee up and seize the day!",
        "GM! Wishing you a productive day ahead. Carpe Diem!",
        "Good morning! Time to hustle and make it a great day!"
    ],
    "noon": [
        "It's noon! Keep grinding, keep accumulating, and support those who support you.",
        "Afternoon grind time! Touch some grass and keep pushing forward.",
        "Midday check-in: Stay focused, help your crew, and keep stacking!",
        "Noon vibes: Accumulate, support, and touch grass!",
        "Afternoon hustle! Remember to support your supporters and keep grinding."
    ],
    "gn": [
        "GN fam! Rest well, spend time with loved ones, and recharge for tomorrow's grind.",
        "Good night! Take time to rest and be with those you love.",
        "Sleep tight! Tomorrow is another day to grind and succeed.",
        "GN! Wishing you restful sleep and quality time with family.",
        "Good night! Recharge and get ready for another day of greatness."
    ]
}
SCHEDULED_HYPE_FILE = os.getenv("SCHEDULED_HYPE_FILE", "scheduled_hype.json")

SCHEDULED_HYPE: Dict[str, list[str]] = {}
scheduled_hype_active: bool = True


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
        "Let's f***ing gooo MoonFish fam 💎🐟",
        "LFG, riders of the moon tide 🌊🌕",
    ],
}

DEFAULT_STARTERS: list[str] = [
    "What's everyone HODLing today? 💎🐟",
    "If MoonFish hits 10x, what's your first move? 🚀",
    "Drop a 🐟 if you're diamond hands till Valhalla!",
    "Who here was early to MoonFish? 🌊🙌",
    "What's stronger: tides 🌊 or diamond hands 💎?",
]

DEFAULT_IDLE: list[str] = [
    "Zzz…",
    "I'm just a fish in the sea…",
    "MoonFish dreams…",
    "Waiting for the tide to turn…",
    "Just keep swimming…",
]

DEFAULT_GENERAL: list[str] = [
    "MoonFish to the moon! 🚀",
    "HODL strong, friends! 💎",
    "Just another day in the school of fish…",
]


# ---- Constants and global state -------------------------------------------------


## Remove duplicate string assignments for file paths
## Only use Path objects as defined above




# Global state
active_chats: Dict[int, bool] = {}
cooldowns_until: Dict[int, float] = {}
last_msg_time: Dict[int, float] = {}
KEYWORDS: Dict[str, List[str]] = {}
GENERAL_REPLIES: List[str] = []
IDLE_MESSAGES: List[str] = []
SCHEDULED_HYPE: Dict[str, List[str]] = {}
scheduled_hype_active: Dict[int, bool] = {}  # Per-chat activation

# Persistent override dicts (for per-chat settings)
idle_minutes_override: Dict[int, int] = {}
keyword_prob_override: Dict[int, float] = {}
mention_prob_override: Dict[int, float] = {}
general_prob_override: Dict[int, float] = {}

# Stats tracking
total_replies_sent: int = 0
total_keyword_replies: int = 0
total_general_replies: int = 0
total_idle_replies: int = 0
bot_start_time: float = asyncio.get_event_loop().time() if hasattr(asyncio, 'get_event_loop') else 0.0

# Persistent overrides
state: Dict[str, object] = {
    "idle_timeout": IDLE_MINUTES,
    "cooldown_seconds": COOLDOWN_SECONDS,
    "keyword_prob": KEYWORD_REPLY_PROB,
    "mention_prob": MENTION_REPLY_PROB,
    "general_prob": GENERAL_REPLY_PROB,
}


# ---- Persistence ----------------------------------------------------------------


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


# ---- External lists load/reload -------------------------------------------------
def _load_scheduled_hype_file(path: Path) -> Dict[str, list[str]]:
    """Load scheduled hype messages from JSON file, with basic validation."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            parsed: Dict[str, list[str]] = {}
            for k in ["gm", "noon", "gn"]:
                v = raw.get(k, [])
                if isinstance(v, list):
                    parsed[k] = [str(x) for x in v if isinstance(x, (str,))]
            return parsed
    except Exception:
        pass
    return {"gm": [], "noon": [], "gn": []}


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


def _load_general_file(path: Path) -> list[str]:
    """Load general replies list from JSON file, with basic validation."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            return [str(x) for x in raw if isinstance(x, (str,))]
    except Exception:
        pass
    return list(DEFAULT_GENERAL)


def load_external_lists() -> None:
    global SCHEDULED_HYPE
    try:
        with open(SCHEDULED_HYPE_FILE, "r", encoding="utf-8") as f:
            SCHEDULED_HYPE = json.load(f)
        print(f"Loaded scheduled hype messages: gm={len(SCHEDULED_HYPE.get('gm', []))}, noon={len(SCHEDULED_HYPE.get('noon', []))}, gn={len(SCHEDULED_HYPE.get('gn', []))}")
    except FileNotFoundError:
        SCHEDULED_HYPE = dict(DEFAULT_SCHEDULED_HYPE)
import datetime
import pytz

async def scheduled_hype_task(application: Application) -> None:
    """Send scheduled hype messages at 8am, 12pm, and 8pm EST to all active chats."""
    est = pytz.timezone("US/Eastern")
    sent_today = {"gm": set(), "noon": set(), "gn": set()}
    while True:
        now_utc = datetime.now(datetime.timezone.utc)
        now_est = now_utc.astimezone(est)
        hour = now_est.hour
        minute = now_est.minute
        today = now_est.date()
        # 8am
        if hour == 8 and minute == 0 and scheduled_hype_active:
            for chat_id in active_chats:
                if chat_id not in sent_today["gm"]:
                    msg = random.choice(SCHEDULED_HYPE.get("gm", DEFAULT_SCHEDULED_HYPE["gm"]))
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg)
                    except Exception:
                        pass
                    sent_today["gm"].add(chat_id)
        # 12pm
        if hour == 12 and minute == 0 and scheduled_hype_active:
            for chat_id in active_chats:
                if chat_id not in sent_today["noon"]:
                    msg = random.choice(SCHEDULED_HYPE.get("noon", DEFAULT_SCHEDULED_HYPE["noon"]))
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg)
                    except Exception:
                        pass
                    sent_today["noon"].add(chat_id)
        # 8pm
        if hour == 20 and minute == 0 and scheduled_hype_active:
            for chat_id in active_chats:
                if chat_id not in sent_today["gn"]:
                    msg = random.choice(SCHEDULED_HYPE.get("gn", DEFAULT_SCHEDULED_HYPE["gn"]))
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg)
                    except Exception:
                        pass
                    sent_today["gn"].add(chat_id)
        # Reset sent_today at midnight
        if hour == 0 and minute == 0:
            sent_today = {"gm": set(), "noon": set(), "gn": set()}
        await asyncio.sleep(60)

async def activate_scheduled_hype_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global scheduled_hype_active
    scheduled_hype_active = True
    await update.message.reply_text("Scheduled hype messages activated.")

async def deactivate_scheduled_hype_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global scheduled_hype_active
    scheduled_hype_active = False
    await update.message.reply_text("Scheduled hype messages deactivated.")
    """Load external keywords, idle, and general messages if JSON files exist.
    This updates the global KEYWORDS, IDLE_MESSAGES, and GENERAL_REPLIES variables.
    If the external files are missing or invalid, the function leaves the defaults intact.
    """
    global KEYWORDS, IDLE_MESSAGES, GENERAL_REPLIES, SCHEDULED_HYPE
    try:
        with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
            KEYWORDS = json.load(f)
        print(f"Loaded {len(KEYWORDS)} keyword groups")
    except FileNotFoundError:
        KEYWORDS = {}

    try:
        with open(IDLE_FILE, "r", encoding="utf-8") as f:
            IDLE_MESSAGES = json.load(f)
        print(f"Loaded {len(IDLE_MESSAGES)} idle messages")
    except FileNotFoundError:
        IDLE_MESSAGES = []

    
    try:
        with open(GENERAL_FILE, "r", encoding="utf-8") as f:
            GENERAL_REPLIES = json.load(f)
        print(f"Loaded {len(GENERAL_REPLIES)} general replies")
    except FileNotFoundError:
        GENERAL_REPLIES = []


# ---- Helpers --------------------------------------------------------------------


def chat_probs(chat_id: int) -> Tuple[float, float, float]:
    """Return per-chat probabilities with env defaults as fallback."""
    k = keyword_prob_override.get(chat_id, KEYWORD_REPLY_PROB)
    m = mention_prob_override.get(chat_id, MENTION_REPLY_PROB)
    g = general_prob_override.get(chat_id, GENERAL_REPLY_PROB)
    return k, m, g


def should_reply(prob: int) -> bool:

    try:
        SCHEDULED_HYPE = _load_scheduled_hype_file(Path("scheduled_hype.json"))
        print(f"Loaded scheduled hype messages: gm={len(SCHEDULED_HYPE['gm'])}, noon={len(SCHEDULED_HYPE['noon'])}, gn={len(SCHEDULED_HYPE['gn'])}")
    except Exception:
        SCHEDULED_HYPE = {"gm": [], "noon": [], "gn": []}

# ---- Scheduled Hype Task -------------------------------------------------------
import pytz
from datetime import datetime, timezone

async def scheduled_hype_task(application: Application) -> None:
    """Send scheduled hype messages at 8am, 12pm, and 8pm EST to active chats."""
    est = pytz.timezone("US/Eastern")
    sent_today = set()
    while True:
        now_utc = datetime.now(timezone.utc)
        now_est = now_utc.astimezone(est)
        hour = now_est.hour
        minute = now_est.minute
        today = now_est.date()
        for chat_id in active_chats:
            if not scheduled_hype_active.get(chat_id, True):
                continue
            if hour == 8 and minute == 0 and (chat_id, "gm", today) not in sent_today:
                if SCHEDULED_HYPE["gm"]:
                    msg = random.choice(SCHEDULED_HYPE["gm"])
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg)
                    except Exception:
                        pass
                    sent_today.add((chat_id, "gm", today))
            elif hour == 12 and minute == 0 and (chat_id, "noon", today) not in sent_today:
                if SCHEDULED_HYPE["noon"]:
                    msg = random.choice(SCHEDULED_HYPE["noon"])
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg)
                    except Exception:
                        pass
                    sent_today.add((chat_id, "noon", today))
            elif hour == 20 and minute == 0 and (chat_id, "gn", today) not in sent_today:
                if SCHEDULED_HYPE["gn"]:
                    msg = random.choice(SCHEDULED_HYPE["gn"])
                    try:
                        await application.bot.send_message(chat_id=chat_id, text=msg)
                    except Exception:
                        pass
                    sent_today.add((chat_id, "gn", today))
        # Reset sent_today at midnight EST
        if hour == 0 and minute == 1:
            sent_today.clear()
        await asyncio.sleep(60)
    """Return True if we should reply given probability."""
    return random.randint(1, 100) <= prob


# ---- Handlers: idle messages ----------------------------------------------------


async def idle_task(application: Application) -> None:
    """Periodically post a starter message if the chat is idle."""
    global total_replies_sent, total_idle_replies
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
                        text=random.choice(IDLE_MESSAGES),
                    )
                    total_replies_sent += 1
                    total_idle_replies += 1
                except Exception:
                    pass
                last_msg_time[chat_id] = now


# ---- Handlers: reply messages ---------------------------------------------------


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply to messages using keyword/mention/general logic."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message or not message.text:
        logger.warning("No chat or message or text, exiting handle_message")
        return

    chat_id = chat.id
    if not active_chats.get(chat_id, True):
        logger.info(f"Chat {chat_id} is inactive, skipping")
        return

    text = message.text.lower()
    logger.info(f"Received message in chat {chat_id}: {text}")

    now = asyncio.get_event_loop().time()
    if now < cooldowns_until.get(chat_id, 0.0):
        remaining = int(cooldowns_until.get(chat_id, 0.0) - now)
        logger.info(f"Chat {chat_id} is in cooldown ({remaining}s remaining), skipping")
        return

    kprob, mprob, gprob = chat_probs(chat_id)
    logger.info(f"Chat probabilities: k={kprob}, m={mprob}, g={gprob}")

    global total_replies_sent, total_keyword_replies, total_general_replies
    # Keyword replies
    for key, responses in KEYWORDS.items():
        if key.lower() in text:
            logger.info(f"Keyword match found: {key}")
            if should_reply(kprob):
                reply = random.choice(responses)
                logger.info(f"Replying to keyword {key}: {reply}")
                await message.reply_text(reply)
                cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
                last_msg_time[chat_id] = now
                total_replies_sent += 1
                total_keyword_replies += 1
                return
            else:
                logger.info(f"Keyword {key} detected but did not pass probability check")

    # Username mentions in entities
    if message.entities:
        for ent in message.entities:
            if ent.type == MessageEntity.MENTION:
                username = message.text[ent.offset : ent.offset + ent.length]
                if username.lower() in KEYWORDS:
                    logger.info(f"Username mention matched keyword: {username}")
                    if should_reply(kprob):
                        reply = random.choice(KEYWORDS[username.lower()])
                        logger.info(f"Replying to username {username}: {reply}")
                        await message.reply_text(reply)
                        cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
                        last_msg_time[chat_id] = now
                        return
                    else:
                        logger.info(f"Username trigger {username} did not pass probability check")

    # Bot mentions with anti-spam logic
    mention_token = f"@{context.bot.username.lower()}"
    if mention_token in text and should_reply(mprob):
        # Anti-spam: Only reply if last reply was more than 30 seconds ago
        last_mention_time = getattr(context.chat_data, 'last_mention_time', None)
        if last_mention_time and now - last_mention_time < 30:
            logger.info(f"Anti-spam: Skipping mention reply in chat {chat_id} (last reply {now - last_mention_time:.1f}s ago)")
            return
        flat = [r for rs in KEYWORDS.values() for r in rs]
        reply = random.choice(flat)
        logger.info(f"Replying to mention: {reply}")
        await message.reply_text(reply)
        cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
        last_msg_time[chat_id] = now
        context.chat_data['last_mention_time'] = now
        return
    else:
        logger.info("Bot mention did not pass probability check")

    # General replies
    if GENERAL_REPLIES and should_reply(gprob):
        reply = random.choice(GENERAL_REPLIES)
        logger.info(f"Replying with general reply: {reply}")
        await message.reply_text(reply)
        cooldowns_until[chat_id] = now + COOLDOWN_SECONDS
        last_msg_time[chat_id] = now
        total_replies_sent += 1
        total_general_replies += 1
        return
    else:
        logger.info("No reply chosen by probability")


# ---- Handlers: track activity ---------------------------------------------------


async def track_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Update last activity time for idle detection."""
    chat = update.effective_chat
    if not chat:
        logger.warning("track_activity: no chat")
        return
    last_msg_time[chat.id] = asyncio.get_event_loop().time()
    logger.info(f"Updated last activity for chat {chat.id}")


# ---- Commands -------------------------------------------------------------------
async def activatehype_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activate scheduled hype messages in this chat."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    scheduled_hype_active[chat.id] = True
    await message.reply_text("Scheduled hype messages activated for this chat.")

async def deactivatehype_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deactivate scheduled hype messages in this chat."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    scheduled_hype_active[chat.id] = False
    await message.reply_text("Scheduled hype messages deactivated for this chat.")

async def reloadscheduled_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reload scheduled hype messages from scheduled_hype.json."""
    global SCHEDULED_HYPE
    try:
        SCHEDULED_HYPE = _load_scheduled_hype_file(Path("scheduled_hype.json"))
        await update.message.reply_text(f"Reloaded scheduled hype messages: gm={len(SCHEDULED_HYPE['gm'])}, noon={len(SCHEDULED_HYPE['noon'])}, gn={len(SCHEDULED_HYPE['gn'])}")
    except Exception as exc:
        await update.message.reply_text(f"Failed to reload scheduled hype messages: {exc}")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Activate the bot."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    active_chats[chat.id] = True
    save_state()
    await message.reply_text("MoonFishHypeBot is now active! 🚀🐟")
    logger.info(f"Activated in chat {chat.id}")


async def shutup_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Deactivate the bot."""
    chat_id = update.effective_chat.id
    message = update.message
    if not chat or not message:
        return
    active_chats[chat.id] = False
    save_state()
    await message.reply_text("MoonFishHypeBot has been silenced! 🤐")
    logger.info(f"Deactivated in chat {chat_id}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report current state and overrides."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    kprob, mprob, gprob = chat_probs(chat.id)
    active = active_chats.get(chat.id, True)
    minutes = idle_minutes_override.get(chat.id, IDLE_MINUTES)
    now = asyncio.get_event_loop().time()
    remaining = max(0, int(cooldowns_until.get(chat.id, 0.0) - now))
    uptime = int(asyncio.get_event_loop().time() - bot_start_time)
    hours, remainder = divmod(uptime, 3600)
    minutes_u, seconds = divmod(remainder, 60)
    await message.reply_text(
        f"Active: {active}\n"
        f"Idle minutes: {minutes}\n"
        f"Keyword prob: {kprob:.2f}\n"
        f"Mention prob: {mprob:.2f}\n"
        f"General prob: {gprob:.2f}\n"
        f"Cooldown remaining: {remaining}s\n"
        f"Total replies sent: {total_replies_sent}\n"
        f"Keyword replies: {total_keyword_replies}\n"
        f"General replies: {total_general_replies}\n"
        f"Idle replies: {total_idle_replies}\n"
        f"Bot uptime: {hours}h {minutes_u}m {seconds}s"
    )
    logger.info("Reported status")


async def setidle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set idle timeout in minutes (persistent)."""
    global IDLE_TIMEOUT
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        value = int(context.args[0])
        if value < 1 or value > 1440:
            await update.message.reply_text("Idle timeout must be between 1 and 1440 minutes.")
            return
        IDLE_TIMEOUT = value
        state["idle_timeout"] = IDLE_TIMEOUT
        save_state()
        await update.message.reply_text(f"Idle timeout set to {IDLE_TIMEOUT} minutes.")
    except Exception:
        await update.message.reply_text("Usage: /setidle <minutes>")


async def setkeyword_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set keyword reply probability (persistent)."""
    global KEYWORD_REPLY_PROB
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        value = int(context.args[0])
        if value < 0 or value > 100:
            await update.message.reply_text("Keyword probability must be between 0 and 100.")
            return
        KEYWORD_REPLY_PROB = value
        state["keyword_prob"] = KEYWORD_REPLY_PROB
        save_state()
        await update.message.reply_text(f"Keyword probability set to {KEYWORD_REPLY_PROB}%")
    except Exception:
        await update.message.reply_text("Usage: /setkeyword <0-100>")


async def setmention_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set mention reply probability (persistent)."""
    global MENTION_REPLY_PROB
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        value = int(context.args[0])
        if value < 0 or value > 100:
            await update.message.reply_text("Mention probability must be between 0 and 100.")
            return
        MENTION_REPLY_PROB = value
        state["mention_prob"] = MENTION_REPLY_PROB
        save_state()
        await update.message.reply_text(f"Mention probability set to {MENTION_REPLY_PROB}%")
    except Exception:
        await update.message.reply_text("Usage: /setmention <0-100>")


async def setreply_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set general reply probability (persistent)."""
    global GENERAL_REPLY_PROB
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        value = int(context.args[0])
        if value < 0 or value > 100:
            await update.message.reply_text("General probability must be between 0 and 100.")
            return
        GENERAL_REPLY_PROB = value
        state["general_prob"] = GENERAL_REPLY_PROB
        save_state()
        await update.message.reply_text(f"General probability set to {GENERAL_REPLY_PROB}%")
    except Exception:
        await update.message.reply_text("Usage: /setreply <0-100>")


async def setcooldown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set cooldown duration (persistent)."""
    global COOLDOWN_SECONDS
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    try:
        value = int(context.args[0])
        if value < 1 or value > 3600:
            await update.message.reply_text("Cooldown must be between 1 and 3600 seconds.")
            return
        COOLDOWN_SECONDS = value
        state["cooldown_seconds"] = COOLDOWN_SECONDS
        save_state()
        await update.message.reply_text(f"Cooldown set to {COOLDOWN_SECONDS}s")
    except Exception:
        await update.message.reply_text("Usage: /setcooldown <seconds>")


async def calmdown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Temporarily increase cooldown 40 seconds (non-persistent)."""
    global COOLDOWN_SECONDS
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    COOLDOWN_SECONDS += 40
    await update.message.reply_text(
        f"Cooldown temporarily increased to {COOLDOWN_SECONDS}s"
    )
    logger.info(f"Cooldown temporarily raised to {COOLDOWN_SECONDS}")


async def reloadidle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reload idle messages from idle_messages.json."""
    global IDLE_MESSAGES
    try:
        load_external_lists()
        IDLE_MESSAGES = _load_idle_file(IDLE_FILE) if IDLE_FILE.exists() else list(DEFAULT_IDLE)
        await update.message.reply_text(f"Reloaded {len(IDLE_MESSAGES)} idle messages.")
        logger.info(f"Reloaded {len(IDLE_MESSAGES)} idle messages from {IDLE_FILE}")
    except Exception as exc:
        await update.message.reply_text(f"Failed to reload idle messages: {exc}")
        print(f"[Console] Failed to reload idle messages: {exc}")


async def reloadkeys_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reload keyword replies from keywords.json."""
    global KEYWORDS
    try:
        load_external_lists()
        KEYWORDS = _load_keywords_file(KEYWORDS_FILE) if KEYWORDS_FILE.exists() else dict(DEFAULT_KEYWORDS)
        await update.message.reply_text(f"Reloaded {len(KEYWORDS)} keyword sets.")
        logger.info(f"Reloaded {len(KEYWORDS)} keyword sets from {KEYWORDS_FILE}")
    except Exception as exc:
        await update.message.reply_text(f"Failed to reload keyword responses: {exc}")
        print(f"[Console] Failed to reload keyword responses: {exc}")


async def reloadgeneral_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reload general replies from general_replies.json."""
    global GENERAL_REPLIES
    try:
        load_external_lists()
        GENERAL_REPLIES = _load_general_file(GENERAL_FILE) if GENERAL_FILE.exists() else list(DEFAULT_GENERAL)
        await update.message.reply_text(f"Reloaded {len(GENERAL_REPLIES)} general replies.")
        logger.info(f"Reloaded {len(GENERAL_REPLIES)} general replies from {GENERAL_FILE}")
    except Exception as exc:
        await update.message.reply_text(f"Failed to reload general replies: {exc}")
        print(f"[Console] Failed to reload general replies: {exc}")


async def hype_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Force send a hype message."""
    chat = update.effective_chat
    message = update.message
    if not chat or not message:
        return
    if not active_chats.get(chat.id, True):
        return
    flat = [r for rs in KEYWORDS.values() for r in rs]
    if flat:
        reply = random.choice(flat)
        await update.message.reply_text(reply)
    logger.info(f"Hype command used, replied: {reply}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message with command descriptions. Admins only; reply is private if possible."""
    chat = update.effective_chat
    message = update.message
    user = update.effective_user
    if not chat or not message or not user:
        return
    # Check admin status
    admins = await context.bot.get_chat_administrators(chat.id)
    if user.id not in [admin.user.id for admin in admins]:
        await message.reply_text("Only group admins can use /help.")
        return
    help_text = (
        "MoonFishHypeBot Command Reference:\n\n"
        "/start - Activate the bot in the current group.\n"
        "/shutup - Deactivate the bot in the current group.\n"
        "/status - Show current global configuration, state, and bot statistics.\n"
        "/hype - Force send a hype message to the group.\n"
        "/setidle X - Set idle timeout in minutes (persistent, 1-1440).\n"
        "/setkeyword X - Set keyword reply probability (persistent, 0-100).\n"
        "/setmention X - Set mention reply probability (persistent, 0-100).\n"
        "/setreply X - Set general reply probability (persistent, 0-100).\n"
        "/setcooldown X - Set global cooldown in seconds (persistent, 1-3600).\n"
        "/calmdown - Temporarily increase cooldown by +40s (non-persistent).\n"
        "/reloadidle - Reload idle messages from idle_messages.json.\n"
        "/reloadkeys - Reload keyword responses from keywords.json.\n"
        "/reloadgeneral - Reload general replies from general_replies.json.\n"
        "/reloadscheduled - Reload scheduled hype messages from scheduled_hype.json.\n"
        "/activatehype - Activate scheduled hype messages for this chat.\n"
        "/deactivatehype - Deactivate scheduled hype messages for this chat.\n"
        "/help - Show this help message (admins only).\n"
    )
    # Try to send privately if possible
    try:
        await context.bot.send_message(chat_id=user.id, text=help_text)
        await message.reply_text("Help sent privately.")
    except Exception:
        await message.reply_text(help_text)


# ---- Lifecycle ------------------------------------------------------------------


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
    app.add_handler(CommandHandler("setcooldown", setcooldown_command))
    app.add_handler(CommandHandler("reloadidle", reloadidle_command))
    app.add_handler(CommandHandler("reloadkeys", reloadkeys_command))
    app.add_handler(CommandHandler("reloadgeneral", reloadgeneral_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("activatehype", activatehype_command))
    app.add_handler(CommandHandler("deactivatehype", deactivatehype_command))
    app.add_handler(CommandHandler("reloadscheduled", reloadscheduled_command))

    asyncio.create_task(idle_task(app))
    asyncio.create_task(scheduled_hype_task(app))
    logger.info("MoonFish Hype Bot is running...")
    await app.run_polling()


if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
