# ╔══════════════════════════════════════════════════════════════════╗
# ║        🤖 YORDAMCHI BOT — VERSIYA v11                          ║
# ║   ✅ Admin panel orqali kanal o'rnatish/o'chirish              ║
# ║   ✅ Guruhda yozish uchun kanalga OBUNA bo'lish shart          ║
# ║   ✅ Guruhda yozish uchun 2 DO'ST TAKLIF qilish shart         ║
# ║   ✅ Chat ID avtomatik aniqlanadi                               ║
# ║   ✅ Har 2 daqiqada taklif xabari                               ║
# ║   ✅ Taklif qilgan odam maqtaladi                               ║
# ║   ✅ JONLI EFIR boshqaruvi (yoqish/o'chirish)                  ║
# ║   ✅ So'kingan foydalanuvchini avtomatik MUTE qilish           ║
# ║   ✅ So'kingan odamga "so'kinma" deydi guruhda                 ║
# ║   ✅ Jonli efirda so'kingan odamni MUTE + ogohlantirish        ║
# ║   ✅ Jonli efirda ovozli/video xabar blok                      ║
# ║   ✅ Admin qo'shishda HUQUQLARNI SO'RASH (inline tanlov)       ║
# ║   ✅ Guruhga odam qo'shishni O'CHIRISH/YOQISH (admin panel)   ║
# ║   ✅ Foydalanuvchini BAN qilish (guruhdan chiqarish)           ║
# ║   ✅ Foydalanuvchini KICK qilish (chiqarib yuborish)           ║
# ║   ✅ Foydalanuvchini UNBAN qilish                               ║
# ║   ✅ Admin panel orqali guruhga ADMIN qo'shish/o'chirish       ║
# ║   ✅ Pastki menyu tugmalari (ReplyKeyboard)                    ║
# ╚══════════════════════════════════════════════════════════════════╝
#
# 💡 ISHGA TUSHIRISH:
#   pip install python-telegram-bot==20.7
#
# ⚙️ BOT SOZLAMALARI (@BotFather):
#   1. Bot Settings → Group Privacy → DISABLE
#   2. Botni guruhga ADMIN qiling
#   3. Admin ruxsatlari: ✅ Invite Users, ✅ Add Members,
#      ✅ Delete Messages, ✅ Restrict Members,
#      ✅ Promote Members ← MUHIM! (Admin qo'shish uchun)
#      ✅ Ban Users ← MUHIM! (Ban/Kick uchun)
#   4. Botni kanalga ham ADMIN qiling (obuna tekshirish uchun)

import logging
import sqlite3
import asyncio
import random
import urllib.parse
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


# ═══════════════════════════════════════════════════════
#                    ⚙️ ASOSIY SOZLAMALAR
# ═══════════════════════════════════════════════════════
BOT_TOKEN        = "8780908767:AAEewN-jTc2_19hUZRu9mf-qudBTKM2A8Gk"
ADMIN_IDS        = [8537782289]
BOT_NAME         = "Yordamchi Bot"
INVITE_INTERVAL  = 120
REQUIRED_INVITES = 2
MUTE_DURATION    = 10  # daqiqa

INVITE_MESSAGE = (
    "👋 <b>Assalom aleykum birodarlar!</b>\n\n"
    "🏆 Do'stlaringizni guruhga taklif qiling!\n"
    "Kim ko'p odam qo'shsa — guruh qahramoni bo'ladi! 💪\n\n"
    "👇 Tugmani bosing va taklif qiling!"
)

invite_links_db: dict = {}  # link → (user_id, user_name, chat_id)

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
        chat_id INTEGER PRIMARY KEY,
        title TEXT,
        username TEXT,
        member_count INTEGER DEFAULT 0,
        added_date TEXT,
        is_banned INTEGER DEFAULT 0,
        ban_reason TEXT DEFAULT '',
        invite_active INTEGER DEFAULT 1,
        livestream_active INTEGER DEFAULT 0,
        invite_disabled INTEGER DEFAULT 0)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        user_id INTEGER,
        username TEXT,
        date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT DEFAULT '')""")
    c.execute("""CREATE TABLE IF NOT EXISTS user_invites (
        chat_id INTEGER,
        user_id INTEGER,
        invite_count INTEGER DEFAULT 0,
        PRIMARY KEY (chat_id, user_id))""")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_username', '')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('channel_link', '')")
    # Migration: ustunlar mavjud bo'lmasa qo'shamiz
    for col in ["livestream_active INTEGER DEFAULT 0", "invite_disabled INTEGER DEFAULT 0"]:
        try:
            c.execute(f"ALTER TABLE groups ADD COLUMN {col}")
        except Exception:
            pass
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect("bot_data.db")

def get_channel_settings() -> tuple:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key='channel_username'")
    row1 = c.fetchone()
    c.execute("SELECT value FROM settings WHERE key='channel_link'")
    row2 = c.fetchone()
    conn.close()
    return (row1[0] if row1 else "", row2[0] if row2 else "")

def save_channel_settings(username: str, link: str):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE settings SET value=? WHERE key='channel_username'", (username,))
    c.execute("UPDATE settings SET value=? WHERE key='channel_link'", (link,))
    conn.commit(); conn.close()

def clear_channel_settings():
    save_channel_settings("", "")

def set_livestream(chat_id: int, active: bool):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET livestream_active=? WHERE chat_id=?", (1 if active else 0, chat_id))
    conn.commit(); conn.close()

def get_livestream_status(chat_id: int) -> bool:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT livestream_active FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close()
    return bool(row and row[0])

def set_invite_disabled(chat_id: int, disabled: bool):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET invite_disabled=? WHERE chat_id=?", (1 if disabled else 0, chat_id))
    conn.commit(); conn.close()

def get_invite_disabled(chat_id: int) -> bool:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT invite_disabled FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close()
    return bool(row and row[0])

def get_user_invite_count(chat_id: int, user_id: int) -> int:
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT invite_count FROM user_invites WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    row = c.fetchone(); conn.close()
    return row[0] if row else 0

def increment_user_invite(chat_id: int, user_id: int) -> int:
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT INTO user_invites (chat_id, user_id, invite_count)
                 VALUES (?, ?, 1)
                 ON CONFLICT(chat_id, user_id)
                 DO UPDATE SET invite_count = invite_count + 1""", (chat_id, user_id))
    conn.commit()
    c.execute("SELECT invite_count FROM user_invites WHERE chat_id=? AND user_id=?", (chat_id, user_id))
    new_count = c.fetchone()[0]
    conn.close()
    return new_count

def add_group(chat_id, title, username):
    conn = get_db(); c = conn.cursor()
    c.execute("""INSERT OR IGNORE INTO groups
        (chat_id, title, username, added_date, invite_active)
        VALUES (?, ?, ?, ?, 1)""",
        (chat_id, title, username or "", datetime.now().strftime("%Y-%m-%d %H:%M")))
    c.execute("UPDATE groups SET title=?, username=? WHERE chat_id=?",
              (title, username or "", chat_id))
    conn.commit(); conn.close()

def ban_group(chat_id, reason=""):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=1, ban_reason=? WHERE chat_id=?", (reason, chat_id))
    conn.commit(); conn.close()

def unban_group(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("UPDATE groups SET is_banned=0, ban_reason='' WHERE chat_id=?", (chat_id,))
    conn.commit(); conn.close()

def is_banned(chat_id):
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT is_banned FROM groups WHERE chat_id=?", (chat_id,))
    row = c.fetchone(); conn.close()
    return row and row[0] == 1

def get_all_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id, title, username, member_count, added_date, is_banned, ban_reason FROM groups")
    rows = c.fetchall(); conn.close()
    return rows

def get_active_groups():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT chat_id FROM groups WHERE is_banned=0 AND invite_active=1")
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]

def get_stats():
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=0"); active = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM groups WHERE is_banned=1"); banned = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages"); total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM messages WHERE date >= date('now')"); today = c.fetchone()[0]
    conn.close()
    return active, banned, total, today

def log_message(chat_id, user_id, username):
    conn = get_db(); c = conn.cursor()
    c.execute("INSERT INTO messages (chat_id, user_id, username, date) VALUES (?, ?, ?, ?)",
              (chat_id, user_id, username, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit(); conn.close()


# ═══════════════════════════════════════════════════════
#                    🛠️ YORDAMCHILAR
# ═══════════════════════════════════════════════════════
logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(uid):
    return uid in ADMIN_IDS

def admin_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Statistika",        callback_data="stats"),
         InlineKeyboardButton("👥 Guruhlar",          callback_data="groups_0")],
        [InlineKeyboardButton("🚫 Taqiqlangan",       callback_data="banned"),
         InlineKeyboardButton("⚙️ Sozlamalar",        callback_data="settings")],
        [InlineKeyboardButton("📢 Broadcast",         callback_data="broadcast_ask")],
        [InlineKeyboardButton("🔔 Kanal sozlash",     callback_data="channel_manage")],
        [InlineKeyboardButton("📡 Jonli efir",        callback_data="livestream_menu")],
        [InlineKeyboardButton("👑 Admin boshqaruv",   callback_data="admin_manage")],
        [InlineKeyboardButton("🚫 Foydalanuvchi ban",  callback_data="ban_user_menu"),
         InlineKeyboardButton("👢 Foydalanuvchi kick", callback_data="kick_user_menu")],
        [InlineKeyboardButton("✅ Foydalanuvchi unban", callback_data="unban_user_menu")],
        [InlineKeyboardButton("🔗 Taklif boshqaruv",  callback_data="invite_manage_menu")],
    ])

def admin_reply_kb():
    return ReplyKeyboardMarkup([
        ["🛠 Admin Panel",    "📊 Statistika"],
        ["🚫 Foydalanuvchi ban", "👢 Foydalanuvchi kick"],
        ["✅ Foydalanuvchi unban", "👑 Admin qo'sh"],
        ["📢 Broadcast", "🔔 Kanal sozlash", "📡 Jonli efir"],
        ["🔗 Taklif boshqaruv"],
    ], resize_keyboard=True, input_field_placeholder="Amalni tanlang...")

def user_kb(bot_username):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Guruhga qo'shish", url=f"https://t.me/{bot_username}?startgroup=true")],
        [InlineKeyboardButton("❓ Qo'llanma",        callback_data="how_to_add")],
        [InlineKeyboardButton("🆘 Adminga yozish",   callback_data="contact_admin")],
    ])

# Admin huquqlari uchun checkbox-style klaviatura
PERM_LABELS = {
    "can_manage_chat":      "🔧 Guruhni boshqarish",
    "can_delete_messages":  "🗑 Xabarlarni o'chirish",
    "can_restrict_members": "🔇 Foydalanuvchini cheklash",
    "can_invite_users":     "🔗 Odam taklif qilish",
    "can_pin_messages":     "📌 Xabarni pin qilish",
    "can_manage_video_chats": "📡 Video chatni boshqarish",
    "can_promote_members":  "👑 Admin qo'shish",
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


# ═══════════════════════════════════════════════════════
#   🔔 OBUNA TEKSHIRUVI
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
            try:
                await msg.delete()
            except Exception:
                pass
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
        try:
            await msg.delete()
        except Exception:
            pass
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

async def safe_delete(msg):
    try:
        await msg.delete()
    except Exception:
        pass


# ═══════════════════════════════════════════════════════
#   🔇 SO'KINISH — AVTOMATIK MUTE + OGOHLANTIRISH
# ═══════════════════════════════════════════════════════
async def mute_user_for_swearing(bot, chat_id: int, user, message_id: int):
    until = datetime.now() + timedelta(minutes=MUTE_DURATION)
    user_mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
    try:
        await bot.restrict_chat_member(
            chat_id=chat_id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=until
        )
        # So'kinmang deydi guruhda
        warning = random.choice(SWEAR_WARNINGS)
        warning_text = warning.replace("{name}", user_mention).replace("{dur}", str(MUTE_DURATION))
        sent = await bot.send_message(
            chat_id=chat_id,
            text=(
                f"{warning_text}\n\n"
                f"⏰ Mute tugaydi: <b>{until.strftime('%H:%M')}</b>"
            ),
            parse_mode=ParseMode.HTML
        )
        logger.info(f"🔇 Mute: {user.first_name} ({user.id}) chat={chat_id}")
        await asyncio.sleep(15)
        try:
            await sent.delete()
        except Exception:
            pass
    except TelegramError as e:
        logger.error(f"Mute xatosi: {e}")


# ═══════════════════════════════════════════════════════
#   👥 TAKLIF TUGMASI
# ═══════════════════════════════════════════════════════
async def handle_invite_button(query, context: ContextTypes.DEFAULT_TYPE, gid: int):
    user = query.from_user
    ch_username, ch_link = get_channel_settings()

    # Guruhda taklif o'chirilgan bo'lsa
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
#   🎉 YANGI A'ZO TRACKING
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
#   📢 HAR 2 DAQIQADA XABAR
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
                conn = get_db(); c = conn.cursor()
                c.execute("UPDATE groups SET invite_active=0 WHERE chat_id=?", (gid,))
                conn.commit(); conn.close()
            else:
                logger.error(f"Taklif xabari xato ({gid}): {e}")
        except Exception as e:
            logger.error(f"Taklif xabari xato ({gid}): {e}")


# ═══════════════════════════════════════════════════════
#                     📨 ASOSIY HANDLERLAR
# ═══════════════════════════════════════════════════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    user     = update.effective_user
    bot_info = await context.bot.get_me()
    if is_admin(user.id):
        active, banned, total, today = get_stats()
        groups = get_active_groups()
        await update.message.reply_text(
            f"👑 Xush kelibsiz, <b>{user.first_name}</b>!\n\n"
            f"🤖 <b>{BOT_NAME}</b> — Admin Panel\n\n"
            f"📊 <b>Holat:</b>\n"
            f"  ✅ Faol guruhlar:  <b>{active}</b>\n"
            f"  🚫 Taqiqlangan:    <b>{banned}</b>\n"
            f"  💬 Jami xabarlar:  <b>{total}</b>\n"
            f"  📅 Bugun:          <b>{today}</b>\n"
            f"  🏠 Taklif guruhi:  <b>{len(groups)} ta</b>\n\n"
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
        await update.message.reply_text(
            f"✨ <b>Assalomu alaykum, {user.first_name}!</b>\n\n"
            f"🤖 Men <b>{BOT_NAME}</b>man!\n\n"
            "🎯 <b>Guruhda yozish uchun:</b>\n"
            f"  1️⃣ Kanalga obuna bo'ling\n"
            f"  2️⃣ {REQUIRED_INVITES} ta do'st taklif qiling\n"
            f"  3️⃣ Shundan keyin erkin yozasiz! ✅\n\n"
            "👇 Tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=user_kb(bot_info.username)
        )

async def cmd_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    await update.message.reply_text("🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML, reply_markup=admin_reply_kb())
    await update.message.reply_text("⬇️ <b>Barcha funksiyalar:</b>", parse_mode=ParseMode.HTML, reply_markup=admin_kb())

async def track_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = update.my_chat_member
    if not r: return
    chat   = r.chat
    status = r.new_chat_member.status
    if chat.type in ("group", "supergroup"):
        if status in (ChatMember.MEMBER, ChatMember.ADMINISTRATOR):
            add_group(chat.id, chat.title, chat.username)
        elif status in (ChatMember.LEFT, ChatMember.BANNED):
            conn = get_db(); c = conn.cursor()
            c.execute("UPDATE groups SET invite_active=0 WHERE chat_id=?", (chat.id,))
            conn.commit(); conn.close()

async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.is_bot: continue
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
                f"🎉 Xush kelibsiz {mn}!\n\n"
                f"📋 <b>Guruhda yozish uchun:</b>\n"
                + "\n".join(steps)
            )
            btns = []
            if ch_username and ch_link:
                btns.append([InlineKeyboardButton(f"📢 {ch_username} — Obuna", url=ch_link)])
            if not get_invite_disabled(update.effective_chat.id):
                btns.append([InlineKeyboardButton("➕ Do'st taklif qilish",
                                                  callback_data=f"invite_{update.effective_chat.id}")])
            await update.message.reply_text(
                greet_text, parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(btns) if btns else None
            )
        else:
            greets = [
                f"🎉 Xush kelibsiz {mn}! 😊🌟",
                f"👋 Salom {mn}! Guruhimizga marhamat! 🎊",
                f"✨ {mn} bilan guruh yanada jonlandi! 💫",
            ]
            await update.message.reply_text(random.choice(greets), parse_mode=ParseMode.HTML)


# ═══════════════════════════════════════════════════════
#   💬 GURUH XABARLARI
# ═══════════════════════════════════════════════════════
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg  = update.message
    if not user or not msg or chat.type not in ("group", "supergroup"):
        return
    if is_banned(chat.id):
        return
    add_group(chat.id, chat.title, chat.username)

    text = msg.text or ""

    # Jonli efir yoqilganda ovozli/video xabarlarni bloklash
    if not is_admin(user.id) and get_livestream_status(chat.id):
        if msg.voice or msg.video_note or msg.video:
            try:
                await msg.delete()
            except Exception:
                pass
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
                try:
                    await sent.delete()
                except Exception:
                    pass
            except Exception:
                pass
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
#   ✉️ ADMIN XABARLAR (private)
# ═══════════════════════════════════════════════════════
async def handle_admin_pm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id) or update.effective_chat.type != "private":
        return
    text = update.message.text or ""

    # ReplyKeyboard tugmalari
    if text == "🛠 Admin Panel":
        await update.message.reply_text("🛠 <b>Admin Panel</b>", parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        return
    if text == "📊 Statistika":
        active, banned, total, today = get_stats()
        groups = get_active_groups()
        ch_username, _ = get_channel_settings()
        await update.message.reply_text(
            "📊 <b>Statistika</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:    <b>{active}</b>\n"
            f"🚫 Taqiqlangan:      <b>{banned}</b>\n"
            f"💬 Jami xabarlar:    <b>{total}</b>\n"
            f"📅 Bugun:            <b>{today}</b>\n"
            f"🏠 Taklif guruhi:    <b>{len(groups)} ta</b>\n"
            f"🔔 Kanal:            <b>{ch_username if ch_username else 'Yoq'}</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
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
            "👑 <b>Guruh ID kiriting</b>\n\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="admin_manage")]]))
        return
    if text == "📢 Broadcast":
        context.user_data["action"] = "broadcast"
        groups = [g for g in get_all_groups() if g[5] == 0]
        await update.message.reply_text(
            f"📢 <b>Broadcast</b>\n\nGuruhlar: <b>{len(groups)}</b>\n\n✍️ Xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))
        return
    if text == "🔔 Kanal sozlash":
        ch_username, ch_link = get_channel_settings()
        status_text = (
            f"✅ <b>Faol kanal:</b> {ch_username}\n🔗 {ch_link}" if ch_username
            else "❌ <b>Kanal o'rnatilmagan</b>"
        )
        await update.message.reply_text(
            f"🔔 <b>Kanal Boshqaruvi</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{status_text}\n\n👇 Amalni tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Kanal o'rnatish / o'zgartirish", callback_data="channel_set")],
                [InlineKeyboardButton("🗑 Kanalni o'chirish",              callback_data="channel_clear")],
                [InlineKeyboardButton("🔙 Orqaga",                         callback_data="back_admin")],
            ]))
        return
    if text == "📡 Jonli efir":
        await update.message.reply_text("📡 Jonli efir:", parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📡 Jonli efir menyu", callback_data="livestream_menu")]]))
        return
    if text == "🔗 Taklif boshqaruv":
        await update.message.reply_text("🔗 Taklif boshqaruvi:", parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Taklif menyu", callback_data="invite_manage_menu")]]))
        return

    # ── Action ishlovchilari ──
    action = context.user_data.get("action")

    if action == "set_channel":
        raw = text.strip()
        if not raw.startswith("@") and not raw.startswith("-"):
            raw = "@" + raw
        link = f"https://t.me/{raw.lstrip('@')}"
        save_channel_settings(raw, link)
        context.user_data.pop("action", None)
        await update.message.reply_text(
            f"✅ <b>Kanal o'rnatildi!</b>\n\n📢 Username: <b>{raw}</b>\n🔗 {link}\n\n"
            f"⚠️ Botni shu kanalga <b>Admin</b> qiling!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Kanal menyu", callback_data="channel_manage")]]))

    elif action == "ban_id":
        try:
            cid = int(text.strip())
            ban_group(cid, "Admin taqiqladi")
            context.user_data.pop("action", None)
            await update.message.reply_text(f"✅ Guruh <code>{cid}</code> taqiqlandi!", parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")

    elif action == "unban_id":
        try:
            cid = int(text.strip())
            unban_group(cid)
            context.user_data.pop("action", None)
            await update.message.reply_text(f"✅ Guruh <code>{cid}</code> tiklandi!", parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID!")

    elif action == "broadcast":
        groups  = [g for g in get_all_groups() if g[5] == 0]
        sent = failed = 0
        for g in groups:
            try:
                await context.bot.send_message(g[0], f"📢 <b>E'lon:</b>\n\n{text}", parse_mode=ParseMode.HTML)
                sent += 1
            except Exception:
                failed += 1
        context.user_data.pop("action", None)
        await update.message.reply_text(f"📢 <b>Yuborildi!</b>\n✅ {sent} ta\n❌ {failed} ta", parse_mode=ParseMode.HTML, reply_markup=admin_kb())

    elif action == "livestream_set_chat":
        raw = text.strip()
        try:
            cid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri ID! Qayta kiriting:")
            return
        context.user_data["ls_chat_id"] = cid
        context.user_data.pop("action", None)
        status = get_livestream_status(cid)
        status_text = "✅ YOQIQ" if status else "❌ O'CHIQ"
        await update.message.reply_text(
            f"📡 <b>Jonli Efir — Guruh:</b> <code>{cid}</code>\nHozirgi holat: <b>{status_text}</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Yoqish",   callback_data=f"ls_on_{cid}")],
                [InlineKeyboardButton("⏹ O'chirish", callback_data=f"ls_off_{cid}")],
                [InlineKeyboardButton("🔙 Orqaga",   callback_data="livestream_menu")],
            ]))

    elif action == "admin_chat_id":
        raw = text.strip()
        try:
            cid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri guruh ID!")
            return
        context.user_data["admin_chat_id"] = cid
        context.user_data.pop("action", None)
        await update.message.reply_text(
            f"✅ Guruh tanlandi: <code>{cid}</code>\n\nNima qilmoqchisiz?",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Admin qo'shish",   callback_data="ask_promote")],
                [InlineKeyboardButton("➖ Admin o'chirish",  callback_data="ask_demote")],
                [InlineKeyboardButton("🔙 Orqaga",           callback_data="admin_manage")],
            ]))

    elif action == "promote_user":
        raw = text.strip()
        try:
            uid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri foydalanuvchi ID!")
            return
        chat_id = context.user_data.get("admin_chat_id")
        if not chat_id:
            await update.message.reply_text("❌ Avval guruh ID sini kiriting.")
            context.user_data.pop("action", None)
            return
        context.user_data["promote_uid"] = uid
        context.user_data.pop("action", None)
        # Huquqlarni so'rash
        context.user_data["perm_selected"] = set(PERM_LABELS.keys())  # default: hammasi
        await update.message.reply_text(
            f"👑 <b>Admin huquqlarini tanlang</b>\n\n"
            f"Guruh: <code>{chat_id}</code>\n"
            f"Foydalanuvchi: <code>{uid}</code>\n\n"
            f"✅ = beriladi  |  ☐ = berilmaydi\n"
            f"Bosib yoqing/o'chiring, keyin <b>Tasdiqlash</b>ni bosing:",
            parse_mode=ParseMode.HTML,
            reply_markup=get_perm_kb(context.user_data["perm_selected"], chat_id, uid))

    elif action == "demote_user":
        raw = text.strip()
        try:
            uid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri foydalanuvchi ID!")
            return
        chat_id = context.user_data.get("admin_chat_id")
        if not chat_id:
            await update.message.reply_text("❌ Avval guruh ID sini kiriting.")
            context.user_data.pop("action", None)
            return
        try:
            await context.bot.promote_chat_member(
                chat_id=chat_id, user_id=uid,
                can_manage_chat=False, can_delete_messages=False,
                can_restrict_members=False, can_invite_users=False,
                can_pin_messages=False, can_manage_video_chats=False,
                can_promote_members=False,
            )
            context.user_data.pop("action", None)
            await update.message.reply_text(
                f"✅ Foydalanuvchi <code>{uid}</code> guruh <code>{chat_id}</code>dan <b>ADMIN</b> olib tashlandi!",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
        except TelegramError as e:
            await update.message.reply_text(f"❌ Xato: <code>{e}</code>", parse_mode=ParseMode.HTML)

    elif action == "ban_user_chat_id":
        raw = text.strip()
        try:
            cid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri guruh ID!")
            return
        context.user_data["ban_chat_id"] = cid
        context.user_data["action"] = "ban_user_id"
        await update.message.reply_text(
            f"🚫 <b>Ban — Guruh:</b> <code>{cid}</code>\n\nFoydalanuvchi <b>ID</b>sini yuboring:\n<i>💡 ID: @userinfobot</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="ban_user_menu")]]))

    elif action == "ban_user_id":
        raw = text.strip()
        try:
            uid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri foydalanuvchi ID!")
            return
        chat_id = context.user_data.get("ban_chat_id")
        if not chat_id:
            await update.message.reply_text("❌ Avval guruh ID sini kiriting.")
            context.user_data.pop("action", None)
            return
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=uid)
            context.user_data.pop("action", None)
            context.user_data.pop("ban_chat_id", None)
            await update.message.reply_text(
                f"✅ <b>Foydalanuvchi BAN qilindi!</b>\n\n👤 User ID: <code>{uid}</code>\n🏠 Guruh ID: <code>{chat_id}</code>",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
            logger.info(f"🚫 BAN: user={uid} chat={chat_id}")
        except TelegramError as e:
            err_str = str(e)
            if "CHAT_ADMIN_REQUIRED" in err_str or "chat_admin_required" in err_str.lower():
                await update.message.reply_text(
                    "❌ <b>Xato:</b> Bot guruhda admin bo'lishi va <b>«Ban Users»</b> ruxsati bo'lishi kerak!",
                    parse_mode=ParseMode.HTML)
            else:
                await update.message.reply_text(f"❌ Xato: <code>{e}</code>", parse_mode=ParseMode.HTML)

    elif action == "kick_user_chat_id":
        raw = text.strip()
        try:
            cid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri guruh ID!")
            return
        context.user_data["kick_chat_id"] = cid
        context.user_data["action"] = "kick_user_id"
        await update.message.reply_text(
            f"👢 <b>Kick — Guruh:</b> <code>{cid}</code>\n\nFoydalanuvchi <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="kick_user_menu")]]))

    elif action == "kick_user_id":
        raw = text.strip()
        try:
            uid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri foydalanuvchi ID!")
            return
        chat_id = context.user_data.get("kick_chat_id")
        if not chat_id:
            await update.message.reply_text("❌ Avval guruh ID sini kiriting.")
            context.user_data.pop("action", None)
            return
        try:
            await context.bot.ban_chat_member(chat_id=chat_id, user_id=uid)
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=uid)
            context.user_data.pop("action", None)
            context.user_data.pop("kick_chat_id", None)
            await update.message.reply_text(
                f"✅ <b>Foydalanuvchi KICK qilindi!</b>\n\n👤 User ID: <code>{uid}</code>\n🏠 Guruh ID: <code>{chat_id}</code>",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
            logger.info(f"👢 KICK: user={uid} chat={chat_id}")
        except TelegramError as e:
            await update.message.reply_text(f"❌ Xato: <code>{e}</code>", parse_mode=ParseMode.HTML)

    elif action == "unban_user_chat_id":
        raw = text.strip()
        try:
            cid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri guruh ID!")
            return
        context.user_data["unban_chat_id"] = cid
        context.user_data["action"] = "unban_user_id"
        await update.message.reply_text(
            f"✅ <b>Unban — Guruh:</b> <code>{cid}</code>\n\nFoydalanuvchi <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="unban_user_menu")]]))

    elif action == "unban_user_id":
        raw = text.strip()
        try:
            uid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri foydalanuvchi ID!")
            return
        chat_id = context.user_data.get("unban_chat_id")
        if not chat_id:
            await update.message.reply_text("❌ Avval guruh ID sini kiriting.")
            context.user_data.pop("action", None)
            return
        try:
            await context.bot.unban_chat_member(chat_id=chat_id, user_id=uid, only_if_banned=True)
            context.user_data.pop("action", None)
            context.user_data.pop("unban_chat_id", None)
            await update.message.reply_text(
                f"✅ <b>Foydalanuvchi UNBAN qilindi!</b>\n\n👤 User ID: <code>{uid}</code>\n🏠 Guruh ID: <code>{chat_id}</code>",
                parse_mode=ParseMode.HTML, reply_markup=admin_kb())
            logger.info(f"✅ UNBAN: user={uid} chat={chat_id}")
        except TelegramError as e:
            await update.message.reply_text(f"❌ Xato: <code>{e}</code>", parse_mode=ParseMode.HTML)

    elif action == "invite_disable_chat_id":
        raw = text.strip()
        try:
            cid = int(raw)
        except ValueError:
            await update.message.reply_text("❌ Noto'g'ri guruh ID!")
            return
        context.user_data.pop("action", None)
        disabled = get_invite_disabled(cid)
        new_state = not disabled
        set_invite_disabled(cid, new_state)
        state_text = "O'CHIRILDI ❌" if new_state else "YOQILDI ✅"
        await update.message.reply_text(
            f"🔗 Guruh <code>{cid}</code>da taklif funksiyasi <b>{state_text}</b>",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════
#   🔘 CALLBACK HANDLER
# ═══════════════════════════════════════════════════════
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q        = update.callback_query
    await q.answer()
    d        = q.data
    uid      = q.from_user.id
    bot_info = await context.bot.get_me()

    # ── Taklif tugmasi ──
    if d.startswith("invite_"):
        gid = int(d.split("_")[1])
        await handle_invite_button(q, context, gid)
        return

    # ── Obuna tekshirish (taklif uchun) ──
    if d.startswith("check_sub_"):
        gid = int(d.split("_")[2])
        user = q.from_user
        ch_username, ch_link = get_channel_settings()
        subscribed = await check_subscription(context.bot, user.id)
        if subscribed:
            await q.answer("✅ Obuna tasdiqlandi!", show_alert=False)
            await handle_invite_button(q, context, gid)
        else:
            await q.answer("❌ Siz hali obuna bo'lmadingiz!", show_alert=True)
        return

    # ── Guruhda yozish uchun obuna tekshirish ──
    if d.startswith("check_write_sub_"):
        chat_id = int(d.split("_")[3])
        user = q.from_user
        subscribed = await check_subscription(context.bot, user.id)
        if subscribed:
            await q.answer("✅ Obuna tasdiqlandi! Endi yoza olasiz.", show_alert=True)
            try: await q.message.delete()
            except Exception: pass
        else:
            await q.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)
        return

    # ── Jonli efir yoqish ──
    if d.startswith("ls_on_"):
        cid = int(d.split("_")[2])
        set_livestream(cid, True)
        await q.edit_message_text(
            f"📡 <b>Jonli efir YOQILDI!</b>\n\nGuruh: <code>{cid}</code>\n\n✅ Ovozli/video xabarlar bloklanadi.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("⏹ O'chirish",  callback_data=f"ls_off_{cid}")],
                [InlineKeyboardButton("🔙 Orqaga",    callback_data="livestream_menu")],
            ]))
        try:
            await context.bot.send_message(
                chat_id=cid,
                text="📡 <b>Jonli efir rejimi YOQILDI! 🔴</b>\n\nOvozli va video xabar yuborish vaqtincha taqiqlangan.",
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    if d.startswith("ls_off_"):
        cid = int(d.split("_")[2])
        set_livestream(cid, False)
        await q.edit_message_text(
            f"📡 <b>Jonli efir O'CHIRILDI!</b>\n\nGuruh: <code>{cid}</code>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Yoqish",    callback_data=f"ls_on_{cid}")],
                [InlineKeyboardButton("🔙 Orqaga",    callback_data="livestream_menu")],
            ]))
        try:
            await context.bot.send_message(
                chat_id=cid,
                text="📡 <b>Jonli efir rejimi O'CHIRILDI.</b>\nEndi ovozli xabar yuborishingiz mumkin.",
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    # ── Jonli efir toggle ──
    if d.startswith("ls_toggle_"):
        cid = int(d.split("_")[2])
        current = get_livestream_status(cid)
        new_status = not current
        set_livestream(cid, new_status)
        icon = "🔴 YOQILDI" if new_status else "⚫ O'CHIRILDI"
        await q.answer(f"📡 Jonli efir {icon}!", show_alert=True)
        try:
            await context.bot.send_message(
                chat_id=cid,
                text=f"📡 <b>Jonli efir {icon}!</b>",
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        groups = get_all_groups()
        active_ls = [(g[0], g[1]) for g in groups if g[5] == 0]
        rows = []
        for gcid, title in active_ls[:8]:
            ls_on = get_livestream_status(gcid)
            icon2 = "🔴" if ls_on else "⚫"
            rows.append([InlineKeyboardButton(f"{icon2} {title[:25]}", callback_data=f"ls_toggle_{gcid}")])
        rows.append([InlineKeyboardButton("📝 ID kiritish", callback_data="ls_enter_id")])
        rows.append([InlineKeyboardButton("🔙 Orqaga",      callback_data="back_admin")])
        try:
            await q.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            pass
        return

    if d == "ls_enter_id":
        context.user_data["action"] = "livestream_set_chat"
        await q.edit_message_text(
            "📡 <b>Jonli Efir — Guruh ID kiriting</b>\n\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="livestream_menu")]]))
        return

    # ── Admin huquq toggle ──
    if d.startswith("perm_toggle_"):
        # perm_toggle_{key}_{chat_id}_{user_id}
        parts = d.split("_", 4)
        # parts: ['perm', 'toggle', key_parts..., chat_id, user_id]
        # Chunki key ham _ bor: qayta parse qilamiz
        rest = d[len("perm_toggle_"):]
        # oxirgi 2 ta _ bo'lakni chat_id va user_id deb olamiz
        tokens = rest.rsplit("_", 2)
        key_name = tokens[0]
        try:
            perm_chat_id = int(tokens[1])
            perm_user_id = int(tokens[2])
        except Exception:
            await q.answer("Xato!", show_alert=True)
            return
        selected = context.user_data.get("perm_selected", set(PERM_LABELS.keys()))
        if key_name in selected:
            selected.discard(key_name)
        else:
            selected.add(key_name)
        context.user_data["perm_selected"] = selected
        try:
            await q.edit_message_reply_markup(reply_markup=get_perm_kb(selected, perm_chat_id, perm_user_id))
        except Exception:
            pass
        return

    if d.startswith("perm_confirm_"):
        rest = d[len("perm_confirm_"):]
        tokens = rest.rsplit("_", 1)
        try:
            perm_chat_id = int(tokens[0])
            perm_user_id = int(tokens[1])
        except Exception:
            await q.answer("Xato!", show_alert=True)
            return
        selected = context.user_data.get("perm_selected", set())
        kwargs = {k: (k in selected) for k in PERM_LABELS.keys()}
        try:
            await context.bot.promote_chat_member(
                chat_id=perm_chat_id,
                user_id=perm_user_id,
                **kwargs
            )
            context.user_data.pop("perm_selected", None)
            context.user_data.pop("promote_uid", None)
            perms_given = [PERM_LABELS[k] for k in selected]
            perms_text  = "\n".join(f"  ✅ {p}" for p in perms_given) if perms_given else "  (hech qanday)"
            await q.edit_message_text(
                f"✅ <b>Admin qo'shildi!</b>\n\n"
                f"👤 User: <code>{perm_user_id}</code>\n"
                f"🏠 Guruh: <code>{perm_chat_id}</code>\n\n"
                f"<b>Berilgan huquqlar:</b>\n{perms_text}",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Panel", callback_data="back_admin")]]))
            logger.info(f"👑 PROMOTE: user={perm_user_id} chat={perm_chat_id} perms={selected}")
        except TelegramError as e:
            err_str = str(e)
            if "CHAT_ADMIN_REQUIRED" in err_str or "chat_admin_required" in err_str.lower():
                await q.edit_message_text(
                    "❌ <b>Xato: Chat_admin_required</b>\n\n"
                    "Bot guruhda admin bo'lishi va <b>«Add New Admins»</b> ruxsati bo'lishi kerak!",
                    parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_manage")]]))
            else:
                await q.edit_message_text(f"❌ Xato: <code>{e}</code>", parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="admin_manage")]]))
        return

    # ── Contact/How ──
    if d == "contact_admin":
        await q.edit_message_text(
            "🆘 <b>Adminga murojaat</b>\n\n📩 Quyidagi tugmani bosing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📩 Adminga yozish", url=f"tg://user?id={ADMIN_IDS[0]}")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ]))
        return

    if d == "back_user":
        await q.edit_message_text(
            f"✨ <b>🤖 {BOT_NAME}</b>\n\n👇 Tanlang:",
            parse_mode=ParseMode.HTML, reply_markup=user_kb(bot_info.username))
        return

    if d == "how_to_add":
        await q.edit_message_text(
            "📖 <b>Botni guruhga qo'shish</b>\n\n"
            "1️⃣ «Guruhga qo'shish» tugmasini bosing\n"
            "2️⃣ Ro'yxatdan guruhingizni tanlang\n"
            "3️⃣ Tasdiqlang\n"
            "4️⃣ Guruh sozlamalari → Adminlar → Botni toping\n"
            "5️⃣ <b>Barcha ruxsatlarni bering</b>\n\n"
            "✅ Tayyor!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Guruhga qo'shish",
                                     url=f"https://t.me/{bot_info.username}?startgroup=true")],
                [InlineKeyboardButton("🔙 Orqaga", callback_data="back_user")],
            ]))
        return

    # ── Adminlik tekshiruvi (quyidagilar faqat admin uchun) ──
    if not is_admin(uid):
        await q.answer("❌ Ruxsat yo'q!", show_alert=True)
        return

    # ══ KANAL BOSHQARUVI ══
    if d == "channel_manage":
        ch_username, ch_link = get_channel_settings()
        status_text = (
            f"✅ <b>Faol kanal:</b> {ch_username}\n🔗 {ch_link}" if ch_username
            else "❌ <b>Kanal o'rnatilmagan</b>"
        )
        await q.edit_message_text(
            f"🔔 <b>Kanal Boshqaruvi</b>\n━━━━━━━━━━━━━━━━━━━━\n\n{status_text}\n\n👇 Amalni tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Kanal o'rnatish / o'zgartirish", callback_data="channel_set")],
                [InlineKeyboardButton("🗑 Kanalni o'chirish",              callback_data="channel_clear")],
                [InlineKeyboardButton("🔙 Orqaga",                         callback_data="back_admin")],
            ]))
        return

    if d == "channel_set":
        context.user_data["action"] = "set_channel"
        await q.edit_message_text(
            "📢 <b>Kanal o'rnatish</b>\n\nKanal username'ini yuboring:\n<i>Misol: @mening_kanalim</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="channel_manage")]]))
        return

    if d == "channel_clear":
        clear_channel_settings()
        await q.edit_message_text(
            "🗑 <b>Kanal o'chirildi!</b>\n\nEndi obuna tekshiruvi o'chiq.",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Kanal menyu", callback_data="channel_manage")],
                [InlineKeyboardButton("🏠 Bosh sahifa",  callback_data="back_admin")],
            ]))
        return

    # ══ JONLI EFIR MENYU ══
    if d == "livestream_menu":
        groups = get_all_groups()
        active_ls = [(g[0], g[1]) for g in groups if g[5] == 0]
        text = "📡 <b>Jonli Efir Boshqaruvi</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
        text += "🔴 = YOQIQ  |  ⚫ = O'CHIQ\n\n"
        rows = []
        for cid, title in active_ls[:8]:
            ls_on = get_livestream_status(cid)
            icon  = "🔴" if ls_on else "⚫"
            rows.append([InlineKeyboardButton(f"{icon} {title[:25]}", callback_data=f"ls_toggle_{cid}")])
        rows.append([InlineKeyboardButton("📝 ID kiritish", callback_data="ls_enter_id")])
        rows.append([InlineKeyboardButton("🔙 Orqaga",      callback_data="back_admin")])
        await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))
        return

    # ══ ADMIN BOSHQARUV ══
    if d == "admin_manage":
        await q.edit_message_text(
            "👑 <b>Admin Boshqaruvi</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            "Bot orqali guruhga admin qo'shish yoki o'chirish.\n\n"
            "⚠️ Bot o'zi guruhda <b>Admin</b> bo'lishi kerak!\n"
            "Ruxsat: <b>Promote Members</b> ✅",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Guruh ID kiriting", callback_data="ask_admin_chat")],
                [InlineKeyboardButton("🔙 Orqaga",            callback_data="back_admin")],
            ]))
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

    if d == "ask_demote":
        context.user_data["action"] = "demote_user"
        chat_id = context.user_data.get("admin_chat_id", "?")
        await q.edit_message_text(
            f"➖ <b>Admin o'chirish</b>\n\nGuruh: <code>{chat_id}</code>\n\nFoydalanuvchi <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="admin_manage")]]))
        return

    # ══ BAN USER MENYU ══
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

    # ══ KICK USER MENYU ══
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

    # ══ UNBAN USER MENYU ══
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

    # ══ TAKLIF BOSHQARUVI ══
    if d == "invite_manage_menu":
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
        await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))
        return

    if d.startswith("inv_toggle_"):
        cid = int(d.split("_")[2])
        current = get_invite_disabled(cid)
        new_state = not current
        set_invite_disabled(cid, new_state)
        state_text = "O'CHIRILDI ❌" if new_state else "YOQILDI ✅"
        await q.answer(f"🔗 Taklif {state_text}!", show_alert=True)
        # menyuni yangilash
        groups = get_all_groups()
        active_groups = [(g[0], g[1]) for g in groups if g[5] == 0]
        rows = []
        for gcid, title in active_groups[:8]:
            inv_off = get_invite_disabled(gcid)
            icon = "❌" if inv_off else "✅"
            rows.append([InlineKeyboardButton(f"{icon} {title[:25]}", callback_data=f"inv_toggle_{gcid}")])
        rows.append([InlineKeyboardButton("📝 ID kiritish", callback_data="inv_enter_id")])
        rows.append([InlineKeyboardButton("🔙 Orqaga",      callback_data="back_admin")])
        try:
            await q.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(rows))
        except Exception:
            pass
        return

    if d == "inv_enter_id":
        context.user_data["action"] = "invite_disable_chat_id"
        await q.edit_message_text(
            "🔗 <b>Taklif boshqaruv — Guruh ID kiriting</b>\n\n"
            "Guruh ID sini yuboring (taklif holati almashtiriladi):\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="invite_manage_menu")]]))
        return

    # ══ STATISTIKA ══
    if d == "stats":
        active, banned, total, today = get_stats()
        groups = get_active_groups()
        ch_username, _ = get_channel_settings()
        await q.edit_message_text(
            "📊 <b>Statistika</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ Faol guruhlar:    <b>{active}</b>\n"
            f"🚫 Taqiqlangan:      <b>{banned}</b>\n"
            f"💬 Jami xabarlar:    <b>{total}</b>\n"
            f"📅 Bugun:            <b>{today}</b>\n"
            f"🏠 Taklif guruhi:    <b>{len(groups)} ta</b>\n"
            f"🔔 Kanal:            <b>{ch_username if ch_username else 'Yoq'}</b>\n\n"
            f"🕐 <i>{datetime.now().strftime('%Y-%m-%d %H:%M')}</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]]))

    elif d == "settings":
        groups = get_active_groups()
        ch_username, _ = get_channel_settings()
        await q.edit_message_text(
            "⚙️ <b>Bot Sozlamalari</b>\n━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🤖 Bot nomi:          <b>{BOT_NAME}</b>\n"
            f"👑 Adminlar:          <b>{len(ADMIN_IDS)}</b>\n"
            f"💬 Kalit so'zlar:     <b>{len(RESPONSES)}</b>\n\n"
            f"📢 Taklif xabari:     <b>har {INVITE_INTERVAL} sek</b>\n"
            f"👥 Yozish uchun:      <b>{REQUIRED_INVITES} ta do'st taklif</b>\n"
            f"🔇 Mute muddati:      <b>{MUTE_DURATION} daqiqa</b>\n"
            f"🏠 Faol guruhlar:     <b>{len(groups)} ta</b>\n"
            f"🔔 Majburiy kanal:    <b>{ch_username if ch_username else 'Ornatilmagan'}</b>\n\n"
            "⚡ Barcha funksiyalar faol!",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_admin")]]))

    elif d.startswith("groups_"):
        page   = int(d.split("_")[1])
        groups = [g for g in get_all_groups() if g[5] == 0]
        per_page = 5
        pg = groups[page * per_page:(page + 1) * per_page]
        text = f"👥 <b>Faol Guruhlar</b> — {len(groups)} ta\n━━━━━━━━━━━━━━━━━━━━\n\n" if groups else "👥 Faol guruh yo'q."
        for g in pg:
            cid, title, uname, _, added, _, _ = g
            un = f"@{uname}" if uname else "—"
            inv_off = get_invite_disabled(cid)
            ls_on   = get_livestream_status(cid)
            text += (
                f"📌 <b>{title}</b>\n"
                f"   🆔 <code>{cid}</code>  {un}\n"
                f"   📅 {added}\n"
                f"   🔗 Taklif: {'❌ O\'chiq' if inv_off else '✅ Yoqiq'}  "
                f"📡 Efir: {'🔴 Yoqiq' if ls_on else '⚫ O\'chiq'}\n\n"
            )
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅️", callback_data=f"groups_{page-1}"))
        if (page + 1) * per_page < len(groups):
            nav.append(InlineKeyboardButton("➡️", callback_data=f"groups_{page+1}"))
        rows = []
        if nav: rows.append(nav)
        rows += [
            [InlineKeyboardButton("🚫 Guruh taqiqlash", callback_data="ask_ban")],
            [InlineKeyboardButton("🔙 Orqaga",          callback_data="back_admin")],
        ]
        await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(rows))

    elif d == "banned":
        groups = [g for g in get_all_groups() if g[5] == 1]
        text = f"🚫 <b>Taqiqlangan</b> — {len(groups)} ta\n\n" if groups else "✅ Taqiqlangan guruh yo'q!"
        for g in groups:
            cid, title, _, _, _, _, reason = g
            text += f"🔴 <b>{title}</b>\n   <code>{cid}</code>\n   📝 {reason or '—'}\n\n"
        await q.edit_message_text(text, parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Tiklash", callback_data="ask_unban")],
                [InlineKeyboardButton("🔙 Orqaga",  callback_data="back_admin")],
            ]))

    elif d == "broadcast_ask":
        context.user_data["action"] = "broadcast"
        groups = [g for g in get_all_groups() if g[5] == 0]
        await q.edit_message_text(
            f"📢 <b>Broadcast</b>\n\nGuruhlar: <b>{len(groups)}</b>\n\n✍️ Xabarni yozing:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="back_admin")]]))

    elif d == "ask_ban":
        context.user_data["action"] = "ban_id"
        await q.edit_message_text(
            "🚫 Guruh <b>ID</b>sini yuboring:\n<i>Misol: -1001234567890</i>",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="groups_0")]]))

    elif d == "ask_unban":
        context.user_data["action"] = "unban_id"
        await q.edit_message_text(
            "✅ Tiklanadigan guruh <b>ID</b>sini yuboring:",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Bekor", callback_data="banned")]]))

    elif d == "back_admin":
        active, banned, total, today = get_stats()
        await q.edit_message_text(
            f"🛠 <b>Admin Panel</b> — {BOT_NAME}\n\n"
            f"✅ Faol: <b>{active}</b>  •  🚫 Taqiqlangan: <b>{banned}</b>  •  💬 Xabarlar: <b>{total}</b>",
            parse_mode=ParseMode.HTML, reply_markup=admin_kb())


# ═══════════════════════════════════════════════════════
#                    🚀 ISHGA TUSHIRISH
# ═══════════════════════════════════════════════════════
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("panel", cmd_panel))

    app.add_handler(ChatMemberHandler(track_bot,               ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(track_new_member_invite, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))

    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_admin_pm))

    # Guruh: matnli xabarlar
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, handle_group_message))
    # Guruh: ovozli/video xabarlar (jonli efir bloki uchun)
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & (filters.VOICE | filters.VIDEO_NOTE | filters.VIDEO) & ~filters.COMMAND,
        handle_group_message))

    app.job_queue.run_repeating(send_group_invite_message, interval=INVITE_INTERVAL, first=30)

    ch_username, _ = get_channel_settings()
    logger.info("=" * 60)
    logger.info(f"🚀 {BOT_NAME} ISHGA TUSHDI! (v11)")
    logger.info(f"🔔 Majburiy kanal:     {ch_username or 'Ornatilmagan'}")
    logger.info(f"👥 Yozish uchun taklif: {REQUIRED_INVITES} ta do'st")
    logger.info(f"🔇 Mute muddati:       {MUTE_DURATION} daqiqa")
    logger.info("=" * 60)

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
