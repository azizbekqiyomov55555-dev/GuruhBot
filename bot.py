# ╔══════════════════════════════════════════════════════════════════════╗
# ║   🤖 YORDAMCHI + TEKSHIRISH + 🎵 MUSIQA BOT — BIRLASHTIRILGAN v2  ║
# ║   ✅ /start bosgan foydalanuvchilarni saqlash                      ║
# ║   ✅ Admin panel — foydalanuvchini ID bo'yicha tekshirish          ║
# ║   ✅ Foydalanuvchi ismi, ID, guruhlari, yozgan guruhlari           ║
# ║   ✅ Obuna bo'lgan kanallar (bot admin bo'lgan kanallar)           ║
# ║   ✅ Guruhda yozish uchun kanalga OBUNA bo'lish shart              ║
# ║   ✅ Guruhda yozish uchun 2 DO'ST TAKLIF qilish shart             ║
# ║   ✅ Har 2 daqiqada taklif xabari                                   ║
# ║   ✅ Taklif qilgan odam maqtaladi                                   ║
# ║   ✅ JONLI EFIR boshqaruvi (yoqish/o'chirish)                      ║
# ║   ✅ So'kingan foydalanuvchini avtomatik MUTE qilish               ║
# ║   ✅ Admin qo'shishda HUQUQLARNI SO'RASH (inline tanlov)           ║
# ║   ✅ Foydalanuvchini BAN / KICK / UNBAN qilish                     ║
# ║   ✅ Pastki menyu tugmalari (ReplyKeyboard)                        ║
# ║   🎵 /play [qo'shiq nomi] — YouTube'dan musiqa yuklash            ║
# ║   🎵 Guruhga yangi a'zo qo'shilganda musiqa xabari                ║
# ║   🎵 Guruhda /play buyrug'i bilan musiqa izlash                    ║
# ╚══════════════════════════════════════════════════════════════════════╝
#
# 💡 ISHGA TUSHIRISH:
#   pip install python-telegram-bot==20.7 yt-dlp
#   sudo apt install ffmpeg   (Linux) yoki ffmpeg.org (Windows)
#
# ⚙️ BOT SOZLAMALARI (@BotFather):
#   1. Bot Settings → Group Privacy → DISABLE
#   2. Botni guruhga ADMIN qiling
#   3. Admin ruxsatlari: ✅ Invite Users, ✅ Add Members,
#      ✅ Delete Messages, ✅ Restrict Members,
#      ✅ Promote Members, ✅ Ban Users

import logging
import sqlite3
import asyncio
import random
import urllib.parse
import os
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


# ═══════════════════════════════════════════════════════
#                    ⚙️ ASOSIY SOZLAMALAR
# ═══════════════════════════════════════════════════════
BOT_TOKEN        = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"   # ← @BotFather dan olingan token
ADMIN_IDS        = [8537782289]                  # ← O'z admin ID ingizni kiriting
BOT_NAME         = "@GuruhYordamchIUZBBOT"
INVITE_INTERVAL  = 120   # sekund (har 2 daqiqada taklif xabari)
REQUIRED_INVITES = 2     # guruhda yozish uchun kerakli taklif soni
MUTE_DURATION    = 10    # daqiqa (so'kingan odamni mute qilish muddati)

INVITE_MESSAGE = (
    "👋 <b>Assalom aleykum birodarlar!</b>\n\n"
    "🏆 Do'stlaringizni guruhga taklif qiling!\n"
    "Kim ko'p odam qo'shsa — guruh qahramoni bo'ladi! 💪\n\n"
    "👇 Tugmani bosing va taklif qiling!"
)

# Xotirada saqlanadigan taklif linklari: link → (user_id, user_name, chat_id)
invite_links_db: dict = {}

# Musiqa kutish holati: user_id → True
waiting_for_music: dict = {}


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
#   🎵 MUSIQA FUNKSIYALARI
# ═══════════════════════════════════════════════════════
async def download_and_send_music(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """YouTube'dan musiqa yuklab yuboradi"""
    msg = await update.message.reply_text(
        f"🔍 <b>{query}</b> — izlanmoqda...",
        parse_mode=ParseMode.HTML
    )

    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": "/tmp/%(title)s.%(ext)s",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch1",
            "noplaylist": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await msg.edit_text(
                f"⏳ <b>{query}</b> — yuklanmoqda...",
                parse_mode=ParseMode.HTML
            )
            info = ydl.extract_info(query, download=True)

            if "entries" in info:
                info = info["entries"][0]

            title    = info.get("title", query)
            duration = info.get("duration", 0)
            uploader = info.get("uploader", "Noma'lum")

            filename = ydl.prepare_filename(info)
            mp3_file = filename.rsplit(".", 1)[0] + ".mp3"

            if not os.path.exists(mp3_file):
                for ext in [".mp3", ".m4a", ".webm", ".opus"]:
                    test_file = filename.rsplit(".", 1)[0] + ext
                    if os.path.exists(test_file):
                        mp3_file = test_file
                        break

            if not os.path.exists(mp3_file):
                await msg.edit_text("❌ Fayl topilmadi. Boshqa nom bilan urinib ko'ring.")
                return

            file_size = os.path.getsize(mp3_file) / (1024 * 1024)
            if file_size > 49:
                await msg.edit_text("❌ Fayl juda katta (50MB dan ortiq). Boshqa qo'shiq tanlang.")
                os.remove(mp3_file)
                return

            minutes = duration // 60
            seconds = duration % 60

            caption = (
                f"🎵 <b>{title}</b>\n"
                f"👤 {uploader}\n"
                f"⏱ {minutes}:{seconds:02d}\n\n"
                f"🤖 {BOT_NAME}"
            )

            await msg.edit_text(
                f"📤 <b>{title}</b> — jo'natilmoqda...",
                parse_mode=ParseMode.HTML
            )

            with open(mp3_file, "rb") as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=title,
                    performer=uploader,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )

            os.remove(mp3_file)
            await msg.delete()

    except Exception as e:
        logger.error(f"Musiqa yuklab olishda xato: {e}")
        await msg.edit_text(
            f"❌ <b>{query}</b> topilmadi yoki xato yuz berdi.\n\n"
            "💡 Boshqa nom bilan urinib ko'ring!\n"
            "📝 <i>Misol: /play Ulug'bek Rahmatullayev</i>",
            parse_mode=ParseMode.HTML
        )


async def cmd_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/play buyrug'i — musiqa izlash"""
    if not context.args:
        await update.message.reply_text(
            "🎵 <b>Qo'shiq nomini kiriting!</b>\n\n"
            "📝 <b>Misol:</b> <code>/play Shahlo Ahmedova</code>\n"
            "🔗 YouTube URL ham ishlaydi:\n"
            "<code>/play https://youtube.com/...</code>",
            parse_mode=ParseMode.HTML
        )
        return

    query = " ".join(context.args)
    await download_and_send_music(update, context, query)


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
        groups = get_active_groups()
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
            "🎵 <b>Musiqa tinglash:</b>\n"
            "  👉 /play [qo'shiq nomi]\n\n"
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
            # Guruhga qo'shilganda salom + musiqa xabari
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"🎵 <b>Assalomu alaykum! Men {BOT_NAME}man!</b> 🎵\n\n"
                        f"✅ Guruhingizga qo'shildim!\n\n"
                        f"🎶 <b>Musiqa tinglash uchun:</b>\n"
                        f"  👉 /play [qo'shiq nomi]\n\n"
                        f"🛡 <b>Guruh himoyasi:</b>\n"
                        f"  ✅ So'kinish filtri\n"
                        f"  ✅ Obuna tekshiruvi\n"
                        f"  ✅ Do'st taklif tizimi\n\n"
                        f"🎵 <i>Musiqa bilan hayot go'zal!</i>"
                    ),
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎵 Musiqa Izla", callback_data="music_search")],
                    ])
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
            logger.info(f"✅ Kanalga admin qo'shildi: {chat.title} ({chat.id})")
            # Kanalga qo'shilganda xabar
            try:
                await context.bot.send_message(
                    chat_id=chat.id,
                    text=(
                        f"🎵 <b>{BOT_NAME} kanalingizga qo'shildi!</b>\n\n"
                        f"✅ Endi bu kanal obuna tekshiruvida ishlatilishi mumkin.\n\n"
                        f"🎶 /play [qo'shiq nomi] — Musiqa yuklash"
                    ),
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass


# ── Yangi a'zo guruhga qo'shilganda ──
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot: continue
        update_user_seen(member)
        save_user_in_group(member.id, update.effective_chat.id)
        add_group(update.effective_chat.id, update.effective_chat.title, update.effective_chat.username)

        mn = f'<a href="tg://user?id={member.id}">{member.first_name}</a>'
        ch_username, ch_link = get_channel_settings()
        invite_count = get_user_invite_count(update.effective_chat.id, member.id)
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
                + "\n\n🎶 <b>Musiqa tinglash:</b> /play [qo'shiq nomi]"
            )
            btns = []
            if ch_username and ch_link:
                btns.append([InlineKeyboardButton(f"📢 {ch_username} — Obuna", url=ch_link)])
            if not get_invite_disabled(update.effective_chat.id):
                btns.append([InlineKeyboardButton("➕ Do'st taklif qilish",
                                                  callback_data=f"invite_{update.effective_chat.id}")])
            btns.append([InlineKeyboardButton("🎵 Musiqa Izla", callback_data="music_search")])
            await update.message.reply_text(
                greet_text, parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btns) if btns else None
            )
        else:
            music_greets = [
                f"🎵 Xush kelibsiz {mn}! Musiqa tinglash uchun /play yozing! 😊🌟",
                f"👋 Salom {mn}! Guruhimizga marhamat! 🎊 /play bilan musiqa eshiting!",
                f"✨ {mn} bilan guruh yanada jonlandi! 💫 🎵 /play [qo'shiq nomi]",
            ]
            await update.message.reply_text(
                random.choice(music_greets),
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎵 Musiqa Izla", callback_data="music_search")]
                ])
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
        # Oddiy foydalanuvchi — musiqa izlash uchun kutish holati
        text = update.message.text or ""
        if waiting_for_music.get(user.id):
            waiting_for_music[user.id] = False
            await download_and_send_music(update, context, text)
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
            "📡 <b>Jonli efir boshqaruvi</b>\n\nGuruh ID sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Guruh tanlash", callback_data="livestream_menu")],
                [InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")],
            ]))
        return

    if text == "🔗 Taklif boshqaruv":
        await on_callback_invite_manage(update, context)
        return

    # ── Amallar (action) ──
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
        uname_str = f"@{info['username']}" if info['username'] else "—"
        groups_str = "\n".join(
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
        group_ids = get_active_groups()
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
                f"✅ <b>Kanal saqlandi!</b>\n\n📢 {uname}\n🔗 {link}",
                parse_mode=ParseMode.HTML
            )
        else:
            await update.message.reply_text("❌ Ikkala qatorda yozing:\n1-qator: @kanal_username\n2-qator: https://t.me/kanal")
        return

    if action == "admin_chat_id":
        context.user_data["action"] = "promote_user"
        context.user_data["admin_chat_id"] = text.strip()
        await update.message.reply_text(
            f"👑 Guruh ID: <code>{text.strip()}</code>\n\nEndi foydalanuvchi ID sini yuboring:",
            parse_mode=ParseMode.HTML
        )
        return

    if action == "promote_user":
        context.user_data.pop("action", None)
        chat_id = context.user_data.get("admin_chat_id")
        try:
            uid = int(text.strip())
            await context.bot.promote_chat_member(
                chat_id=int(chat_id), user_id=uid,
                can_manage_chat=True, can_delete_messages=True,
                can_restrict_members=True, can_invite_users=True,
            )
            await update.message.reply_text(f"✅ <code>{uid}</code> admin qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "ban_user_chat_id":
        context.user_data["action"] = "ban_user_id"
        context.user_data["ban_chat_id"] = text.strip()
        await update.message.reply_text(
            f"🚫 Guruh: <code>{text.strip()}</code>\n\nEndi ban qilinadigan foydalanuvchi ID sini yuboring:",
            parse_mode=ParseMode.HTML
        )
        return

    if action == "ban_user_id":
        context.user_data.pop("action", None)
        chat_id = context.user_data.get("ban_chat_id")
        try:
            uid = int(text.strip())
            await context.bot.ban_chat_member(chat_id=int(chat_id), user_id=uid)
            await update.message.reply_text(f"✅ <code>{uid}</code> ban qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "kick_user_chat_id":
        context.user_data["action"] = "kick_user_id"
        context.user_data["kick_chat_id"] = text.strip()
        await update.message.reply_text(
            f"👢 Guruh: <code>{text.strip()}</code>\n\nEndi kick qilinadigan foydalanuvchi ID sini yuboring:",
            parse_mode=ParseMode.HTML
        )
        return

    if action == "kick_user_id":
        context.user_data.pop("action", None)
        chat_id = context.user_data.get("kick_chat_id")
        try:
            uid = int(text.strip())
            await context.bot.ban_chat_member(chat_id=int(chat_id), user_id=uid)
            await asyncio.sleep(1)
            await context.bot.unban_chat_member(chat_id=int(chat_id), user_id=uid)
            await update.message.reply_text(f"✅ <code>{uid}</code> kick qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "unban_user_chat_id":
        context.user_data["action"] = "unban_user_id"
        context.user_data["unban_chat_id"] = text.strip()
        await update.message.reply_text(
            f"✅ Guruh: <code>{text.strip()}</code>\n\nEndi unban qilinadigan foydalanuvchi ID sini yuboring:",
            parse_mode=ParseMode.HTML
        )
        return

    if action == "unban_user_id":
        context.user_data.pop("action", None)
        chat_id = context.user_data.get("unban_chat_id")
        try:
            uid = int(text.strip())
            await context.bot.unban_chat_member(chat_id=int(chat_id), user_id=uid)
            await update.message.reply_text(f"✅ <code>{uid}</code> unban qilindi!", parse_mode=ParseMode.HTML)
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return

    if action == "invite_disable_chat_id":
        context.user_data.pop("action", None)
        try:
            cid = int(text.strip())
            current = get_invite_disabled(cid)
            set_invite_disabled(cid, not current)
            state = "O'CHIRILDI ❌" if not current else "YOQILDI ✅"
            await update.message.reply_text(
                f"🔗 Guruh <code>{cid}</code> uchun taklif: <b>{state}</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Xato: {e}")
        return


async def on_callback_invite_manage(update_or_query, context):
    """Taklif boshqaruvi — tugma yoki matn orqali"""
    groups = get_all_groups()
    active_groups = [(g[0], g[1]) for g in groups if g[5] == 0]
    text = "🔗 <b>Taklif Boshqaruvi</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
    text += "✅ = taklif YOQIQ  |  ❌ = taklif O'CHIQ\n\n"
    rows = []
    for cid, title in active_groups[:8]:
        inv_off = get_invite_disabled(cid)
        icon = "❌" if inv_off else "✅"
        rows.append([InlineKeyboardButton(f"{icon} {title[:25]}", callback_data=f"inv_toggle_{cid}")])
    rows.append([InlineKeyboardButton("📝 ID kiritish", callback_data="inv_enter_id")])
    rows.append([InlineKeyboardButton("🔙 Orqaga",      callback_data="back_admin")])
    if hasattr(update_or_query, 'message'):
        await update_or_query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))
    else:
        await update_or_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))


# ═══════════════════════════════════════════════════════
#   🔘 CALLBACK QUERY HANDLER
# ═══════════════════════════════════════════════════════
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q: return
    await q.answer()
    d = q.data or ""
    user = q.from_user

    # ── Musiqa izlash ──
    if d == "music_search":
        waiting_for_music[user.id] = True
        await q.message.reply_text(
            "🎵 <b>Qo'shiq nomini yozing:</b>\n\n"
            "📝 <i>Misol: Ulug'bek Rahmatullayev</i>\n"
            "🔗 <i>Yoki YouTube URL ham ishlaydi</i>",
            parse_mode=ParseMode.HTML
        )
        return

    # ── Taklif tugmasi ──
    if d.startswith("invite_"):
        gid = int(d.split("_", 1)[1])
        await handle_invite_button(q, context, gid)
        return

    # ── Obuna tekshirish ──
    if d.startswith("check_sub_"):
        gid = int(d.split("_")[-1])
        ch_username, ch_link = get_channel_settings()
        is_sub = await check_subscription(context.bot, user.id)
        if is_sub:
            await q.edit_message_text(
                f"✅ <b>{user.first_name}, obuna tasdiqlandi!</b>\n\n"
                "Endi guruhda do'st taklif qilishingiz mumkin! 🎉",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Do'st taklif qilish", callback_data=f"invite_{gid}")],
                ])
            )
        else:
            await q.answer("❌ Siz hali obuna bo'lmagansiz!", show_alert=True)
        return

    # ── Guruhda yozish — obuna tekshirish ──
    if d.startswith("check_write_sub_"):
        chat_id = int(d.split("_")[-1])
        is_sub = await check_subscription(context.bot, user.id)
        if is_sub:
            await q.edit_message_text(
                f"✅ <b>{user.first_name}, obuna tasdiqlandi!</b>\n\nEndi guruhda yozishingiz mumkin! 🎉",
                parse_mode=ParseMode.HTML
            )
        else:
            await q.answer("❌ Siz hali obuna bo'lmagansiz!", show_alert=True)
        return

    # ── Taklif toggle ──
    if d.startswith("inv_toggle_"):
        cid = int(d.split("_")[-1])
        current = get_invite_disabled(cid)
        set_invite_disabled(cid, not current)
        state = "O'CHIRILDI ❌" if not current else "YOQILDI ✅"
        await q.answer(f"Taklif {state}")
        await on_callback_invite_manage(q, context)
        return

    if d == "inv_enter_id":
        context.user_data["action"] = "invite_disable_chat_id"
        await q.edit_message_text(
            "🔗 <b>Taklif boshqaruv — Guruh ID kiriting</b>\n\n"
            "Guruh ID sini yuboring:\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="invite_manage_menu")]]))
        return

    # ── Admin panel tugmalari ──
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
        groups = get_active_groups()
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
        page = int(d.split("_")[1])
        all_g = get_all_groups()
        per_page = 5
        start = page * per_page
        end   = start + per_page
        chunk = all_g[start:end]
        lines = [f"👥 <b>Guruhlar ({start+1}-{min(end, len(all_g))} / {len(all_g)})</b>\n━━━━━━━━━━━━━━━━━━━━\n"]
        for g in chunk:
            ban_str = " 🚫" if g[5] else ""
            un = f"@{g[2]}" if g[2] else "—"
            lines.append(f"📌 <b>{g[1]}</b>{ban_str}\n   🆔 <code>{g[0]}</code>  {un}\n")
        rows = []
        nav = []
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
        await q.edit_message_text("❌ Bekor qilindi.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
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

    # ── Admin manage ──
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

    # ── Ban/Kick/Unban ──
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

    # ── Livestream ──
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
        cid = int(d.split("_")[-1])
        current = get_livestream_status(cid)
        set_livestream(cid, not current)
        state = "YOQILDI 🔴" if not current else "O'CHIRILDI ⚫"
        await q.answer(f"Jonli efir {state}")
        return

    # ─ Perm toggle ──
    if d.startswith("perm_toggle_"):
        parts = d.split("_")
        key = "_".join(parts[2:-2])
        try:
            chat_id_p = int(parts[-2])
            uid_p = int(parts[-1])
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
            uid_p = int(parts[-1])
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
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Commandlar
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("panel",  cmd_panel))
    app.add_handler(CommandHandler("play",   cmd_play))      # 🎵 MUSIQA
    app.add_handler(CommandHandler("music",  cmd_play))      # 🎵 /music ham ishlaydi
    app.add_handler(CommandHandler("help",   cmd_play))      # /help — play ga yo'naltirish

    # Bot guruh/kanalga qo'shilganda
    app.add_handler(ChatMemberHandler(track_bot,               ChatMemberHandler.MY_CHAT_MEMBER))
    # Yangi a'zo taklif tracking
    app.add_handler(ChatMemberHandler(track_new_member_invite, ChatMemberHandler.CHAT_MEMBER))
    # Yangi a'zo xush kelibsiz
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    # Callback tugmalar
    app.add_handler(CallbackQueryHandler(on_callback))

    # Admin private xabarlar (va oddiy foydalanuvchi musiqa izlashi)
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        handle_admin_pm
    ))

    # Guruh: matnli xabarlar
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
        handle_group_message
    ))
    # Guruh: ovozli/video xabarlar (jonli efir bloki uchun)
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & (filters.VOICE | filters.VIDEO_NOTE | filters.VIDEO) & ~filters.COMMAND,
        handle_group_message
    ))

    # Har INVITE_INTERVAL sekundda taklif xabari
    app.job_queue.run_repeating(send_group_invite_message, interval=INVITE_INTERVAL, first=30)

    ch_username, _ = get_channel_settings()
    logger.info("=" * 65)
    logger.info(f"🚀 {BOT_NAME} ISHGA TUSHDI! (Birlashtirilgan v2 + Musiqa)")
    logger.info(f"🎵 Musiqa buyruq:       /play [nom]")
    logger.info(f"🔔 Majburiy kanal:      {ch_username or 'Ornatilmagan'}")
    logger.info(f"👥 Yozish uchun taklif: {REQUIRED_INVITES} ta do'st")
    logger.info(f"🔇 Mute muddati:        {MUTE_DURATION} daqiqa")
    logger.info("=" * 65)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
