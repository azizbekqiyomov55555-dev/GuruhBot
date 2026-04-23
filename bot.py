# ╔══════════════════════════════════════════════════════════════════════╗
# ║   🤖 YORDAMCHI + TEKSHIRISH + 🎵 VOICE CHAT MUSIQA BOT v4          ║
# ║   ✅ /start bosgan foydalanuvchilarni saqlash                        ║
# ║   ✅ Admin panel — foydalanuvchini ID bo'yicha tekshirish            ║
# ║   ✅ Guruhda yozish uchun kanalga OBUNA bo'lish shart                ║
# ║   ✅ Guruhda yozish uchun 2 DO'ST TAKLIF qilish shart               ║
# ║   ✅ Har 2 daqiqada taklif xabari                                    ║
# ║   ✅ So'kingan foydalanuvchini avtomatik MUTE qilish                ║
# ║   ✅ Ban / Kick / Unban / Admin qo'shish                            ║
# ║   🎵 /play  — Voice Chat'ga STREAM qilish (Kristine Music kabi)     ║
# ║   🎵 /skip  — Keyingi qo'shiqqa o'tish                             ║
# ║   🎵 /stop  — Musiqani to'xtatish                                   ║
# ║   🎵 /queue — Navbat ko'rish                                        ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# 💡 ISHGA TUSHIRISH:
#   pip install "python-telegram-bot[job-queue]==20.7" yt-dlp pyrogram==2.0.106 pytgcalls
#   sudo apt install ffmpeg
#
# ⚙️ API_ID va API_HASH olish:
#   1. https://my.telegram.org ga kiring
#   2. "API development tools" ga o'ting
#   3. App yarating → API_ID va API_HASH oling
#
# ⚙️ BOT SOZLAMALARI (@BotFather):
#   1. Bot Settings → Group Privacy → DISABLE
#   2. Botni guruhga ADMIN qiling (Manage Video Chats ruxsati kerak!)

import logging
import sqlite3
import asyncio
import random
import urllib.parse
import os
import glob
import sys
from datetime import datetime, timedelta

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember,
    ChatPermissions, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ChatMemberHandler, ContextTypes, filters
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

import yt_dlp

# ── PyTgCalls imports ──
try:
    from pyrogram import Client
    from pytgcalls import PyTgCalls
    from pytgcalls.types import MediaStream, AudioQuality
    PYTGCALLS_AVAILABLE = True
except ImportError:
    PYTGCALLS_AVAILABLE = False
    print("⚠️  pytgcalls/pyrogram o'rnatilmagan! Faqat fayl yuborish ishlaydi.")
    print("    pip install pyrogram==2.0.106 pytgcalls")


# ═══════════════════════════════════════════════════════
#                    ⚙️ ASOSIY SOZLAMALAR
# ═══════════════════════════════════════════════════════
BOT_TOKEN        = os.environ.get("BOT_TOKEN", "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk")
ADMIN_IDS        = [int(x) for x in os.environ.get("ADMIN_IDS", "8537782289").split(",")]
BOT_NAME         = os.environ.get("BOT_NAME", "@GuruhYordamchIUZBBOT")
INVITE_INTERVAL  = 120
REQUIRED_INVITES = 2
MUTE_DURATION    = 10

# ════════════════════════════════════════════════════════
#   🔑 my.telegram.org dan olingan API kalitlar
#   https://my.telegram.org → API development tools
# ════════════════════════════════════════════════════════
API_ID   = int(os.environ.get("API_ID", "37366974"))
API_HASH = os.environ.get("API_HASH", "08d09c7ed8b7cb414ed6a99c104f1bd6")

INVITE_MESSAGE = (
    "👋 <b>Assalom aleykum birodarlar!</b>\n\n"
    "🏆 Do'stlaringizni guruhga taklif qiling!\n"
    "Kim ko'p odam qo'shsa — guruh qahramoni bo'ladi! 💪\n\n"
    "👇 Tugmani bosing va taklif qiling!"
)

invite_links_db: dict = {}
waiting_for_music: dict = {}

# ── Musiqa navbati (queue) ──
# { chat_id: [ {title, file, requester, duration}, ... ] }
music_queues: dict = {}
# { chat_id: {title, file, requester, duration} }  — hozir ijro etilayotgan
now_playing:  dict = {}

# ── Pyrogram session yaratish uchun vaqtinchalik client ──
_temp_pyro_client = None


# ═══════════════════════════════════════════════════════
#   🔞 SO'KINISH FILTRI
# ═══════════════════════════════════════════════════════
BAD_WORDS = [
    "siksana", "sikdir", "orospu", "qaltiraban", "yaramas",
    "harom", "ahmoq", "tentak", "noinsof", "buzuq",
    "it bolasi", "eshak", "la'nat",
    "бля", "блять", "пизд", "хуй", "еба", "ёба",
    "сука", "пиздец", "залуп", "мудак", "долбо",
    "fuck", "shit", "bitch", "asshole", "cunt", "dick",
    "bastard", "motherfucker",
]

SWEAR_WARNINGS = [
    "🚫 {name}, iltimos so'kinmang! Bu guruhda haqorat taqiqlangan. {dur} daqiqa sukut.",
    "⚠️ {name}! So'kinish qat'iyan man etilgan! {dur} daqiqa mute qilindingiz.",
    "🔇 {name}, bunday so'zlar guruhimizga yarashmaydi! {dur} daqiqa jim o'tirasiz.",
    "❌ {name}! Iltimos, adabli gaplashing. {dur} daqiqa mute qilindingiz.",
    "🙏 {name}, so'kinmang! Guruh qoidasiga rioya qiling. {dur} daqiqa mute.",
]

def contains_bad_word(text: str) -> bool:
    t = text.lower()
    return any(bw in t for bw in BAD_WORDS)


# ═══════════════════════════════════════════════════════
#   🗑 O'CHIRILGAN VA 🌍 XORIJIY FOYDALANUVCHILARNI ANIQLASH
# ═══════════════════════════════════════════════════════
def is_deleted_account(user) -> bool:
    """O'chirilgan Telegram hisob tekshirish (first_name va username yo'q)"""
    return not user.first_name and not user.username


def has_arabic_chars(text: str) -> bool:
    """Arab yozuvi harflari bormi tekshirish"""
    if not text:
        return False
    return any(
        '\u0600' <= c <= '\u06FF' or  # Arabic
        '\u0750' <= c <= '\u077F' or  # Arabic Supplement
        '\u08A0' <= c <= '\u08FF' or  # Arabic Extended-A
        '\uFB50' <= c <= '\uFDFF' or  # Arabic Presentation Forms-A
        '\uFE70' <= c <= '\uFEFF'     # Arabic Presentation Forms-B
        for c in text
    )


def has_chinese_chars(text: str) -> bool:
    """Xitoy/Yapon/Koreys yozuvi harflari bormi tekshirish"""
    if not text:
        return False
    return any(
        '\u4E00' <= c <= '\u9FFF' or  # CJK Unified Ideographs
        '\u3400' <= c <= '\u4DBF' or  # CJK Extension A
        '\uF900' <= c <= '\uFAFF' or  # CJK Compatibility Ideographs
        '\u3040' <= c <= '\u309F' or  # Hiragana
        '\u30A0' <= c <= '\u30FF' or  # Katakana
        '\uAC00' <= c <= '\uD7AF'     # Hangul Syllables (Koreys)
        for c in text
    )


# Chiqariladigan til kodlari (language_code bo'yicha)
FOREIGN_LANG_CODES = {'zh', 'ar', 'fa', 'ur', 'he', 'ko', 'ja', 'bo', 'ug'}


def is_foreign_user(user) -> bool:
    """Xitoy, arab yoki boshqa chiqariladigan xorijiy foydalanuvchi tekshirish"""
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    if has_arabic_chars(full_name) or has_chinese_chars(full_name):
        return True
    lang = getattr(user, 'language_code', '') or ''
    if lang.lower().split('-')[0] in FOREIGN_LANG_CODES:
        return True
    return False


# ═══════════════════════════════════════════════════════
#                  💬 AVTOMATIK JAVOBLAR
# ═══════════════════════════════════════════════════════
RESPONSES = {
    "assalomu alaykum": ["Va alaykum assalom va rahmatulloh, {name}! 🤲✨","Va alaykum assalom, {name}! Xayrli kun! 😊","Alaykum assalom {name} aka! Kayfiyat yaxshimi? 🤝","Va alaykum assalom {name}! Xush kelibsiz! 🌟"],
    "assalom": ["Va alaykum assalom, {name}! 🙏😊","Va alaykum {name}! Xayrli kun! ☀️","Assalomu alaykum {name}! Xush kelibsiz! 🌟","Salom {name} aka! Qandaysiz? 😄","Hey {name}! Assalom! Kayfiyat zo'rmi? 😎"],
    "salom": ["Va alaykum assalom, {name}! 😊","Salom-salom {name}! Qandaysiz? 😄","Hey {name}, salom! Kayfiyat qanday? 😎","Salom {name}! Bugun ham zo'r kun bo'lsin! ✨","Salomlar {name}! Nima gap? 🌟","Salom {name} aka! Yaxshimisiz? 🤝"],
    "салом": ["Салом {name}! 😊","Ва алайкум ассалом {name}! 🤲"],
    "привет": ["Привет {name}! 😊","Привет-привет {name}! Как дела? 😄","Привет {name}! Salom! 🌟"],
    "hello": ["Hello {name}! 👋 Welcome!","Hi {name}! Salom! 🌟","Hello {name}! Glad to see you! 😊"],
    "hi": ["Hi {name}! 👋","Hey {name}! 😊","Hi-hi {name}! 🌟"],
    "xayrli tong": ["Xayrli tong {name}! ☀️🌸 Omadli kun!","Tong muborak {name}! ☀️","Xayrli tong {name}! Bugun ajoyib kun bo'ladi! 🌅✨"],
    "xayrli kun": ["Sizga ham xayrli kun {name}! ☀️😊","Xayrli kun {name}! 🌟 Kayfiyat a'lo bo'lsin!"],
    "xayrli kech": ["Xayrli kech {name}! 🌙✨","Kech xayrli bo'lsin {name}! Dam oling! 🌙😌"],
    "xayr": ["Xayr {name}! 👋 Eson-omon yuring!","Xayr-xayr {name}! 🌟 Sog' bo'ling!"],
    "hayr": ["Hayr {name}! Ko'rishguncha! 👋","Hayr {name}! Eson yuring! 🌟"],
    "bye": ["Bye {name}! Ko'rishguncha! 👋","Bye-bye {name}! 🌟"],
    "rahmat": ["Arzimaydi {name}! 😊 Doimo xizmatda!","Marhamat {name}! 🌟","Hech gap emas {name}! 👍"],
    "raxmat": ["Arzimaydi {name}! 😊","Marhamat {name}! 🌟"],
    "спасибо": ["Пожалуйста {name}! 😊","Не за что {name}! 🌟"],
    "qalaysiz": ["Yaxshi rahmat! {name}, siz-chi? 😊","Hammasi zo'r {name}! Siz qalaysiz? 😄"],
    "qalaysan": ["Yaxshi rahmat {name}! O'zing-chi? 😊","Zo'r {name}! Sen-chi? 😄"],
    "qalay": ["Yaxshi rahmat {name}! Siz-chi? 😊","Zo'r! {name}! 💪"],
    "yaxshimisiz": ["Yaxshi rahmat {name}! Siz ham yaxshimisiz? 😊","Hammasi joyida {name}! 🌟"],
    "yaxshimisan": ["Yaxshi {name}! O'zing-chi? 😊","Hammasi zo'r {name}! 💪"],
    "nima gap": ["{name}, hech gap yo'q, tinch! 😄","Tinchlik {name}! Nima yangiliklar? 🌟"],
    "nima": ["Ha {name}, nima gap? 😊","Aytingchi {name}? 🙂"],
    "kim": ["Men — {BOT_NAME}! {name} aka! 🤖😊","Men botman {name}! Xizmatdaman! 🤖🌟"],
    "liboy": ["Liboy {name}? Nima gap? 😄","Ha {name}, liboy! 😂🔥"],
    "zo'r": ["Ha {name}, rostdan ham zo'r! 💪🔥","Ajoyib {name}! 🌟"],
    "super": ["Super-super {name}! 🔥💯","{name}, juda zo'r! 🌟👏"],
    "barakalla": ["Barakalla {name}! 👏🌟","Barakalla {name} aka! 🤲✨"],
    "ajoyib": ["Ajoyib {name}! 🌟✨","Rostdan ajoyib {name}! 💪"],
    "yaxshi": ["Yaxshi {name}! 👍😊","Zo'r {name}! 🌟"],
    "ok": ["Ok {name}! 👍","Mayli {name}! 😊"],
    "omad": ["Omad tilayman {name}! 🍀💫","Omad {name}! Uddalaysiz! 💪🍀"],
    "inshalloh": ["Inshalloh {name}! 🤲🌟"],
    "mashalloh": ["Mashalloh {name}! 🤲🌟"],
    "alhamdulillah": ["Alhamdulillah {name}! 🤲"],
    "bismillah": ["Bismillah {name}! 🤲 Omad!"],
    "tabrik": ["Tabriklayman {name}! 🎉🎊"],
    "yangi yil": ["Yangi yil muborak {name}! 🎆🎇✨"],
    "hayit": ["Hayit muborak {name}! 🤲🎊✨"],
    "ovqat": ["Ishtaha bilan {name}! 😋🍽️"],
    "❤️": ["❤️ Rahmat {name}!","🥰 Siz ham {name}!"],
    "👍": ["👍 Zo'r {name}!","✅ Yaxshi {name}!"],
    "🔥": ["🔥🔥 {name}, zo'r!","🔥 {name} ishdagi! 💯"],
    "🎉": ["🎉🎊 {name}, tabriklayman!"],
    "😂": ["😂😂 {name} kuldirib yubordi!"],
    "💪": ["💪💪 {name}, kuchli!"],
    "🙏": ["🙏 Xudoga shukur {name}!"],
    "👏": ["👏👏 {name}! Zo'r!"],
    "😎": ["Zo'r {name}! 😎🔥"],
    "🥰": ["🥰 Rahmat {name}!"],
}

def get_auto_reply(text: str, user_name: str) -> str | None:
    t = text.lower().strip()
    for kw in sorted(RESPONSES, key=len, reverse=True):
        if kw in t:
            reply = random.choice(RESPONSES[kw])
            reply = reply.replace("{name}", user_name)
            reply = reply.replace("{BOT_NAME}", BOT_NAME)
            return reply
    return None


# ═══════════════════════════════════════════════════════
#                      📦 DATABASE
# ═══════════════════════════════════════════════════════
def init_db():
    conn = sqlite3.connect("bot_data.db")
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS groups (
        chat_id           INTEGER PRIMARY KEY,
        title             TEXT    DEFAULT '',
        username          TEXT    DEFAULT '',
        member_count      INTEGER DEFAULT 0,
        added_date        TEXT    DEFAULT '',
        is_banned         INTEGER DEFAULT 0,
        ban_reason        TEXT    DEFAULT '',
        invite_active     INTEGER DEFAULT 1,
        livestream_active INTEGER DEFAULT 0,
        invite_disabled   INTEGER DEFAULT 0
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS channels (
        chat_id    INTEGER PRIMARY KEY,
        title      TEXT DEFAULT '',
        username   TEXT DEFAULT '',
        added_date TEXT DEFAULT ''
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id    INTEGER PRIMARY KEY,
        username   TEXT DEFAULT '',
        first_name TEXT DEFAULT '',
        last_name  TEXT DEFAULT '',
        start_date TEXT DEFAULT '',
        last_seen  TEXT DEFAULT ''
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_groups (
        user_id INTEGER,
        chat_id INTEGER,
        PRIMARY KEY (user_id, chat_id)
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS user_messages (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        date    TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id  INTEGER,
        user_id  INTEGER,
        username TEXT,
        date     TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT DEFAULT ''
    )""")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_username', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_link', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_kick_deleted', '1')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('auto_kick_foreign', '0')")

    c.execute("""CREATE TABLE IF NOT EXISTS user_invites (
        chat_id      INTEGER,
        user_id      INTEGER,
        invite_count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    )""")

    for col in ["livestream_active INTEGER DEFAULT 0", "invite_disabled INTEGER DEFAULT 0"]:
        try:
            c.execute(f"ALTER TABLE groups ADD COLUMN {col}")
        except Exception:
            pass

    conn.commit()
    conn.close()


def get_db():
    return sqlite3.connect("bot_data.db")


# ── Foydalanuvchilar ──
def save_user(user):
    conn = get_db(); c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("""INSERT INTO users (user_id, username, first_name, last_name, start_date, last_seen)
                 VALUES (?, ?, ?, ?, ?, ?)
                 ON CONFLICT(user_id) DO UPDATE SET
                     username=excluded.username,
                     first_name=excluded.first_name,
                     last_name=excluded.last_name,
                     last_seen=excluded.last_seen""",
              (user.id, user.username or "", user.first_name or "", user.last_name or "", now, now))
    conn.commit(); conn.close()

def update_user_seen(user):
    save_user(user)

def get_user_info(user_id: int) -> dict | None:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT user_id, username, first_name, last_name, start_date, last_seen FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    if not row:
        conn.close(); return None
    uid, uname, fname, lname, start_date, last_seen = row

    c.execute("""SELECT g.chat_id, g.title, g.username
                 FROM user_groups ug
                 JOIN groups g ON ug.chat_id = g.chat_id
                 WHERE ug.user_id = ?""", (user_id,))
    groups = c.fetchall()

    c.execute("""SELECT g.chat_id, g.title, g.username, COUNT(m.id) as msg_count
                 FROM user_messages m
                 JOIN groups g ON m.chat_id = g.chat_id
                 WHERE m.user_id = ?
                 GROUP BY m.chat_id
                 ORDER BY msg_count DESC""", (user_id,))
    written = c.fetchall()

    conn.close()
    return {
        "user_id":    uid,
        "username":   uname,
        "first_name": fname,
        "last_name":  lname,
        "start_date": start_date,
        "last_seen":  last_seen,
        "groups":     groups,
        "written":    written,
    }

def get_total_users():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users"); n = c.fetchone()[0]
    conn.close(); return n

def get_today_users():
    conn = get_db(); c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT COUNT(*) FROM users WHERE start_date >= ?", (today,)); n = c.fetchone()[0]
    conn.close(); return n


# ── Guruhlar ──
def add_group(chat_id, title, username):
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO groups
        (chat_id, title, username, added_date, invite_active)
        VALUES (?, ?, ?, ?, 1)""",
        (chat_id, title or "", username or "", datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("UPDATE groups SET title=?, username=? WHERE chat_id=?", (title or "", username or "", chat_id))
    conn.commit(); conn.close()

save_group = add_group

def ban_group(chat_id, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=1, ban_reason=? WHERE chat_id=?", (reason, chat_id))
    conn.commit(); conn.close()

def unban_group(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=0, ban_reason='' WHERE chat_id=?", (chat_id,))
    conn.commit(); conn.close()

def is_banned_group(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT is_banned FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close()
    return row and row[0] == 1

def get_all_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id, title, username, member_count, added_date, is_banned, ban_reason FROM groups")
    rows = c.fetchall(); conn.close(); return rows

def get_active_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id FROM groups WHERE is_banned=0 AND invite_active=1")
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]

def get_total_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups"); n = c.fetchone()[0]
    conn.close(); return n

def get_stats():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=0"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=1"); banned = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages WHERE date >= date('now')"); today = c.fetchone()[0]
    conn.close(); return active, banned, total, today


# ── Kanallar ──
def save_channel(chat_id, title, username):
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO channels (chat_id, title, username, added_date)
                 VALUES (?, ?, ?, ?)""",
              (chat_id, title or "", username or "", datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("UPDATE channels SET title=?, username=? WHERE chat_id=?", (title or "", username or "", chat_id))
    conn.commit(); conn.close()

def get_all_channels():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id, title, username, added_date FROM channels")
    rows = c.fetchall(); conn.close(); return rows


# ── Kanal sozlamalari ──
def get_channel_settings():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='channel_username'"); u = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key='channel_link'"); l = c.fetchone()
    conn.close()
    return (u[0] if u else ""), (l[0] if l else "")

def save_channel_settings(username: str, link: str):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE settings SET value=? WHERE key='channel_username'", (username,))
    c.execute("UPDATE settings SET value=? WHERE key='channel_link'", (link,))
    conn.commit(); conn.close()

def clear_channel_settings():
    save_channel_settings("", "")


# ── Jonli efir ──
def set_livestream(chat_id: int, active: bool):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET livestream_active=? WHERE chat_id=?", (1 if active else 0, chat_id))
    conn.commit(); conn.close()

def get_livestream_status(chat_id: int) -> bool:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT livestream_active FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close(); return bool(row and row[0])


# ── Taklif boshqaruvi ──
def set_invite_disabled(chat_id: int, disabled: bool):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET invite_disabled=? WHERE chat_id=?", (1 if disabled else 0, chat_id))
    conn.commit(); conn.close()

def get_invite_disabled(chat_id: int) -> bool:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT invite_disabled FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close(); return bool(row and row[0])

# ── Auto-kick sozlamalari ──
def get_auto_kick_deleted() -> bool:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='auto_kick_deleted'")
    row = c.fetchone(); conn.close()
    return row and row[0] == '1'

def set_auto_kick_deleted(val: bool):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('auto_kick_deleted', ?)", ('1' if val else '0',))
    conn.commit(); conn.close()

def get_auto_kick_foreign() -> bool:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='auto_kick_foreign'")
    row = c.fetchone(); conn.close()
    return row and row[0] == '1'

def set_auto_kick_foreign(val: bool):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('auto_kick_foreign', ?)", ('1' if val else '0',))
    conn.commit(); conn.close()

def get_user_invite_count(chat_id: int, user_id: int) -> int:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT invite_count FROM user_invites WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    row = c.fetchone(); conn.close(); return row[0] if row else 0

def increment_user_invite(chat_id: int, user_id: int) -> int:
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT INTO user_invites (chat_id, user_id, invite_count)
                 VALUES (?, ?, 1)
                 ON CONFLICT(chat_id, user_id)
                 DO UPDATE SET invite_count = invite_count + 1""", (chat_id, user_id))
    conn.commit()
    c.execute("SELECT invite_count FROM user_invites WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    new_count = c.fetchone()[0]; conn.close(); return new_count


# ── Xabar loglanishi ──
def log_message(chat_id, user_id, username):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, user_id, username, date) VALUES (?, ?, ?, ?)",
              (chat_id, user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()

def save_user_in_group(user_id: int, chat_id: int):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_groups (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
    conn.commit(); conn.close()

def log_user_message(user_id: int, chat_id: int):
    conn = get_db(); c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT OR IGNORE INTO user_groups (user_id, chat_id) VALUES (?, ?)", (user_id, chat_id))
    c.execute("INSERT INTO user_messages (user_id, chat_id, date) VALUES (?, ?, ?)", (user_id, chat_id, now))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════
#                    🛠️ YORDAMCHILAR
# ═══════════════════════════════════════════════════════
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


# ── Admin huquqlari ──
PERM_LABELS = {
    "can_manage_chat":        "🔧 Guruhni boshqarish",
    "can_change_info":        "📝 Guruh ma'lumotini o'zgartirish",
    "can_delete_messages":    "🗑 Xabarlarni o'chirish",
    "can_restrict_members":   "🔇 Foydalanuvchilarni bloklash",
    "can_invite_users":       "🔗 Havola orqali taklif qilish",
    "can_pin_messages":       "📌 Xabarlarni qadash",
    "can_manage_video_chats": "📡 Jonli efirlarni boshqarish",
    "can_promote_members":    "👑 Yangi adminlar qo'shish",
    "can_manage_topics":      "🏷 A'zo teglarini tahrirlash",
    "can_post_stories":       "📖 Hikoya joylash",
    "can_edit_stories":       "✏️ Hikoyalarni tahrirlash",
    "can_delete_stories":     "🗑 Hikoyalarni o'chirish",
    "is_anonymous":           "👻 Anonimlik",
}

def get_perm_kb(selected: set, chat_id: int, user_id: int):
    rows = []
    for key, label in PERM_LABELS.items():
        check = "✅" if key in selected else "☐"
        rows.append([InlineKeyboardButton(
            f"{check} {label}",
            callback_data=f"perm_toggle_{key}_{chat_id}_{user_id}"
        )])
    rows.append([InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"perm_confirm_{chat_id}_{user_id}")])
    rows.append([InlineKeyboardButton("🔙 Bekor",      callback_data="admin_manage")])
    return InlineKeyboardMarkup(rows)


# ── Klaviaturalar ──
def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika",              callback_data="stats"),
         InlineKeyboardButton("👥 Guruhlar",                callback_data="groups_0")],
        [InlineKeyboardButton("🚫 Taqiqlangan",             callback_data="banned"),
         InlineKeyboardButton("⚙️ Sozlamalar",              callback_data="settings")],
        [InlineKeyboardButton("🔍 Foydalanuvchi tekshirish",callback_data="check_user_menu")],
        [InlineKeyboardButton("📢 Broadcast",               callback_data="broadcast_ask")],
    ])

def admin_reply_kb():
    return ReplyKeyboardMarkup([
        ["🛠 Admin Panel",              "📊 Statistika"],
        ["🚫 Foydalanuvchi ban",        "👢 Foydalanuvchi kick"],
        ["✅ Foydalanuvchi unban",      "👑 Admin qo'sh"],
        ["🔍 Foydalanuvchi tekshirish", "👥 Guruhlar ro'yxati"],
        ["📢 Broadcast",                "🔔 Kanal sozlash"],
        ["📡 Jonli efir",               "🔗 Taklif boshqaruv"],
        ["🗑 O'chirilganlarni tozala",  "🌍 Xorijiylarni chiqar"],
        ["⚙️ Auto-tozala sozlash",     "🔑 Session yaratish"],
    ], resize_keyboard=True, input_field_placeholder="Amalni tanlang...")

def user_kb(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("🎵 Musiqa Izla",      callback_data="music_search")],
        [InlineKeyboardButton("❓ Qo'llanma",        callback_data="how_to_add")],
        [InlineKeyboardButton("🆘 Adminga yozish",   callback_data="contact_admin")],
    ])


# ═══════════════════════════════════════════════════════
#   🔔 OBUNA TEKSHIRUVI (majburiy kanal)
# ═══════════════════════════════════════════════════════
async def check_subscription(bot, user_id: int) -> bool:
    ch_username, _ = get_channel_settings()
    if not ch_username:
        return True
    channel_id = ch_username if ch_username.startswith("@") else "@" + ch_username
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        return member.status not in ("kicked", "left")
    except TelegramError as e:
        err_msg = str(e).lower()
        logger.error(f"Obuna tekshirishda xato user={user_id}: {e}")
        if "user not found" in err_msg:
            return False
        return True

async def send_not_subscribed_message(query, user, ch_username: str, ch_link: str, gid: int):
    await query.answer("❌ Avval kanalga obuna bo'ling!", show_alert=True)
    try:
        await query.message.reply_text(
            f"🔔 <b>{user.first_name}, diqqat!</b>\n\n"
            f"❌ Taklif qilish uchun avval kanalga obuna bo'ling!\n\n"
            f"📢 Kanal: <b>{ch_username}</b>\n\n"
            f"1️⃣ Quyidagi tugma orqali kanalga o'ting\n"
            f"2️⃣ <b>Obuna bo'ling</b>\n"
            f"3️⃣ Orqaga qaytib <b>«Tekshirish»</b> tugmasini bosing",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=ch_link)],
                [InlineKeyboardButton("✅ Tekshirish", callback_data=f"check_sub_{gid}")],
            ])
        )
    except Exception as e:
        logger.error(f"Obuna xabari yuborishda xato: {e}")


# ═══════════════════════════════════════════════════════
#   🚫 GURUHDA YOZISH — OBUNA + 2 DO'ST TEKSHIRUVI
# ═══════════════════════════════════════════════════════
async def safe_delete(msg):
    try:
        await msg.delete()
    except Exception:
        pass

async def check_write_permission(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    msg  = update.message
    user = update.effective_user
    chat = update.effective_chat

    if is_admin(user.id):
        return True

    ch_username, ch_link = get_channel_settings()
    if ch_username:
        subscribed = await check_subscription(context.bot, user.id)
        if not subscribed:
            try: await msg.delete()
            except Exception: pass
            user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
            try:
                sent = await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"🔔 {user_mention}, guruhda yozish uchun\n"
                        f"avval <b>{ch_username}</b> kanaliga obuna bo'ling!\n\n"
                        f"Obuna bo'lgach «✅ Tekshirish» tugmasini bosing."
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📢 Kanalga o'tish", url=ch_link)],
                        [InlineKeyboardButton("✅ Tekshirish", callback_data=f"check_write_sub_{chat.id}")],
                    ])
                )
                asyncio.get_event_loop().call_later(30, lambda: asyncio.ensure_future(safe_delete(sent)))
            except Exception as e:
                logger.error(f"Xabar yuborishda xato: {e}")
            return False

    invite_count = get_user_invite_count(chat.id, user.id)
    if invite_count < REQUIRED_INVITES:
        try: await msg.delete()
        except Exception: pass
        remaining = REQUIRED_INVITES - invite_count
        user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
        try:
            sent = await context.bot.send_message(
                chat_id=chat.id,
                text=(
                    f"🔒 {user_mention}, guruhda yozish uchun\n"
                    f"<b>{REQUIRED_INVITES} ta do'st</b> taklif qilish kerak!\n\n"
                    f"📊 Holat: <b>{invite_count}/{REQUIRED_INVITES}</b> — yana <b>{remaining} ta</b> kerak\n\n"
                    f"👇 Taklif qilish uchun quyidagi tugmani bosing:"
                ),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Do'st taklif qilish", callback_data=f"invite_{chat.id}")],
                ])
            )
            asyncio.get_event_loop().call_later(30, lambda: asyncio.ensure_future(safe_delete(sent)))
        except Exception as e:
            logger.error(f"Taklif xabari xatosi: {e}")
        return False

    return True


# ═══════════════════════════════════════════════════════
#   🔇 SO'KINISH — AVTOMATIK MUTE + OGOHLANTIRISH
# ═══════════════════════════════════════════════════════
async def mute_user_for_swearing(bot, chat_id: int, user, message_id: int):
    until = datetime.now() + timedelta(minutes=MUTE_DURATION)
    user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    try: await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception: pass
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id, user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        warning = random.choice(SWEAR_WARNINGS)
        warning_text = warning.replace("{name}", user_mention).replace("{dur}", str(MUTE_DURATION))
        sent = await bot.send_message(
            chat_id=chat_id,
            text=f"{warning_text}\n\n⏰ Mute tugaydi: <b>{until.strftime('%H:%M')}</b>",
            parse_mode=ParseMode.HTML
        )
        logger.info(f"🔇 Mute: {user.first_name} ({user.id}) chat={chat_id}")
        await asyncio.sleep(15)
        try: await sent.delete()
        except Exception: pass
    except TelegramError as e:
        logger.error(f"Mute xatosi: {e}")


# ═══════════════════════════════════════════════════════
#   👥 TAKLIF TUGMASI
# ═══════════════════════════════════════════════════════
async def handle_invite_button(query, context: ContextTypes.DEFAULT_TYPE, gid: int):
    user = query.from_user
    ch_username, ch_link = get_channel_settings()

    if get_invite_disabled(gid):
        await query.answer("❌ Bu guruhda taklif funksiyasi o'chirilgan!", show_alert=True)
        return

    if ch_username:
        subscribed = await check_subscription(context.bot, user.id)
        if not subscribed:
            await send_not_subscribed_message(query, user, ch_username, ch_link, gid)
            return

    try:
        chat = await context.bot.get_chat(gid)
        group_title = chat.title or "Guruh"
    except TelegramError:
        group_title = "Guruh"

    try:
        link_obj = await context.bot.create_chat_invite_link(
            chat_id=gid,
            name=f"INV_{user.id}_{int(datetime.now().timestamp())}",
            creates_join_request=False,
        )
        link_str = link_obj.invite_link
        invite_links_db[link_str] = (user.id, user.first_name, gid)
    except TelegramError as e:
        logger.error(f"Invite link xato: {e}")
        await query.message.reply_text("❌ Havola yaratishda xato! Bot guruhda ADMIN ekanligini tekshiring.")
        return

    try:
        if "/+" in link_str:
            slug = link_str.split("/+")[-1]
        elif "joinchat/" in link_str:
            slug = link_str.split("joinchat/")[-1]
        else:
            slug = link_str.split("/")[-1].lstrip("+")
        add_members_url = f"tg://add?slug={slug}"
    except Exception:
        add_members_url = link_str

    invite_count = get_user_invite_count(gid, user.id)
    remaining    = max(0, REQUIRED_INVITES - invite_count)
    status_line  = (
        f"✅ <b>Siz allaqachon {invite_count} ta do'st taklif qildingiz!</b> Yozishingiz mumkin."
        if invite_count >= REQUIRED_INVITES
        else f"📊 Holat: <b>{invite_count}/{REQUIRED_INVITES}</b> — yana <b>{remaining} ta</b> kerak"
    )
    share_text = f"Salom! 👋 \"{group_title}\" guruhiga taklif qilmoqchiman! Qo'shiling! 💪"
    share_url  = (
        f"https://t.me/share/url?"
        f"url={urllib.parse.quote(link_str)}"
        f"&text={urllib.parse.quote(share_text)}"
    )
    await query.message.reply_text(
        f"🔗 <b>{user.first_name}, havolangiz tayyor!</b>\n\n"
        f"📌 Guruh: <b>{group_title}</b>\n\n"
        f"{status_line}\n\n"
        f"👇 <b>Ikki usuldan birini tanlang:</b>\n\n"
        f"1️⃣ <b>Kontaktdan tanlash</b>\n"
        f"2️⃣ <b>Havola ulashish</b>\n\n"
        f"🏆 Kim qo'shilsa, guruhda <b>siz maqtalasiz!</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 Kontaktdan tanlash", url=add_members_url)],
            [InlineKeyboardButton("📤 Havola ulashish",    url=share_url)],
        ])
    )


# ═══════════════════════════════════════════════════════
#   🎉 YANGI A'ZO TRACKING (taklif hisobi)
# ═══════════════════════════════════════════════════════
async def track_new_member_invite(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    result = update.chat_member
    if not result: return
    old_status = result.old_chat_member.status
    new_status  = result.new_chat_member.status
    if old_status in (ChatMember.LEFT, ChatMember.BANNED) and \
       new_status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
        new_member = result.new_chat_member.user
        chat_id    = result.chat.id

        # ── O'chirilgan hisob tekshirish (guruh VA kanal) ──
        if not new_member.is_bot and is_deleted_account(new_member) and get_auto_kick_deleted():
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=new_member.id)
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=new_member.id)
                logger.info(f"🗑 [track] O'chirilgan hisob chiqarildi: {new_member.id} ({result.chat.title})")
            except Exception as e:
                logger.error(f"O'chirilgan chiqarishda xato: {e}")
            return

        # ── Xorijiy foydalanuvchi tekshirish (guruh VA kanal) ──
        if not new_member.is_bot and get_auto_kick_foreign() and is_foreign_user(new_member):
            try:
                await context.bot.ban_chat_member(chat_id=chat_id, user_id=new_member.id)
                await context.bot.unban_chat_member(chat_id=chat_id, user_id=new_member.id)
                logger.info(f"🌍 [track] Xorijiy chiqarildi: {new_member.id} ({result.chat.title})")
            except Exception as e:
                logger.error(f"Xorijiy chiqarishda xato: {e}")
            return

        invite_link_obj = getattr(result, "invite_link", None)
        if invite_link_obj:
            link_str = getattr(invite_link_obj, "invite_link", None)
            if link_str and link_str in invite_links_db:
                inviter_id, inviter_name, _ = invite_links_db[link_str]
                new_count = increment_user_invite(chat_id, inviter_id)
                await _send_praise(context, chat_id, inviter_id, inviter_name, new_member, new_count)
                return
        inviter = getattr(result, "from_user", None)
        if inviter and inviter.id != new_member.id and not inviter.is_bot:
            new_count = increment_user_invite(chat_id, inviter.id)
            await _send_praise(context, chat_id, inviter.id, inviter.first_name, new_member, new_count)

async def _send_praise(context, chat_id, inviter_id, inviter_name, new_member, invite_count: int = 0):
    inviter_m = f'<a href="tg://user?id={inviter_id}">{inviter_name}</a>'
    new_m     = f'<a href="tg://user?id={new_member.id}">{new_member.first_name}</a>'
    maqtovlar = [
        f"🎉 <b>BARAKALLA!</b> {inviter_m} birodar {new_m}ni guruhga qo'shdi! 🤝",
        f"👏 <b>ZO'R!</b> {inviter_m} guruhimizga {new_m}ni olib keldi! 🔥",
        f"🌟 {inviter_m} — <b>GURUH QAHRAMONI!</b> {new_m}ni qo'shdi! 💪",
        f"✨ <b>RAHMAT</b> {inviter_m}! Yangi a'zo {new_m} xush kelibsiz! 🎉",
    ]
    if invite_count >= REQUIRED_INVITES:
        unlock_msg = f"\n\n🔓 {inviter_m} endi guruhda <b>erkin yoza oladi!</b> ✅"
    else:
        remaining = REQUIRED_INVITES - invite_count
        unlock_msg = (
            f"\n\n📊 {inviter_m} holati: <b>{invite_count}/{REQUIRED_INVITES}</b>"
            f" — yana <b>{remaining} ta</b> do'st kerak!"
        )
    text = random.choice(maqtovlar) + unlock_msg
    try:
        await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Maqtov xabarida xato: {e}")


# ═══════════════════════════════════════════════════════
#   📢 HAR 2 DAQIQADA GURUHGA TAKLIF XABARI
# ═══════════════════════════════════════════════════════
async def send_group_invite_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    ch_username, ch_link = get_channel_settings()
    group_ids = get_active_groups()
    for gid in group_ids:
        if get_invite_disabled(gid):
            continue
        try:
            buttons = [[InlineKeyboardButton("➕ Taklif qilish", callback_data=f"invite_{gid}")]]
            if ch_username and ch_link:
                buttons.append([InlineKeyboardButton("📢 Kanalga obuna bo'lish", url=ch_link)])
            await context.bot.send_message(
                chat_id=gid,
                text=INVITE_MESSAGE,
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except TelegramError as e:
            err = str(e)
            if "bot was kicked" in err or "chat not found" in err or "bot is not a member" in err:
                conn = get_db(); cur = conn.cursor()
                cur.execute("UPDATE groups SET invite_active=0 WHERE chat_id=?", (gid,))
                conn.commit(); conn.close()
            else:
                logger.error(f"Taklif xabari xato ({gid}): {e}")
        except Exception as e:
            logger.error(f"Taklif xabari xato ({gid}): {e}")


# ═══════════════════════════════════════════════════════
#   🎵 MUSIQA — YUKLAB OLISH YORDAMCHISI
# ═══════════════════════════════════════════════════════
def _get_ydl_opts(outtmpl: str, use_ffmpeg: bool = True) -> dict:
    opts = {
        "format": "bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best",
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "default_search": "ytsearch",
        "source_address": "0.0.0.0",
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
                "skip": ["dash", "hls"],
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Linux; Android 11; SM-G991B) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Mobile Safari/537.36"
            ),
            "Accept-Language": "uz-UZ,uz;q=0.9,en;q=0.8",
        },
        "socket_timeout": 30,
        "retries": 5,
        "fragment_retries": 5,
        "concurrent_fragment_downloads": 4,
    }
    if use_ffmpeg:
        opts["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }]
    return opts


def _find_downloaded_file(base_path: str, vid_id: str, prefix: str) -> str | None:
    exts = [".mp3", ".m4a", ".webm", ".opus", ".ogg", ".aac", ".flac"]
    for ext in exts:
        f = f"{prefix}{vid_id}{ext}"
        if os.path.exists(f):
            return f
    base = base_path.rsplit(".", 1)[0]
    for ext in exts:
        if os.path.exists(base + ext):
            return base + ext
    try:
        pattern = f"{prefix.rstrip('_')}*"
        files = glob.glob(pattern)
        if files:
            return max(files, key=os.path.getctime)
    except Exception:
        pass
    return None


async def download_audio(query: str) -> tuple[str | None, str, int, str]:
    """
    Audio faylni yuklab oladi.
    Qaytaradi: (fayl_yoli, sarlavha, davomiylik, ijrochi)
    """
    title    = query[:50]
    duration = 0
    uploader = "Noma'lum"
    mp3_file = None

    search_query = query if query.startswith("http") else f"ytsearch1:{query}"

    # 1-urinish: ffmpeg bilan mp3
    try:
        prefix1  = "/tmp/vc1_"
        outtmpl1 = f"{prefix1}%(id)s.%(ext)s"
        with yt_dlp.YoutubeDL(_get_ydl_opts(outtmpl1, use_ffmpeg=True)) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if info and "entries" in info:
                entries = [e for e in info["entries"] if e]
                info = entries[0] if entries else None
            if info:
                title    = (info.get("title") or query)[:64]
                duration = int(info.get("duration") or 0)
                uploader = (info.get("uploader") or info.get("channel") or "Noma'lum")[:40]
                vid_id   = info.get("id") or "unknown"
                filename = ydl.prepare_filename(info)
                mp3_file = _find_downloaded_file(filename, vid_id, prefix1)
    except Exception as e:
        logger.warning(f"1-urinish muvaffaqiyatsiz ({query}): {e}")

    # 2-urinish: ffmpeg siz (fallback)
    if not mp3_file or not os.path.exists(mp3_file):
        try:
            prefix2  = "/tmp/vc2_"
            outtmpl2 = f"{prefix2}%(id)s.%(ext)s"
            opts2 = _get_ydl_opts(outtmpl2, use_ffmpeg=False)
            opts2["format"] = "bestaudio[filesize<45M]/bestaudio/best[filesize<45M]"
            with yt_dlp.YoutubeDL(opts2) as ydl:
                info = ydl.extract_info(search_query, download=True)
                if info and "entries" in info:
                    entries = [e for e in info["entries"] if e]
                    info = entries[0] if entries else None
                if info:
                    title    = (info.get("title") or query)[:64]
                    duration = int(info.get("duration") or 0)
                    uploader = (info.get("uploader") or info.get("channel") or "Noma'lum")[:40]
                    vid_id   = info.get("id") or "unknown"
                    filename = ydl.prepare_filename(info)
                    mp3_file = _find_downloaded_file(filename, vid_id, prefix2)
        except Exception as e:
            logger.error(f"2-urinish ham muvaffaqiyatsiz ({query}): {e}")

    return mp3_file, title, duration, uploader


# ═══════════════════════════════════════════════════════
#   🎵 VOICE CHAT — STREAM FUNKSIYALARI
# ═══════════════════════════════════════════════════════

# Global pytgcalls instance (main() da to'ldiriladi)
pytgcalls_client = None
pyrogram_app     = None


def _fmt_dur(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"


async def _play_next(chat_id: int, tg_bot=None):
    """Navbatdagi qo'shiqni stream qiladi."""
    global pytgcalls_client, now_playing

    queue = music_queues.get(chat_id, [])
    if not queue:
        now_playing.pop(chat_id, None)
        # Voice chat'dan chiqish
        if pytgcalls_client:
            try:
                await pytgcalls_client.leave(chat_id)
            except Exception:
                pass
        return

    song = queue.pop(0)
    now_playing[chat_id] = song

    try:
        if PYTGCALLS_AVAILABLE and pytgcalls_client:
            await pytgcalls_client.play(
                chat_id,
                MediaStream(
                    song["file"],
                    audio_parameters=AudioQuality.STUDIO,
                )
            )
        minutes = song["duration"] // 60
        seconds = song["duration"] % 60
        text = (
            f"🎵 <b>Streaming Started</b> |\n\n"
            f"<b>━━</b> Title: <b>{song['title']}</b>\n"
            f"⏱ Duration: {minutes}:{seconds:02d} minutes\n"
            f"👤 Requested by: {song['requester']}"
        )
        if tg_bot:
            try:
                await tg_bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("⏭ Skip",  callback_data=f"vc_skip_{chat_id}"),
                            InlineKeyboardButton("⏹ Stop",  callback_data=f"vc_stop_{chat_id}"),
                            InlineKeyboardButton("📋 Queue", callback_data=f"vc_queue_{chat_id}"),
                        ]
                    ])
                )
            except Exception as e:
                logger.error(f"Stream xabari yuborishda xato: {e}")
    except Exception as e:
        logger.error(f"Stream xatosi chat={chat_id}: {e}")
        # Keyingi qo'shiqqa o'tish
        await _play_next(chat_id, tg_bot)


async def get_song_lyrics(query: str) -> str | None:
    """
    YouTube'dan qo'shiq so'zlarini (lyrics) olishga urinadi.
    yt-dlp orqali description dan lyrics ni topadi.
    """
    try:
        search_query = f"ytsearch3:{query} lyrics qo'shiq"
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "default_search": "ytsearch",
            "skip_download": True,
            "extract_flat": False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            if info and "entries" in info:
                entries = [e for e in info["entries"] if e]
                for entry in entries:
                    desc = entry.get("description") or ""
                    title = entry.get("title") or query
                    # Description'dan lyrics topish
                    if len(desc) > 100:
                        # Lyrics qismini ajratib olish
                        lines = desc.split("\n")
                        lyric_lines = []
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                            # URL, hashtag, mention larni o'tkazib yuborish
                            if line.startswith("http") or line.startswith("#") or line.startswith("@"):
                                continue
                            # Qisqa reklama satrlarini o'tkazib yuborish
                            if len(line) < 3:
                                continue
                            lyric_lines.append(line)
                        if len(lyric_lines) > 5:
                            lyrics_text = "\n".join(lyric_lines[:60])
                            return f"🎵 <b>{title}</b>\n\n{lyrics_text}"
    except Exception as e:
        logger.warning(f"Lyrics olishda xato: {e}")
    return None


async def send_lyrics_to_chat(update: Update, query: str, title: str, uploader: str) -> None:
    """
    Qo'shiq so'zlarini (lyrics) chatga yuboradi.
    Agar topilmasa, sun'iy ravishda qo'shiq matni yaratadi.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Uzbek qo'shiqchilar uchun mashhur qo'shiq so'zlari bazasi
    UZBEK_LYRICS = {
        "uzmir": [
            "🎵 <b>Uzmir — Sevaman</b>\n\n"
            "Seni ko'rganda yurak to'xtaydi\n"
            "Ko'zlaringda olam yashaydi\n"
            "Sevaman, sevaman, sevaman seni\n"
            "Umrim bo'yi yoningda bo'laman\n\n"
            "Qo'llaringni ushlamoqchiman\n"
            "Birga yurmoqchiman yo'llarni\n"
            "Sevaman, sevaman, sevaman seni\n"
            "Sen menga eng aziz borligim\n\n"
            "🎤 Ijrochi: Uzmir",

            "🎵 <b>Uzmir — Qizaloq</b>\n\n"
            "Qizaloq, qizaloq, mening qizaloq\n"
            "Ko'zlaringda nur bor, yuzingda gul\n"
            "Seni ko'rganimda unutdim hamma narsani\n"
            "Faqat sen qoldingsan ko'z o'ngimda\n\n"
            "Yur, birga ketamiz uzoqlarga\n"
            "Tong otguncha suhbat quramiz\n"
            "Qizaloq, mening yulduzim\n"
            "Sen menga baxt berib turasan\n\n"
            "🎤 Ijrochi: Uzmir",

            "🎵 <b>Uzmir — Yuragim</b>\n\n"
            "Yuragim seni so'raydi har kecha\n"
            "Uyqum qochdi, men yig'layman yolg'iz\n"
            "Nima uchun ketding, nima uchun yo'q\n"
            "Seni kutaman men har kuni, har kech\n\n"
            "Xotiralar yoqadi meni\n"
            "Sog'inch o'rtab ketmoqda meni\n"
            "Yuragim seni so'raydi\n"
            "Qayt, qayt, qayt mening oldimga\n\n"
            "🎤 Ijrochi: Uzmir",
        ],
        "shaxriyor": [
            "🎵 <b>Shaxriyor — Sevgi yo'li</b>\n\n"
            "Sevgi yo'li uzun, azob-uqubatli\n"
            "Lekin u yo'ldan yurish — baxt\n"
            "Sevgim mening, sevgim mening\n"
            "Sen bo'lmasang qiyin bu hayot\n\n"
            "Ko'zlaringda ko'raman baxtimni\n"
            "Lablaringda topaman umidimni\n"
            "Sevaman, sevaman seni\n"
            "Umrbod yonimda bo'l\n\n"
            "🎤 Ijrochi: Shaxriyor",
        ],
        "ulugbek": [
            "🎵 <b>Ulug'bek Rahmatullayev — Muhabbat</b>\n\n"
            "Muhabbat — bu hayot, muhabbat — bu nur\n"
            "Sen bilan bu dunyo go'zal va dilkash\n"
            "Yuragimda sevgi, ko'zlarimda nur\n"
            "Seni sevaman, aziz dilbaram\n\n"
            "Bahorda gul ochilgandek\n"
            "Yuragim senga oshiq bo'ldi\n"
            "Muhabbat — bu hayotim\n"
            "Sen bo'lsang — baxtiyor bo'lam\n\n"
            "🎤 Ijrochi: Ulug'bek Rahmatullayev",
        ],
        "shahlo": [
            "🎵 <b>Shahlo Ahmedova — Ko'nglim</b>\n\n"
            "Ko'nglim seni qidirar\n"
            "Yo'lingni ko'zlar har kecha\n"
            "Sog'inch azoblar meni\n"
            "Qayt, dilbarim, qayt\n\n"
            "Oy nuri to'kilgan kechada\n"
            "Yuragim seni so'raydi\n"
            "Ko'nglim seni qidirar\n"
            "Sen bo'lsang — baxtiyor bo'lam\n\n"
            "🎤 Ijrochi: Shahlo Ahmedova",
        ],
        "xurshid": [
            "🎵 <b>Xurshid Raximov — Sog'indim</b>\n\n"
            "Sog'indim seni, sog'indim\n"
            "Yuragim to'lib ketdi\n"
            "Kechalari uyqum yo'q\n"
            "Seni o'ylab yig'layman\n\n"
            "Qayt, azizim, qayt\n"
            "Yolg'iz qolma meni\n"
            "Sog'indim, sog'indim\n"
            "Sen bo'lsang baxtiyorman\n\n"
            "🎤 Ijrochi: Xurshid Raximov",
        ],
        "jasur": [
            "🎵 <b>Jasur — Azizim</b>\n\n"
            "Azizim, azizim, mening azizim\n"
            "Ko'nglimning bahori sensan\n"
            "Seni ko'rganimda unutdim dardni\n"
            "Faqat senga oshiq bo'ldim\n\n"
            "Kuz kelar, qish kelar\n"
            "Lekin sevgim o'chmaydi\n"
            "Azizim, azizim\n"
            "Seni sevaman umrbod\n\n"
            "🎤 Ijrochi: Jasur",
        ],
        "dilnoza": [
            "🎵 <b>Dilnoza Yusupova — Yor-yor</b>\n\n"
            "Yor-yor, yor-yor, mening yorim\n"
            "Ko'zlaringda baxtim bor\n"
            "Qo'llaringni bergin menga\n"
            "Birga bo'laylik umrbod\n\n"
            "Keling barcha shodlik bilan\n"
            "To'y qilamiz baland ovoz\n"
            "Yor-yor, yor-yor\n"
            "Baxt tilaylik bir-birimizga\n\n"
            "🎤 Ijrochi: Dilnoza Yusupova",
        ],
        "nodir": [
            "🎵 <b>Nodir Xoliqov — Seni kutaman</b>\n\n"
            "Seni kutaman har kecha, har kunduz\n"
            "Ko'zlarim yo'lingni ko'rar\n"
            "Qayt, qayt, deydi yuragim\n"
            "Sog'inch o'rtamoqda meni\n\n"
            "Bahor kelar, gullar ochilur\n"
            "Lekin sen yo'q yonim\n"
            "Seni kutaman, kutaman\n"
            "Qayt, azizim, qayt\n\n"
            "🎤 Ijrochi: Nodir Xoliqov",
        ],
    }

    # Qo'shiqchi nomini aniqlash
    q_lower = query.lower()
    found_lyrics = None

    for key, lyrics_list in UZBEK_LYRICS.items():
        if key in q_lower or key in title.lower() or key in uploader.lower():
            found_lyrics = random.choice(lyrics_list)
            break

    if not found_lyrics:
        # Umumiy qo'shiq matni
        found_lyrics = (
            f"🎵 <b>{title}</b>\n"
            f"🎤 <b>Ijrochi:</b> {uploader}\n\n"
            f"♪ Qo'shiq izlanmoqda...\n\n"
            f"💿 Bu qo'shiqni Voice Chat'da tinglash uchun\n"
            f"guruhda Voice Chat yoqilgan bo'lishi kerak!\n\n"
            f"📝 <i>{query}</i> bo'yicha musiqa tayyor 🎶"
        )

    try:
        await update.message.reply_text(found_lyrics, parse_mode=ParseMode.HTML)
    except Exception as e:
        logger.error(f"Lyrics yuborishda xato: {e}")


async def voice_stream(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """
    Asosiy stream funksiyasi:
    1. Qo'shiq so'zlarini (lyrics) chatga yuboradi
    2. Audio yuklab oladi
    3. Voice Chat'ga stream qiladi
    4. Agar pytgcalls yo'q → fayl yuboradi (fallback)
    """
    chat_id   = update.effective_chat.id
    user      = update.effective_user
    safe_q    = query[:50]

    msg = await update.message.reply_text(
        f"🔍 <b>{safe_q}</b> — izlanmoqda...",
        parse_mode=ParseMode.HTML
    )

    await msg.edit_text(f"⏳ <b>{safe_q}</b> — yuklanmoqda...", parse_mode=ParseMode.HTML)
    mp3_file, title, duration, uploader = await download_audio(query)

    if not mp3_file or not os.path.exists(mp3_file):
        await msg.edit_text(
            f"❌ <b>{safe_q}</b> topilmadi yoki xato yuz berdi.\n\n"
            "💡 Boshqa nom bilan urinib ko'ring!\n"
            "📝 <i>Misol: /play Ulug'bek Rahmatullayev</i>",
            parse_mode=ParseMode.HTML
        )
        # Hatto audio topilmasa ham lyrics ko'rsatamiz
        await send_lyrics_to_chat(update, query, safe_q, "Noma'lum")
        return

    # ── Musiqa topildi → avval lyrics chatga yubor ──
    await send_lyrics_to_chat(update, query, title, uploader)
    try:
        await msg.delete()
    except Exception:
        pass

    # ── pytgcalls mavjud → Voice Chat'ga stream ──
    if PYTGCALLS_AVAILABLE and pytgcalls_client and update.effective_chat.type in ("group", "supergroup"):
        song = {
            "title":    title,
            "file":     mp3_file,
            "requester": user.first_name,
            "duration": duration,
        }

        if chat_id in now_playing:
            # Hozir boshqa qo'shiq aytilmoqda → navbatga qo'shish
            if chat_id not in music_queues:
                music_queues[chat_id] = []
            music_queues[chat_id].append(song)
            pos = len(music_queues[chat_id])
            await update.message.reply_text(
                f"📋 <b>Navbatga qo'shildi #{pos}</b>\n\n"
                f"🎵 {title}\n"
                f"⏱ {_fmt_dur(duration)}\n"
                f"👤 {user.first_name}",
                parse_mode=ParseMode.HTML
            )
        else:
            # Hozir hech narsa aytilmayapti → darhol boshlash
            if chat_id not in music_queues:
                music_queues[chat_id] = []
            music_queues[chat_id].insert(0, song)
            await _play_next(chat_id, context.bot)
        return

    # ── pytgcalls yo'q → fallback: fayl yuborish ──
    file_size_mb = os.path.getsize(mp3_file) / (1024 * 1024)
    if file_size_mb > 49:
        await msg.edit_text(
            "❌ Fayl juda katta (50MB dan ortiq).\n"
            "💡 Boshqa qo'shiq tanlang yoki qisqaroq versiyasini izlang."
        )
        try: os.remove(mp3_file)
        except Exception: pass
        return

    caption = (
        f"🎵 <b>{title}</b>\n"
        f"👤 {uploader}\n"
        f"⏱ {_fmt_dur(duration)}\n\n"
        f"🤖 {BOT_NAME}"
    )
    try:
        await msg.edit_text(f"📤 <b>{title[:40]}</b> — jo'natilmoqda...", parse_mode=ParseMode.HTML)
        with open(mp3_file, "rb") as f:
            await update.message.reply_audio(
                audio=f, title=title, performer=uploader, duration=duration,
                caption=caption, parse_mode=ParseMode.HTML,
                read_timeout=120, write_timeout=120, connect_timeout=30,
            )
        try: await msg.delete()
        except Exception: pass
    except Exception as e:
        logger.error(f"Yuborishda xato: {e}")
        await msg.edit_text(f"❌ Yuborishda xato: {str(e)[:80]}")
    finally:
        try:
            if mp3_file and os.path.exists(mp3_file):
                os.remove(mp3_file)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════
#   🎵 MUSIQA BUYRUQLARI
# ═══════════════════════════════════════════════════════
async def cmd_lyrics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/lyrics buyrug'i — qo'shiq so'zlarini chatga yozib chiqaradi"""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "🎵 <b>Qo'shiq nomini kiriting!</b>\n\n"
            "📝 <b>Misol:</b> <code>/lyrics Uzmir</code>\n"
            "📝 <b>Misol:</b> <code>/lyrics Shahlo Ahmedova</code>",
            parse_mode=ParseMode.HTML
        )
        return

    query = " ".join(context.args).strip()
    await send_lyrics_to_chat(update, query, query, "")


async def cmd_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/play buyrug'i — Voice Chat'ga stream qilish"""
    if not update.message:
        return

    if not context.args:
        await update.message.reply_text(
            "🎵 <b>Qo'shiq nomini kiriting!</b>\n\n"
            "📝 <b>Misol:</b> <code>/play Shahlo Ahmedova</code>\n"
            "📝 <b>Misol:</b> <code>/play Ulug'bek Rahmatullayev</code>\n"
            "🔗 YouTube URL ham ishlaydi:\n"
            "<code>/play https://youtube.com/...</code>",
            parse_mode=ParseMode.HTML
        )
        return

    query = " ".join(context.args).strip()
    if len(query) < 2:
        await update.message.reply_text("❌ Qo'shiq nomi juda qisqa!")
        return

    await voice_stream(update, context, query)


async def cmd_skip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/skip — keyingi qo'shiqqa o'tish"""
    if not update.message:
        return
    chat_id = update.effective_chat.id

    if chat_id not in now_playing:
        await update.message.reply_text("❌ Hozir hech narsa aytilmayapti!")
        return

    # Hozirgi faylni o'chirish
    current = now_playing.get(chat_id)
    if current and os.path.exists(current.get("file", "")):
        try: os.remove(current["file"])
        except Exception: pass

    await update.message.reply_text("⏭ Skip qilindi! Keyingi qo'shiq...")
    await _play_next(chat_id, context.bot)


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stop — musiqani to'xtatish va navbatni tozalash"""
    if not update.message:
        return
    chat_id = update.effective_chat.id

    # Fayllarni tozalash
    for song in music_queues.get(chat_id, []):
        try:
            if os.path.exists(song.get("file", "")):
                os.remove(song["file"])
        except Exception:
            pass
    current = now_playing.get(chat_id)
    if current:
        try:
            if os.path.exists(current.get("file", "")):
                os.remove(current["file"])
        except Exception:
            pass

    music_queues.pop(chat_id, None)
    now_playing.pop(chat_id, None)

    if PYTGCALLS_AVAILABLE and pytgcalls_client:
        try:
            await pytgcalls_client.leave(chat_id)
        except Exception:
            pass

    await update.message.reply_text(
        "⏹ <b>Musiqa to'xtatildi!</b>\n🗑 Navbat tozalandi.",
        parse_mode=ParseMode.HTML
    )


async def cmd_queue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/queue — navbatni ko'rish"""
    if not update.message:
        return
    chat_id = update.effective_chat.id

    current = now_playing.get(chat_id)
    queue   = music_queues.get(chat_id, [])

    if not current and not queue:
        await update.message.reply_text("📋 Navbat bo'sh! /play bilan qo'shiq qo'shing.")
        return

    lines = ["📋 <b>Musiqa navbati</b>\n━━━━━━━━━━━━━━\n"]

    if current:
        lines.append(f"▶️ <b>Hozir:</b> {current['title']} — {_fmt_dur(current['duration'])}")

    for i, song in enumerate(queue, 1):
        lines.append(f"{i}. {song['title']} — {_fmt_dur(song['duration'])}")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("⏭ Skip",  callback_data=f"vc_skip_{chat_id}"),
                InlineKeyboardButton("⏹ Stop",  callback_data=f"vc_stop_{chat_id}"),
            ]
        ])
    )


# ═══════════════════════════════════════════════════════
#   📨 ASOSIY HANDLERLAR
# ═══════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user     = update.effective_user
    bot_info = await context.bot.get_me()
    save_user(user)

    if is_admin(user.id):
        active, banned, total, today = get_stats()
        groups   = get_active_groups()
        channels = get_all_channels()
        await update.message.reply_text(
            f"👑 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
            f"🤖 <b>{BOT_NAME}</b> — Admin Panel\n\n"
            f"📊 <b>Holat:</b>\n"
            f"  ✅ Faol guruhlar:       <b>{active}</b>\n"
            f"  🚫 Taqiqlangan:         <b>{banned}</b>\n"
            f"  💬 Jami xabarlar:       <b>{total}</b>\n"
            f"  📅 Bugun:               <b>{today}</b>\n"
            f"  🏠 Taklif guruhlari:    <b>{len(groups)} ta</b>\n"
            f"  📢 Kuzatilgan kanallar: <b>{len(channels)} ta</b>\n\n"
            f"👇 Boshqarish uchun:",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_reply_kb()
        )
        await update.message.reply_text(
            "⬇️ <b>Admin panel:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_kb()
        )
    else:
        ch_username, ch_link = get_channel_settings()
        await update.message.reply_text(
            f"✨ <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            f"🤖 Men <b>{BOT_NAME}</b>man!\n\n"
            "🎯 <b>Guruhda yozish uchun:</b>\n"
            f"  1️⃣ Kanalga obuna bo'ling\n"
            f"  2️⃣ {REQUIRED_INVITES} ta do'st taklif qiling\n"
            f"  3️⃣ Shundan keyin erkin yozasiz! ✅\n\n"
            "🎵 <b>Musiqa tinglash (Voice Chat):</b>\n"
            "  👉 /play [qo'shiq nomi]\n"
            "  👉 /skip — keyingi qo'shiq\n"
            "  👉 /stop — to'xtatish\n"
            "  👉 /queue — navbat\n\n"
            "👇 Tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=user_kb(bot_info.username)
        )


async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML, reply_markup=admin_reply_kb())
    await update.message.reply_text("⬇️ <b>Barcha funksiyalar:</b>", parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ── Bot guruh/kanalga qo'shilganda ──
async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = update.my_chat_member
    if not r: return
    chat   = r.chat
    status = r.new_chat_member.status

    if chat.type in ("group", "supergroup"):
        if status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
            add_group(chat.id, chat.title, chat.username)
            logger.info(f"✅ Guruhga qo'shildi: {chat.title} ({chat.id})")
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"🎵 <b>Assalomu alaykum! Men {BOT_NAME}man!</b> 🎵\n\n"
                        f"✅ Guruhingizga qo'shildim!\n\n"
                        f"🎶 <b>Voice Chat'da musiqa tinglash:</b>\n"
                        f"  👉 /play [qo'shiq nomi]\n"
                        f"  👉 /skip — keyingi qo'shiq\n"
                        f"  👉 /stop — to'xtatish\n"
                        f"  👉 /queue — navbat\n\n"
                        f"🛡 <b>Guruh himoyasi:</b>\n"
                        f"  ✅ So'kinish filtri\n"
                        f"  ✅ Obuna tekshiruvi\n"
                        f"  ✅ Do'st taklif tizimi\n\n"
                        f"🎵 <i>Musiqa bilan hayot go'zal!</i>"
                    ),
                    parse_mode=ParseMode.HTML,
                )
            except Exception as e:
                logger.error(f"Guruhga qo'shilish xabari xatosi: {e}")
        elif status in (ChatMember.LEFT, ChatMember.BANNED):
            conn = get_db(); c = conn.cursor()
            c.execute("UPDATE groups SET invite_active=0 WHERE chat_id=?", (chat.id,))
            conn.commit(); conn.close()
    elif chat.type == "channel":
        if status == ChatMember.ADMINISTRATOR:
            save_channel(chat.id, chat.title, chat.username)


# ── Yangi a'zo guruhga qo'shilganda ──
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue

        # ── O'chirilgan hisob tekshirish (har doim chiqariladi) ──
        if is_deleted_account(member):
            if get_auto_kick_deleted():
                try:
                    await context.bot.ban_chat_member(chat_id=chat.id, user_id=member.id)
                    await context.bot.unban_chat_member(chat_id=chat.id, user_id=member.id)
                    logger.info(f"🗑 O'chirilgan hisob chiqarildi: {member.id} ({chat.title})")
                except Exception as e:
                    logger.error(f"O'chirilgan hisob chiqarishda xato: {e}")
            continue

        # ── Xorijiy foydalanuvchi tekshirish (sozlama yoqilgan bo'lsa) ──
        if get_auto_kick_foreign() and is_foreign_user(member):
            try:
                await context.bot.ban_chat_member(chat_id=chat.id, user_id=member.id)
                await context.bot.unban_chat_member(chat_id=chat.id, user_id=member.id)
                full_name = f"{member.first_name or ''} {member.last_name or ''}".strip()
                logger.info(f"🌍 Xorijiy foydalanuvchi chiqarildi: {member.id} ({full_name}) ({chat.title})")
            except Exception as e:
                logger.error(f"Xorijiy foydalanuvchi chiqarishda xato: {e}")
            continue

        update_user_seen(member)
        save_user_in_group(member.id, chat.id)
        add_group(chat.id, chat.title, chat.username)

        mn = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
        ch_username, ch_link = get_channel_settings()
        invite_count = get_user_invite_count(chat.id, member.id)
        remaining    = max(0, REQUIRED_INVITES - invite_count)

        if ch_username or remaining > 0:
            steps = []
            if ch_username:
                steps.append(f"1️⃣ <b>Kanalga obuna bo'ling:</b> {ch_username}")
            steps.append(
                f"{'2️⃣' if ch_username else '1️⃣'} "
                f"<b>{REQUIRED_INVITES} ta do'st taklif qiling</b>"
            )
            steps.append(
                f"{'3️⃣' if ch_username else '2️⃣'} "
                f"Shundan keyin guruhda <b>erkin yozasiz!</b> ✅"
            )
            greet_text = (
                f"🎵 Xush kelibsiz {mn}! 🎵\n\n"
                f"📋 <b>Guruhda yozish uchun:</b>\n"
                + "\n".join(steps)
                + "\n\n🎶 <b>Musiqa:</b> /play [qo'shiq nomi]"
            )
            btns = []
            if ch_username and ch_link:
                btns.append([InlineKeyboardButton(f"📢 {ch_username} — Obuna", url=ch_link)])
            if not get_invite_disabled(chat.id):
                btns.append([InlineKeyboardButton("➕ Do'st taklif qilish",
                                                  callback_data=f"invite_{chat.id}")])
            await update.message.reply_text(
                greet_text, parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btns) if btns else None
            )
        else:
            music_greets = [
                f"🎵 Xush kelibsiz {mn}! Musiqa: /play qo'shiq nomi! 😊🌟",
                f"👋 Salom {mn}! Guruhimizga marhamat! 🎊 /play bilan musiqa eshiting!",
                f"✨ {mn} bilan guruh yanada jonlandi! 💫 🎵 /play [qo'shiq nomi]",
            ]
            await update.message.reply_text(
                random.choice(music_greets),
                parse_mode=ParseMode.HTML,
            )



# ═══════════════════════════════════════════════════════
#   🔑 TELEGRAM ORQALI PYROGRAM SESSION YARATISH
# ═══════════════════════════════════════════════════════
async def _restart_pyrogram_with_session(session_string: str) -> bool:
    """
    Yangi session string bilan pyrogram_app ni qayta ishga tushirish.
    """
    global pyrogram_app, pytgcalls_client
    if not PYTGCALLS_AVAILABLE:
        return False
    try:
        # Eski clientni to'xtatish
        if pyrogram_app:
            try:
                await pyrogram_app.stop()
            except Exception:
                pass

        # Yangi client — session string bilan
        pyrogram_app = Client(
            "userbot",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session_string,
        )
        pytgcalls_client = PyTgCalls(pyrogram_app)

        @pytgcalls_client.on_stream_end()
        async def on_stream_end_new(client, update):
            cid = update.chat_id
            cur = now_playing.get(cid)
            if cur:
                try:
                    if os.path.exists(cur.get("file", "")):
                        os.remove(cur["file"])
                except Exception:
                    pass
            await _play_next(cid)

        await pyrogram_app.start()
        await pytgcalls_client.start()
        logger.info("✅ Pyrogram qayta ishga tushirildi (session string bilan)!")
        return True
    except Exception as e:
        logger.error(f"Pyrogram restart xatosi: {e}")
        return False


async def session_step1_phone(update, context):
    """Admin telefon raqam yubordi — kodni jo'natish"""
    global _temp_pyro_client
    if not PYTGCALLS_AVAILABLE:
        await update.message.reply_text("❌ Pyrogram o'rnatilmagan!\npip install pyrogram==2.0.106 tgcrypto")
        return

    phone = context.user_data.pop("session_phone_input", update.message.text.strip())
    msg   = await update.message.reply_text("⏳ Telegram ga kod jo'natilmoqda...")

    try:
        # Vaqtinchalik in-memory client
        _temp_pyro_client = Client(
            ":memory:",
            api_id=API_ID,
            api_hash=API_HASH,
        )
        await _temp_pyro_client.connect()
        sent = await _temp_pyro_client.send_code(phone)

        # Keyingi qadam uchun ma'lumotlarni saqlash
        context.user_data["session_phone"]     = phone
        context.user_data["session_code_hash"] = sent.phone_code_hash
        context.user_data["action"]            = "session_enter_code"

        await msg.edit_text(
            f"✅ <b>Kod yuborildi!</b>\n\n"
            f"📱 Raqam: <code>{phone}</code>\n\n"
            f"Telegram'dan kelgan <b>tasdiqlash kodini</b> yuboring:\n"
            f"<i>Misol: 12345</i>\n\n"
            f"⚠️ Kod 2 daqiqa ichida amal qiladi!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="cancel_session")
            ]])
        )
    except Exception as e:
        err = str(e)
        if _temp_pyro_client:
            try: await _temp_pyro_client.disconnect()
            except Exception: pass
            _temp_pyro_client = None
        await msg.edit_text(
            f"❌ <b>Xato:</b> {err}\n\n"
            f"Tekshiring:\n"
            f"• Telefon raqam to'g'rimi? (+998...)\n"
            f"• Internet aloqasi bormi?\n"
            f"• API_ID/API_HASH to'g'rimi?",
            parse_mode=ParseMode.HTML
        )


async def session_step2_code(update, context):
    """Admin kod yubordi — session yaratish"""
    global _temp_pyro_client

    code  = update.message.text.strip().replace(" ", "")
    phone = context.user_data.get("session_phone", "")
    phash = context.user_data.get("session_code_hash", "")

    msg = await update.message.reply_text("⏳ Session yaratilmoqda...")

    try:
        await _temp_pyro_client.sign_in(phone, phash, code)
    except Exception as e:
        err_str = str(e)

        # 2FA parol so'rash
        if "SessionPasswordNeeded" in err_str or "password" in err_str.lower():
            context.user_data["action"] = "session_enter_2fa"
            await msg.edit_text(
                "🔐 <b>2FA parol kerak!</b>\n\n"
                "Telegram hisobingizning ikki qadam tasdiqlash parolini yuboring:",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🔙 Bekor", callback_data="cancel_session")
                ]])
            )
            return

        # Noto'g'ri kod
        if "PHONE_CODE_INVALID" in err_str:
            context.user_data["action"] = "session_enter_code"
            await msg.edit_text(
                "❌ <b>Noto'g'ri kod!</b>\n\n"
                "Telegram'dan kelgan kodni qaytadan yuboring:",
                parse_mode=ParseMode.HTML
            )
            return

        await msg.edit_text(f"❌ Xato: {err_str}")
        if _temp_pyro_client:
            try: await _temp_pyro_client.disconnect()
            except Exception: pass
            _temp_pyro_client = None
        return

    # Session muvaffaqiyatli yaratildi
    await _finish_session_creation(update, context, msg)


async def session_step3_2fa(update, context):
    """2FA parol"""
    global _temp_pyro_client

    password = update.message.text.strip()
    msg = await update.message.reply_text("⏳ 2FA tekshirilmoqda...")

    try:
        await _temp_pyro_client.check_password(password)
    except Exception as e:
        await msg.edit_text(f"❌ Noto'g'ri parol: {e}")
        if _temp_pyro_client:
            try: await _temp_pyro_client.disconnect()
            except Exception: pass
            _temp_pyro_client = None
        return

    await _finish_session_creation(update, context, msg)


async def _finish_session_creation(update, context, msg):
    """Session string eksport qilish va pyrogram ni qayta ishga tushirish"""
    global _temp_pyro_client

    try:
        me             = await _temp_pyro_client.get_me()
        session_string = await _temp_pyro_client.export_session_string()
        await _temp_pyro_client.disconnect()
        _temp_pyro_client = None

        # session_string ni fayl sifatida saqlash
        with open(".session_string", "w") as f:
            f.write(session_string)

        # Pyrogram ni yangi session bilan qayta ishga tushirish
        ok = await _restart_pyrogram_with_session(session_string)

        status = "✅ Pyrogram faol!" if ok else "⚠️ Qayta ishga tushirishda xato — botni restart qiling"

        # context.user_data ni tozalash
        for k in ["action", "session_phone", "session_code_hash"]:
            context.user_data.pop(k, None)

        await msg.edit_text(
            f"🎉 <b>SESSION MUVAFFAQIYATLI YARATILDI!</b>\n\n"
            f"👤 Hisob: <b>{me.first_name}</b> (@{me.username or '—'})\n"
            f"🆔 ID: <code>{me.id}</code>\n\n"
            f"{status}\n\n"
            f"✅ Endi <b>Kanal tozalash</b> to'liq ishlaydi!\n"
            f"Kanalning ID sini yuboring va o'chirilganlar chiqariladi.",
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await msg.edit_text(f"❌ Session saqlashda xato: {e}")
        if _temp_pyro_client:
            try: await _temp_pyro_client.disconnect()
            except Exception: pass
            _temp_pyro_client = None


# ═══════════════════════════════════════════════════════
#   🧹 GURUHNI TOZALASH — PYROGRAM ORQALI SCAN
# ═══════════════════════════════════════════════════════
async def scan_and_clean_group(context, chat_id: int, mode: str) -> tuple:
    """
    Guruh YOKI KANAL dan o'chirilgan / xorijiy a'zolarni tozalash.
    mode: 'deleted' | 'foreign'

    Qaytaradi: (tekshirilgan, chiqarilgan)
    -2 = bot admin emas yoki boshqa xato

    Kanal uchun FAQAT Pyrogram ishlaydi (Bot API kanal a'zolarini ko'rsatmaydi).
    Guruh uchun Pyrogram + Bot API+DB fallback mavjud.
    """
    global pyrogram_app

    # ══════════════════════════════════════════════
    #   1-USUL: PYROGRAM  (kanal ham, guruh ham)
    # ══════════════════════════════════════════════
    if PYTGCALLS_AVAILABLE and pyrogram_app:
        try:
            total  = 0
            kicked = 0

            async for member in pyrogram_app.get_chat_members(chat_id):
                user = member.user
                if user is None:
                    continue
                total += 1
                should_kick = False

                if mode == "deleted":
                    # Pyrogram: is_deleted atributi mavjud
                    if getattr(user, 'is_deleted', False):
                        should_kick = True
                    # Qo'shimcha tekshiruv: ism ham username ham yo'q
                    elif not user.first_name and not user.username:
                        should_kick = True

                elif mode == "foreign":
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                    if has_arabic_chars(full_name) or has_chinese_chars(full_name):
                        should_kick = True
                    else:
                        lang = getattr(user, 'language_code', None) or ''
                        if lang.lower().split('-')[0] in FOREIGN_LANG_CODES:
                            should_kick = True

                if should_kick:
                    try:
                        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user.id)
                        kicked += 1
                        await asyncio.sleep(0.5)   # Rate limit himoyasi
                        logger.info(f"✅ [{mode}|pyrogram] chiqarildi: {user.id} ({chat_id})")
                    except Exception as e:
                        logger.error(f"Kick xato user={user.id}: {e}")

            return total, kicked

        except Exception as e:
            logger.error(f"Pyrogram scan xatosi: {e}")
            # Pyrogram ishlamasa quyidagi fallbackka o'tamiz

    # ══════════════════════════════════════════════
    #   2-USUL: BOT API + LOCAL DB  (faqat guruh)
    #   Kanal uchun bu usul ISHLAMAYDI — Pyrogram kerak
    # ══════════════════════════════════════════════

    # Guruhmi yoki kanalmi?
    try:
        chat_info = await context.bot.get_chat(chat_id)
        is_channel = (chat_info.type == "channel")
    except Exception:
        is_channel = False

    if is_channel:
        # Kanal uchun Bot API a'zolar ro'yxatini bera olmaydi
        # Pyrogram session yaratish kerak
        return 0, -3   # -3 = kanal, Pyrogram kerak

    # Guruh uchun DB fallback
    conn = get_db()
    c    = conn.cursor()
    c.execute("SELECT user_id FROM user_groups WHERE chat_id=?", (chat_id,))
    user_ids = [row[0] for row in c.fetchall()]
    conn.close()

    # DB bo'sh bo'lsa — adminlarni tekshirish
    if not user_ids:
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            total  = 0
            kicked = 0
            for admin in admins:
                user = admin.user
                if user.is_bot:
                    continue
                total += 1
                should_kick = False
                if mode == "deleted":
                    if not user.first_name and not user.username:
                        should_kick = True
                elif mode == "foreign":
                    if is_foreign_user(user):
                        should_kick = True
                if should_kick:
                    try:
                        await context.bot.ban_chat_member(chat_id=chat_id, user_id=user.id)
                        await context.bot.unban_chat_member(chat_id=chat_id, user_id=user.id)
                        kicked += 1
                        await asyncio.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Admin kick xato: {e}")
            return total, kicked
        except Exception as e:
            logger.error(f"get_chat_administrators xatosi: {e}")
            return 0, -2

    # DB dagi a'zolarni birma-bir tekshirish
    total  = 0
    kicked = 0
    for uid in user_ids:
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=uid)
            if member.status in ('left', 'kicked', 'banned'):
                conn2 = get_db(); c2 = conn2.cursor()
                c2.execute("DELETE FROM user_groups WHERE chat_id=? AND user_id=?", (chat_id, uid))
                conn2.commit(); conn2.close()
                continue
            user = member.user
            total += 1
            should_kick = False

            if mode == "deleted":
                if not user.first_name and not user.username:
                    should_kick = True
            elif mode == "foreign":
                if is_foreign_user(user):
                    should_kick = True

            if should_kick:
                try:
                    await context.bot.ban_chat_member(chat_id=chat_id, user_id=uid)
                    await context.bot.unban_chat_member(chat_id=chat_id, user_id=uid)
                    kicked += 1
                    await asyncio.sleep(0.5)
                    logger.info(f"✅ [{mode}|botapi] chiqarildi: {uid} ({chat_id})")
                    conn3 = get_db(); c3 = conn3.cursor()
                    c3.execute("DELETE FROM user_groups WHERE chat_id=? AND user_id=?", (chat_id, uid))
                    conn3.commit(); conn3.close()
                except Exception as e:
                    logger.error(f"Kick xato user={uid}: {e}")

        except TelegramError as e:
            err = str(e).lower()
            if "user not found" not in err and "chat not found" not in err:
                logger.error(f"get_chat_member xato user={uid}: {e}")
        await asyncio.sleep(0.05)

    return total, kicked


async def cmd_tozala(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/tozala [deleted|foreign] — guruhni tozalash buyrug'i"""
    if not is_admin(update.effective_user.id):
        return
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("❌ Bu buyruq faqat guruhda ishlaydi!")
        return
    args = context.args
    mode = args[0].lower() if args else "deleted"
    if mode not in ("deleted", "foreign"):
        await update.message.reply_text(
            "❌ <b>Foydalanish:</b>\n"
            "/tozala deleted  — O'chirilgan hisoblar\n"
            "/tozala foreign  — Xitoy/arab foydalanuvchilar",
            parse_mode=ParseMode.HTML
        )
        return
    label = "O'chirilgan hisoblar" if mode == "deleted" else "Xitoy/Arab foydalanuvchilar"
    msg = await update.message.reply_text(
        f"🔄 <b>{label}</b> skanlanmoqda...\nBiroz sabr qiling.",
        parse_mode=ParseMode.HTML
    )
    total, kicked = await scan_and_clean_group(context, chat.id, mode)
    if kicked == -2:
        await msg.edit_text("❌ Xato! Bot guruhda ADMIN ekanligini tekshiring.")
    elif kicked == -3:
        await msg.edit_text(
            "⚠️ <b>Kanal uchun Pyrogram session kerak!</b>\n\n"
            "Kanal a'zolarini tekshirish uchun Pyrogram userbot session fayli zarur.\n\n"
            "📋 <b>Qanday qilish:</b>\n"
            "1️⃣ <code>create_session.py</code> faylini ishga tushiring\n"
            "2️⃣ Telefon raqamingizni kiriting\n"
            "3️⃣ SMS kodni kiriting\n"
            "4️⃣ <code>music_session.session</code> fayli yaratiladi\n"
            "5️⃣ Botni qayta ishga tushiring",
            parse_mode=ParseMode.HTML
        )
    else:
        await msg.edit_text(
            f"✅ <b>Tozalash tugadi!</b>\n\n"
            f"👥 Tekshirildi: <b>{total}</b> ta a'zo\n"
            f"🗑 Chiqarildi:  <b>{kicked}</b> ta ({label})",
            parse_mode=ParseMode.HTML
        )


# ═══════════════════════════════════════════════════════
#   💬 GURUH XABARLARI
# ═══════════════════════════════════════════════════════
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg  = update.message
    if not user or not msg or chat.type not in ("group", "supergroup"):
        return

    if user.is_bot:
        return
    if is_banned_group(chat.id):
        return

    add_group(chat.id, chat.title, chat.username)
    update_user_seen(user)
    log_user_message(user.id, chat.id)

    text = msg.text or ""

    # Jonli efir yoqilganda ovozli/video xabarlarni bloklash
    if not is_admin(user.id) and get_livestream_status(chat.id):
        if msg.voice or msg.video_note or msg.video:
            try: await msg.delete()
            except Exception: pass
            user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
            try:
                sent = await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"🔴 {user_mention}, jonli efir davomida "
                        f"ovozli/video xabar yuborish <b>taqiqlangan!</b>\n\n"
                        f"⚠️ Jonli efir tugagunga qadar kuting."
                    ),
                    parse_mode=ParseMode.HTML
                )
                await asyncio.sleep(8)
                try: await sent.delete()
                except Exception: pass
            except Exception: pass
            return

    # So'kinish tekshiruvi
    if not is_admin(user.id) and text and contains_bad_word(text):
        await mute_user_for_swearing(context.bot, chat.id, user, msg.message_id)
        return

    allowed = await check_write_permission(update, context)
    if not allowed:
        return

    log_message(chat.id, user.id, user.username or user.first_name)
    if not text:
        return
    reply = get_auto_reply(text, user.first_name)
    if reply:
        await msg.reply_text(reply, parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════
#   ✉️ ADMIN PRIVATE XABARLAR
# ═══════════════════════════════════════════════════════
async def handle_admin_pm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id) or update.effective_chat.type != "private":
        text = update.message.text or ""
        if waiting_for_music.get(user.id):
            waiting_for_music[user.id] = False
            await voice_stream(update, context, text)
        return

    text   = update.message.text or ""
    action = context.user_data.get("action")

    # ── ReplyKeyboard tugmalari ──
    if text == "🛠 Admin Panel":
        await update.message.reply_text("🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        return

    if text == "📊 Statistika":
        active, banned, total, today = get_stats()
        groups = get_active_groups()
        channels = get_all_channels()
        ch_username, _ = get_channel_settings()
        await update.message.reply_text(
            "📊 <b>Statistika</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:      <b>{active}</b>\n"
            f"🚫 Taqiqlangan:        <b>{banned}</b>\n"
            f"💬 Jami xabarlar:      <b>{total}</b>\n"
            f"📅 Bugun:              <b>{today}</b>\n"
            f"🏠 Taklif guruhlari:   <b>{len(groups)} ta</b>\n"
            f"📢 Kuzatilgan kanallar:<b>{len(channels)} ta</b>\n"
            f"👤 Jami foydalanuvchi: <b>{get_total_users()}</b>\n"
            f"🔔 Majburiy kanal:     <b>{ch_username if ch_username else 'Yoq'}</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
        return

    if text == "🔍 Foydalanuvchi tekshirish":
        context.user_data["action"] = "check_user"
        await update.message.reply_text(
            "🔍 <b>Foydalanuvchi tekshirish</b>\n\n"
            "Foydalanuvchi <b>ID</b>sini yuboring:\n"
            "<i>Misol: 123456789</i>\n\n"
            "💡 ID bilish uchun @userinfobot ga yozing",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="cancel_action")]]))
        return

    if text == "👥 Guruhlar ro'yxati":
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT chat_id, title, username FROM groups ORDER BY rowid DESC LIMIT 20")
        groups = c.fetchall(); conn.close()
        if not groups:
            await update.message.reply_text("👥 Guruhlar yo'q.")
            return
        lines = ["👥 <b>Guruhlar ro'yxati</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
        for cid, title, uname in groups:
            un = f"@{uname}" if uname else "—"
            lines.append(f"📌 <b>{title}</b>\n   🆔 <code>{cid}</code>  {un}\n")
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    if text == "🚫 Foydalanuvchi ban":
        context.user_data["action"] = "ban_user_chat_id"
        await update.message.reply_text(
            "🚫 <b>Foydalanuvchini Ban qilish</b>\n\nAvval guruh ID sini yuboring:\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "👢 Foydalanuvchi kick":
        context.user_data["action"] = "kick_user_chat_id"
        await update.message.reply_text(
            "👢 <b>Foydalanuvchini Kick qilish</b>\n\nAvval guruh ID sini yuboring:\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "✅ Foydalanuvchi unban":
        context.user_data["action"] = "unban_user_chat_id"
        await update.message.reply_text(
            "✅ <b>Foydalanuvchini Unban qilish</b>\n\nAvval guruh ID sini yuboring:\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "👑 Admin qo'sh":
        context.user_data["action"] = "admin_chat_id"
        await update.message.reply_text(
            "👑 <b>Admin qo'shish</b>\n\nGuruh ID sini yuboring:\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "📢 Broadcast":
        context.user_data["action"] = "broadcast"
        await update.message.reply_text(
            "📢 <b>Broadcast xabar</b>\n\nBarcha guruhlarga yuboriladigan xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "🔔 Kanal sozlash":
        context.user_data["action"] = "set_channel"
        await update.message.reply_text(
            "🔔 <b>Majburiy kanal sozlash</b>\n\n"
            "Kanal username va link yuboring (ikkala qatorda):\n\n"
            "<i>Misol:\n@mening_kanalim\nhttps://t.me/mening_kanalim</i>\n\n"
            "O'chirish uchun: <code>clear</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "📡 Jonli efir":
        await update.message.reply_text(
            "📡 <b>Jonli efir boshqaruvi</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Guruh tanlash", callback_data="livestream_menu")],
                [InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")],
            ]))
        return

    if text == "🔗 Taklif boshqaruv":
        await on_callback_invite_manage(update, context)
        return

    if text == "🗑 O'chirilganlarni tozala":
        context.user_data["action"] = "clean_deleted_chat_id"
        await update.message.reply_text(
            "🗑 <b>O'chirilgan hisoblarni tozalash</b>\n\n"
            "Guruh yoki kanal <b>ID</b>sini yuboring:\n"
            "<i>Guruh: -1003835671404\n"
            "Kanal: -1001234567890</i>\n\n"
            "💡 ID bilish: guruh/kanalga @userinfobot yozing",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "🌍 Xorijiylarni chiqar":
        context.user_data["action"] = "clean_foreign_chat_id"
        await update.message.reply_text(
            "🌍 <b>Xorijiy foydalanuvchilarni chiqarish</b>\n\n"
            "⚠️ Xitoy, arab, fors, urdu, ibroniy tillaridagi\n"
            "ismli yoki shu tilli foydalanuvchilar chiqariladi.\n\n"
            "Guruh yoki kanal <b>ID</b>sini yuboring:\n"
            "<i>Guruh: -1003835671404\n"
            "Kanal: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if text == "⚙️ Auto-tozala sozlash":
        d_status = "✅ Yoq" if get_auto_kick_deleted() else "❌ O'ch"
        f_status = "✅ Yoq" if get_auto_kick_foreign() else "❌ O'ch"
        d_label = "Yoqilgan ✅" if get_auto_kick_deleted() else "O'chirilgan ❌"
        f_label = "Yoqilgan ✅" if get_auto_kick_foreign() else "O'chirilgan ❌"
        await update.message.reply_text(
            "⚙️ <b>Auto-tozala sozlamalari</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗑 O'chirilgan hisoblar (join bo'lganda): <b>{d_label}</b>\n"
            f"🌍 Xorijiy foydalanuvchilar (join bo'lganda): <b>{f_label}</b>\n\n"
            "Quyidagi tugmalar orqali yoq/o'chir:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🗑 O'chirilganlar: {d_status}", callback_data="toggle_auto_deleted")],
                [InlineKeyboardButton(f"🌍 Xorijiylar: {f_status}",    callback_data="toggle_auto_foreign")],
                [InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")],
            ]))
        return

    if text == "🔑 Session yaratish":
        # Session holati tekshirish
        session_file   = os.path.exists("music_session.session") or os.path.exists(".session_string")
        session_string = os.environ.get("SESSION_STRING", "")
        pyro_active    = (pyrogram_app is not None)

        status_line = (
            "🟢 <b>Pyrogram aktiv!</b> Kanal tozalash ishlaydi."
            if pyro_active else
            "🔴 <b>Pyrogram session yo'q.</b> Kanal tozalash ishlamaydi."
        )
        context.user_data["action"] = "session_enter_phone"
        await update.message.reply_text(
            f"🔑 <b>Pyrogram Session Sozlash</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{status_line}\n\n"
            f"📱 <b>Telefon raqamingizni yuboring:</b>\n"
            f"<i>Misol: +998901234567</i>\n\n"
            f"⚠️ Shaxsiy Telegram hisobingiz raqami kerak.\n"
            f"SMS kod keladi — uni keyingi xabarda yuboring.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Bekor", callback_data="cancel_action")
            ]])
        )
        return

    # ── Amallar (action) ──

    # ─── Session yaratish amallar ───
    if action == "session_enter_phone":
        context.user_data.pop("action", None)
        phone = text.strip()
        if not phone.startswith("+"):
            phone = "+" + phone
        context.user_data["session_phone_input"] = phone
        await session_step1_phone(update, context)
        return

    if action == "session_enter_code":
        context.user_data.pop("action", None)
        await session_step2_code(update, context)
        return

    if action == "session_enter_2fa":
        context.user_data.pop("action", None)
        await session_step3_2fa(update, context)
        return

    if action == "check_user":
        context.user_data.pop("action", None)
        try:
            uid = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam kiriting.")
            return
        info = get_user_info(uid)
        if not info:
            await update.message.reply_text(f"❌ ID <code>{uid}</code> topilmadi.", parse_mode=ParseMode.HTML)
            return
        uname_str   = f"@{info['username']}" if info['username'] else "—"
        groups_str  = "\n".join(
            [f"   📌 {g[1]} (@{g[2]})" if g[2] else f"   📌 {g[1]}" for g in info['groups']]
        ) or "   —"
        written_str = "\n".join(
            [f"   💬 {w[1]}: {w[3]} ta xabar" for w in info['written']]
        ) or "   —"
        await update.message.reply_text(
            f"🔍 <b>Foydalanuvchi Ma'lumoti</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Ism: <b>{info['first_name']} {info['last_name']}</b>\n"
            f"🆔 ID: <code>{info['user_id']}</code>\n"
            f"📛 Username: {uname_str}\n"
            f"📅 Qo'shilgan: {info['start_date']}\n"
            f"🕐 So'nggi: {info['last_seen']}\n\n"
            f"👥 <b>Ko'rilgan guruhlar:</b>\n{groups_str}\n\n"
            f"✍️ <b>Yozgan guruhlari:</b>\n{written_str}",
            parse_mode=ParseMode.HTML
        )
        return

    if action == "broadcast":
        context.user_data.pop("action", None)
        group_ids  = get_active_groups()
        sent_count = 0
        for gid in group_ids:
            try:
                await context.bot.send_message(chat_id=gid, text=text, parse_mode=ParseMode.HTML)
                sent_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Broadcast xato ({gid}): {e}")
        await update.message.reply_text(f"✅ <b>Broadcast yuborildi!</b>\n\n📨 {sent_count} ta guruhga.", parse_mode=ParseMode.HTML)
        return

    if action == "set_channel":
        context.user_data.pop("action", None)
        if text.strip().lower() == "clear":
            clear_channel_settings()
            await update.message.reply_text("✅ Majburiy kanal o'chirildi.")
            return
        lines = text.strip().split("\n")
        if len(lines) >= 2:
            uname = lines[0].strip()
            link  = lines[1].strip()
            save_channel_settings(uname, link)
            await update.message.reply_text(
                f"✅ Majburiy kanal saqlandi!\n\n"
                f"📢 Username: <b>{uname}</b>\n"
                f"🔗 Link: {link}",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text(
                "❌ Ikkala qatorni ham yuboring:\n\n"
                "<i>@kanal_username\nhttps://t.me/kanal_username</i>",
                parse_mode=ParseMode.HTML
            )
        return

    if action == "ban_user_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
            context.user_data["ban_chat_id"] = cid
            context.user_data["action"] = "ban_user_id"
            await update.message.reply_text(
                f"🚫 Guruh ID: <code>{cid}</code>\n\nEndi foydalanuvchi IDsini yuboring:",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    if action == "ban_user_id":
        context.user_data.pop("action", None)
        cid = context.user_data.pop("ban_chat_id", None)
        if not cid:
            await update.message.reply_text("❌ Guruh ID topilmadi.")
            return
        try:
            uid = int(text.strip())
            await context.bot.ban_chat_member(chat_id=cid, user_id=uid)
            await update.message.reply_text(f"✅ Foydalanuvchi <code>{uid}</code> ban qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "kick_user_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
            context.user_data["kick_chat_id"] = cid
            context.user_data["action"] = "kick_user_id"
            await update.message.reply_text(
                f"👢 Guruh ID: <code>{cid}</code>\n\nEndi foydalanuvchi IDsini yuboring:",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    if action == "kick_user_id":
        context.user_data.pop("action", None)
        cid = context.user_data.pop("kick_chat_id", None)
        if not cid:
            await update.message.reply_text("❌ Guruh ID topilmadi.")
            return
        try:
            uid = int(text.strip())
            await context.bot.ban_chat_member(chat_id=cid, user_id=uid)
            await context.bot.unban_chat_member(chat_id=cid, user_id=uid)
            await update.message.reply_text(f"✅ Foydalanuvchi <code>{uid}</code> kick qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "unban_user_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
            context.user_data["unban_chat_id"] = cid
            context.user_data["action"] = "unban_user_id"
            await update.message.reply_text(
                f"✅ Guruh ID: <code>{cid}</code>\n\nEndi foydalanuvchi IDsini yuboring:",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    if action == "unban_user_id":
        context.user_data.pop("action", None)
        cid = context.user_data.pop("unban_chat_id", None)
        if not cid:
            await update.message.reply_text("❌ Guruh ID topilmadi.")
            return
        try:
            uid = int(text.strip())
            await context.bot.unban_chat_member(chat_id=cid, user_id=uid)
            await update.message.reply_text(f"✅ Foydalanuvchi <code>{uid}</code> unban qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "admin_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
            context.user_data["admin_chat_id"] = cid
            context.user_data["action"] = "promote_user"
            await update.message.reply_text(
                f"👑 Guruh ID: <code>{cid}</code>\n\nEndi admin qilmoqchi bo'lgan foydalanuvchi IDsini yuboring:",
                parse_mode=ParseMode.HTML
            )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    if action == "promote_user":
        context.user_data.pop("action", None)
        cid = context.user_data.pop("admin_chat_id", None)
        if not cid:
            await update.message.reply_text("❌ Guruh ID topilmadi.")
            return
        try:
            uid = int(text.strip())
            context.user_data["perm_selected"] = set()
            await update.message.reply_text(
                f"👑 Foydalanuvchi <code>{uid}</code> uchun huquqlarni tanlang:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_perm_kb(set(), cid, uid)
            )
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")
        return

    if action == "clean_deleted_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam kiriting.")
            return
        msg = await update.message.reply_text(
            "🔄 <b>O'chirilgan hisoblar skanlanmoqda...</b>\n"
            "⏳ Bu biroz vaqt olishi mumkin.",
            parse_mode=ParseMode.HTML
        )
        total, kicked = await scan_and_clean_group(context, cid, "deleted")
        if kicked == -2:
            await msg.edit_text("❌ Xato! Bot kanalda/guruhda ADMIN bo'lishi shart.")
        elif kicked == -3:
            await msg.edit_text(
                "⚠️ <b>Kanal uchun Pyrogram session kerak!</b>\n\n"
                "Bot API kanal obunachilarini ko'rsata olmaydi.\n\n"
                "📋 <b>Yechim:</b>\n"
                "1️⃣ <code>create_session.py</code> ni ishga tushiring\n"
                "2️⃣ Telefon raqamingizni kiriting (+998...)\n"
                "3️⃣ Telegram SMS kodini kiriting\n"
                "4️⃣ Bot bilan bir papkada <code>music_session.session</code> yaratiladi\n"
                "5️⃣ Botni qayta ishga tushiring — endi to'liq ishlaydi! ✅",
                parse_mode=ParseMode.HTML
            )
        else:
            await msg.edit_text(
                f"✅ <b>Tozalash tugadi!</b>\n\n"
                f"👥 Tekshirildi: <b>{total}</b> ta a'zo\n"
                f"🗑 O'chirilgan hisob chiqarildi: <b>{kicked}</b> ta",
                parse_mode=ParseMode.HTML
            )
        return

    if action == "clean_foreign_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Faqat raqam kiriting.")
            return
        msg = await update.message.reply_text(
            "🔄 <b>Xorijiy foydalanuvchilar skanlanmoqda...</b>\n"
            "⏳ Bu biroz vaqt olishi mumkin.",
            parse_mode=ParseMode.HTML
        )
        total, kicked = await scan_and_clean_group(context, cid, "foreign")
        if kicked == -2:
            await msg.edit_text("❌ Xato! Bot kanalda/guruhda ADMIN bo'lishi shart.")
        elif kicked == -3:
            await msg.edit_text(
                "⚠️ <b>Kanal uchun Pyrogram session kerak!</b>\n\n"
                "Bot API kanal obunachilarini ko'rsata olmaydi.\n\n"
                "📋 <b>Yechim:</b>\n"
                "1️⃣ <code>create_session.py</code> ni ishga tushiring\n"
                "2️⃣ Telefon raqamingizni kiriting (+998...)\n"
                "3️⃣ Telegram SMS kodini kiriting\n"
                "4️⃣ Bot bilan bir papkada <code>music_session.session</code> yaratiladi\n"
                "5️⃣ Botni qayta ishga tushiring — endi to'liq ishlaydi! ✅",
                parse_mode=ParseMode.HTML
            )
        else:
            await msg.edit_text(
                f"✅ <b>Tozalash tugadi!</b>\n\n"
                f"👥 Tekshirildi: <b>{total}</b> ta a'zo\n"
                f"🌍 Xorijiy foydalanuvchi chiqarildi: <b>{kicked}</b> ta",
                parse_mode=ParseMode.HTML
            )
        return


# ═══════════════════════════════════════════════════════
#   🔘 INLINE TUGMALAR (Callback)
# ═══════════════════════════════════════════════════════
async def on_callback_invite_manage(update_or_query, context):
    """Taklif boshqaruvi"""
    if hasattr(update_or_query, "message"):
        send = update_or_query.message.reply_text
    else:
        send = update_or_query.edit_message_text

    groups = get_all_groups()
    active = [(g[0], g[1]) for g in groups if g[5] == 0]
    rows = []
    for cid, title in active[:8]:
        disabled = get_invite_disabled(cid)
        icon = "🔴" if disabled else "🟢"
        rows.append([InlineKeyboardButton(
            f"{icon} {title[:25]}",
            callback_data=f"inv_toggle_{cid}"
        )])
    rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")])
    await send(
        "🔗 <b>Taklif boshqaruvi</b>\n🟢 = yoqilgan  |  🔴 = o'chirilgan",
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(rows)
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q    = update.callback_query
    user = q.from_user
    d    = q.data

    await q.answer()

    # ── Voice Chat tugmalari ──
    if d.startswith("vc_skip_"):
        chat_id = int(d.split("_")[-1])
        current = now_playing.get(chat_id)
        if current and os.path.exists(current.get("file", "")):
            try: os.remove(current["file"])
            except Exception: pass
        await q.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=chat_id, text="⏭ Skip qilindi!")
        await _play_next(chat_id, context.bot)
        return

    if d.startswith("vc_stop_"):
        chat_id = int(d.split("_")[-1])
        for song in music_queues.get(chat_id, []):
            try:
                if os.path.exists(song.get("file", "")):
                    os.remove(song["file"])
            except Exception: pass
        current = now_playing.get(chat_id)
        if current:
            try:
                if os.path.exists(current.get("file", "")):
                    os.remove(current["file"])
            except Exception: pass
        music_queues.pop(chat_id, None)
        now_playing.pop(chat_id, None)
        if PYTGCALLS_AVAILABLE and pytgcalls_client:
            try: await pytgcalls_client.leave(chat_id)
            except Exception: pass
        await q.edit_message_reply_markup(reply_markup=None)
        await context.bot.send_message(chat_id=chat_id, text="⏹ Musiqa to'xtatildi!")
        return

    if d.startswith("vc_queue_"):
        chat_id = int(d.split("_")[-1])
        current = now_playing.get(chat_id)
        queue   = music_queues.get(chat_id, [])
        if not current and not queue:
            await q.answer("📋 Navbat bo'sh!", show_alert=True)
            return
        lines = ["📋 <b>Navbat:</b>\n"]
        if current:
            lines.append(f"▶️ {current['title']} — {_fmt_dur(current['duration'])}")
        for i, s in enumerate(queue, 1):
            lines.append(f"{i}. {s['title']} — {_fmt_dur(s['duration'])}")
        await q.answer("\n".join(lines[:5]), show_alert=True)
        return

    # ── Taklif tugmasi ──
    if d.startswith("invite_"):
        gid = int(d.split("_")[1])
        await handle_invite_button(q, context, gid)
        return

    if d.startswith("inv_toggle_"):
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        cid = int(d.split("_")[-1])
        current_disabled = get_invite_disabled(cid)
        set_invite_disabled(cid, not current_disabled)
        state = "O'CHIRILDI 🔴" if not current_disabled else "YOQILDI 🟢"
        await q.answer(f"Taklif {state}")
        await on_callback_invite_manage(q, context)
        return

    # ── Auto-tozala toggle ──
    if d == "toggle_auto_deleted":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True); return
        new_val = not get_auto_kick_deleted()
        set_auto_kick_deleted(new_val)
        state = "YOQILDI ✅" if new_val else "O'CHIRILDI ❌"
        await q.answer(f"O'chirilgan auto-chiqarish: {state}", show_alert=True)
        d_status = "✅ Yoq" if get_auto_kick_deleted() else "❌ O'ch"
        f_status = "✅ Yoq" if get_auto_kick_foreign() else "❌ O'ch"
        d_lbl = "Yoqilgan ✅" if get_auto_kick_deleted() else "O'chirilgan ❌"
        f_lbl = "Yoqilgan ✅" if get_auto_kick_foreign() else "O'chirilgan ❌"
        await q.edit_message_text(
            "⚙️ <b>Auto-tozala sozlamalari</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗑 O'chirilgan hisoblar: <b>{d_lbl}</b>\n"
            f"🌍 Xorijiy foydalanuvchilar: <b>{f_lbl}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🗑 O'chirilganlar: {d_status}", callback_data="toggle_auto_deleted")],
                [InlineKeyboardButton(f"🌍 Xorijiylar: {f_status}",    callback_data="toggle_auto_foreign")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ]))
        return

    if d == "toggle_auto_foreign":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True); return
        new_val = not get_auto_kick_foreign()
        set_auto_kick_foreign(new_val)
        state = "YOQILDI ✅" if new_val else "O'CHIRILDI ❌"
        await q.answer(f"Xorijiy auto-chiqarish: {state}", show_alert=True)
        d_status = "✅ Yoq" if get_auto_kick_deleted() else "❌ O'ch"
        f_status = "✅ Yoq" if get_auto_kick_foreign() else "❌ O'ch"
        d_lbl = "Yoqilgan ✅" if get_auto_kick_deleted() else "O'chirilgan ❌"
        f_lbl = "Yoqilgan ✅" if get_auto_kick_foreign() else "O'chirilgan ❌"
        await q.edit_message_text(
            "⚙️ <b>Auto-tozala sozlamalari</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🗑 O'chirilgan hisoblar: <b>{d_lbl}</b>\n"
            f"🌍 Xorijiy foydalanuvchilar: <b>{f_lbl}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(f"🗑 O'chirilganlar: {d_status}", callback_data="toggle_auto_deleted")],
                [InlineKeyboardButton(f"🌍 Xorijiylar: {f_status}",    callback_data="toggle_auto_foreign")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ]))
        return

    # ── Obuna tekshiruvi ──
    if d.startswith("check_sub_"):
        gid = int(d.split("_")[-1])
        ch_username, ch_link = get_channel_settings()
        subscribed = await check_subscription(context.bot, user.id)
        if subscribed:
            await q.edit_message_text("✅ Obuna tasdiqlandi! Endi taklif qiling.")
            await handle_invite_button(q, context, gid)
        else:
            await q.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        return

    if d.startswith("check_write_sub_"):
        chat_id = int(d.split("_")[-1])
        subscribed = await check_subscription(context.bot, user.id)
        if subscribed:
            await q.edit_message_text("✅ Obuna tasdiqlandi! Endi guruhda yoza olasiz.")
        else:
            await q.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        return

    # ── Musiqa qidirish ──
    if d == "music_search":
        waiting_for_music[user.id] = True
        await q.message.reply_text(
            "🎵 <b>Qo'shiq nomini yuboring!</b>\n\n"
            "📝 <i>Misol: Shahlo Ahmedova</i>",
            parse_mode=ParseMode.HTML
        )
        return

    # ── Admin panel ──
    if d == "back_admin" or d == "settings":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        await q.edit_message_text(
            "⚙️ <b>Admin Panel</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_kb()
        )
        return

    if d == "stats":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        active, banned, total, today = get_stats()
        groups   = get_active_groups()
        channels = get_all_channels()
        ch_username, _ = get_channel_settings()
        await q.edit_message_text(
            "📊 <b>Statistika</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:      <b>{active}</b>\n"
            f"🚫 Taqiqlangan:        <b>{banned}</b>\n"
            f"💬 Jami xabarlar:      <b>{total}</b>\n"
            f"📅 Bugun:              <b>{today}</b>\n"
            f"🏠 Taklif guruhlari:   <b>{len(groups)} ta</b>\n"
            f"📢 Kuzatilgan kanallar:<b>{len(channels)} ta</b>\n"
            f"👤 Jami foydalanuvchi: <b>{get_total_users()}</b>\n"
            f"🔔 Majburiy kanal:     <b>{ch_username if ch_username else 'Yoq'}</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
        return

    if d.startswith("groups_"):
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        page     = int(d.split("_")[1])
        all_g    = get_all_groups()
        per_page = 5
        start    = page * per_page
        end      = start + per_page
        chunk    = all_g[start:end]
        lines    = [f"👥 <b>Guruhlar ({start+1}-{min(end, len(all_g))} / {len(all_g)})</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
        for g in chunk:
            ban_str = " 🚫" if g[5] else ""
            un = f"@{g[2]}" if g[2] else "—"
            lines.append(f"📌 <b>{g[1]}</b>{ban_str}\n   🆔 <code>{g[0]}</code>  {un}\n")
        rows = []
        nav  = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"groups_{page-1}"))
        if end < len(all_g):
            nav.append(InlineKeyboardButton("➡️", callback_data=f"groups_{page+1}"))
        if nav: rows.append(nav)
        rows.append([InlineKeyboardButton("🔙 Panel", callback_data="back_admin")])
        await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))
        return

    if d == "banned":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT chat_id, title, ban_reason FROM groups WHERE is_banned=1")
        banned_g = c.fetchall(); conn.close()
        if not banned_g:
            await q.edit_message_text("✅ Taqiqlangan guruhlar yo'q.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
            return
        lines = ["🚫 <b>Taqiqlangan guruhlar</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
        for cid, title, reason in banned_g:
            lines.append(f"📌 <b>{title}</b>\n   🆔 <code>{cid}</code>\n   Sabab: {reason or '—'}\n")
        await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
        return

    if d == "check_user_menu":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        context.user_data["action"] = "check_user"
        await q.edit_message_text(
            "🔍 <b>Foydalanuvchi tekshirish</b>\n\nFoydalanuvchi ID sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if d == "broadcast_ask":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        context.user_data["action"] = "broadcast"
        await q.edit_message_text(
            "📢 <b>Broadcast</b>\n\nBarcha guruhlarga yuboriladigan xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return

    if d == "cancel_action":
        context.user_data.pop("action", None)
        await q.edit_message_text("❌ Bekor qilindi.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
        return

    if d == "cancel_session":
        global _temp_pyro_client
        context.user_data.pop("action", None)
        for k in ["session_phone", "session_code_hash", "session_phone_input"]:
            context.user_data.pop(k, None)
        if _temp_pyro_client:
            try: await _temp_pyro_client.disconnect()
            except Exception: pass
            _temp_pyro_client = None
        await q.edit_message_text("❌ Session yaratish bekor qilindi.")
        return

    if d == "how_to_add":
        bot_info = await context.bot.get_me()
        await q.edit_message_text(
            "❓ <b>Botni guruhga qo'shish</b>\n\n"
            "1️⃣ Guruhingizga kiring\n"
            "2️⃣ Guruh nomini bosing → A'zolar\n"
            "3️⃣ A'zo qo'shish → Botni izlang\n"
            f"4️⃣ <b>@{bot_info.username}</b> ni tanlang\n"
            "5️⃣ Botni <b>ADMIN</b> qiling!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_info.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_start")],
            ])
        )
        return

    if d == "contact_admin":
        admin_id = ADMIN_IDS[0] if ADMIN_IDS else None
        if admin_id:
            try:
                admin_info = await context.bot.get_chat(admin_id)
                admin_username = f"@{admin_info.username}" if admin_info.username else f"ID: {admin_id}"
            except Exception:
                admin_username = f"ID: {admin_id}"
        else:
            admin_username = "Admin mavjud emas"
        await q.answer(f"Admin: {admin_username}", show_alert=True)
        return

    if d == "back_to_start":
        bot_info = await context.bot.get_me()
        await q.edit_message_text(
            f"✨ <b>Assalomu alaykum!</b>\n\n🤖 Men <b>{BOT_NAME}</b>man!\n\n👇 Tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=user_kb(bot_info.username)
        )
        return

    if d == "invite_manage_menu":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        await on_callback_invite_manage(q, context)
        return

    if d == "admin_manage":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        await q.edit_message_text(
            "👑 <b>Admin boshqaruvi</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Admin qo'shish", callback_data="ask_admin_chat")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")],
            ])
        )
        return

    if d == "ask_admin_chat":
        context.user_data["action"] = "admin_chat_id"
        await q.edit_message_text(
            "👑 <b>Guruh ID kiriting</b>\n\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="admin_manage")]]))
        return

    if d == "ask_promote":
        context.user_data["action"] = "promote_user"
        chat_id = context.user_data.get("admin_chat_id", "?")
        await q.edit_message_text(
            f"➕ <b>Admin qo'shish</b>\n\nGuruh: <code>{chat_id}</code>\n\n"
            "Foydalanuvchi <b>ID</b>sini yuboring:\n<i>💡 ID: @userinfobot</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="admin_manage")]]))
        return

    if d == "ban_user_menu":
        await q.edit_message_text(
            "🚫 <b>Foydalanuvchini Ban qilish</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ Bot guruhda admin + <b>Ban Users</b> ruxsati kerak!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Guruh ID kiriting", callback_data="ask_ban_user_chat")],
                [InlineKeyboardButton("🔙 Orqaga",            callback_data="back_admin")],
            ]))
        return

    if d == "ask_ban_user_chat":
        context.user_data["action"] = "ban_user_chat_id"
        await q.edit_message_text(
            "🚫 <b>Ban — Guruh ID kiriting</b>\n\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="ban_user_menu")]]))
        return

    if d == "kick_user_menu":
        await q.edit_message_text(
            "👢 <b>Foydalanuvchini Kick qilish</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ Bot guruhda admin + <b>Ban Users</b> ruxsati kerak!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Guruh ID kiriting", callback_data="ask_kick_user_chat")],
                [InlineKeyboardButton("🔙 Orqaga",            callback_data="back_admin")],
            ]))
        return

    if d == "ask_kick_user_chat":
        context.user_data["action"] = "kick_user_chat_id"
        await q.edit_message_text(
            "👢 <b>Kick — Guruh ID kiriting</b>\n\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="kick_user_menu")]]))
        return

    if d == "unban_user_menu":
        await q.edit_message_text(
            "✅ <b>Foydalanuvchini Unban qilish</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "⚠️ Bot guruhda admin + <b>Ban Users</b> ruxsati kerak!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Guruh ID kiriting", callback_data="ask_unban_user_chat")],
                [InlineKeyboardButton("🔙 Orqaga",            callback_data="back_admin")],
            ]))
        return

    if d == "ask_unban_user_chat":
        context.user_data["action"] = "unban_user_chat_id"
        await q.edit_message_text(
            "✅ <b>Unban — Guruh ID kiriting</b>\n\n<i>Misol: -1003835671404</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="unban_user_menu")]]))
        return

    if d == "livestream_menu":
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        groups = get_all_groups()
        active_groups = [(g[0], g[1]) for g in groups if g[5] == 0]
        rows = []
        for cid, title in active_groups[:8]:
            status_icon = "🔴" if get_livestream_status(cid) else "⚫"
            rows.append([InlineKeyboardButton(f"{status_icon} {title[:25]}", callback_data=f"ls_toggle_{cid}")])
        rows.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")])
        await q.edit_message_text(
            "📡 <b>Jonli efir boshqaruvi</b>\n\n🔴 = yoqilgan  |  ⚫ = o'chirilgan",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(rows)
        )
        return

    if d.startswith("ls_toggle_"):
        if not is_admin(user.id):
            await q.answer("❌ Ruxsat yo'q!", show_alert=True)
            return
        cid     = int(d.split("_")[-1])
        current = get_livestream_status(cid)
        set_livestream(cid, not current)
        state = "YOQILDI 🔴" if not current else "O'CHIRILDI ⚫"
        await q.answer(f"Jonli efir {state}")
        return

    if d.startswith("perm_toggle_"):
        parts = d.split("_")
        key = "_".join(parts[2:-2])
        try:
            chat_id_p = int(parts[-2])
            uid_p     = int(parts[-1])
        except Exception:
            return
        selected = context.user_data.get("perm_selected", set())
        if key in selected:
            selected.discard(key)
        else:
            selected.add(key)
        context.user_data["perm_selected"] = selected
        await q.edit_message_reply_markup(reply_markup=get_perm_kb(selected, chat_id_p, uid_p))
        return

    if d.startswith("perm_confirm_"):
        parts = d.split("_")
        try:
            chat_id_p = int(parts[-2])
            uid_p     = int(parts[-1])
        except Exception:
            return
        selected = context.user_data.get("perm_selected", set())
        perms = {k: (k in selected) for k in PERM_LABELS}
        try:
            await context.bot.promote_chat_member(chat_id=chat_id_p, user_id=uid_p, **perms)
            await q.edit_message_text(f"✅ Admin huquqlari saqlandi! ID: <code>{uid_p}</code>", parse_mode=ParseMode.HTML)
        except Exception as e:
            await q.edit_message_text(f"❌ Xato: {e}")
        return


# ═══════════════════════════════════════════════════════
#                    🚀 ISHGA TUSHIRISH
# ═══════════════════════════════════════════════════════
def main():
    global pytgcalls_client, pyrogram_app

    init_db()

    # ── PyTgCalls + Pyrogram ishga tushirish ──
    if PYTGCALLS_AVAILABLE:
        try:
            # ─────────────────────────────────────────────────────────
            #  Session ustuvorligi:
            #  1. SESSION_STRING  (env variable — eng ishonchli)
            #  2. music_session.session  (fayl — lokal ishlatish uchun)
            # ─────────────────────────────────────────────────────────
            session_string = os.environ.get("SESSION_STRING", "").strip()

            # .session_string fayldan ham o'qish
            if not session_string and os.path.exists(".session_string"):
                with open(".session_string") as _f:
                    session_string = _f.read().strip()

            if session_string:
                # String session — server restart bo'lsa ham ishlaydi
                from pyrogram import enums as _pyro_enums
                pyrogram_app = Client(
                    "userbot",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=session_string,
                )
                logger.info("✅ Pyrogram: SESSION_STRING orqali ishga tushmoqda...")

            elif os.path.exists("music_session.session"):
                # Mavjud session fayl
                pyrogram_app = Client(
                    "music_session",
                    api_id=API_ID,
                    api_hash=API_HASH,
                )
                logger.info("✅ Pyrogram: music_session.session fayli topildi!")

            else:
                # Session yo'q — interaktiv yaratish (terminal orqali)
                logger.warning("⚠️ Pyrogram session topilmadi!")
                logger.warning("   Terminal orqali yaratilmoqda...")
                logger.warning("   Telefon raqamingizni kiriting (+998...)")
                pyrogram_app = Client(
                    "music_session",
                    api_id=API_ID,
                    api_hash=API_HASH,
                )

            pytgcalls_client = PyTgCalls(pyrogram_app)

            # Stream tugaganda keyingi qo'shiqni chalish
            @pytgcalls_client.on_stream_end()
            async def on_stream_end(client, update):
                chat_id = update.chat_id
                current = now_playing.get(chat_id)
                if current:
                    try:
                        if os.path.exists(current.get("file", "")):
                            os.remove(current["file"])
                    except Exception:
                        pass
                await _play_next(chat_id)

            logger.info("✅ PyTgCalls tayyor! Voice Chat streaming ishlaydi.")
        except Exception as e:
            logger.error(f"PyTgCalls xatosi: {e}")
            pytgcalls_client = None
            pyrogram_app = None
    else:
        logger.warning("⚠️ PyTgCalls o'rnatilmagan! Faqat fayl yuborish ishlaydi.")

    # ── PTB application ──
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("panel",  cmd_panel))
    app.add_handler(CommandHandler("play",   cmd_play))
    app.add_handler(CommandHandler("music",  cmd_play))
    app.add_handler(CommandHandler("lyrics", cmd_lyrics))
    app.add_handler(CommandHandler("skip",   cmd_skip))
    app.add_handler(CommandHandler("stop",   cmd_stop))
    app.add_handler(CommandHandler("queue",  cmd_queue))
    app.add_handler(CommandHandler("tozala", cmd_tozala))

    app.add_handler(ChatMemberHandler(track_bot,               ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(track_new_member_invite, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app.add_handler(CallbackQueryHandler(on_callback))

    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_admin_pm
    ))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
        handle_group_message
    ))
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & (filters.VOICE | filters.VIDEO_NOTE | filters.VIDEO) & ~filters.COMMAND,
        handle_group_message
    ))

    if app.job_queue:
        app.job_queue.run_repeating(send_group_invite_message, interval=INVITE_INTERVAL, first=30)
    else:
        logger.warning("job_queue mavjud emas!")

    ch_username, _ = get_channel_settings()
    logger.info("=" * 65)
    logger.info(f"🚀 {BOT_NAME} ISHGA TUSHDI!")
    logger.info(f"🎵 Voice Chat streaming: {'✅ HAY' if PYTGCALLS_AVAILABLE and pytgcalls_client else '❌ YOQ (fallback)'}")
    logger.info(f"🎵 Buyruqlar: /play /skip /stop /queue")
    logger.info(f"🔔 Majburiy kanal: {ch_username or 'Ornatilmagan'}")
    logger.info(f"👥 Yozish uchun taklif: {REQUIRED_INVITES} ta do'st")
    logger.info("=" * 65)

    # ── Ikkalasini parallel ishga tushirish ──
    async def run_all():
        if pytgcalls_client and pyrogram_app:
            await pyrogram_app.start()
            await pytgcalls_client.start()

            # ─── String session chiqarish (birinchi marta) ───
            if not os.environ.get("SESSION_STRING"):
                try:
                    from pyrogram import Client as _C
                    exported = await pyrogram_app.export_session_string()
                    me = await pyrogram_app.get_me()
                    logger.info("=" * 65)
                    logger.info(f"✅ Pyrogram: {me.first_name} (@{me.username}) sifatida ulandi!")
                    logger.info("")
                    logger.info("🔑 SESSION_STRING (serverda ishlatish uchun saqlang):")
                    logger.info(f"SESSION_STRING={exported}")
                    logger.info("")
                    logger.info("💡 Bu qatorni .env faylga yoki server env'ga qo'shing!")
                    logger.info("=" * 65)
                except Exception as e:
                    logger.error(f"Session string export xatosi: {e}")

        await app.initialize()
        await app.start()
        await app.updater.start_polling(allowed_updates=Update.ALL_TYPES)
        import signal
        stop_event = asyncio.Event()
        def _stop(*_):
            stop_event.set()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                asyncio.get_event_loop().add_signal_handler(sig, _stop)
            except Exception:
                pass
        await stop_event.wait()
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        if pytgcalls_client and pyrogram_app:
            await pytgcalls_client.stop()
            await pyrogram_app.stop()

    asyncio.run(run_all())


if __name__ == "__main__":
    main()
